"""
Evolution - Pet evolution system

Handles evolution stages, conditions, and transformations.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from pathlib import Path


class EvolutionStage(Enum):
    """Evolution stages for the pet - Extended to 10 stages."""
    EGG = 0
    HATCHLING = 1
    BABY = 2
    CHILD = 3
    PRE_TEEN = 4
    TEEN = 5
    YOUNG_ADULT = 6
    ADULT = 7
    ELDER = 8
    ANCIENT = 9


class EvolutionPath(Enum):
    """Different evolution paths based on playstyle."""
    BALANCED = "balanced"
    CODER = "coder"        # Evolves faster with file creation/editing
    WARRIOR = "warrior"     # Evolves faster with error fixing
    SOCIAL = "social"      # Evolves faster with interactions
    NIGHT_OWL = "night_owl" # Evolves faster with late-night coding


class Evolution:
    """Manages pet evolution mechanics."""

    # Level requirements for each stage - Updated for 10 stages
    LEVEL_REQUIREMENTS = {
        EvolutionStage.EGG: 0,
        EvolutionStage.HATCHLING: 1,
        EvolutionStage.BABY: 4,
        EvolutionStage.CHILD: 8,
        EvolutionStage.PRE_TEEN: 13,
        EvolutionStage.TEEN: 19,
        EvolutionStage.YOUNG_ADULT: 26,
        EvolutionStage.ADULT: 36,
        EvolutionStage.ELDER: 51,
        EvolutionStage.ANCIENT: 71
    }

    # Stage names
    STAGE_NAMES = {
        EvolutionStage.EGG: "Egg",
        EvolutionStage.HATCHLING: "Hatchling",
        EvolutionStage.BABY: "Baby",
        EvolutionStage.CHILD: "Child",
        EvolutionStage.PRE_TEEN: "Pre-Teen",
        EvolutionStage.TEEN: "Teen",
        EvolutionStage.YOUNG_ADULT: "Young Adult",
        EvolutionStage.ADULT: "Adult",
        EvolutionStage.ELDER: "Elder",
        EvolutionStage.ANCIENT: "Ancient"
    }

    # Sprite sizes for each stage
    STAGE_SIZES = {
        EvolutionStage.EGG: (32, 32),
        EvolutionStage.HATCHLING: (40, 40),
        EvolutionStage.BABY: (48, 48),
        EvolutionStage.CHILD: (64, 64),
        EvolutionStage.PRE_TEEN: (72, 72),
        EvolutionStage.TEEN: (80, 80),
        EvolutionStage.YOUNG_ADULT: (96, 96),
        EvolutionStage.ADULT: (112, 112),
        EvolutionStage.ELDER: (128, 128),
        EvolutionStage.ANCIENT: (160, 160)
    }

    # Special abilities unlocked per stage
    STAGE_ABILITIES = {
        EvolutionStage.EGG: [],
        EvolutionStage.HATCHLING: ["basic_emotions", "wobble"],
        EvolutionStage.BABY: ["basic_emotions", "tumble"],
        EvolutionStage.CHILD: ["basic_emotions", "particle_effects", "jump"],
        EvolutionStage.PRE_TEEN: ["basic_emotions", "particle_effects", "speech_bubbles", "jump"],
        EvolutionStage.TEEN: ["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash"],
        EvolutionStage.YOUNG_ADULT: ["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode"],
        EvolutionStage.ADULT: ["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode", "mentor_mode"],
        EvolutionStage.ELDER: ["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode", "mentor_mode", "wisdom_boost"],
        EvolutionStage.ANCIENT: ["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode", "mentor_mode", "wisdom_boost", "legendary_aura", "time_warp"]
    }

    def __init__(self):
        """Initialize evolution system."""
        self.current_path = EvolutionPath.BALANCED
        self.evolution_history: List[Dict[str, Any]] = []

    @classmethod
    def get_evolution_file(cls) -> Path:
        """Get the path to the evolution config file."""
        plugin_root = Path(__file__).parent.parent.parent.parent
        return plugin_root / 'data' / 'evolution_paths.json'

    @classmethod
    def load_evolution_data(cls) -> Dict[str, Any]:
        """Load evolution path data from file."""
        evo_file = cls.get_evolution_file()
        if evo_file.exists():
            try:
                with open(evo_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return cls._get_default_evolution_data()

    @staticmethod
    def _get_default_evolution_data() -> Dict[str, Any]:
        """Get default evolution data."""
        return {
            "paths": {
                "balanced": {
                    "name": "Balanced",
                    "description": "A well-rounded coding companion",
                    "bonus_conditions": {
                        "files_modified": 1.0,
                        "errors_fixed": 1.0,
                        "interactions": 1.0
                    },
                    "sprites": {
                        "0": "egg.png",
                        "1": "baby_balanced.png",
                        "2": "child_balanced.png",
                        "3": "teen_balanced.png",
                        "4": "adult_balanced.png",
                        "5": "elder_balanced.png",
                        "6": "ancient_balanced.png"
                    }
                },
                "coder": {
                    "name": "Coder",
                    "description": "Specializes in file manipulation",
                    "bonus_conditions": {
                        "files_created": 1.5,
                        "files_modified": 1.5,
                        "errors_fixed": 0.8,
                        "interactions": 1.0
                    },
                    "sprites": {
                        "0": "egg.png",
                        "1": "baby_coder.png",
                        "2": "child_coder.png",
                        "3": "teen_coder.png",
                        "4": "adult_coder.png",
                        "5": "elder_coder.png",
                        "6": "ancient_coder.png"
                    }
                },
                "warrior": {
                    "name": "Warrior",
                    "description": "Bug-slaying specialist",
                    "bonus_conditions": {
                        "files_created": 0.8,
                        "files_modified": 1.0,
                        "errors_fixed": 2.0,
                        "interactions": 0.8
                    },
                    "sprites": {
                        "0": "egg.png",
                        "1": "baby_warrior.png",
                        "2": "child_warrior.png",
                        "3": "teen_warrior.png",
                        "4": "adult_warrior.png",
                        "5": "elder_warrior.png",
                        "6": "ancient_warrior.png"
                    }
                },
                "social": {
                    "name": "Social",
                    "description": "Thrives on interaction",
                    "bonus_conditions": {
                        "files_created": 1.0,
                        "files_modified": 1.0,
                        "errors_fixed": 1.0,
                        "interactions": 2.0
                    },
                    "sprites": {
                        "0": "egg.png",
                        "1": "baby_social.png",
                        "2": "child_social.png",
                        "3": "teen_social.png",
                        "4": "adult_social.png",
                        "5": "elder_social.png",
                        "6": "ancient_social.png"
                    }
                },
                "night_owl": {
                    "name": "Night Owl",
                    "description": "Late-night coding specialist",
                    "bonus_conditions": {
                        "files_created": 1.2,
                        "files_modified": 1.2,
                        "errors_fixed": 1.2,
                        "interactions": 1.0,
                        "night_hours_xp": 1.5
                    },
                    "sprites": {
                        "0": "egg.png",
                        "1": "baby_night.png",
                        "2": "child_night.png",
                        "3": "teen_night.png",
                        "4": "adult_night.png",
                        "5": "elder_night.png",
                        "6": "ancient_night.png"
                    }
                }
            }
        }

    def get_current_stage(self, evolution_stage: int) -> EvolutionStage:
        """Get EvolutionStage from integer."""
        for stage in EvolutionStage:
            if stage.value == evolution_stage:
                return stage
        return EvolutionStage.EGG

    def can_evolve(self, state) -> bool:
        """Check if pet can evolve based on level and current stage."""
        current_stage = self.get_current_stage(state.evolution_stage)

        # Already at max stage
        if current_stage == EvolutionStage.ANCIENT:
            return False

        # Get next stage
        next_stage = EvolutionStage(current_stage.value + 1)
        required_level = self.LEVEL_REQUIREMENTS[next_stage]

        return state.level >= required_level

    def evolve(self, state) -> Dict[str, Any]:
        """Evolve the pet to the next stage."""
        current_stage = self.get_current_stage(state.evolution_stage)

        if current_stage == EvolutionStage.ANCIENT:
            return {
                "success": False,
                "message": "Already at max evolution stage!"
            }

        next_stage = EvolutionStage(current_stage.value + 1)
        required_level = self.LEVEL_REQUIREMENTS[next_stage]

        if state.level < required_level:
            return {
                "success": False,
                "message": f"Need level {required_level} to evolve to {self.STAGE_NAMES[next_stage]}!"
            }

        # Perform evolution
        old_stage = current_stage
        state.evolution_stage = next_stage.value
        state.update_evolution_name()

        # Record in history
        evolution_record = {
            "from_stage": old_stage.value,
            "to_stage": next_stage.value,
            "level": state.level,
            "timestamp": state.last_updated
        }
        self.evolution_history.append(evolution_record)

        # Get new abilities
        new_abilities = self.STAGE_ABILITIES.get(next_stage, [])

        return {
            "success": True,
            "old_stage": self.STAGE_NAMES[old_stage],
            "new_stage": self.STAGE_NAMES[next_stage],
            "new_abilities": new_abilities,
            "sprite_size": self.STAGE_SIZES[next_stage],
            "message": f"🌟 Evolution! {state.name} evolved into {self.STAGE_NAMES[next_stage]}!"
        }

    def determine_evolution_path(self, state) -> EvolutionPath:
        """Determine the best evolution path based on playstyle."""
        scores = {
            EvolutionPath.CODER: state.files_created * 2 + state.files_modified,
            EvolutionPath.WARRIOR: state.errors_fixed * 3,
            EvolutionPath.SOCIAL: state.times_fed * 2 + state.times_played * 2,
            EvolutionPath.NIGHT_OWL: 0  # Determined by activity time
        }

        # Check for night owl (coding past midnight)
        # This would be tracked separately in actual implementation

        return max(scores.keys(), key=lambda k: scores[k])

    def get_sprite_for_stage(self, stage: int, path: EvolutionPath = None) -> str:
        """Get sprite filename for a given stage and path."""
        if path is None:
            path = self.current_path

        data = self.load_evolution_data()
        path_key = path.value if isinstance(path, EvolutionPath) else path
        path_data = data.get("paths", {}).get(path_key, {})
        sprites = path_data.get("sprites", {})

        return sprites.get(str(stage), f"stage_{stage}.png")

    def get_abilities_for_stage(self, stage: int) -> List[str]:
        """Get abilities available at a given stage."""
        evo_stage = self.get_current_stage(stage)
        return self.STAGE_ABILITIES.get(evo_stage, [])

    def get_evolution_progress(self, state) -> Dict[str, Any]:
        """Get progress towards next evolution."""
        current_stage = self.get_current_stage(state.evolution_stage)

        if current_stage == EvolutionStage.ANCIENT:
            return {
                "current_stage": "Ancient",
                "next_stage": None,
                "level_required": None,
                "current_level": state.level,
                "ready": True,
                "progress_percent": 100
            }

        next_stage = EvolutionStage(current_stage.value + 1)
        required_level = self.LEVEL_REQUIREMENTS[next_stage]

        # Calculate progress (from previous level requirement to next)
        prev_level = self.LEVEL_REQUIREMENTS[current_stage]
        levels_gained = state.level - prev_level
        levels_needed = required_level - prev_level

        progress = min(100, int((levels_gained / levels_needed) * 100))

        return {
            "current_stage": self.STAGE_NAMES[current_stage],
            "next_stage": self.STAGE_NAMES[next_stage],
            "level_required": required_level,
            "current_level": state.level,
            "levels_until": required_level - state.level,
            "ready": state.level >= required_level,
            "progress_percent": progress
        }


# Convenience functions
def check_evolution(state) -> Optional[Dict[str, Any]]:
    """Check and perform evolution if ready."""
    evo = Evolution()
    if evo.can_evolve(state):
        return evo.evolve(state)
    return None


def get_evolution_info(state) -> Dict[str, Any]:
    """Get evolution progress information."""
    evo = Evolution()
    return evo.get_evolution_progress(state)


def get_sprite_info(state) -> tuple[str, tuple[int, int]]:
    """Get sprite filename and size for current state."""
    evo = Evolution()
    stage = evo.get_current_stage(state.evolution_stage)
    sprite = evo.get_sprite_for_stage(state.evolution_stage)
    size = evo.STAGE_SIZES.get(stage, (64, 64))
    return sprite, size


if __name__ == "__main__":
    from pet_state import PetState

    # Test evolution system
    state = PetState()
    evo = Evolution()

    print("Testing Evolution System")
    print(f"Current stage: {evo.get_current_stage(state.evolution_stage).name}")

    # Set level high enough to evolve
    state.level = 10
    print(f"Level set to {state.level}")

    progress = evo.get_evolution_progress(state)
    print(f"Evolution progress: {progress}")

    if evo.can_evolve(state):
        result = evo.evolve(state)
        print(f"Evolution result: {result}")
