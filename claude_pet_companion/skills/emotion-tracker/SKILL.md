# Emotion Tracker Skill

Monitors coding activities and calculates pet emotions in real-time.

## Description

This skill tracks your coding patterns and updates your pet's emotional state based on:
- Success/failure rate of commands
- Time since last interaction
- Current stats levels (hunger, happiness, energy)
- Coding streak patterns

## How Emotions Work

The pet's mood is calculated from several factors:

| Mood | Trigger |
|------|---------|
| Happy | High stats, recent success |
| Excited | Very high stats + long success streak |
| Worried | Recent errors or failures |
| Sad | Low happiness or many failures |
| Sleepy | Low energy or nighttime |
| Hungry | Low hunger |
| Content | Default balanced state |

## Scripts

- `scripts/activity_monitor.py` - Tracks coding activities
- `scripts/emotion_calculator.py` - Calculates mood from state
