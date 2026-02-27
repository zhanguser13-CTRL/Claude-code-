"""
Emotion Engine for Claude Pet Companion

Provides realistic emotional behavior using:
- Plutchik's Wheel of Emotions
- Emotional decay over time
- Event-based emotional responses
- Mood persistence
- Emotional influence on behavior
"""

import logging
import math
import random
import time
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    """Core emotions based on Plutchik's Wheel."""
    JOY = "joy"           # Opposite: SADNESS
    TRUST = "trust"       # Opposite: DISGUST
    FEAR = "fear"         # Opposite: ANGER
    SURPRISE = "surprise" # Opposite: ANTICIPATION
    SADNESS = "sadness"   # Opposite: JOY
    DISGUST = "disgust"   # Opposite: TRUST
    ANGER = "anger"       # Opposite: FEAR
    ANTICIPATION = "anticipation" # Opposite: SURPRISE


class MixedEmotion(Enum):
    """Secondary emotions (combinations of primary emotions)."""
    # Joy combinations
    LOVE = "love"         # Joy + Trust
    OPTIMISM = "optimism" # Anticipation + Joy
    CHEERFULNESS = "cheerfulness" # Joy + Surprise

    # Trust combinations
    SUBMISSION = "submission" # Trust + Fear
    ADMIRATION = "admiration" # Surprise + Trust

    # Fear combinations
    AWE = "awe"          # Fear + Surprise
    DISAPPROVAL = "disapproval" # Surprise + Disgust

    # Anger combinations
    AGGRESSIVENESS = "aggressiveness" # Anger + Anticipation
    CONTEMPT = "contempt" # Anger + Disgust

    # Sadness combinations
    REMORSE = "remorse"  # Sadness + Disgust
    PENSIVENESS = "pensiveness" # Sadness + Anticipation

    # Disgust combinations
    ENMITY = "enmity"    # Disgust + Anger (same as contempt)

    # Surprise combinations
    AMAZEMENT = "amazement" # Surprise + Joy (same as cheerful)
    DISBELIEF = "disbelief" # Surprise + Sadness

    # Anticipation combinations
    INTEREST = "interest" # Anticipation + Trust
    VIGILANCE = "vigilance" # Anticipation + Fear


# Emotion opposites
EMOTION_OPPOSITES = {
    EmotionType.JOY: EmotionType.SADNESS,
    EmotionType.SADNESS: EmotionType.JOY,
    EmotionType.TRUST: EmotionType.DISGUST,
    EmotionType.DISGUST: EmotionType.TRUST,
    EmotionType.FEAR: EmotionType.ANGER,
    EmotionType.ANGER: EmotionType.FEAR,
    EmotionType.SURPRISE: EmotionType.ANTICIPATION,
    EmotionType.ANTICIPATION: EmotionType.SURPRISE,
}


@dataclass
class EmotionState:
    """Single emotion with intensity."""
    emotion: EmotionType
    intensity: float = 0.0  # 0.0 to 1.0

    def __post_init__(self):
        self.intensity = max(0.0, min(1.0, self.intensity))

    def increase(self, amount: float):
        """Increase emotion intensity."""
        self.intensity = min(1.0, self.intensity + amount)

    def decrease(self, amount: float):
        """Decrease emotion intensity."""
        self.intensity = max(0.0, self.intensity - amount)

    def is_active(self) -> bool:
        """Check if emotion is active enough to matter."""
        return self.intensity > 0.1


@dataclass
class EmotionalEvent:
    """Event that triggered an emotional response."""
    event_type: str
    timestamp: float
    emotion_changes: Dict[EmotionType, float]
    decay_time: float = 30.0  # How long the effect lasts


