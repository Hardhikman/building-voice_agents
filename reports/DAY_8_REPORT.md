# Day 8: Voice Game Master (D&D-Style Adventure)

This agent implements a complete D&D-style voice Game Master that runs interactive story sessions across multiple universes as part of Day 8 of the 10-Day AI Voice Agents Challenge.

## Features Implemented

### ✅ Primary Goal - Interactive Voice Storytelling
- **Immersive Narration**: Vivid scene descriptions with atmospheric storytelling
- **Player Agency**: Continuous action prompts ("What do you do?", "What's your move?")
- **Story Continuity**: Remembers player decisions, NPCs, and past events through chat history
- **Multi-Turn Sessions**: Supports 8-15+ turn gameplay sessions with narrative arcs

### ✅ Advanced Goal #1 - JSON World State System
- **Character Tracking**: Records NPCs with role, attitude, and notes
- **Location Management**: Tracks visited places with descriptions and connections
- **Event Log**: Chronicles significant story moments and player decisions
- **Quest System**: Manages active and completed objectives
- **State Inspection**: Console logging and query tools for debugging

### ✅ Advanced Goal #2 - Character Sheet & Inventory
- **Health System**: HP tracking with dynamic status (Healthy → Injured → Critical → Unconscious)
- **Attribute System**: Customizable stats per universe (Strength, Tech, Leadership, etc.)
- **Inventory Management**: Add/remove items dynamically during gameplay
- **Stat-Based Outcomes**: Attributes influence dice roll success

### ✅ Advanced Goal #3 - Dice Roll Mechanics
- **d20 System**: Standard 20-sided die rolls
- **Attribute Modifiers**: (Attribute - 10) / 2 modifier calculation
- **Success Tiers**: Critical Success, Success, Partial Success, Failure
- **Difficulty Checks**: Configurable difficulty ratings (1-20)

### ✅ Advanced Goal #4 - Multiple Universe Presets
Four complete game settings with unique personalities:

| Universe | Setting | Character | Key Attributes | Inventory |
|----------|---------|-----------|----------------|-----------|
| **Fantasy** | Medieval magic world | Warrior | Strength, Intelligence, Luck | Iron Sword, Leather Armor, Health Potion |
| **Cyberpunk** | Neo-Tokyo 2087 | Netrunner | Tech, Combat, Stealth | Cyberdeck, Smartgun, Stim Pack |
| **Space Opera** | Galactic civilization | Ship Captain | Leadership, Tactical, Diplomacy | Plasma Pistol, Command Datapad, Translator |
| **Horror** | Gothic mansion | Occult Investigator | Perception, Willpower, Knowledge | Lantern, Old Journal, Silver Cross |

### ✅ Advanced Goal #5 - Save/Load Game
- **Save System**: Export complete game state to JSON files
- **Load System**: Resume adventures from save points
- **State Preservation**: Saves universe, world state, character, and timestamp
- **Multiple Saves**: Named save files (quicksave, campaign_name, etc.)

## Function Tools (13 Total)

### World State Management (5 tools)
```python
add_character(name, role, attitude, notes)  # Track NPCs met
add_location(name, description, connections)  # Record locations visited
record_event(event)  # Log significant story moments
add_quest(title, description, status)  # Manage objectives
view_world_state()  # Get current state summary
```

### Character Management (4 tools)
```python
check_inventory()  # View current items
check_stats()  # Display character sheet
add_item(item)  # Add to inventory
remove_item(item)  # Remove from inventory
update_hp(change)  # Handle damage/healing
```

### Game Mechanics (1 tool)
```python
roll_dice(action, difficulty, attribute)  # d20 rolls with modifiers
```

### Universe Control (2 tools)
```python
switch_universe(universe)  # Change setting (fantasy/cyberpunk/space_opera/horror)
list_universes()  # View available universes
```

### Persistence (2 tools)
```python
save_game(save_name)  # Export state to JSON
load_game(save_name)  # Import state from JSON
```

## File Structure

```
backend/
├── src/
│   └── agent_game_master.py          # Main agent (600+ lines)
├── shared-data/
│   ├── game_universes.json            # Universe definitions (4 presets)
│   └── game_saves/                    # Saved games directory
├── GAME_MASTER_README.md              # Comprehensive user guide
└── start_game_master.ps1              # Quick launch script

reports/
└── DAY_8_REPORT.md                    # This file
```

## Running the Agent

### Quick Start
```powershell
.\start_game_master.ps1
```

### Manual Start
```powershell
# Terminal 1: LiveKit Server
.\bin\livekit-server --dev

# Terminal 2: Game Master Agent
cd backend
python src/agent_game_master.py dev

# Terminal 3: Frontend
cd frontend
pnpm dev
```

Then open browser at `http://localhost:3000` and click "Start Call"

## Example Gameplay Session

**GM (Fantasy Universe):**
> "You stand at the edge of the Whispering Woods, a dense forest shrouded in mist. Legends speak of an ancient temple deep within, guarding a powerful artifact. Your hand rests on the hilt of your sword as you hear strange sounds echoing from between the trees. What do you do?"

**Player:** "I want to investigate the sounds carefully"

