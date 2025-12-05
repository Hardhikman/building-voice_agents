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
import db

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class CoordinatorAgent(Agent):
    """Main coordinator that greets users and handles mode switching."""

    def __init__(self, content: list) -> None:
        self.content = content
        super().__init__(
            instructions="""You are a friendly learning coordinator for a programming tutor system.

            Your role is to help users choose between three learning modes:
            1. LEARN mode - I will explain programming concepts to you
            2. QUIZ mode - I will ask you questions to test your knowledge
            3. TEACH-BACK mode - You explain concepts back to me and I'll give feedback

            Be warm and encouraging. Ask the user which mode they'd like to start with,
            or help them switch modes if they request it during the conversation."""
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active."""
        # Ensure voice is Matthew
        self.session.tts = murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        )
        await self.session.generate_reply(
            instructions="""Greet the user warmly and introduce yourself as their learning coordinator.
            Briefly explain the three learning modes available (learn, quiz, teach-back) and ask 
            which mode they'd like to start with."""
        )

    @function_tool()
    async def switch_to_learn(self, context: RunContext):
        """Switch to learn mode where the agent explains programming concepts."""
        return LearnAgent(self.content), "Switching to learn mode"

    @function_tool()
    async def switch_to_quiz(self, context: RunContext):
        """Switch to quiz mode where the agent asks questions to test knowledge."""
        return QuizAgent(self.content), "Switching to quiz mode"

    @function_tool()
    async def switch_to_teach_back(self, context: RunContext):
        """Switch to teach-back mode where the user explains concepts to the agent."""
        return TeachBackAgent(self.content), "Switching to teach-back mode"


class LearnAgent(Agent):
    """Learn mode agent that explains concepts using Matthew's voice."""

    def __init__(self, content: list) -> None:
        self.content = content
        self.concepts_dict = {c["id"]: c for c in content}
        concepts_list = ", ".join([c["title"] for c in content])
        super().__init__(
            instructions=f"""You are a patient and knowledgeable programming tutor in LEARN mode.

            Available concepts you can teach: {concepts_list}

            Your role:
            - Explain programming concepts clearly and thoroughly
            - Use analogies and examples to make concepts easy to understand
            - Be encouraging and supportive
            - Answer follow-up questions about the concepts
            - If asked about a concept, use the detailed summary provided in your knowledge

            When the user wants to switch modes, use the appropriate switch tool."""
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active."""
        # Ensure voice is Matthew
        self.session.tts = murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        )
        concepts_list = ", ".join([c["title"] for c in self.content])
        await self.session.generate_reply(
            instructions=f"""You are now in LEARN mode. 
            
            IMPORTANT: Do NOT ask what they want to learn if they just told you. 
            Continue the conversation naturally based on what they just said.
            
            If they already mentioned a concept, start explaining it immediately.
            If they haven't mentioned a specific concept yet, briefly say you're ready to teach them about: {concepts_list}.
            
            Be conversational and natural - don't repeat questions they already answered."""
        )

    @function_tool()
    async def explain_concept(self, context: RunContext, concept_name: str):
        """Explain a programming concept to the user.

        Args:
            concept_name: The name or ID of the concept to explain (e.g., 'variables', 'loops', 'functions')
        """
        concept = None
        concept_name_lower = concept_name.lower()
        for c in self.content:
            if c["id"] == concept_name_lower or c["title"].lower() == concept_name_lower:
                concept = c
                break
        if concept:
            return f"Here's the explanation for {concept['title']}: {concept['summary']}"
        else:
            available = ", ".join([c["title"] for c in self.content])
            return f"I don't have information about '{concept_name}'. I can teach you about: {available}"

    @function_tool()
    async def switch_to_quiz(self, context: RunContext):
        """Switch to quiz mode to test your knowledge."""
        return QuizAgent(self.content), "Switching to quiz mode"

    @function_tool()
    async def switch_to_teach_back(self, context: RunContext):
        """Switch to teach-back mode where you explain concepts."""
        return TeachBackAgent(self.content), "Switching to teach-back mode"