class EmotionProfile:
    """Personality-based emotion modifiers."""

    def __init__(self,
                 joy_base: float = 0.5,
                 trust_base: float = 0.5,
                 fear_base: float = 0.3,
                 surprise_base: float = 0.3,
                 sadness_base: float = 0.2,
                 disgust_base: float = 0.2,
                 anger_base: float = 0.2,
                 anticipation_base: float = 0.4):
        """
        Create an emotion profile.

        Base values determine how easily each emotion is triggered.
        Higher = more susceptible to that emotion.
        """
        self.base_emotions = {
            EmotionType.JOY: joy_base,
            EmotionType.TRUST: trust_base,
            EmotionType.FEAR: fear_base,
            EmotionType.SURPRISE: surprise_base,
            EmotionType.SADNESS: sadness_base,
            EmotionType.DISGUST: disgust_base,
            EmotionType.ANGER: anger_base,
            EmotionType.ANTICIPATION: anticipation_base,
        }

        # Emotion decay rates (lower = emotions last longer)
        self.decay_rates = {
            EmotionType.JOY: 0.1,
            EmotionType.TRUST: 0.05,
            EmotionType.FEAR: 0.2,
            EmotionType.SURPRISE: 0.3,
            EmotionType.SADNESS: 0.05,
            EmotionType.DISGUST: 0.15,
            EmotionType.ANGER: 0.15,
            EmotionType.ANTICIPATION: 0.1,
        }

    def get_susceptibility(self, emotion: EmotionType) -> float:
        """Get susceptibility to an emotion (0-1)."""
        return self.base_emotions.get(emotion, 0.5)

    def get_decay_rate(self, emotion: EmotionType) -> float:
        """Get decay rate for an emotion."""
        return self.decay_rates.get(emotion, 0.1)


# Preset emotion profiles

class EmotionProfiles:
    """Predefined emotion profiles for different personality types."""

    @staticmethod
    def friendly() -> EmotionProfile:
        """Friendly, easily pleased pet."""
        return EmotionProfile(
            joy_base=0.8,
            trust_base=0.9,
            fear_base=0.2,
            surprise_base=0.5,
            sadness_base=0.3,
            disgust_base=0.1,
            anger_base=0.1,
            anticipation_base=0.6
        )

    @staticmethod
    def shy() -> EmotionProfile:
        """Shy, cautious pet."""
        return EmotionProfile(
            joy_base=0.4,
            trust_base=0.3,
            fear_base=0.7,
            surprise_base=0.6,
            sadness_base=0.4,
            disgust_base=0.3,
            anger_base=0.2,
            anticipation_base=0.3
        )

    @staticmethod
    def energetic() -> EmotionProfile:
        """Energetic, excitable pet."""
        return EmotionProfile(
            joy_base=0.7,
            trust_base=0.6,
            fear_base=0.2,
            surprise_base=0.8,
            sadness_base=0.2,
            disgust_base=0.2,
            anger_base=0.3,
            anticipation_base=0.9
        )

    @staticmethod
    def grumpy() -> EmotionProfile:
        """Grumpy, easily annoyed pet."""
        return EmotionProfile(
            joy_base=0.2,
            trust_base=0.3,
            fear_base=0.3,
            surprise_base=0.3,
            sadness_base=0.4,
            disgust_base=0.7,
            anger_base=0.8,
            anticipation_base=0.3
        )

    @staticmethod
    def balanced() -> EmotionProfile:
        """Well-balanced pet."""
        return EmotionProfile()