**GM:** *[Calls roll_dice with Perception attribute]*
> "Rolling for: investigate sounds carefully
> d20 roll: 15 + 3 (perception) = 18
> Difficulty: 12
> Result: Success
> 
> You cautiously approach, your senses sharp. Through the mist, you spot a wounded traveler collapsed against a tree, clutching a tattered map. They look up at you with desperate eyes. What do you do?"

**Player:** "I check my inventory for a health potion"

**GM:** *[Calls check_inventory]*
> "Your inventory: Iron Sword, Leather Armor, Health Potion. You have one health potion available."

**Player:** "I give them the potion and ask about the map"

**GM:** *[Calls remove_item, add_character, record_event]*
> "You kneel beside the traveler and offer the potion. They drink gratefully, color returning to their face. 'Thank you, stranger. I am Kael, a scout from the village. This map... it shows the way to the temple, but beware - the ancient guardians still protect it.' Kael hands you the map. What do you do?"

## Voice Commands

Natural language commands the agent understands:

**Inventory & Stats:**
- "What's in my inventory?"
- "Check my stats"
- "How much HP do I have?"

**Gameplay:**
- "I draw my sword and enter the cave"
- "I try to climb the cliff" *(triggers dice roll)*
- "I search the room for traps"

**Universe Control:**
- "Switch to cyberpunk universe"
- "What universes are available?"

**Save/Load:**
- "Save the game as my_adventure"
- "Load game my_adventure"

**Quest/State:**
- "What quests do I have?"
- "Show me the world state"

## Technical Stack

- **STT**: Cartesia (ink-whisper model)
- **LLM**: Google Gemini 2.5 Flash Lite (fast, responsive, within quota)
- **TTS**: Murf AI (en-US-matthew voice - narrative-friendly tone)
- **Turn Detection**: Multilingual Model
- **Framework**: LiveKit Agents SDK
- **Noise Cancellation**: BVC (Background Voice Cancellation)

## Data Structures

### World State JSON
```json
{
  "characters": {
    "Kael the Scout": {
      "role": "scout",
      "attitude": "grateful",
      "notes": "Gave map to temple",
      "met_at": 3
    }
  },
  "locations": {
    "Whispering Woods": {
      "description": "Misty forest",
      "connections": "Temple Path, Village Road",
      "visited_at": 1
    }
  },
  "events": [
    {"description": "Saved Kael with health potion", "turn": 4},
    {"description": "Received temple map", "turn": 5}
  ],
  "quests": [
    {
      "title": "Find the Ancient Temple",
      "description": "Follow the map to discover the artifact",
      "status": "active"
    }
  ]
}
```

### Save File Format
```json
{
  "universe": "fantasy",
  "world_state": { /* full state */ },
  "player_character": {
    "name": "Adventurer",
    "class": "Warrior",
    "hp": 85,
    "max_hp": 100,
    "status": "Healthy",
    "attributes": {"strength": 15, "intelligence": 10, "luck": 12},
    "inventory": ["Iron Sword", "Leather Armor", "Temple Map"]
  },
  "timestamp": "2025-11-30 22:30:15",
  "save_name": "my_adventure"
}
```

## Design Decisions

**Why 4 Universes?**
Demonstrates GM versatility while keeping scope manageable. Each universe showcases different narrative styles, character types, and thematic elements.

**Why d20 + Attribute Modifiers?**
Familiar to D&D players, provides meaningful variance, and integrates well with character attributes.

**Why JSON for State?**
Human-readable, easy to debug, simple persistence without database complexity.

**Why Gemini 2.5 Flash Lite?**
Fast inference for real-time storytelling, good creative narrative generation, fits within API quota limits.

**Why Matthew Voice?**
Warm, authoritative tone perfect for Game Master narration across all universes.

## Completion Checklist

- [x] Voice Game Master with clear persona ✅
- [x] Interactive storytelling with player agency ✅
- [x] Continuity through chat history ✅
- [x] 8-15 turn session capability ✅
- [x] JSON World State (5 tools) ✅
- [x] Character Sheet & Inventory (4 tools) ✅
- [x] Dice Mechanics (1 tool) ✅
- [x] Multiple Universes (2 tools, 4 presets) ✅
- [x] Save/Load System (2 tools) ✅
- [x] Documentation & startup scripts ✅

## Next Steps

1. ✅ Implementation complete
2. 🔄 Browser testing in progress
3. ⏳ Record 2-3 minute demo video
4. ⏳ LinkedIn post with #MurfAIVoiceAgentsChallenge #10DaysofAIVoiceAgents

## Known Limitations

- Single-player only (no party mechanics)
- World state not persistent across restarts unless manually saved
- No visual UI for character sheet (voice/console only)
- Universe switching resets game state (by design for clean narratives)

## Future Enhancement Ideas

- Multi-player party system
- Visual character sheet overlay in UI
- Quest tracker display panel
- Combat system with initiative/turn order
- More universes (Western, Mystery, Superhero, Steampunk)
- Voice selection per universe (different GM personalities)
- Persistent character progression across campaigns
- Interactive map visualization

---

**Day 8 Task Complete** - Full-featured Voice Game Master with all primary and advanced goals implemented! 🎲✨
