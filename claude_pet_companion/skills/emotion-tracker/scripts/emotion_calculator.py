"""
EmotionCalculator - Calculates pet emotions from state and activity data

Analyzes various factors to determine the pet's current emotional state.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum


class Emotion(Enum):
    """Pet emotion states."""
    CONTENT = "content"
    HAPPY = "happy"
    EXCITED = "excited"
    ECSTATIC = "ecstatic"
    WORRIED = "worried"
    SAD = "sad"
    SLEEPY = "sleepy"
    HUNGRY = "hungry"
    CONFUSED = "confused"
    PROUD = "proud"
    LONELY = "lonely"


class EmotionCalculator:
    """Calculates pet emotions based on state and activities."""

    # Emotion weights for different factors
    WEIGHTS = {
        "happiness": 0.3,
        "hunger": 0.2,
        "energy": 0.2,
        "success_streak": 0.15,
        "failure_streak": -0.1,
        "interaction": 0.15
    }

    # Thresholds for emotion triggers
    CRITICAL_THRESHOLD = 20
    WARNING_THRESHOLD = 50
    HIGH_THRESHOLD = 80

    def __init__(self):
        """Initialize emotion calculator."""
        self.last_emotion = Emotion.CONTENT
        self.emotion_history: List[Tuple[str, str]] = []

    def calculate_emotion(self, state) -> Emotion:
        """Calculate the pet's current emotion."""
        # Check critical states first (highest priority)
        if state.is_sleeping:
            return Emotion.SLEEPY

        if state.hunger <= self.CRITICAL_THRESHOLD:
            return Emotion.HUNGRY

        if state.energy <= self.CRITICAL_THRESHOLD:
            return Emotion.SLEEPY

        # Check failure streak
        if state.consecutive_failures >= 5:
            return Emotion.WORRIED

        if state.consecutive_failures >= 3:
            if state.happiness <= self.CRITICAL_THRESHOLD:
                return Emotion.SAD
            return Emotion.CONFUSED

        # Check success streak
        if state.consecutive_successes >= 20:
            return Emotion.ECSTATIC

        if state.consecutive_successes >= 10:
            return Emotion.EXCITED

        # Check for loneliness (no recent interaction)
        if self._is_lonely(state):
            return Emotion.LONELY

        # Check for pride (recent level up or achievement)
        if self._recently_accomplished(state):
            return Emotion.PROUD

        # Calculate overall mood from stats
        avg_stats = (state.happiness + state.hunger + state.energy) / 3

        if avg_stats >= self.HIGH_THRESHOLD:
            return Emotion.HAPPY

        if state.happiness <= self.WARNING_THRESHOLD:
            return Emotion.SAD

        # Default
        return Emotion.CONTENT

    def _is_lonely(self, state) -> bool:
        """Check if pet is lonely due to lack of interaction."""
        if not state.last_interaction:
            # New pet, not lonely yet
            return False

        try:
            last_interaction = datetime.fromisoformat(state.last_interaction)
            hours_since = (datetime.now() - last_interaction).total_seconds() / 3600
            return hours_since > 4  # Lonely after 4 hours no interaction
        except (ValueError, TypeError):
            return False

    def _recently_accomplished(self, state) -> bool:
        """Check if pet recently had an accomplishment."""
        try:
            last_updated = datetime.fromisoformat(state.last_updated)
            minutes_since = (datetime.now() - last_updated).total_seconds() / 60
            # Proud if leveled up or got achievement in last 5 minutes
            # (In real implementation, would check specific flags)
            return minutes_since < 5
        except (ValueError, TypeError):
            return False

    def get_emotion_change(self, old_emotion: str, new_emotion: Emotion) -> str:
        """Get description of emotion change."""
        old = old_emotion.lower()
        new = new_emotion.value.lower()

        if old == new:
            return f"{state.name if 'state' in globals() else 'Pet'} is feeling {new}."

        transitions = {
            ("content", "happy"): "perked up",
            ("content", "worried"): "became concerned",
            ("content", "sad"): "looks down",
            ("content", "sleepy"): "is getting tired",
            ("content", "hungry"): "is feeling hungry",
            ("sad", "happy"): "cheered up!",
            ("worried", "content"): "calmed down",
            ("worried", "happy"): "feels relieved!",
            ("sleepy", "content"): "woke up",
            ("hungry", "content"): "is satisfied",
            ("happy", "excited"): "is super happy!",
            ("happy", "ecstatic"): "is overjoyed!"
        }

        return transitions.get((old, new), f"went from {old} to {new}")

    def get_emotion_emoji(self, emotion: Emotion) -> str:
        """Get emoji for an emotion."""
        emojis = {
            Emotion.CONTENT: "😊",
            Emotion.HAPPY: "😄",
            Emotion.EXCITED: "🤩",
            Emotion.ECSTATIC: "🥳",
            Emotion.WORRIED: "😟",
            Emotion.SAD: "😢",
            Emotion.SLEEPY: "😴",
            Emotion.HUNGRY: "😋",
            Emotion.CONFUSED: "😕",
            Emotion.PROUD: "😎",
            Emotion.LONELY: "😔"
        }
        return emojis.get(emotion, "🐾")

    def get_emotion_color(self, emotion: Emotion) -> str:
        """Get color associated with an emotion (for UI)."""
        colors = {
            Emotion.CONTENT: "#4CAF50",      # Green
            Emotion.HAPPY: "#FFEB3B",        # Yellow
            Emotion.EXCITED: "#FF9800",      # Orange
            Emotion.ECSTATIC: "#E91E63",     # Pink
            Emotion.WORRIED: "#9C27B0",      # Purple
            Emotion.SAD: "#607D8B",          # Blue Gray
            Emotion.SLEEPY: "#3F51B5",       # Indigo
            Emotion.HUNGRY: "#FF5722",       # Deep Orange
            Emotion.CONFUSED: "#00BCD4",     # Cyan
            Emotion.PROUD: "#FFC107",        # Amber
            Emotion.LONELY: "#795548"        # Brown
        }
        return colors.get(emotion, "#999999")

    def get_emotion_description(self, emotion: Emotion) -> str:
        """Get a text description of what the pet is feeling."""
        descriptions = {
            Emotion.CONTENT: "feeling content and balanced",
            Emotion.HAPPY: "feeling happy and energetic",
            Emotion.EXCITED: "bursting with excitement!",
            Emotion.ECSTATIC: "absolutely overjoyed!",
            Emotion.WORRIED: "a bit worried about things",
            Emotion.SAD: "feeling a bit down",
            Emotion.SLEEPY: "getting very sleepy",
            Emotion.HUNGRY: "quite hungry right now",
            Emotion.CONFUSED: "feeling a bit confused",
            Emotion.PROUD: "very proud of recent work!",
            Emotion.LONELY: "feeling lonely and wants attention"
        }
        return descriptions.get(emotion, "feeling okay")

    def record_emotion(self, emotion: Emotion):
        """Record an emotion in history."""
        self.last_emotion = emotion
        self.emotion_history.append((datetime.now().isoformat(), emotion.value))

        # Keep only last 100 emotions
        if len(self.emotion_history) > 100:
            self.emotion_history = self.emotion_history[-100:]

    def get_emotion_summary(self, state) -> Dict:
        """Get a complete emotion summary."""
        emotion = self.calculate_emotion(state)

        return {
            "emotion": emotion.value,
            "emoji": self.get_emotion_emoji(emotion),
            "color": self.get_emotion_color(emotion),
            "description": self.get_emotion_description(emotion),
            "factors": {
                "happiness": state.happiness,
                "hunger": state.hunger,
                "energy": state.energy,
                "success_streak": state.consecutive_successes,
                "failure_streak": state.consecutive_failures
            }
        }