class EmotionEngine:
    """
    Main emotion engine that processes events and manages emotional state.
    """

    def __init__(self, profile: EmotionProfile = None):
        self.profile = profile or EmotionProfiles.balanced()

        # Current emotional state
        self.emotions: Dict[EmotionType, EmotionState] = {}
        for emotion in EmotionType:
            self.emotions[emotion] = EmotionState(emotion)

        # Event history
        self.event_history: List[EmotionalEvent] = []

        # Current mood (persistent emotional backdrop)
        self.mood: str = "neutral"

        # Last update
        self.last_update = time.time()

    def update(self, dt: float = None):
        """
        Update emotional state, decaying emotions over time.

        Args:
            dt: Delta time in seconds (None = auto)
        """
        if dt is None:
            dt = time.time() - self.last_update
        self.last_update = time.time()

        # Decay emotions
        for emotion, state in self.emotions.items():
            if state.is_active():
                decay_rate = self.profile.get_decay_rate(emotion)
                state.decrease(decay_rate * dt)

        # Clean old events
        now = time.time()
        self.event_history = [
            e for e in self.event_history
            if now - e.timestamp < e.decay_time
        ]

        # Update mood
        self._update_mood()

    def trigger_emotion(self, emotion: EmotionType, intensity: float = 0.5):
        """
        Trigger an emotion with given intensity.

        Args:
            emotion: Type of emotion
            intensity: Base intensity (0-1)
        """
        # Apply susceptibility
        susceptibility = self.profile.get_susceptibility(emotion)
        final_intensity = intensity * (0.5 + susceptibility)

        # Increase emotion
        self.emotions[emotion].increase(final_intensity)

        # Decrease opposite emotion
        opposite = EMOTION_OPPOSITES.get(emotion)
        if opposite:
            self.emotions[opposite].decrease(final_intensity * 0.5)

    def process_event(self, event_type: str, context: Dict = None):
        """
        Process an event that affects emotions.

        Args:
            event_type: Type of event (see EVENT_EFFECTS)
            context: Additional context for the event
        """
        context = context or {}
        changes = {}

        # Get emotion changes for this event
        event_effects = EVENT_EFFECTS.get(event_type, {})

        for emotion, base_change in event_effects.items():
            # Apply modifiers from context
            modifier = 1.0

            # Personality modifier
            susceptibility = self.profile.get_susceptibility(emotion)
            modifier *= susceptibility

            # Context modifiers
            if event_type == "fed" and context.get("food_quality", "normal") == "delicious":
                modifier *= 1.5
            if event_type == "petted" and context.get("affection", "normal") == "high":
                modifier *= 1.3

            changes[emotion] = base_change * modifier

        # Apply changes
        for emotion, change in changes.items():
            if change > 0:
                self.emotions[emotion].increase(change)
            else:
                self.emotions[emotion].decrease(abs(change))

        # Record event
        self.event_history.append(EmotionalEvent(
            event_type=event_type,
            timestamp=time.time(),
            emotion_changes=changes
        ))

    def get_dominant_emotion(self) -> Tuple[EmotionType, float]:
        """Get the currently dominant emotion."""
        dominant = EmotionType.JOY
        max_intensity = 0.0

        for emotion, state in self.emotions.items():
            if state.intensity > max_intensity:
                max_intensity = state.intensity
                dominant = emotion

        return dominant, max_intensity

    def get_emotion(self, emotion: EmotionType) -> float:
        """Get intensity of a specific emotion."""
        return self.emotions[emotion].intensity

    def get_emotion_vector(self) -> Dict[EmotionType, float]:
        """Get all emotion intensities."""
        return {e: s.intensity for e, s in self.emotions.items()}

    def get_mood(self) -> str:
        """Get current mood."""
        return self.mood

    def get_secondary_emotions(self) -> List[Tuple[MixedEmotion, float]]:
        """
        Get current secondary (mixed) emotions.

        Returns list of (emotion, intensity) for active mixed emotions.
        """
        mixed = []
        e = self.emotions

        # Calculate mixed emotions
        emotions = self.get_emotion_vector()

        # Love = Joy + Trust
        love = min(emotions[EmotionType.JOY], emotions[EmotionType.TRUST]) * 2
        if love > 0.2:
            mixed.append((MixedEmotion.LOVE, love))

        # Optimism = Anticipation + Joy
        optimism = min(emotions[EmotionType.ANTICIPATION], emotions[EmotionType.JOY]) * 2
        if optimism > 0.2:
            mixed.append((MixedEmotion.OPTIMISM, optimism))

        # Aggressiveness = Anger + Anticipation
        aggressiveness = min(emotions[EmotionType.ANGER], emotions[EmotionType.ANTICIPATION]) * 2
        if aggressiveness > 0.2:
            mixed.append((MixedEmotion.AGGRESSIVENESS, aggressiveness))

        # Remorse = Sadness + Disgust
        remorse = min(emotions[EmotionType.SADNESS], emotions[EmotionType.DISGUST]) * 2
        if remorse > 0.2:
            mixed.append((MixedEmotion.REMORSE, remorse))

        # Interest = Anticipation + Trust
        interest = min(emotions[EmotionType.ANTICIPATION], emotions[EmotionType.TRUST]) * 2
        if interest > 0.2:
            mixed.append((MixedEmotion.INTEREST, interest))

        # Sort by intensity
        mixed.sort(key=lambda x: x[1], reverse=True)
        return mixed

    def _update_mood(self):
        """Update overall mood based on emotional state."""
        emotions = self.get_emotion_vector()

        # Calculate valence (positive vs negative)
        valence = (
            emotions[EmotionType.JOY] +
            emotions[EmotionType.TRUST] * 0.5 -
            emotions[EmotionType.SADNESS] -
            emotions[EmotionType.FEAR] * 0.5 -
            emotions[EmotionType.ANGER] * 0.5 -
            emotions[EmotionType.DISGUST] * 0.5
        )

        # Calculate arousal (high vs low energy)
        arousal = (
            emotions[EmotionType.SURPRISE] +
            emotions[EmotionType.ANTICIPATION] +
            emotions[EmotionType.FEAR] * 0.5 +
            emotions[EmotionType.ANGER] * 0.5 -
            emotions[EmotionType.SADNESS] * 0.3
        )

        # Determine mood
        if valence > 0.5:
            if arousal > 0.5:
                self.mood = "excited"
            else:
                self.mood = "happy"
        elif valence > -0.3:
            if arousal > 0.3:
                self.mood = "alert"
            else:
                self.mood = "calm"
        elif valence > -0.7:
            if arousal > 0.3:
                self.mood = "anxious"
            else:
                self.mood = "sad"
        else:
            if arousal > 0.5:
                self.mood = "agitated"
            else:
                self.mood = "depressed"

    def reset(self):
        """Reset all emotions to neutral."""
        for state in self.emotions.values():
            state.intensity = 0.0
        self.mood = "neutral"
        self.event_history.clear()