class QuizAgent(Agent):
    """Quiz mode agent that asks questions using Alicia's voice."""

    def __init__(self, content: list) -> None:
        self.content = content
        self.concepts_dict = {c["id"]: c for c in content}
        quiz_info = "\n".join([f"- {c['title']}: {c['sample_question']}" for c in content])
        super().__init__(
            instructions=f"""You are an engaging quiz tutor in QUIZ mode.

            Available quiz topics and sample questions:
            {quiz_info}

            Your role:
            - Ask questions about programming concepts to test understanding
            - Provide feedback on answers (correct or incorrect)
            - Encourage the user and help them learn from mistakes
            - Ask follow-up questions to deepen understanding
            - Use the sample questions as a guide, but feel free to ask related questions

            When the user wants to switch modes, use the appropriate switch tool."""
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active."""
        # Set voice to Alicia
        self.session.tts = murf.TTS(
            voice="en-US-alicia",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        )
        topics = ", ".join([c["title"] for c in self.content])
        await self.session.generate_reply(
            instructions=f"""You are now in QUIZ mode.
            
            IMPORTANT: Do NOT ask what topic they want if they just told you.
            Continue the conversation naturally based on what they just said.
            
            If they already mentioned a topic, ask a question about it immediately.
            If they haven't mentioned a specific topic yet, briefly say you can quiz them on: {topics}.
            
            Be conversational and natural - don't repeat questions they already answered."""
        )

    @function_tool()
    async def ask_question(self, context: RunContext, topic: str):
        """Ask a quiz question about a specific topic.

        Args:
            topic: The topic to ask about (e.g., 'variables', 'loops', 'functions')
        """
        topic_lower = topic.lower()
        concept = None
        for c in self.content:
            if c["id"] == topic_lower or c["title"].lower() == topic_lower:
                concept = c
                break
        if concept:
            return f"Here's a question about {concept['title']}: {concept['sample_question']}"
        else:
            available = ", ".join([c["title"] for c in self.content])
            return f"I don't have questions about '{topic}'. I can quiz you on: {available}"

    @function_tool()
    async def switch_to_coordinator(self, context: RunContext):
        """Return to the main coordinator to choose a different mode."""
        return CoordinatorAgent(self.content), "Returning to coordinator"

    @function_tool()
    async def switch_to_learn(self, context: RunContext):
        """Switch to learn mode to have concepts explained."""
        return LearnAgent(self.content), "Switching to learn mode"

    @function_tool()
    async def switch_to_teach_back(self, context: RunContext):
        """Switch to teach-back mode where you explain concepts."""
        return TeachBackAgent(self.content), "Switching to teach-back mode"


