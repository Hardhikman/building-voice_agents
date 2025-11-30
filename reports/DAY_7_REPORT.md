# Food & Grocery Ordering Voice Agent

This agent implements a voice-based food and grocery ordering system as part of Day 7 of the 10-Day AI Voice Agents Challenge.

## Features

- **Catalog Search**: Search through a diverse catalog of food and grocery items
- **Cart Management**: Add, remove, and update quantities of items in a shopping cart
- **Recipe Intelligence**: Handle requests like "ingredients for a peanut butter sandwich" by automatically adding all required ingredients
- **Order Placement**: Place orders and save them to JSON files
- **Order History**: View past orders and check order status

## File Structure

- `src/agent_food_ordering.py` - Main agent implementation
- `shared-data/food_catalog.json` - Food catalog with items and recipes

## Running the Agent

To run the food ordering agent:

```console
uv run python src/agent_food_ordering.py console
```

Or for development mode with frontend connectivity:

```console
uv run python src/agent_food_ordering.py dev
```

## Voice Commands

The agent understands natural language commands such as:

- "I need ingredients for a peanut butter sandwich"
- "Add 2 loaves of bread to my cart"
- "What's in my cart?"
- "Place my order"
- "Show me my order history"

## Data Persistence

Orders are saved to `shared-data/orders.json` with the following structure:

```json
{
  "order_id": "order_1234567890",
  "timestamp": "2025-11-30 15:30:45",
  "items": [
    {
      "item_id": "bread_whole_wheat",
      "name": "Whole Wheat Bread",
      "price": 2.99,
      "unit": "loaf",
      "quantity": 2
    }
  ],
  "total": 5.98,
  "status": "received"
}
```