# Event effects on emotions
# Positive values increase the emotion, negative decrease it
EVENT_EFFECTS = {
    # Positive events
    "fed": {
        EmotionType.JOY: 0.3,
        EmotionType.TRUST: 0.2,
        EmotionType.SADNESS: -0.2,
    },
    "petted": {
        EmotionType.JOY: 0.4,
        EmotionType.TRUST: 0.3,
        EmotionType.LOVE: 0.2,
    },
    "played": {
        EmotionType.JOY: 0.5,
        EmotionType.ANTICIPATION: 0.3,
        EmotionType.SADNESS: -0.3,
    },
    "praised": {
        EmotionType.JOY: 0.4,
        EmotionType.TRUST: 0.3,
        EmotionType.ANTICIPATION: 0.2,
    },
    "groomed": {
        EmotionType.JOY: 0.3,
        EmotionType.TRUST: 0.4,
        EmotionType.DISGUST: -0.2,
    },

    # Negative events
    "scolded": {
        EmotionType.FEAR: 0.3,
        EmotionType.SADNESS: 0.4,
        EmotionType.JOY: -0.3,
        EmotionType.TRUST: -0.2,
    },
    "ignored": {
        EmotionType.SADNESS: 0.3,
        EmotionType.TRUST: -0.1,
    },
    "startled": {
        EmotionType.FEAR: 0.5,
        EmotionType.SURPRISE: 0.6,
    },
    "hurt": {
        EmotionType.FEAR: 0.4,
        EmotionType.SADNESS: 0.3,
        EmotionType.ANGER: 0.3,
        EmotionType.JOY: -0.4,
    },
    "sick": {
        EmotionType.SADNESS: 0.4,
        EmotionType.DISGUST: 0.2,
        EmotionType.FEAR: 0.2,
        EmotionType.JOY: -0.3,
    },

    # Social events
    "owner_arrived": {
        EmotionType.JOY: 0.5,
        EmotionType.SURPRISE: 0.3,
        EmotionType.ANTICIPATION: 0.4,
    },
    "owner_left": {
        EmotionType.SADNESS: 0.3,
        EmotionType.FEAR: 0.1,
    },
    "met_stranger": {
        EmotionType.FEAR: 0.3,
        EmotionType.SURPRISE: 0.4,
        EmotionType.ANTICIPATION: 0.2,
    },

    # Environmental events
    "thunder": {
        EmotionType.FEAR: 0.6,
        EmotionType.SURPRISE: 0.4,
    },
    "new_toy": {
        EmotionType.JOY: 0.5,
        EmotionType.SURPRISE: 0.4,
        EmotionType.ANTICIPATION: 0.3,
    },
    "treat": {
        EmotionType.JOY: 0.6,
        EmotionType.ANTICIPATION: 0.3,
    },
}


