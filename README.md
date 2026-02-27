# Claude Pet Companion

![Version](https://img.shields.io/badge/version-2.3.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-green)

A virtual pet for Claude Code with evolution system, memory tracking, conversation history, and productivity features.

---

## Quick Start

```bash
pip install claude-pet-companion
```

### Desktop Pet
```bash
claude-pet
```

### Claude Code Plugin
```bash
claude-pet install
```

---

## What's New in v2.3

- **Daemon Mode** - Single-instance background process
- **IPC Communication** - Real-time pet state queries
- **Conversation History** - Save and restore chat contexts
- **`/pet:restore`** - Continue previous conversations
- **`/pet:continue`** - Seamless conversation continuation

---

## Usage Guide

### Desktop Pet

```bash
# Launch pet
claude-pet

# Daemon commands
claude-pet daemon start    # Start background daemon
claude-pet daemon status   # Check status
claude-pet daemon stop     # Stop daemon
```

### Claude Code Commands

| Command | Description |
|---------|-------------|
| `/pet:status` | View pet stats, level, mood |
| `/pet:feed` | Feed pet (+30 hunger) |
| `/pet:play` | Play with pet (+25 happiness) |
| `/pet:sleep` | Toggle sleep mode |
| `/pet:restore` | List & restore conversations |
| `/pet:continue [id]` | Continue a conversation |

### Conversation History

```bash
# List recent conversations
/pet:restore

# Restore specific conversation
/pet:restore abc123

# Continue conversation
/pet:continue abc123
```

---

## Evolution System

### 10 Stages
Egg → Hatchling → Baby → Child → Pre-Teen → Teen → Young Adult → Adult → Elder → Ancient

### 5 Paths

| Path | Style |
|------|-------|
| Coder | Blue/Green tech theme |
| Warrior | Orange/Red battle theme |
| Social | Pink/Heart cute theme |
| Night Owl | Purple/Yellow mystery |
| Balanced | Green/Teal harmony |

---

## Features

- **3D Pseudo-Rendering** - Multi-layer depth with dynamic lighting
- **Memory System** - Remembers your coding activities
- **Productivity Tracking** - Score, focus, combos, flow state
- **5 Themes** - Blue, Pink, Green, Dark, Purple
- **Mouse Tracking** - Eyes follow cursor
- **Dynamic Expressions** - Happy, thinking, working, error, success

---

## Configuration

`~/.claude-pet-companion/config.json`

```json
{
  "theme": "default",
  "pet_name": "Claude",
  "animation_speed": 1.0,
  "daemon_enabled": true,
  "ipc_port": 15340
}
```

---

## Requirements

- Python 3.8+
- tkinter (included with Python)

---

## License

MIT License
