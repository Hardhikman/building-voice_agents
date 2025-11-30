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

logger = logging.getLogger("food-ordering-agent")

load_dotenv(".env.local")


class FoodOrderingAgent(Agent):
    """Food & Grocery Ordering Voice Agent."""

    def __init__(self) -> None:
        # Load the food catalog
        catalog_path = Path(__file__).parent.parent / "shared-data" / "food_catalog.json"
        try:
            with open(catalog_path, "r") as f:
                self.catalog = json.load(f)
            logger.info(f"Loaded food catalog with {len(self.catalog.get('categories', {}))} categories")
        except Exception as e:
            logger.error(f"Failed to load food catalog: {e}")
            self.catalog = {"categories": {}, "recipes": {}}
        
        # Initialize cart
        self.cart = []
        self.order_history = []
        
        super().__init__(
            instructions="""You are a friendly and helpful food & grocery ordering assistant for QuickCart, a fictional online grocery store.
            
            Your role:
            - Help users order food and groceries from our catalog
            - Understand what users want, including specific items, quantities, or recipe-based requests like "ingredients for a peanut butter sandwich"
            - Maintain a cart of items as the conversation progresses
            - Add, remove, and update quantities of items in the cart
            - List what's currently in the cart when asked
            - Place orders and save them to JSON files when users are done
            - Answer questions about order status if the advanced tracking feature is implemented
            
            Guidelines:
            - Be warm, friendly, and conversational
            - Ask for clarification when needed (quantity, specific brand, etc.)
            - Confirm cart changes with the user
            - When users are done shopping, summarize their order and place it
            Ask how you can help them with their shopping today."""
        )

    @function_tool()
    async def search_catalog(self, context: RunContext, query: str):
        """Search the food catalog for items matching the query.
        
        Args:
            query: The user's search query (e.g., "bread", "apples", "pizza")
        """
        query_lower = query.lower()
        matches = []
        
        # Search through all categories
        for category_name, items in self.catalog.get("categories", {}).items():
            for item in items:
                # Match by name, brand, or tags
                name_match = query_lower in item["name"].lower()
                brand_match = query_lower in item.get("brand", "").lower()
                tag_match = any(query_lower in tag.lower() for tag in item.get("tags", []))
                
                if name_match or brand_match or tag_match:
                    matches.append(item)
        
        if matches:
            # Format top 5 matches
            result = "I found these items matching your search:\n"
            for i, item in enumerate(matches[:5]):
                result += f"{i+1}. {item['name']} - ${item['price']}/{item['unit']}\n"
            return result
        else:
            return f"I couldn't find any items matching '{query}'. Would you like to try a different search?"

    @function_tool()
    async def add_to_cart(self, context: RunContext, item_id: str, quantity: int = 1):
        """Add an item to the shopping cart.
        
        Args:
            item_id: The ID of the item to add
            quantity: The quantity to add (default: 1)
        """
        # Find the item in the catalog
        item = None
        # First try exact ID match
        for category_items in self.catalog.get("categories", {}).values():
            for catalog_item in category_items:
                if catalog_item["id"] == item_id:
                    item = catalog_item
                    break
            if item:
                break
        
        # If not found, try matching by name (case-insensitive)
        if not item:
            for category_items in self.catalog.get("categories", {}).values():
                for catalog_item in category_items:
                    if catalog_item["name"].lower() == item_id.lower():
                        item = catalog_item
                        break
                if item:
                    break
        
        # If still not found, try partial match
        if not item:
            matches = []
            for category_items in self.catalog.get("categories", {}).values():
                for catalog_item in category_items:
                    if item_id.lower() in catalog_item["name"].lower():
                        matches.append(catalog_item)
            
            if len(matches) == 1:
                item = matches[0]
            elif len(matches) > 1:
                # Return a helpful message asking for clarification
                options = ", ".join([m["name"] for m in matches])
                return f"I found multiple items matching '{item_id}': {options}. Which one would you like?"

        if not item:
            return f"Sorry, I couldn't find an item with ID or name '{item_id}' in our catalog."
        
        # Check if item is already in cart
        existing_item = None
        for cart_item in self.cart:
            if cart_item["item_id"] == item["id"]:
                existing_item = cart_item
                break
        
        if existing_item:
            # Update quantity
            existing_item["quantity"] += quantity
            return f"Updated {item['name']} quantity to {existing_item['quantity']} in your cart."
        else:
            # Add new item
            cart_item = {
                "item_id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "unit": item["unit"],
                "quantity": quantity
            }
            self.cart.append(cart_item)
            return f"Added {quantity} {item['name']} to your cart."
    
    @function_tool()
    async def remove_from_cart(self, context: RunContext, item_id: str):
        """Remove an item from the shopping cart.
        
        Args:
            item_id: The ID of the item to remove
        """
        # Find and remove the item
        for i, cart_item in enumerate(self.cart):
            if cart_item["item_id"] == item_id or cart_item["name"].lower() == item_id.lower():
                removed_item = self.cart.pop(i)
                return f"Removed {removed_item['name']} from your cart."
        
        return f"I couldn't find an item with ID or name '{item_id}' in your cart."
    
    @function_tool()
    async def update_cart_quantity(self, context: RunContext, item_id: str, quantity: int):
        """Update the quantity of an item in the shopping cart.
        
        Args:
            item_id: The ID of the item to update
            quantity: The new quantity
        """
        if quantity <= 0:
            return await self.remove_from_cart(context, item_id)
        
        # Find and update the item
        for cart_item in self.cart:
            if cart_item["item_id"] == item_id or cart_item["name"].lower() == item_id.lower():
                old_quantity = cart_item["quantity"]
                cart_item["quantity"] = quantity
                return f"Updated {cart_item['name']} quantity from {old_quantity} to {quantity}."
        
        return f"I couldn't find an item with ID or name '{item_id}' in your cart."
    
    @function_tool()
    async def list_cart(self, context: RunContext):
        """List all items currently in the shopping cart."""
        if not self.cart:
            return "Your cart is currently empty."
        
        result = "Here's what's in your cart:\n"
        total = 0
        
        for item in self.cart:
            item_total = item["price"] * item["quantity"]
            total += item_total
            result += f"- {item['name']}: {item['quantity']} x ${item['price']}/${item['unit']} = ${item_total:.2f}\n"
        
        result += f"\nCart total: ${total:.2f}"
        return result

    @function_tool()
    async def add_recipe_ingredients(self, context: RunContext, recipe_name: str):
        """Add all ingredients for a recipe to the cart.
        
        Args:
            recipe_name: The name of the recipe (e.g., "peanut butter sandwich")
        """
        # Find the recipe
        recipe_key = None
        # Try to find exact or partial matches
        for key, recipe in self.catalog.get("recipes", {}).items():
            if (recipe_name.lower() == recipe["name"].lower() or 
                recipe_name.lower() == key.lower() or
                recipe_name.lower() in recipe["name"].lower() or 
                recipe_name.lower() in key.lower()):
                recipe_key = key
                break
        
        if not recipe_key:
            available = ", ".join([r["name"] for r in self.catalog.get("recipes", {}).values()])
            return f"I don't have a recipe for '{recipe_name}'. Available recipes: {available}"
        
        recipe = self.catalog["recipes"][recipe_key]
        added_items = []
        
        # Add all ingredients
        for ingredient in recipe["ingredients"]:
            item_id = ingredient["item_id"]
            quantity = ingredient["quantity"]
            
            # Find the item in the catalog
            item = None
            for category_items in self.catalog.get("categories", {}).values():
                for catalog_item in category_items:
                    if catalog_item["id"] == item_id:
                        item = catalog_item
                        break
                if item:
                    break
            
            if item:
                # Add to cart manually to avoid async issues
                # Check if item is already in cart
                existing_item = None
                for cart_item in self.cart:
                    if cart_item["item_id"] == item_id:
                        existing_item = cart_item
                        break
                
                if existing_item:
                    # Update quantity
                    existing_item["quantity"] += quantity
                else:
                    # Add new item
                    cart_item = {
                        "item_id": item_id,
                        "name": item["name"],
                        "price": item["price"],
                        "unit": item["unit"],
                        "quantity": quantity
                    }
                    self.cart.append(cart_item)
                added_items.append(f"{quantity} x {item['name']}")
        
        if added_items:
            items_list = ", ".join(added_items)
            return f"I've added the ingredients for {recipe['name']} to your cart: {items_list}. {recipe['description']}"
        else:
            return f"I couldn't add the ingredients for {recipe['name']} to your cart."
    
    @function_tool()
    async def place_order(self, context: RunContext):
        """Place the current cart as an order and save it to a JSON file."""
        if not self.cart:
            return "Your cart is empty. Add some items before placing an order."
        
        # Calculate total
        total = sum(item["price"] * item["quantity"] for item in self.cart)
        
        # Create order object
        import time
        order = {
            "order_id": f"order_{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "items": self.cart.copy(),
            "total": round(total, 2),
            "status": "received"
        }
        
        # Save to JSON file
        orders_file = Path(__file__).parent.parent / "shared-data" / "orders.json"
        all_orders = []
        
        # Load existing orders
        if orders_file.exists():
            try:
                with open(orders_file, "r") as f:
                    all_orders = json.load(f)
            except:
                pass
        
        # Add new order
        all_orders.append(order)
        
        # Save back to file
        try:
            with open(orders_file, "w") as f:
                json.dump(all_orders, f, indent=2)
            
            # Clear cart
            self.cart = []
            
            return f"Your order has been placed successfully! Order ID: {order['order_id']}. Total: ${order['total']:.2f}. Thank you for shopping with QuickCart!"
        except Exception as e:
            logger.error(f"Failed to save order: {e}")
            return f"I'm sorry, I encountered an error while placing your order. Please try again."
    
    @function_tool()
    async def check_order_status(self, context: RunContext, order_id: str = None):
        """Check the status of an order.
        
        Args:
            order_id: The ID of the order to check (if None, checks the latest order)
        """
        orders_file = Path(__file__).parent.parent / "shared-data" / "orders.json"
        
        if not orders_file.exists():
            return "No orders found."
        
        try:
            with open(orders_file, "r") as f:
                orders = json.load(f)
            
            if not orders:
                return "No orders found."
            
            # Find the order
            target_order = None
            if order_id:
                for order in orders:
                    if order["order_id"] == order_id:
                        target_order = order
                        break
            else:
                # Get the latest order
                target_order = orders[-1]
            
            if target_order:
                return f"Order {target_order['order_id']} status: {target_order['status']}. Placed on {target_order['timestamp']}."
            else:
                return f"Order {order_id} not found."
        except Exception as e:
            logger.error(f"Failed to check order status: {e}")
            return "I'm sorry, I encountered an error while checking your order status."
    
    @function_tool()
    async def list_order_history(self, context: RunContext):
        """List the user's order history."""
        orders_file = Path(__file__).parent.parent / "shared-data" / "orders.json"
        
        if not orders_file.exists():
            return "No order history found."
        
        try:
            with open(orders_file, "r") as f:
                orders = json.load(f)
            
            if not orders:
                return "Your order history is empty."
            
            result = "Here's your order history:\n"
            for order in orders[-5:]:  # Show last 5 orders
                result += f"- Order {order['order_id']}: ${order['total']:.2f} ({order['status']})\n"
            
            return result
        except Exception as e:
            logger.error(f"Failed to load order history: {e}")
            return "I'm sorry, I encountered an error while loading your order history."

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    # Create the food ordering agent
    agent = FoodOrderingAgent()

    # Create agent session
    session_agent = AgentSession(
        stt=cartesia.STT(model="ink-whisper"),
        llm=google.LLM(model="gemini-2.5-flash"),
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