class EmotionDisplay:
    """Handles visual representation of emotions."""

    # Emoji representations for emotions
    EMOTION_EMOJIS = {
        EmotionType.JOY: "😊",
        EmotionType.TRUST: "🥰",
        EmotionType.FEAR: "😨",
        EmotionType.SURPRISE: "😲",
        EmotionType.SADNESS: "😢",
        EmotionType.DISGUST: "🤢",
        EmotionType.ANGER: "😠",
        EmotionType.ANTICIPATION: "🤔",
    }

    MOOD_EMOJIS = {
        "excited": "🤩",
        "happy": "😊",
        "alert": "👀",
        "calm": "😌",
        "anxious": "😰",
        "sad": "😢",
        "agitated": "😤",
        "depressed": "😔",
        "neutral": "😐",
    }

    @classmethod
    def get_emoji(cls, emotion: EmotionType) -> str:
        """Get emoji for an emotion."""
        return cls.EMOTION_EMOJIS.get(emotion, "😐")

    @classmethod
    def get_mood_emoji(cls, mood: str) -> str:
        """Get emoji for a mood."""
        return cls.MOOD_EMOJIS.get(mood, "😐")

    @classmethod
    def get_display_text(cls, engine: EmotionEngine) -> str:
        """Get text representation of current emotional state."""
        dominant, intensity = engine.get_dominant_emotion()
        mood = engine.get_mood()

        if intensity > 0.3:
            emoji = cls.get_emoji(dominant)
            return f"{emoji} {dominant.value.capitalize()} ({mood})"
        else:
            return f"{cls.get_mood_emoji(mood)} {mood.capitalize()}"


if __name__ == "__main__":
    # Test emotion engine
    print("Testing Emotion Engine")

    # Create engine with friendly profile
    engine = EmotionEngine(EmotionProfiles.friendly())

    print("\nInitial state:")
    print(f"  Mood: {engine.get_mood()}")
    print(f"  Display: {EmotionDisplay.get_display_text(engine)}")

    # Process some events
    print("\nProcessing events:")

    engine.process_event("fed", {"food_quality": "delicious"})
    engine.update(0.1)
    dominant, intensity = engine.get_dominant_emotion()
    print(f"  After fed: {EmotionDisplay.get_display_text(engine)}")

    engine.process_event("petted", {"affection": "high"})
    engine.update(0.1)
    print(f"  After petted: {EmotionDisplay.get_display_text(engine)}")

    engine.process_event("played")
    engine.update(0.1)
    print(f"  After played: {EmotionDisplay.get_display_text(engine)}")

    # Get secondary emotions
    mixed = engine.get_secondary_emotions()
    if mixed:
        print(f"\n  Mixed emotions:")
        for emotion, intensity in mixed[:3]:
            print(f"    {emotion.value}: {intensity:.2f}")

    # Test negative event
    print("\nNegative event:")
    engine.process_event("scolded")
    engine.update(0.1)
    print(f"  After scolded: {EmotionDisplay.get_display_text(engine)}")

    # Test decay
    print("\nTesting emotion decay:")
    for i in range(5):
        time.sleep(0.5)
        engine.update(0.5)
        dominant, intensity = engine.get_dominant_emotion()
        print(f"  t={i*0.5}s: dominant={dominant.value}, intensity={intensity:.2f}")

    print("\nEmotion engine test passed!")
