# Day 2 Task Checklist - Coffee Shop Barista Agent

## 🎯 Primary Goal (Required)

Build a coffee shop barista voice agent that can take orders and save them to a JSON file.

---

## ✅ Implementation Checklist

### 1. Agent Persona & Instructions
- [ ] Update agent instructions in [`backend/src/agent.py`](file:///c:/SmartQ/ten-days-of-voice-agents-2025/backend/src/agent.py)
  - [ ] Change persona to friendly barista
  - [ ] Choose a coffee brand (e.g., "Brew Haven", "Java Junction", etc.)
  - [ ] Add instructions for taking orders
  - [ ] Add instructions for asking clarifying questions

### 2. Order State Management
- [ ] Create order state data structure with fields:
  - [ ] `drinkType` (string) - e.g., "Latte", "Cappuccino", "Espresso"
  - [ ] `size` (string) - e.g., "Small", "Medium", "Large"
  - [ ] `milk` (string) - e.g., "Whole", "Skim", "Oat", "Almond"
  - [ ] `extras` (array of strings) - e.g., ["Whipped Cream", "Extra Shot"]
  - [ ] `name` (string) - Customer name

### 3. Function Tools Implementation
- [ ] Create a function tool to save order to JSON file
  - [ ] Use `@function_tool` decorator
  - [ ] Function should accept order parameters
  - [ ] Save to `orders/order_<timestamp>.json` or similar
  - [ ] Return confirmation message

### 4. Agent Behavior Logic
- [ ] Agent asks for drink type if not provided
- [ ] Agent asks for size if not provided
- [ ] Agent asks for milk preference if not provided
- [ ] Agent asks for extras/add-ons if not provided
- [ ] Agent asks for customer name if not provided
- [ ] Agent confirms complete order before saving
- [ ] Agent calls the save function tool when order is complete

### 5. Testing & Validation
- [ ] Test the agent can take a complete order
- [ ] Verify JSON file is created with correct data
- [ ] Test agent asks clarifying questions for missing fields
- [ ] Test agent handles different drink types
- [ ] Test agent handles different sizes and milk options

### 6. Recording & Documentation
- [ ] Record a video of placing a coffee order
- [ ] Show the generated JSON file in the video
- [ ] Prepare LinkedIn post description

### 7. LinkedIn Post
- [ ] Post video on LinkedIn
- [ ] Include description of Day 2 task completion
- [ ] Mention building with Murf Falcon (fastest TTS API)
- [ ] Tag official Murf AI handle
- [ ] Use hashtag: `#MurfAIVoiceAgentsChallenge`
- [ ] Use hashtag: `#10DaysofAIVoiceAgents`
- [ ] Mention: "Murf AI Voice Agent Challenge"

---

## 🚀 Advanced Challenge (Optional)

Only attempt this if you want an extra challenge!

### HTML Beverage Visualization
- [ ] Create HTML-based drink image generation system
- [ ] Render different cup sizes based on order size
- [ ] Add visual elements for extras (e.g., whipped cream)
- [ ] Alternative: Create HTML order receipt instead
- [ ] Use LiveKit data streams or RPC to send HTML to frontend
- [ ] Display the HTML visualization in the frontend

---

## 📚 Helpful Resources

### Required Reading
- [LiveKit Agents - Tools](https://docs.livekit.io/agents/build/tools/)
- [LiveKit Agents - Passing State](https://docs.livekit.io/agents/build/agents-handoffs/#passing-state)
- [LiveKit Agents - Tasks](https://docs.livekit.io/agents/build/tasks/)
- [Example: Drive-Thru Agent](https://github.com/livekit/agents/blob/main/examples/drive-thru/agent.py)

### Advanced Challenge Resources
- [LiveKit - Text Streams](https://docs.livekit.io/home/client/data/text-streams/)
- [LiveKit - RPC](https://docs.livekit.io/home/client/data/rpc/)

---

## 📝 Example Order State

```json
{
  "drinkType": "Caramel Latte",
  "size": "Large",
  "milk": "Oat Milk",
  "extras": ["Extra Shot", "Whipped Cream"],
  "name": "Alex"
}
```

---

## 💡 Implementation Tips

### 1. Agent Instructions Example
```python
instructions="""You are a friendly barista at [Your Coffee Shop Name]. 
You help customers place coffee orders by asking about their preferences.

Always ask for:
- What drink they'd like
- What size (Small, Medium, or Large)
- What type of milk (Whole, Skim, Oat, Almond, etc.)
- Any extras (Extra shot, whipped cream, caramel drizzle, etc.)
- Their name for the order

Once you have all the information, confirm the order and save it using the save_order tool.
Be friendly, conversational, and helpful!"""
```

### 2. Function Tool Example Structure
```python
from livekit.agents import function_tool, RunContext
import json
from datetime import datetime
import os

@function_tool
async def save_order(
    self,
    context: RunContext,
    drink_type: str,
    size: str,
    milk: str,
    extras: list[str],
    name: str
):
    """Save the customer's coffee order to a JSON file.
    
    Args:
        drink_type: Type of drink (e.g., Latte, Cappuccino)
        size: Size of drink (Small, Medium, Large)
        milk: Type of milk (Whole, Skim, Oat, Almond)
        extras: List of extras (e.g., Extra Shot, Whipped Cream)
        name: Customer name
    """
    # Create order object
    order = {
        "drinkType": drink_type,
        "size": size,
        "milk": milk,
        "extras": extras,
        "name": name,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save to file
    os.makedirs("orders", exist_ok=True)
    filename = f"orders/order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(order, indent=2)
    
    return f"Order saved! {name}, your {size} {drink_type} with {milk} will be ready soon!"
```

### 3. State Management Approach

You can manage state in a few ways:
- **Option A:** Let the LLM track the order in conversation context and call the tool when ready
- **Option B:** Use agent state to explicitly track what's been collected
- **Option C:** Use LiveKit's state passing features for more complex scenarios

For Day 2, **Option A** (letting the LLM manage it) is the simplest and recommended approach.

---

## 🎬 Video Recording Checklist

Make sure your video shows:
- [ ] Starting the conversation with the barista
- [ ] Agent asking clarifying questions
- [ ] You providing all order details
- [ ] Agent confirming the order
- [ ] The saved JSON file with your order details
- [ ] (Optional) The HTML visualization if you did the advanced challenge

---

## ✅ Completion Criteria

You've completed Day 2 when:
1. ✅ Your agent can take a complete coffee order via voice
2. ✅ The order is saved to a JSON file with all required fields
3. ✅ You've recorded a video showing the order process
4. ✅ You've posted the video on LinkedIn with required tags/mentions

---

## 🔄 Current Status

- [x] Day 1 - Voice agent running ✅
- [ ] Day 2 - Coffee shop barista agent
  - [ ] Primary goal (required)
  - [ ] Advanced challenge (optional)

Good luck with Day 2! 🚀☕
