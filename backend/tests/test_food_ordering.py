import pytest
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_food_ordering import FoodOrderingAgent

@pytest.fixture
def mock_catalog():
    return {
        "categories": {
            "groceries": [
                {
                    "id": "bread_whole_wheat",
                    "name": "Whole Wheat Bread",
                    "category": "groceries",
                    "subcategory": "bakery",
                    "price": 2.99,
                    "unit": "loaf",
                    "brand": "Nature's Own",
                    "tags": ["whole grain", "fiber", "healthy"]
                }
            ]
        },
        "recipes": {
            "pb_sandwich": {
                "name": "Peanut Butter Sandwich",
                "ingredients": [
                    {"item_id": "bread_whole_wheat", "quantity": 2}
                ],
                "description": "A classic peanut butter sandwich"
            }
        }
    }

@pytest.fixture
def agent(mock_catalog, monkeypatch):
    # Mock the file reading
    monkeypatch.setattr("agent_food_ordering.FoodOrderingAgent.__init__", lambda self: setattr(self, 'catalog', mock_catalog) or setattr(self, 'cart', []) or setattr(self, 'order_history', []) or object.__init__(self))
    agent = FoodOrderingAgent()
    agent.catalog = mock_catalog
    agent.cart = []
    agent.order_history = []
    return agent

@pytest.mark.asyncio
async def test_search_catalog(agent):
    # Test searching for bread
    response = await agent.search_catalog(None, "bread")
    assert "Whole Wheat Bread" in response
    assert "$2.99/loaf" in response

@pytest.mark.asyncio
async def test_add_to_cart(agent):
    # Test adding item to cart
    response = await agent.add_to_cart(None, "bread_whole_wheat", 2)
    assert "Added 2 Whole Wheat Bread to your cart" in response
    assert len(agent.cart) == 1
    assert agent.cart[0]["item_id"] == "bread_whole_wheat"
    assert agent.cart[0]["quantity"] == 2

@pytest.mark.asyncio
async def test_update_cart_quantity(agent):
    # Add item first
    await agent.add_to_cart(None, "bread_whole_wheat", 1)
    
    # Test updating quantity
    response = await agent.update_cart_quantity(None, "bread_whole_wheat", 3)
    assert "Updated Whole Wheat Bread quantity from 1 to 3" in response
    assert agent.cart[0]["quantity"] == 3

@pytest.mark.asyncio
async def test_remove_from_cart(agent):
    # Add item first
    await agent.add_to_cart(None, "bread_whole_wheat", 1)
    
    # Test removing item
    response = await agent.remove_from_cart(None, "bread_whole_wheat")
    assert "Removed Whole Wheat Bread from your cart" in response
    assert len(agent.cart) == 0

@pytest.mark.asyncio
async def test_list_cart(agent):
    # Test empty cart
    response = await agent.list_cart(None)
    assert "Your cart is currently empty" in response
    
    # Add item and test listing
    await agent.add_to_cart(None, "bread_whole_wheat", 2)
    response = await agent.list_cart(None)
    assert "Whole Wheat Bread" in response
    assert "2 x $2.99/loaf = $5.98" in response
    assert "Cart total: $5.98" in response

@pytest.mark.asyncio
async def test_add_recipe_ingredients(agent):
    # Test adding recipe ingredients
    response = await agent.add_recipe_ingredients(None, "peanut butter sandwich")
    assert "Added the ingredients for Peanut Butter Sandwich" in response
    assert len(agent.cart) == 1
    assert agent.cart[0]["item_id"] == "bread_whole_wheat"
    assert agent.cart[0]["quantity"] == 2