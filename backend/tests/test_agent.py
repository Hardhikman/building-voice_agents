import pytest
from livekit.agents import AgentSession, inference, llm
import json
from pathlib import Path

from agent import CoordinatorAgent, LearnAgent, QuizAgent, TeachBackAgent


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


def _load_test_content():
    """Load the learning content for tests."""
    content_path = Path(__file__).parent.parent / "shared-data" / "day4_tutor_content.json"
    with open(content_path, "r") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_coordinator_greeting() -> None:
    """Test that the coordinator greets users and asks about learning mode."""
    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        content = _load_test_content()
        await session.start(CoordinatorAgent(content))

        # Run an agent turn following the user's greeting
        result = await session.run(user_input="Hello")

        # Evaluate the agent's response for friendliness and mode explanation
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                test_llm,
                intent="""
                Greets the user warmly and introduces the learning system.
                
                Should include:
                - A friendly greeting
                - Explanation of available learning modes (learn, quiz, teach-back)
                - Asking which mode the user would like to try
                
                The response should be welcoming and helpful.
                """,
            )
        )

        # Ensures there are no function calls or other unexpected events
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_handoff_to_learn_mode() -> None:
    """Test that the coordinator can hand off to learn mode."""
    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        content = _load_test_content()
        await session.start(CoordinatorAgent(content))

        # User requests learn mode
        result = await session.run(user_input="I want to learn about programming concepts")

        # Should call the switch_to_learn tool
        result.expect.next_event().is_tool_call(name="switch_to_learn")
        
        # Should get a handoff event
        result.expect.next_event().is_handoff()
        
        # New agent should introduce itself
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                test_llm,
                intent="""
                Introduces itself as the learning tutor and offers to explain concepts.
                Should mention available topics or ask what the user wants to learn.
                """,
            )
        )


@pytest.mark.asyncio
async def test_handoff_to_quiz_mode() -> None:
    """Test that the coordinator can hand off to quiz mode."""
    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        content = _load_test_content()
        await session.start(CoordinatorAgent(content))

        # User requests quiz mode
        result = await session.run(user_input="I want to test my knowledge with a quiz")

        # Should call the switch_to_quiz tool
        result.expect.next_event().is_tool_call(name="switch_to_quiz")
        
        # Should get a handoff event
        result.expect.next_event().is_handoff()
        
        # New agent should introduce itself
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                test_llm,
                intent="""
                Introduces itself as the quiz tutor and offers to test knowledge.
                Should mention available quiz topics or start asking a question.
                """,
            )
        )


@pytest.mark.asyncio
async def test_handoff_to_teach_back_mode() -> None:
    """Test that the coordinator can hand off to teach-back mode."""
    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        content = _load_test_content()
        await session.start(CoordinatorAgent(content))

        # User requests teach-back mode
        result = await session.run(user_input="I want to explain concepts back to you")

        # Should call the switch_to_teach_back tool
        result.expect.next_event().is_tool_call(name="switch_to_teach_back")
        
        # Should get a handoff event
        result.expect.next_event().is_handoff()
        
        # New agent should introduce itself
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                test_llm,
                intent="""
                Introduces itself as the teach-back coach and asks the user to explain a concept.
                Should mention available concepts or encourage the user to teach.
                """,
            )
        )


@pytest.mark.asyncio
async def test_learn_mode_explains_concept() -> None:
    """Test that learn mode can explain concepts."""
    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        content = _load_test_content()
        await session.start(LearnAgent(content))

        # User asks about variables
        result = await session.run(user_input="Can you explain what variables are?")

        # Should call explain_concept or provide explanation
        # The agent might call the tool or just explain directly
        # We'll check that there's a message with an explanation
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                test_llm,
                intent="""
                Provides a clear explanation of variables in programming.
                Should cover what variables are and why they're useful.
                The explanation should be educational and helpful.
                """,
            )
        )


@pytest.mark.asyncio
async def test_quiz_mode_asks_questions() -> None:
    """Test that quiz mode asks questions."""
    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        content = _load_test_content()
        await session.start(QuizAgent(content))

        # User wants to be quizzed on loops
        result = await session.run(user_input="Quiz me on loops")

        # Should ask a question about loops
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                test_llm,
                intent="""
                Asks a question about loops in programming.
                The question should test understanding of loops.
                Should be clear and educational.
                """,
            )
        )


@pytest.mark.asyncio
async def test_mode_switching_from_learn_to_quiz() -> None:
    """Test that users can switch from learn mode to quiz mode."""
    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        content = _load_test_content()
        await session.start(LearnAgent(content))

        # User wants to switch to quiz mode
        result = await session.run(user_input="I'd like to switch to quiz mode now")

        # Should call switch_to_quiz
        result.expect.next_event().is_tool_call(name="switch_to_quiz")
        
        # Should get a handoff event
        result.expect.next_event().is_handoff()
        
        # Quiz agent should introduce itself
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                test_llm,
                intent="""
                Introduces itself as the quiz tutor.
                Should offer to test knowledge or ask about quiz topics.
                """,
            )
        )


@pytest.mark.asyncio
async def test_content_loading() -> None:
    """Test that content is properly loaded and accessible."""
    content = _load_test_content()
    
    # Verify content structure
    assert len(content) > 0, "Content should not be empty"
    
    for concept in content:
        assert "id" in concept, "Each concept should have an id"
        assert "title" in concept, "Each concept should have a title"
        assert "summary" in concept, "Each concept should have a summary"
        assert "sample_question" in concept, "Each concept should have a sample_question"
    
    # Verify specific concepts exist
    concept_ids = [c["id"] for c in content]
    assert "variables" in concept_ids, "Should have variables concept"
    assert "loops" in concept_ids, "Should have loops concept"