# Convenience functions
def calculate_emotion(state) -> str:
    """Calculate current emotion for a state."""
    calculator = EmotionCalculator()
    emotion = calculator.calculate_emotion(state)
    return emotion.value


def update_and_get_emotion(state) -> Dict:
    """Update state mood and return emotion summary."""
    calculator = EmotionCalculator()
    emotion = calculator.calculate_emotion(state)

    # Update state
    state.update_mood(emotion.value)
    calculator.record_emotion(emotion)

    return calculator.get_emotion_summary(state)


def get_emotion_display(emotion: str) -> Tuple[str, str]:
    """Get emoji and color for an emotion string."""
    try:
        emotion_enum = Emotion(emotion.lower())
        calculator = EmotionCalculator()
        return (
            calculator.get_emotion_emoji(emotion_enum),
            calculator.get_emotion_color(emotion_enum)
        )
    except (ValueError, KeyError):
        return "🐾", "#999999"


if __name__ == "__main__":
    from pet_state import PetState

    # Test emotion calculator
    state = PetState()
    calculator = EmotionCalculator()

    print("Testing EmotionCalculator")

    # Test various states
    state.hunger = 80
    state.happiness = 90
    state.energy = 85
    state.consecutive_successes = 15

    summary = calculator.get_emotion_summary(state)
    print(f"Emotion: {summary['emotion']} {summary['emoji']}")
    print(f"Description: {summary['description']}")

    # Test sad state
    state.happiness = 20
    summary = calculator.get_emotion_summary(state)
    print(f"\nAfter sadness: {summary['emotion']} {summary['emoji']}")
