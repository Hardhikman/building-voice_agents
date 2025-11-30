import logging
import asyncio
import json
import os
import sys
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
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

logger = logging.getLogger("game-master-agent")

load_dotenv(".env.local")


class GameMasterAgent(Agent):
    """D&D-style Voice Game Master Agent with full RPG mechanics."""

    def __init__(self, universe: str = "fantasy") -> None:
        # Load universes from JSON
        universes_path = Path(__file__).parent.parent / "shared-data" / "game_universes.json"
        try:
            with open(universes_path, "r") as f:
                self.universes = json.load(f)
            logger.info(f"Loaded {len(self.universes)} universes from {universes_path}")
        except Exception as e:
            logger.error(f"Failed to load universes: {e}")
            self.universes = {}
        
        # Set current universe
        self.current_universe = universe
        if universe not in self.universes:
            logger.warning(f"Universe '{universe}' not found, defaulting to 'fantasy'")
            self.current_universe = "fantasy"
        
        universe_data = self.universes.get(self.current_universe, {})
        
        # Initialize world state (JSON state system - Advanced Goal #1)
        self.world_state = {
            "characters": {},  # NPCs the player has met
            "locations": {},   # Places visited
            "events": [],      # Key events that happened
            "quests": []       # Active and completed quests
        }
        
        # Initialize player character (Advanced Goal #2)
        player_template = universe_data.get("player_template", {})
        self.player_character = {
            "name": player_template.get("name", "Adventurer"),
            "class": player_template.get("class", "Wanderer"),
            "hp": player_template.get("hp", 100),
            "max_hp": player_template.get("max_hp", 100),
            "status": "Healthy",
            "attributes": player_template.get("attributes", {
                "strength": 10,
                "intelligence": 10,
                "luck": 10
            }),
            "inventory": player_template.get("inventory", []).copy()
        }
        
        # Starting scenario
        self.starting_scenario = universe_data.get("starting_scenario", "The adventure begins...")
        
        # Construct system instructions
        base_prompt = universe_data.get("system_prompt", "You are a Game Master.")
        additional_context = f"""
        
WORLD STATE MANAGEMENT:
- Track important NPCs the player meets in the characters field
- Track locations the player visits
- Record significant events and decisions
- Manage active quests and objectives

PLAYER CHARACTER:
- Name: {self.player_character['name']}
- Class: {self.player_character['class']}
- HP: {self.player_character['hp']}/{self.player_character['max_hp']}
- Attributes: {', '.join(f'{k}: {v}' for k, v in self.player_character['attributes'].items())}
- Starting Inventory: {', '.join(self.player_character['inventory'])}

MECHANICS:
- When player attempts risky actions, call the roll_dice tool
- Update character HP, inventory, and stats as the story progresses
- Use world state to maintain consistency
- If player asks about inventory or stats, call the appropriate tool

Remember to:
1. Be vivid and immersive in your descriptions
2. Give the player agency - let their choices matter
3. End each response with a prompt for player action
4. Reference past events and decisions to maintain continuity
"""
        
        super().__init__(
            instructions=base_prompt + additional_context
        )
    
    async def on_enter(self) -> None:
        """Called when this agent becomes active."""
        self.session.tts = murf.TTS(
            voice="en-US-matthew",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        )
        
        # Start the adventure with the opening scenario
        await self.session.generate_reply(
            instructions=f"""Begin the adventure by narrating the opening scene:

{self.starting_scenario}

Be dramatic and engaging. Set the mood and atmosphere. Then ask the player what they do."""
        )

    # ===== WORLD STATE TOOLS (Advanced Goal #1) =====
    
    @function_tool()
    async def add_character(
        self, 
        context: RunContext, 
        name: str, 
        role: str, 
        attitude: str = "neutral",
        notes: str = ""
    ):
        """Track a new NPC character the player has met.
        
        Args:
            name: Character's name
            role: Their role (merchant, guard, wizard, etc.)
            attitude: Their attitude toward player (friendly, hostile, neutral)
            notes: Additional notes about this character
        """
        self.world_state["characters"][name] = {
            "role": role,
            "attitude": attitude,
            "notes": notes,
            "met_at": len(self.world_state["events"])
        }
        logger.info(f"Added character: {name} ({role}, {attitude})")
        return f"Noted: {name} the {role} (attitude: {attitude})"
    
    @function_tool()
    async def add_location(
        self,
        context: RunContext,
        name: str,
        description: str,
        connections: str = ""
    ):
        """Track a location the player has visited.
        
        Args:
            name: Location name
            description: Brief description
            connections: Connected locations or paths
        """
        self.world_state["locations"][name] = {
            "description": description,
            "connections": connections,
            "visited_at": len(self.world_state["events"])
        }
        logger.info(f"Added location: {name}")
        return f"Location tracked: {name}"
    
    @function_tool()
    async def record_event(self, context: RunContext, event: str):
        """Record a significant event or player decision.
        
        Args:
            event: Description of the event
        """
        self.world_state["events"].append({
            "description": event,
            "turn": len(self.world_state["events"]) + 1
        })
        logger.info(f"Event recorded: {event}")
        return f"Event recorded: {event}"
    
    @function_tool()
    async def add_quest(
        self,
        context: RunContext,
        title: str,
        description: str,
        status: str = "active"
    ):
        """Track a quest or objective.
        
        Args:
            title: Quest title
            description: Quest details
            status: Quest status (active, completed, failed)
        """
        quest = {
            "title": title,
            "description": description,
            "status": status
        }
        self.world_state["quests"].append(quest)
        logger.info(f"Quest added: {title} ({status})")
        return f"Quest {status}: {title}"
    
    @function_tool()
    async def view_world_state(self, context: RunContext):
        """Get a summary of the current world state."""
        summary = []
        
        if self.world_state["characters"]:
            chars = ", ".join(self.world_state["characters"].keys())
            summary.append(f"Characters met: {chars}")
        
        if self.world_state["locations"]:
            locs = ", ".join(self.world_state["locations"].keys())
            summary.append(f"Locations visited: {locs}")
        
        if self.world_state["quests"]:
            active_quests = [q["title"] for q in self.world_state["quests"] if q["status"] == "active"]
            if active_quests:
                summary.append(f"Active quests: {', '.join(active_quests)}")
        
        logger.info(f"World state: {json.dumps(self.world_state, indent=2)}")
        
        if summary:
            return "Current world state:\n" + "\n".join(summary)
        else:
            return "The adventure has just begun. No major events yet."
    
    # ===== CHARACTER SHEET TOOLS (Advanced Goal #2) =====
    
    @function_tool()
    async def check_inventory(self, context: RunContext):
        """Show the player's current inventory."""
        if not self.player_character["inventory"]:
            return "Your inventory is empty."
        
        items = ", ".join(self.player_character["inventory"])
        return f"Your inventory: {items}"
    
    @function_tool()
    async def check_stats(self, context: RunContext):
        """Show the player character's stats and status."""
        pc = self.player_character
        stats = []
        stats.append(f"Name: {pc['name']} the {pc['class']}")
        stats.append(f"HP: {pc['hp']}/{pc['max_hp']} ({pc['status']})")
        
        for attr, value in pc["attributes"].items():
            stats.append(f"{attr.capitalize()}: {value}")
        
        return "\n".join(stats)
    
    @function_tool()
    async def add_item(self, context: RunContext, item: str):
        """Add an item to the player's inventory.
        
        Args:
            item: Name of the item to add
        """
        self.player_character["inventory"].append(item)
        logger.info(f"Added item: {item}")
        return f"Added {item} to your inventory."
    
    @function_tool()
    async def remove_item(self, context: RunContext, item: str):
        """Remove an item from the player's inventory.
        
        Args:
            item: Name of the item to remove
        """
        if item in self.player_character["inventory"]:
            self.player_character["inventory"].remove(item)
            logger.info(f"Removed item: {item}")
            return f"Removed {item} from your inventory."
        else:
            return f"You don't have {item} in your inventory."
    
    @function_tool()
    async def update_hp(self, context: RunContext, change: int):
        """Update the player's HP (positive for healing, negative for damage).
        
        Args:
            change: Amount to change HP by
        """
        old_hp = self.player_character["hp"]
        self.player_character["hp"] = max(0, min(
            self.player_character["max_hp"],
            self.player_character["hp"] + change
        ))
        new_hp = self.player_character["hp"]
        
        # Update status
        hp_percent = (new_hp / self.player_character["max_hp"]) * 100
        if hp_percent >= 75:
            self.player_character["status"] = "Healthy"
        elif hp_percent >= 40:
            self.player_character["status"] = "Injured"
        elif hp_percent > 0:
            self.player_character["status"] = "Critical"
        else:
            self.player_character["status"] = "Unconscious"
        
        logger.info(f"HP changed: {old_hp} -> {new_hp} ({self.player_character['status']})")
        
        if change > 0:
            return f"You heal {change} HP. Current HP: {new_hp}/{self.player_character['max_hp']}"
        else:
            return f"You take {abs(change)} damage! Current HP: {new_hp}/{self.player_character['max_hp']}"
    
    # ===== DICE MECHANICS (Advanced Goal #3) =====
    
    @function_tool()
    async def roll_dice(
        self,
        context: RunContext,
        action: str,
        difficulty: int = 10,
        attribute: str = "luck"
    ):
        """Roll dice to determine the outcome of an action.
        
        Args:
            action: What the player is attempting
            difficulty: Difficulty rating (1-20, default 10)
            attribute: Which attribute to use for modifier (strength, intelligence, luck, etc.)
        """
        # Roll a d20
        roll = random.randint(1, 20)
        
        # Get attribute modifier
        attr_value = self.player_character["attributes"].get(attribute.lower(), 10)
        # Modifier is (attribute - 10) / 2, rounded down
        modifier = (attr_value - 10) // 2
        
        total = roll + modifier
        
        # Determine success level
        if total >= difficulty + 5:
            outcome = "Critical Success"
        elif total >= difficulty:
            outcome = "Success"
        elif total >= difficulty - 3:
            outcome = "Partial Success"
        else:
            outcome = "Failure"
        
        result = f"Rolling for: {action}\n"
        result += f"d20 roll: {roll} + {modifier} ({attribute}) = {total}\n"
        result += f"Difficulty: {difficulty}\n"
        result += f"Result: {outcome}"
        
        logger.info(result)
        return result
    
    # ===== UNIVERSE SWITCHING (Advanced Goal #4) =====
    
    @function_tool()
    async def switch_universe(self, context: RunContext, universe: str):
        """Switch to a different universe/setting.
        
        Args:
            universe: Universe to switch to (fantasy, cyberpunk, space_opera, horror)
        """
        if universe not in self.universes:
            available = ", ".join(self.universes.keys())
            return f"Universe '{universe}' not found. Available: {available}"
        
        self.current_universe = universe
        universe_data = self.universes[universe]
        
        # Reset world state and character for new universe
        self.world_state = {
            "characters": {},
            "locations": {},
            "events": [],
            "quests": []
        }
        
        player_template = universe_data.get("player_template", {})
        self.player_character = {
            "name": player_template.get("name", "Adventurer"),
            "class": player_template.get("class", "Wanderer"),
            "hp": player_template.get("hp", 100),
            "max_hp": player_template.get("max_hp", 100),
            "status": "Healthy",
            "attributes": player_template.get("attributes", {}),
            "inventory": player_template.get("inventory", []).copy()
        }
        
        self.starting_scenario = universe_data.get("starting_scenario", "")
        
        logger.info(f"Switched to universe: {universe}")
        return f"Switched to {universe_data['name']}! Starting new adventure..."
    
    @function_tool()
    async def list_universes(self, context: RunContext):
        """List all available universes."""
        universes_list = []
        for key, data in self.universes.items():
            universes_list.append(f"{key}: {data['name']} - {data['description']}")
        return "Available universes:\n" + "\n".join(universes_list)
    
    # ===== SAVE/LOAD GAME (Advanced Goal #5) =====
    
    @function_tool()
    async def save_game(self, context: RunContext, save_name: str = "quicksave"):
        """Save the current game state to a file.
        
        Args:
            save_name: Name for the save file
        """
        save_data = {
            "universe": self.current_universe,
            "world_state": self.world_state,
            "player_character": self.player_character,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "save_name": save_name
        }
        
        # Create saves directory if it doesn't exist
        saves_dir = Path(__file__).parent.parent / "shared-data" / "game_saves"
        saves_dir.mkdir(exist_ok=True)
        
        save_file = saves_dir / f"{save_name}.json"
        
        try:
            with open(save_file, "w") as f:
                json.dump(save_data, f, indent=2)
            logger.info(f"Game saved to {save_file}")
            return f"Game saved as '{save_name}' at {save_data['timestamp']}"
        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return f"Error saving game: {e}"
    
    @function_tool()
    async def load_game(self, context: RunContext, save_name: str = "quicksave"):
        """Load a previously saved game.
        
        Args:
            save_name: Name of the save file to load
        """
        saves_dir = Path(__file__).parent.parent / "shared-data" / "game_saves"
        save_file = saves_dir / f"{save_name}.json"
        
        if not save_file.exists():
            return f"Save file '{save_name}' not found."
        
        try:
            with open(save_file, "r") as f:
                save_data = json.load(f)
            
            self.current_universe = save_data["universe"]
            self.world_state = save_data["world_state"]
            self.player_character = save_data["player_character"]
            
            logger.info(f"Game loaded from {save_file}")
            return f"Game loaded from '{save_name}' (saved at {save_data['timestamp']}). Resuming adventure..."
        except Exception as e:
            logger.error(f"Failed to load game: {e}")
            return f"Error loading game: {e}"


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    # Create the game master agent (default to fantasy universe)
    agent = GameMasterAgent(universe="fantasy")

    # Create agent session
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
