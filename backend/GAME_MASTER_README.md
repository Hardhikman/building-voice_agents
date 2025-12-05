# Day 8: Voice Game Master Agent 🎲

A D&D-style voice Game Master agent that runs interactive story sessions across multiple universes.

## Features Implemented

### ✅ Primary Goal
- **Interactive Voice Storytelling**: Immersive narration with player action prompts
- **Continuity**: Remembers player decisions and past events through chat history
- **Rich Descriptions**: Vivid scene-setting and atmospheric storytelling

### ✅ Advanced Goals (All Implemented!)

1. **JSON World State System**
   - Tracks NPCs, locations, events, and quests
   - Maintains story consistency across the session
   - Console logging for debugging

2. **Character Sheet & Inventory**
   - HP tracking with status (Healthy/Injured/Critical)
   - Attribute system (Strength, Intelligence, Luck, etc.)
   - Dynamic inventory management
   - Stat-based outcomes

3. **Dice Roll Mechanics**
   - d20 rolls with attribute modifiers
   - Difficulty checks
   - Success tiers: Critical Success, Success, Partial Success, Failure

4. **Multiple Universe Presets**
   - **Classic Fantasy**: Dragons, magic, medieval quests
   - **Cyberpunk City**: Neo-Tokyo 2087, hackers and corps
   - **Space Opera**: Galactic adventures across alien worlds
   - **Gothic Horror**: Haunted mansions and supernatural terrors
   - Switch universes mid-session or start fresh

5. **Save/Load Game**
   - Save game state to JSON files
   - Resume adventures from save points
   - Preserves world state, character, and progress

## Available Tools

### World State
- `add_character(name, role, attitude, notes)` - Track NPCs
- `add_location(name, description, connections)` - Track locations
- `record_event(event)` - Log significant events
- `add_quest(title, description, status)` - Manage quests
- `view_world_state()` - Get current state summary

### Character Management
- `check_inventory()` - View items
- `check_stats()` - View character stats
- `add_item(item)` - Add to inventory
- `remove_item(item)` - Remove from inventory
- `update_hp(change)` - Heal or damage player

### Game Mechanics
- `roll_dice(action, difficulty, attribute)` - Roll for actions

### Universe Control
- `switch_universe(universe)` - Change to different setting
- `list_universes()` - See available universes

### Save/Load
- `save_game(save_name)` - Save current game
- `load_game(save_name)` - Load saved game

## Quick Start

### Option 1: Use the Startup Script
```powershell
.\start_game_master.ps1
```

### Option 2: Manual Start
```powershell
# Terminal 1: Start LiveKit Server
.\bin\livekit-server --dev

# Terminal 2: Start Game Master Agent
cd backend
python -m uv run python src/agent_game_master.py dev

# Terminal 3: Start Frontend
cd frontend
pnpm dev
```

### Option 3: Use Existing Script (modify agent path)
Edit `start_app.ps1` line 6:
```powershell
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd backend; python -m uv run python src/agent_game_master.py dev"
```

## How to Play

1. **Start a Session**: Click "Start Call" in the web interface
2. **Listen to the GM**: The Game Master will describe the opening scene
3. **Speak Your Actions**: Use your voice to respond ("I draw my sword and enter the cave")
4. **Ask Questions**: 
   - "What's in my inventory?"
   - "Check my stats"
   - "What quests do I have?"
5. **Roll Dice**: Attempt risky actions - the GM will automatically roll when needed
6. **Switch Universes**: Say "Switch to cyberpunk universe" to change settings
7. **Save Your Progress**: "Save the game as my_adventure"
8. **Load Later**: "Load game my_adventure"

## Example Gameplay

**GM**: *"You stand at the edge of the Whispering Woods, a dense forest shrouded in mist. Legends speak of an ancient temple deep within, guarding a powerful artifact. Your hand rests on the hilt of your sword as you hear strange sounds echoing from between the trees. What do you do?"*

**Player**: "I want to investigate the sounds carefully"

**GM**: *[Calls roll_dice tool]* "You rolled 15! You cautiously move closer and spot glowing eyes in the undergrowth. A magnificent silver wolf emerges, watching you intently. What do you do?"

## Universe Details

### Fantasy
- Setting: Medieval world of magic
- Character: Adventurer/Warrior
- Attributes: Strength, Intelligence, Luck
- Starting Items: Iron Sword, Leather Armor, Health Potion

### Cyberpunk
- Setting: Neo-Tokyo 2087
- Character: Netrunner
- Attributes: Tech, Combat, Stealth
- Starting Items: Cyberdeck, Smartgun, Stim Pack

### Space Opera
- Setting: Galactic civilization
- Character: Ship Captain
- Attributes: Leadership, Tactical, Diplomacy
- Starting Items: Plasma Pistol, Command Datapad, Translator

### Horror
- Setting: Gothic mansion
- Character: Occult Investigator
- Attributes: Perception, Willpower, Knowledge
- Starting Items: Lantern, Old Journal, Silver Cross

## Data Files

- **game_universes.json**: Universe definitions and templates
- **game_saves/** directory: Saved game states

## Architecture

The agent uses:
- **LiveKit Agents SDK**: Voice pipeline
- **Murf TTS**: High-quality text-to-speech (en-US-matthew voice)
- **Gemini 2.0 Flash**: Fast LLM for GM narration
- **Cartesia STT**: Speech-to-text for player input
- **Function Tools**: All game mechanics as callable tools

## Tips for Best Experience

1. **Speak Clearly**: Describe your actions naturally
2. **Be Specific**: "I search the room for traps" vs "I look around"
3. **Roleplay**: Get into character for immersion
4. **Use Tools**: Ask to check stats, inventory, or world state
5. **Save Often**: Use save/load for longer campaigns
6. **Try Different Universes**: Each has unique flavor

## Day 8 Completion Checklist

- [x] Voice Game Master with clear persona ✅
- [x] Interactive storytelling with voice ✅
- [x] Continuity through chat history ✅
- [x] 8-15 turn session capability ✅
- [x] JSON world state tracking ✅
- [x] Character sheet & inventory ✅
- [x] Dice mechanics ✅
- [x] Multiple universes ✅
- [x] Save/load system ✅
- [ ] Browser testing ⏳
- [ ] Record demo video ⏳
- [ ] LinkedIn post ⏳

## Next Steps

1. Test the agent in browser
2. Record a demo gameplay session
3. Post to LinkedIn with #MurfAIVoiceAgentsChallenge #10DaysofAIVoiceAgents

Enjoy your adventure! 🎲✨
