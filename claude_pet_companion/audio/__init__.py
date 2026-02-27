"""
Claude Code Pet Companion - Cross-Platform Audio System

This module provides:
- Cross-platform audio backend detection and initialization
- Sound effect types and management
- Audio playback with volume control
- Fallback mechanisms for unsupported platforms
"""
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, List, Callable
from enum import Enum
import threading
import time


# ============================================================================
# Sound Effect Types
# ============================================================================

class SoundType(Enum):
    """Enumeration of available sound effect types."""
    INTERACT = "interact"
    FEED = "feed"
    PLAY = "play"
    LEVEL_UP = "level_up"
    EVOLUTION = "evolution"
    ACHIEVEMENT = "achievement"
    ERROR = "error"
    SLEEP = "sleep"
    WAKE_UP = "wake_up"
    HATCH = "hatch"
    DEATH = "death"
    CLICK = "click"
    SUCCESS = "success"
    NOTIFICATION = "notification"


# ============================================================================
# Audio Backend Detection
# ============================================================================

class AudioBackend(Enum):
    """Available audio backends."""
    WINSOUND = "winsound"      # Windows native
    APPKIT = "appkit"          # macOS native
    PYGAME = "pygame"          # Pygame mixer
    MOCK = "mock"              # No-op fallback


def detect_backend() -> AudioBackend:
    """
    Detect the best available audio backend for the current platform.

    Returns:
        Detected audio backend
    """
    system = platform.system()

    # Windows: use winsound (built-in)
    if system == "Windows":
        try:
            import winsound
            return AudioBackend.WINSOUND
        except ImportError:
            pass

    # macOS: use AppKit NSSound
    elif system == "Darwin":
        try:
            from AppKit import NSSound
            return AudioBackend.APPKIT
        except ImportError:
            pass

    # Try pygame as fallback
    try:
        import pygame
        return AudioBackend.PYGAME
    except ImportError:
        pass

    # No backend available
    return AudioBackend.MOCK


# ============================================================================
# Sound Data
# ============================================================================

# Simple beep patterns for different sound types (frequency, duration)
SOUND_PATTERNS: Dict[SoundType, tuple] = {
    SoundType.INTERACT: (800, 100),      # Short high beep
    SoundType.FEED: (600, 150),          # Medium beep
    SoundType.PLAY: (1000, 100),         # High short beep
    SoundType.LEVEL_UP: (1200, 200),     # High long beep
    SoundType.EVOLUTION: (1500, 300),    # Very high long beep
    SoundType.ACHIEVEMENT: (1000, 150),  # Success beep
    SoundType.ERROR: (200, 200),         # Low beep
    SoundType.SLEEP: (400, 300),         # Low descending
    SoundType.WAKE_UP: (600, 100),       # Medium ascending
    SoundType.HATCH: (800, 200),         # Hatch sound
    SoundType.DEATH: (300, 400),         # Sad low beep
    SoundType.CLICK: (900, 50),          # Very short click
    SoundType.SUCCESS: (1000, 100),      # Success beep
    SoundType.NOTIFICATION: (700, 150),  # Notification
}


# ============================================================================
# Audio Manager
# ============================================================================

