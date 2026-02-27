# Pet Core Skill

The core skill for managing the Claude Code Pet Companion.

## Description

This skill provides the foundational systems for the virtual pet, including:
- State management and persistence
- Stats tracking (hunger, happiness, energy)
- XP and leveling system
- Evolution mechanics
- Achievement tracking

## Commands

Use the pet commands to interact with your companion:

- `/pet:feed` - Feed your pet to restore hunger
- `/pet:play` - Play with your pet to increase happiness
- `/pet:sleep` - Put your pet to sleep to restore energy
- `/pet:status` - View your pet's current stats and progress

## How It Works

The pet companion tracks your coding activity through hooks:

- **Write/Edit**: Grants XP, increases happiness
- **Bash success**: Grants small XP bonus
- **Errors**: Decrease happiness, pet becomes worried
- **Sessions**: Completion grants bonus XP

Stats decay over time, so remember to:
- Feed your pet regularly (especially during meal hours!)
- Play to keep happiness up
- Let your pet sleep at night

## Evolution

Your pet evolves as it levels up:
- Level 1: Egg → Baby
- Level 10: Baby → Child
- Level 20: Child → Teen
- Level 30: Teen → Adult
- Level 50: Adult → Elder
- Level 75: Elder → Ancient

Each evolution stage unlocks new abilities and visual changes.

## Files

- `scripts/pet_state.py` - Core state class
- `scripts/stats_manager.py` - Stats management
- `scripts/xp_system.py` - XP and leveling
- `scripts/evolution.py` - Evolution mechanics
- `scripts/achievements.py` - Achievement tracking
