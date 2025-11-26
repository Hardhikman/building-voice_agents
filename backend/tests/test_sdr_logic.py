import pytest
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sdr import SDRAgent

@pytest.fixture
def mock_company_data():
    return {
        "company": "TestCorp",
        "description": "A test company",
        "pricing": {"standard": "100 USD"},
        "faqs": [
            {"question": "What is this?", "answer": "It is a test."},
            {"question": "How much?", "answer": "It costs money."}
        ]
    }

@pytest.fixture
def agent(mock_company_data):
    return SDRAgent(company_data=mock_company_data)

@pytest.mark.asyncio
async def test_answer_faq_match(agent):
    # Test exact match
    response = await agent.answer_faq(None, "What is this?")
    assert "It is a test" in response

    # Test partial match
    response = await agent.answer_faq(None, "tell me what is this")
    assert "It is a test" in response

@pytest.mark.asyncio
async def test_answer_faq_no_match(agent):
    response = await agent.answer_faq(None, "Where are you located?")
    assert "I don't have a specific FAQ" in response

@pytest.mark.asyncio
async def test_save_lead_info(agent):
    # Test saving info
    response = await agent.save_lead_info(None, name="John Doe", email="john@example.com")
    assert "Information saved" in response
    assert agent.lead_info["name"] == "John Doe"
    assert agent.lead_info["email"] == "john@example.com"
    
    # Test updating info
    await agent.save_lead_info(None, company="Acme Inc")
    assert agent.lead_info["company"] == "Acme Inc"
    assert agent.lead_info["name"] == "John Doe" # Should persist

@pytest.mark.asyncio
async def test_end_call_summary(agent):
    agent.lead_info = {"name": "Jane", "company": "Tech"}
    response = await agent.end_call_and_summarize(None)
    assert "Jane" in response
    assert "Tech" in response