class TeachBackAgent(Agent):
    """Teach-back mode agent that listens to user explanations using Ken's voice."""

    def __init__(self, content: list) -> None:
        self.content = content
        self.concepts_dict = {c["id"]: c for c in content}
        concepts_list = ", ".join([c["title"] for c in content])
        super().__init__(
            instructions=f"""You are a supportive coach in TEACH-BACK mode.

            Available concepts: {concepts_list}

            Your role:
            - Ask the user to explain a programming concept back to you
            - Listen carefully to their explanation
            - Provide constructive, qualitative feedback on their explanation
            - Point out what they got right and what could be improved
            - Be encouraging and supportive, even if they struggle
            - Help them refine their understanding

            When evaluating explanations, consider:
            - Did they cover the main points?
            - Did they use good examples or analogies?
            - Was the explanation clear and accurate?

            When the user wants to switch modes, use the appropriate switch tool."""
        )

    async def on_enter(self) -> None:
        """Called when this agent becomes active."""
        # Set voice to Ken
        self.session.tts = murf.TTS(
            voice="en-US-ken",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        )
        concepts_list = ", ".join([c["title"] for c in self.content])
        await self.session.generate_reply(
            instructions=f"""You are now in TEACH-BACK mode.
            
            IMPORTANT: Do NOT ask what concept they want to explain if they just told you.
            Continue the conversation naturally based on what they just said.
            
            If they already mentioned a concept, ask them to explain it to you immediately.
            If they haven't mentioned a specific concept yet, briefly say they can teach you about: {concepts_list}.
            
            Be conversational and natural - don't repeat questions they already answered."""
        )

    @function_tool()
    async def evaluate_explanation(self, context: RunContext, concept: str, user_explanation: str):
        """Evaluate the user's explanation of a concept and provide feedback, updating mastery stats."""
        concept_lower = concept.lower()
        concept_data = None
        for c in self.content:
            if c["id"] == concept_lower or c["title"].lower() == concept_lower:
                concept_data = c
                break
        if not concept_data:
            return f"I'm not sure about the concept '{concept}'. Let's try one of these: {', '.join([c['title'] for c in self.content])}"
        # Simple scoring based on word overlap with official summary
        summary_words = set(concept_data["summary"].lower().split())
        explanation_words = set(user_explanation.lower().split())
        overlap = len(summary_words.intersection(explanation_words)) / (len(summary_words) or 1)
        score = int(overlap * 100)
        
        # Update mastery stats in database
        db_path = Path(__file__).parent.parent / "shared-data" / "mastery.db"
        database = db.Database(str(db_path))
        database.update_teach_back_score(concept_data["id"], score)
        
        feedback = f"Great job! You covered {int(overlap * 100)}% of the key points."
        return f"{feedback}\n\nReference summary: {concept_data['summary']}"

    @function_tool()
    async def get_weakest_concepts(self, context: RunContext, top_n: int = 3):
        """Return the concepts with the lowest average mastery score.
        Useful for the user to ask "Which concepts am I weakest at?".
        """
        db_path = Path(__file__).parent.parent / "shared-data" / "mastery.db"
        database = db.Database(str(db_path))
        weakest = database.get_weakest_concepts(limit=top_n)
        
        if not weakest:
            return "No concept scores recorded yet. Try teaching back a concept first."
            
        lines = []
        for title, avg_score, count in weakest:
            lines.append(f"{title}: avg score {avg_score:.1f}% (attempts {count})")
        return "\n".join(lines)

    @function_tool()
    async def switch_to_coordinator(self, context: RunContext):
        """Return to the main coordinator to choose a different mode."""
        return CoordinatorAgent(self.content), "Returning to coordinator"

    @function_tool()
    async def switch_to_learn(self, context: RunContext):
        """Switch to learn mode to have concepts explained."""
        return LearnAgent(self.content), "Switching to learn mode"

    @function_tool()
    async def switch_to_quiz(self, context: RunContext):
        """Switch to quiz mode to test your knowledge."""
        return QuizAgent(self.content), "Switching to quiz mode"


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    # Load learning content from JSON file
    content_path = Path(__file__).parent.parent / "shared-data" / "day4_tutor_content.json"
    try:
        with open(content_path, "r") as f:
            learning_content = json.load(f)
        logger.info(f"Loaded {len(learning_content)} concepts from {content_path}")
    except Exception as e:
        logger.error(f"Failed to load learning content: {e}")
        learning_content = []

    # Initialize database and populate concepts
    db_path = Path(__file__).parent.parent / "shared-data" / "mastery.db"
    database = db.Database(str(db_path))
    for c in learning_content:
        database.upsert_concept(c["id"], c["title"])

    # Create the coordinator agent
    agent = CoordinatorAgent(content=learning_content)

    # Create agent session with voice configuration
    session_agent = AgentSession(
        stt=cartesia.STT(model="ink-whisper"),
        llm=google.LLM(model="gemini-2.5-flash-lite"),
        tts=murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
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