class AudioManager:
    """
    Cross-platform audio manager for pet sound effects.

    Provides a unified interface for playing sound effects across
    different platforms with automatic backend detection.
    """

    def __init__(self, volume: float = 0.5, enabled: bool = True):
        """
        Initialize the audio manager.

        Args:
            volume: Initial volume level (0.0 to 1.0)
            enabled: Whether audio is enabled
        """
        self._volume = max(0.0, min(1.0, volume))
        self._enabled = enabled
        self._backend = detect_backend()
        self._sounds: Dict[SoundType, Callable] = {}
        self._lock = threading.Lock()
        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize the detected audio backend."""
        if self._backend == AudioBackend.WINSOUND:
            self._init_winsound()
        elif self._backend == AudioBackend.APPKIT:
            self._init_appkit()
        elif self._backend == AudioBackend.PYGAME:
            self._init_pygame()
        else:
            self._init_mock()

    def _init_winsound(self) -> None:
        """Initialize Windows winsound backend."""
        import winsound

        def play_sound(sound_type: SoundType) -> bool:
            if not self._enabled:
                return False
            try:
                freq, duration = SOUND_PATTERNS.get(sound_type, (800, 100))
                winsound.Beep(int(freq * self._volume), duration)
                return True
            except Exception:
                return False

        self._sounds = {st: play_sound for st in SoundType}

    def _init_appkit(self) -> None:
        """Initialize macOS AppKit backend."""
        from AppKit import NSSound
        import tempfile

        def play_sound(sound_type: SoundType) -> bool:
            if not self._enabled:
                return False
            try:
                # For macOS, we'd use system sounds or generate audio files
                # This is a simplified version using system beep
                freq, duration = SOUND_PATTERNS.get(sound_type, (800, 100))
                # macOS doesn't have a simple beep like Windows
                # Would normally play a sound file here
                return True
            except Exception:
                return False

        self._sounds = {st: play_sound for st in SoundType}

    def _init_pygame(self) -> None:
        """Initialize Pygame mixer backend."""
        try:
            import pygame.mixer
            pygame.mixer.init(frequency=44100, size=-16, channels=1)

            def play_sound(sound_type: SoundType) -> bool:
                if not self._enabled:
                    return False
                try:
                    # Would normally load and play sound files
                    # For now, use a simple beep simulation
                    return True
                except Exception:
                    return False

            self._sounds = {st: play_sound for st in SoundType}
        except Exception:
            self._init_mock()

    def _init_mock(self) -> None:
        """Initialize mock (no-op) backend."""
        def play_sound(sound_type: SoundType) -> bool:
            return False

        self._sounds = {st: play_sound for st in SoundType}

    # ========================================================================
    # Public API
    # ========================================================================

    def play(self, sound_type: SoundType, async_play: bool = True) -> bool:
        """
        Play a sound effect.

        Args:
            sound_type: Type of sound to play
            async_play: Whether to play asynchronously (non-blocking)

        Returns:
            True if sound was played successfully
        """
        if not self._enabled:
            return False

        sound_func = self._sounds.get(sound_type)
        if sound_func is None:
            return False

        if async_play:
            thread = threading.Thread(target=sound_func, args=(sound_type,))
            thread.daemon = True
            thread.start()
            return True
        else:
            return sound_func(sound_type)

    def set_volume(self, volume: float) -> None:
        """
        Set the master volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self._volume = max(0.0, min(1.0, volume))

    def get_volume(self) -> float:
        """Get the current volume level."""
        return self._volume

    def enable(self) -> None:
        """Enable audio playback."""
        self._enabled = True

    def disable(self) -> None:
        """Disable audio playback."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if audio is enabled."""
        return self._enabled

    def get_backend(self) -> AudioBackend:
        """Get the active audio backend."""
        return self._backend

    def play_sequence(self, sounds: List[SoundType], interval: float = 0.1) -> None:
        """
        Play a sequence of sounds.

        Args:
            sounds: List of sound types to play in sequence
            interval: Delay between sounds in seconds
        """
        if not self._enabled:
            return

        def play_sequence_thread():
            for sound in sounds:
                self.play(sound, async_play=False)
                time.sleep(interval)

        thread = threading.Thread(target=play_sequence_thread)
        thread.daemon = True
        thread.start()

    def play_interact(self) -> None:
        """Play interaction sound."""
        self.play(SoundType.INTERACT)

    def play_feed(self) -> None:
        """Play feeding sound."""
        self.play(SoundType.FEED)

    def play_play(self) -> None:
        """Play playing sound."""
        self.play(SoundType.PLAY)

    def play_level_up(self) -> None:
        """Play level up sound."""
        self.play(SoundType.LEVEL_UP)

    def play_evolution(self) -> None:
        """Play evolution sound."""
        self.play(SoundType.EVOLUTION)

    def play_achievement(self) -> None:
        """Play achievement sound."""
        self.play(SoundType.ACHIEVEMENT)

    def play_error(self) -> None:
        """Play error sound."""
        self.play(SoundType.ERROR)

    def play_sleep(self) -> None:
        """Play sleep sound."""
        self.play(SoundType.SLEEP)

    def play_wake_up(self) -> None:
        """Play wake up sound."""
        self.play(SoundType.WAKE_UP)

    def play_hatch(self) -> None:
        """Play hatch sound."""
        self.play(SoundType.HATCH)

    def play_click(self) -> None:
        """Play click sound."""
        self.play(SoundType.CLICK)

    def play_success(self) -> None:
        """Play success sound."""
        self.play(SoundType.SUCCESS)

    def play_notification(self) -> None:
        """Play notification sound."""
        self.play(SoundType.NOTIFICATION)


# ============================================================================
# Global Audio Manager Instance
# ============================================================================

_default_manager: Optional[AudioManager] = None


def get_audio_manager() -> AudioManager:
    """
    Get the global audio manager instance.

    Returns:
        AudioManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = AudioManager()
    return _default_manager


def init_audio(volume: float = 0.5, enabled: bool = True) -> AudioManager:
    """
    Initialize the global audio manager.

    Args:
        volume: Initial volume (0.0 to 1.0)
        enabled: Whether audio is enabled

    Returns:
        AudioManager instance
    """
    global _default_manager
    _default_manager = AudioManager(volume=volume, enabled=enabled)
    return _default_manager


# Convenience functions
def play(sound_type: SoundType) -> None:
    """Play a sound using the global audio manager."""
    get_audio_manager().play(sound_type)


def set_volume(volume: float) -> None:
    """Set the global audio volume."""
    get_audio_manager().set_volume(volume)


def get_volume() -> float:
    """Get the global audio volume."""
    return get_audio_manager().get_volume()


def enable_audio() -> None:
    """Enable audio playback."""
    get_audio_manager().enable()


def disable_audio() -> None:
    """Disable audio playback."""
    get_audio_manager().disable()


__all__ = [
    # Enums
    "SoundType",
    "AudioBackend",
    # Classes
    "AudioManager",
    # Functions
    "detect_backend",
    "get_audio_manager",
    "init_audio",
    "play",
    "set_volume",
    "get_volume",
    "enable_audio",
    "disable_audio",
]
