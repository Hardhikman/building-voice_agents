import logging
import asyncio
import json
import os
import sys
from pathlib import Path
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
    RunContext,
)
from livekit.plugins import murf, silero, google, cartesia, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger("sdr-agent")

load_dotenv(".env.local")


class SDRAgent(Agent):
    """SDR Agent for Razorpay that answers FAQs and collects lead info."""

    def __init__(self, company_data: dict) -> None:
        self.company_data = company_data
        self.lead_info = {}
        
        # Prepare context for the agent
        company_name = company_data["company"]
        description = company_data["description"]
        pricing = json.dumps(company_data["pricing"], indent=2)
        
        super().__init__(
            instructions=f"""You are a friendly and professional Sales Development Representative (SDR) for {company_name}.
            
            Company Description: {description}
            
            Your goals:
            1. Answer user questions about {company_name}, its products, and pricing using the provided tools.
            2. Collect the following lead information naturally during the conversation:
               - Name
               - Company Name
               - Email
               - Role
               - Use Case (what they want to use Razorpay for)
               - Team Size
               - Timeline (when they plan to start)
            
            Guidelines:
            - Be warm, polite, and helpful.
            - Don't interrogate the user. Ask for 1-2 pieces of information at a time, ideally after answering their questions.
            - If asked about pricing, use the pricing information provided.
            - If asked a question you don't know, admit it and offer to connect them with a specialist (which is part of the lead collection).
            - When the user indicates they are done (e.g., "That's all", "Thanks", "I'm done"), summarize what you've discussed and the details you've collected.
            
            Pricing Info:
            {pricing}
            """
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active."""
        # Use a professional voice
        self.session.tts = murf.TTS(
            voice="en-IN-Anisha", # Professional female voice
            style="Promo",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        )
        
        await self.session.generate_reply(
            instructions=f"""Greet the user warmly as an SDR for {self.company_data['company']}. 
            Ask how you can help them today or what brings them to {self.company_data['company']}."""
        )

    @function_tool()
    async def answer_faq(self, context: RunContext, query: str):
        """Search the company FAQ to answer a specific question.
        
        Args:
            query: The user's question or keywords.
        """
        query_lower = query.lower()
        best_match = None
        max_overlap = 0
        
        for faq in self.company_data["faqs"]:
            # Simple keyword matching
            q_words = set(faq["question"].lower().split())
            query_words = set(query_lower.split())
            overlap = len(q_words.intersection(query_words))
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_match = faq
        
        if best_match and max_overlap > 0:
            return f"Here is what I found: {best_match['answer']}"
        else:
            return "I don't have a specific FAQ for that, but I can tell you about our general products and pricing."

    @function_tool()
    async def save_lead_info(self, context: RunContext, 
                             name: str = None, 
                             company: str = None, 
                             email: str = None, 
                             role: str = None, 
                             use_case: str = None, 
                             team_size: str = None, 
                             timeline: str = None):
        """Save collected lead information. Call this whenever the user provides new details.
        
        Args:
            name: User's name
            company: User's company name
            email: User's email address
            role: User's job role
            use_case: What the user wants to use the product for
            team_size: Size of the user's team or company
            timeline: When the user plans to implement
        """
        # Update only provided fields
        if name: self.lead_info["name"] = name
        if company: self.lead_info["company"] = company
        if email: self.lead_info["email"] = email
        if role: self.lead_info["role"] = role
        if use_case: self.lead_info["use_case"] = use_case
        if team_size: self.lead_info["team_size"] = team_size
        if timeline: self.lead_info["timeline"] = timeline
        
        # Save to file immediately (append to list or update current session file)
        # For this task, we'll just keep updating a single file for the current session or append to a log
        # Let's append to a list in lead_data.json
        
        lead_file = Path(__file__).parent.parent / "shared-data" / "lead_data.json"
        
        try:
            if lead_file.exists():
                with open(lead_file, "r") as f:
                    try:
                        all_leads = json.load(f)
                    except json.JSONDecodeError:
                        all_leads = []
            else:
                all_leads = []
            
            # Check if we already have an entry for this session (simplified: just append new or update last if empty)
            # For simplicity in this task, we'll just append a new entry or update the last one if it matches (not robust but fine for demo)
            # Actually, let's just save the current state as a "current_lead"
            
            # Better approach: Read all, find if we are already editing one? No, too complex for stateless.
            # Let's just write the current self.lead_info to a separate file for the current session, 
            # and also append to the main list when "done".
            
            # For the MVP, let's just overwrite a "current_lead.json" for debugging and append to "lead_data.json" on completion.
            # But the instructions say "Store the answers in a JSON file as the user responds."
            
            # Let's just read, append/update.
            # We will assume one active lead for this demo run.
            
            with open(lead_file, "w") as f:
                # We'll just store the current lead info as a single object for this demo file, 
                # or a list of leads. Let's do a list.
                
                # If we are updating, we might want to replace the last one if it's the same person?
                # Let's just append for now, or maybe just write the current lead to a specific file.
                # The task says "Store the answers in a JSON file".
                
                # Let's write to `current_lead.json` for the active session.
                pass

        except Exception as e:
            logger.error(f"Error saving lead info: {e}")
            
        # Write to a persistent file
        target_file = Path(__file__).parent.parent / "shared-data" / "lead_data.json"
        
        # We will read the existing list, and if we have an ID we update, else append.
        # Since we don't have session IDs easily here without more plumbing, 
        # let's just write the CURRENT lead to a file `active_lead.json` which satisfies "Store... as user responds"
        # and we can append to a history file at the end.
        
        active_file = Path(__file__).parent.parent / "shared-data" / "active_lead.json"
        with open(active_file, "w") as f:
            json.dump(self.lead_info, f, indent=2)
            
        return "Information saved."

    @function_tool()
    async def end_call_and_summarize(self, context: RunContext):
        """End the call, provide a verbal summary, and save the final lead data."""
        
        summary_text = f"Thanks for chatting! I've noted that you are {self.lead_info.get('name', 'there')} "
        if self.lead_info.get('company'):
            summary_text += f"from {self.lead_info['company']}. "
        
        summary_text += "We'll be in touch soon."
        
        # Save to permanent history
        history_file = Path(__file__).parent.parent / "shared-data" / "lead_data.json"
        all_leads = []
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    all_leads = json.load(f)
            except:
                pass
        
        all_leads.append(self.lead_info)
        with open(history_file, "w") as f:
            json.dump(all_leads, f, indent=2)
            
        return summary_text


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    # Load company data
    data_path = Path(__file__).parent.parent / "shared-data" / "company_data.json"
    try:
        with open(data_path, "r") as f:
            company_data = json.load(f)
        logger.info(f"Loaded company data for {company_data.get('company')}")
    except Exception as e:
        logger.error(f"Failed to load company data: {e}")
        company_data = {"company": "Unknown", "description": "", "pricing": {}, "faqs": []}

    # Create the SDR agent
    agent = SDRAgent(company_data=company_data)

    # Create agent session
    session_agent = AgentSession(
        stt=cartesia.STT(model="ink-whisper"),
        llm=google.LLM(model="gemini-2.5-flash-lite"),
        tts=murf.TTS(
            voice="en-IN-Anisha",
            style="Promo",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
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

    shutdown_future = asyncio.Future()

    @ctx.room.on("disconnected")
    def on_disconnected(reason):
        if not shutdown_future.done():
            shutdown_future.set_result(None)

    await shutdown_future


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
