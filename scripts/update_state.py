#!/usr/bin/env python3
"""
update_state.py - Hook script for updating pet state based on Claude Code events

This script is called by hooks to track coding activity and update pet state.
"""
import sys
import os
import argparse
from datetime import datetime

# Add the skills directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'pet-core', 'scripts'))

from pet_state import PetState, get_state, save_state
from stats_manager import StatsManager, update_mood_from_stats
from xp_system import XPSystem, ActivityType
from achievements import AchievementSystem, check_and_unlock


def handle_post_tool_use(tool: str, status: str, exit_code: int = 0, **kwargs):
    """Handle successful tool use events."""
    state = get_state()

    # Track activity
    if tool in ["Write", "Edit"]:
        activity_type = "file_created" if tool == "Write" else "file_modified"
        state.record_activity(activity_type, success=True)

        # Award XP
        xp_system = XPSystem()
        activity = ActivityType.WRITE_FILE if tool == "Write" else ActivityType.EDIT_FILE
        result = xp_system.grant_activity_xp(state, activity)

        # Update mood
        state.modify_stat("happiness", 2)
        update_mood_from_stats(state)

    elif tool == "Bash":
        activity_type = "command_run"
        state.record_activity(activity_type, success=(exit_code == 0))

        if exit_code == 0:
            xp_system = XPSystem()
            xp_system.grant_activity_xp(state, ActivityType.BASH_SUCCESS)
            state.modify_stat("happiness", 1)
        else:
            state.consecutive_failures += 1
            state.modify_stat("happiness", -5)

        update_mood_from_stats(state)

    # Save state
    save_state(state)
    print(f"Pet state updated: {state.mood}, Level {state.level}, {state.xp} XP")


def handle_post_tool_failure(tool: str, error: str = "", **kwargs):
    """Handle tool failure events."""
    state = get_state()

    # Record failure
    state.consecutive_failures += 1
    state.consecutive_successes = 0

    # Affect mood
    state.modify_stat("happiness", -10)
    state.update_mood("worried")

    # Check if this looks like an error being fixed
    # (user trying different commands = attempting to fix)
    if tool in ["Write", "Edit"]:
        state.record_activity("file_modified", success=False)

    update_mood_from_stats(state)
    save_state(state)

    print(f"Pet is worried! 😟 {error[:50] if error else ''}...")


def handle_session_start(**kwargs):
    """Handle session start events."""
    state = get_state()

    # Apply time-based decay since last session
    manager = StatsManager(state)
    manager.apply_decay(state)

    # Check if should be sleeping
    if state.should_be_sleeping() and not state.is_sleeping:
        state.update_mood("sleepy")

    # Update mood based on current stats
    update_mood_from_stats(state)

    # Check achievements
    newly_unlocked = check_and_unlock(state)
    if newly_unlocked:
        for result in newly_unlocked:
            print(result.get("message", "Achievement unlocked!"))

    save_state(state)
    print(f"Welcome back! {state.name} is {state.mood}.")


def handle_session_end(**kwargs):
    """Handle session end events."""
    state = get_state()

    # Increment session count
    state.total_sessions += 1

    # Award completion XP
    xp_system = XPSystem()
    result = xp_system.grant_activity_xp(state, ActivityType.SESSION_COMPLETE)

    # Bonus happiness for completing a session
    state.modify_stat("happiness", 15)

    # Check for achievements
    newly_unlocked = check_and_unlock(state)

    save_state(state)

    messages = [f"Session complete! +{result['xp_gained']} XP"]
    if newly_unlocked:
        for result in newly_unlocked:
            messages.append(result.get("message", ""))

    print(" | ".join(messages))


def handle_pre_tool_use(tool: str, **kwargs):
    """Handle pre-tool use events (before execution)."""
    state = get_state()

    # Wake up pet if sleeping and user is active
    if state.is_sleeping and tool in ["Write", "Edit", "Bash"]:
        state.is_sleeping = False
        state.update_mood("content")
        save_state(state)
        print(f"{state.name} woke up to help you code!")


def main():
    """Main entry point for hook script."""
    parser = argparse.ArgumentParser(description="Update pet state based on Claude Code events")
    parser.add_argument("--event", required=True, help="Event type")
    parser.add_argument("--tool", help="Tool name")
    parser.add_argument("--status", help="Status (success/failure)")
    parser.add_argument("--exit_code", type=int, default=0, help="Exit code for Bash commands")
    parser.add_argument("--error", help="Error message")

    args = parser.parse_args()

    try:
        if args.event == "PostToolUse":
            if args.status == "success":
                handle_post_tool_use(args.tool, args.status, args.exit_code)
        elif args.event == "PostToolUseFailure":
            handle_post_tool_failure(args.tool, args.error)
        elif args.event == "SessionStart":
            handle_session_start()
        elif args.event == "SessionEnd":
            handle_session_end()
        elif args.event == "PreToolUse":
            handle_pre_tool_use(args.tool)
        else:
            print(f"Unknown event: {args.event}")
            sys.exit(1)

    except Exception as e:
        print(f"Error in update_state.py: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
