"""
ActivityMonitor - Tracks coding activities for emotion calculation

Monitors user coding patterns and provides data for emotion calculation.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ActivityEvent:
    """Represents a single activity event."""
    timestamp: str
    event_type: str  # write, edit, bash_success, bash_failure, error
    tool: str
    success: bool
    metadata: Dict = None


class ActivityMonitor:
    """Monitors and tracks coding activities."""

    # Activity window for emotion calculation (in minutes)
    ACTIVITY_WINDOW = 30

    # Streak decay time (in minutes)
    STREAK_DECAY_TIME = 60

    def __init__(self, state=None):
        """Initialize activity monitor."""
        self.state = state
        self.activities: deque = deque(maxlen=100)
        self.last_activity_time: Optional[datetime] = None

    @classmethod
    def get_activity_log_file(cls) -> Path:
        """Get the path to the activity log file."""
        plugin_root = Path(__file__).parent.parent.parent.parent
        return plugin_root / 'data' / 'activity_log.json'

    def record_activity(self, event_type: str, tool: str, success: bool,
                        metadata: Dict = None) -> ActivityEvent:
        """Record a new activity event."""
        event = ActivityEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            tool=tool,
            success=success,
            metadata=metadata or {}
        )
        self.activities.append(event)
        self.last_activity_time = datetime.now()
        return event

    def get_recent_activities(self, minutes: int = None) -> List[ActivityEvent]:
        """Get activities within the specified time window."""
        if minutes is None:
            minutes = self.ACTIVITY_WINDOW

        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = []

        for activity in reversed(self.activities):
            try:
                activity_time = datetime.fromisoformat(activity.timestamp)
                if activity_time >= cutoff:
                    recent.append(activity)
                else:
                    break
            except (ValueError, TypeError):
                continue

        return recent

    def get_success_rate(self, minutes: int = 30) -> float:
        """Calculate success rate for recent activities."""
        recent = self.get_recent_activities(minutes)
        if not recent:
            return 1.0  # Default to positive

        successful = sum(1 for a in recent if a.success)
        return successful / len(recent)

    def get_activity_frequency(self, minutes: int = 30) -> int:
        """Get number of activities in the time window."""
        return len(self.get_recent_activities(minutes))

    def get_error_count(self, minutes: int = 30) -> int:
        """Count errors in the time window."""
        recent = self.get_recent_activities(minutes)
        return sum(1 for a in recent if not a.success)

    def get_consecutive_successes(self) -> int:
        """Get current consecutive success count from state."""
        if self.state:
            return self.state.consecutive_successes
        return 0

    def get_consecutive_failures(self) -> int:
        """Get current consecutive failure count from state."""
        if self.state:
            return self.state.consecutive_failures
        return 0

    def is_inactive(self, minutes: int = 30) -> bool:
        """Check if user has been inactive."""
        if self.last_activity_time is None:
            return True

        inactive_time = datetime.now() - self.last_activity_time
        return inactive_time >= timedelta(minutes=minutes)

    def get_activity_summary(self) -> Dict:
        """Get a summary of recent activity."""
        recent = self.get_recent_activities()

        return {
            "total_activities": len(recent),
            "successful": sum(1 for a in recent if a.success),
            "failed": sum(1 for a in recent if not a.success),
            "success_rate": self.get_success_rate(),
            "is_inactive": self.is_inactive(),
            "minutes_since_last_activity": self._minutes_since_last_activity()
        }

    def _minutes_since_last_activity(self) -> Optional[int]:
        """Get minutes since last activity."""
        if self.last_activity_time is None:
            return None

        delta = datetime.now() - self.last_activity_time
        return int(delta.total_seconds() / 60)

    def save_to_file(self):
        """Save activity log to file."""
        try:
            log_file = self.get_activity_log_file()
            log_file.parent.mkdir(parents=True, exist_ok=True)

            data = [
                {
                    "timestamp": a.timestamp,
                    "event_type": a.event_type,
                    "tool": a.tool,
                    "success": a.success,
                    "metadata": a.metadata
                }
                for a in self.activities
            ]

            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving activity log: {e}")

    @classmethod
    def load_from_file(cls) -> 'ActivityMonitor':
        """Load activity monitor from file."""
        monitor = cls()
        log_file = cls.get_activity_log_file()

        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for item in data:
                    event = ActivityEvent(
                        timestamp=item.get("timestamp"),
                        event_type=item.get("event_type"),
                        tool=item.get("tool"),
                        success=item.get("success", True),
                        metadata=item.get("metadata", {})
                    )
                    monitor.activities.append(event)

                # Set last activity time
                if monitor.activities:
                    try:
                        monitor.last_activity_time = datetime.fromisoformat(
                            monitor.activities[-1].timestamp
                        )
                    except (ValueError, TypeError):
                        pass

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading activity log: {e}")

        return monitor


# Convenience functions
def record_event(event_type: str, tool: str, success: bool, state=None) -> ActivityEvent:
    """Record an activity event."""
    monitor = ActivityMonitor(state)
    return monitor.record_activity(event_type, tool, success)


def get_activity_summary(state=None) -> Dict:
    """Get activity summary."""
    monitor = ActivityMonitor.load_from_file()
    monitor.state = state
    return monitor.get_activity_summary()


if __name__ == "__main__":
    # Test activity monitor
    monitor = ActivityMonitor()

    print("Testing ActivityMonitor")

    # Record some activities
    monitor.record_activity("write", "Write", True)
    monitor.record_activity("bash", "Bash", True)
    monitor.record_activity("edit", "Edit", True)
    monitor.record_activity("bash", "Bash", False)

    summary = monitor.get_activity_summary()
    print(f"Activity summary: {summary}")
