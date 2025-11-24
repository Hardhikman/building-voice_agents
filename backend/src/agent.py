import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    tokenize,
    function_tool,
    RunContext
)
from livekit.plugins import murf, silero, google, cartesia, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import json
import os
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("agent")

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self, mcp_client: ClientSession) -> None:
        self.mcp_client = mcp_client
        super().__init__(
            instructions="""You are a supportive, grounded Health & Wellness Voice Companion.
            Your goal is to check in with the user about their mood and intentions for the day.
            
            Structure your conversation:
            1. Ask about their mood and energy levels today.
            2. Ask about 1-3 simple, actionable objectives for the day.
            3. Offer brief, grounded advice or encouragement (non-medical).
            4. Recap their mood and objectives to confirm.
            5. Once confirmed, use the add_log tool to save the entry.
            
            Be warm, empathetic, and concise. Avoid medical diagnoses.""",
        )

    @function_tool
    async def add_log(
        self,
        context: RunContext,
        mood: str,
        objectives: list[str],
        summary: str
    ):
        """Add a new wellness log entry.
        
        Args:
            mood: User's mood.
            objectives: List of objectives.
            summary: Agent's summary.
        """
        try:
            result = await self.mcp_client.call_tool("add_log", arguments={"mood": mood, "objectives": objectives, "summary": summary})
            return str(result)
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            return "Failed to save log."

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Connect to MCP Server
    server_params = StdioServerParameters(
        command="python",
        args=["wellness_db_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Load context from MCP
            context_summary = "This is the first check-in."
            try:
                result = await session.call_tool("get_latest_log", arguments={})
                # Parse the result content
                # MCP returns a list of content items, usually TextContent
                # We need to inspect the structure of result
                # For now, let's assume the tool returns a string in the first content item
                if result and result.content:
                     # result.content is a list of types like TextContent
                     # We assume the first item has the text
                     content_text = result.content[0].text
                     if content_text != "No previous logs found.":
                         log_data = json.loads(content_text)
                         mood = log_data.get('mood', 'unknown')
                         objs = log_data.get('objectives', [])
                         objs_str = ', '.join(objs) if objs else 'none'
                         context_summary = f"Previous check-in on {log_data.get('timestamp', 'unknown')}: Mood was {mood}, Goals were {objs_str}."
            except Exception as e:
                logger.error(f"Failed to load context from MCP: {e}")

            # Update instructions with context
            instructions = f"""You are a supportive, grounded Health & Wellness Voice Companion.
            Your goal is to check in with the user about their mood and intentions for the day.
            
            Context from previous session: {context_summary}
            
            Structure your conversation:
            1. Ask about their mood and energy levels today.
            2. Ask about 1-3 simple, actionable objectives for the day.
            3. Offer brief, grounded advice or encouragement (non-medical).
            4. Recap their mood and objectives to confirm.
            5. Once confirmed, use the add_log tool to save the entry.
            
            Be warm, empathetic, and concise. Avoid medical diagnoses."""

            agent = Assistant(mcp_client=session)
            agent.instructions = instructions

            session_agent = AgentSession(
                stt=cartesia.STT(model="ink-whisper"),
                llm=google.LLM(model="gemini-2.5-flash-lite"),
                tts=murf.TTS(
                    voice="en-US-matthew", 
                    style="Conversation",
                    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                    text_pacing=True
                ),
                turn_detection=MultilingualModel(),
                vad=ctx.proc.userdata["vad"],
                preemptive_generation=True,
            )

            usage_collector = metrics.UsageCollector()

            @session_agent.on("metrics_collected")
            def _on_metrics_collected(ev: MetricsCollectedEvent):
                metrics.log_metrics(ev.metrics)
                usage_collector.collect(ev.metrics)

            async def log_usage():
                summary = usage_collector.get_summary()
                logger.info(f"Usage: {summary}")

            ctx.add_shutdown_callback(log_usage)

            await session_agent.start(
                agent=agent,
                room=ctx.room,
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )

            await ctx.connect()
            
            # Keep the MCP session alive while the agent is running
            # We need to wait until the room is disconnected
            # ctx.connect() returns immediately? No, it waits for connection.
            # But we need to keep the session open.
            # The agent runs in the background.
            # We can wait for the room to disconnect.
            
            # Actually, `ctx.connect()` connects to the room. The agent loop runs inside `session_agent`.
            # We need to prevent the `async with` block from exiting.
            # We can wait on a future that completes when the room disconnects.
            
            # LiveKit JobContext doesn't have a simple "wait until done" method that blocks?
            # Usually the worker keeps running.
            # But here we are inside `entrypoint`. If `entrypoint` returns, the job might end?
            # Or `ctx.connect()` is just the start.
            
            # Let's look at how to keep it alive.
            # We can create a future and resolve it on disconnect.
            
            shutdown_future = asyncio.Future()
            
            @ctx.room.on("disconnected")
            def on_disconnected(reason):
                if not shutdown_future.done():
                    shutdown_future.set_result(None)
            
            await shutdown_future

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
