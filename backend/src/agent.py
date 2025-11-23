import logging

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

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly barista at Hard Coffee Shop. The user is interacting with you via voice.
            Your job is to help customers place coffee orders by asking about their preferences in a natural, conversational way.
            
            You need to collect the following information for each order:
            - Drink type (e.g., Latte, Cappuccino, Espresso, Americano, Mocha, etc.)
            - Quantity (Number of cups)
            - Size (Small, Medium, or Large)
            - Milk preference (Whole, Skim, Oat, Almond, Soy, or None for black coffee)
            - Any extras (e.g., Extra shot, Whipped cream, Caramel drizzle, Vanilla syrup, etc.)
            - Customer's name for the order
            
            Ask for missing information naturally in conversation. Once you have all the details, confirm the complete order with the customer.
            After confirmation, use the save_order tool to save their order.
            
            Be warm, friendly, and enthusiastic about coffee! Keep responses concise and conversational.
            Do not use emojis, asterisks, or complex formatting in your responses.""",
        )

    @function_tool
    async def save_order(
        self,
        context: RunContext,
        drink_type: str,
        quantity: int,
        size: str,
        milk: str,
        extras: list[str],
        name: str
    ):
        """Save the customer's coffee order to a JSON file.
        
        Use this tool ONLY after you have collected all order information and the customer has confirmed their order.
        
        Args:
            drink_type: Type of drink (e.g., Latte, Cappuccino, Espresso, Americano, Mocha)
            quantity: Number of cups (integer)
            size: Size of drink (Small, Medium, or Large)
            milk: Type of milk (Whole, Skim, Oat, Almond, Soy, or None)
            extras: List of extras/add-ons (e.g., ["Extra shot", "Whipped cream"]). Use empty list [] if no extras.
            name: Customer's name for the order
        """
        # Create order object
        order = {
            "drinkType": drink_type,
            "quantity": quantity,
            "size": size,
            "milk": milk,
            "extras": extras,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "orderNumber": datetime.now().strftime("%Y%m%d%H%M%S")
        }
        
        # Create orders directory if it doesn't exist
        orders_dir = "orders"
        os.makedirs(orders_dir, exist_ok=True)
        
        # Generate filename with timestamp
        filename = os.path.join(orders_dir, f"order_{order['orderNumber']}.json")
        
        # Save order to JSON file
        with open(filename, 'w') as f:
            json.dump(order, f, indent=2)
        
        logger.info(f"Order saved: {filename}")
        logger.info(f"Order details: {order}")
        
        # Send order data to frontend via data channel
        try:
            room = context.room
            # Send as JSON string with a topic identifier
            order_json = json.dumps({"type": "coffee_order", "order": order})
            await room.local_participant.publish_data(
                order_json.encode('utf-8'),
                topic="coffee_order"
            )
            logger.info("Order data sent to frontend")
        except Exception as e:
            logger.error(f"Failed to send order to frontend: {e}")
        
        return f"Perfect! Your order has been placed, {name}. {quantity} {size} {drink_type}(s) with {milk} will be ready soon. Your order number is {order['orderNumber']}. Thank you for visiting Brew Haven!"


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=cartesia.STT( model="ink-whisper"), #this can be changed to elevenlabs/deepgram/
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-2.5-flash",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="en-US-matthew", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
