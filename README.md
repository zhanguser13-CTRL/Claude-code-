# Claude Pet Companion

![Version](https://img.shields.io/badge/version-2.5.0-blue)
![PyPI](https://img.shields.io/badge/PyPI-claude--pet--companion-orange)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-green)

A virtual pet for Claude Code with evolution system, memory tracking, conversation history, productivity features, and enhanced security.

---

## What's New in v2.5.0

- **🔒 Security Hardening** - Comprehensive security audit and fixes
  - Removed unsafe pickle deserialization
  - Fixed IPC message handling vulnerabilities
  - Added JSON type validation
  - Implemented path traversal protection
  - Set restrictive file permissions
  - Atomic file operations for data integrity

- **🛡️ Enhanced Stability** - Improved error handling and recovery
- **📝 Better Logging** - Detailed security and error logs
- **✅ Full Compliance** - OWASP Top 10 and CWE standards

### Previous Features (v2.3.1+)

- **Fixed Installation Bugs** - Fixed `check_installed()` and `data_dir` issues
- **Error Handling System** - Centralized logging and error management
- **Cross-Platform Audio** - Sound effects system (Windows/macOS/Linux)
- **Extended Achievements** - 30+ achievements with rarity levels
- **Customization System** - Accessories, colors, and appearance options
- **Animation Library** - Keyframe animations with easing functions
- **Minigames** - Catch and Memory games with rewards
- **Unit Tests** - 36 tests with 100% pass rate
- **Daemon Mode** - Single-instance background process
- **IPC Communication** - Real-time pet state queries
- **Conversation History** - Save and restore chat contexts

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
- **Security Hardened** - Comprehensive security audit and fixes

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

## Security

This release includes comprehensive security hardening:

- ✅ No unsafe deserialization
- ✅ Path traversal protection
- ✅ Secure file operations
- ✅ Type validation
- ✅ Restrictive file permissions
- ✅ OWASP Top 10 compliant

See [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) for details.

---

## Requirements

- Python 3.8+
- tkinter (included with Python)

---

## License

MIT License

---

## Contributing

Contributions welcome! Please ensure:
- Code passes security audit
- Tests pass
- Documentation updated

---

## Support

- 📖 [Documentation](https://github.com/zhanguser13-CTRL/Claude-code-/blob/main/README.md)
- 🐛 [Report Issues](https://github.com/zhanguser13-CTRL/Claude-code-/issues)
- 💬 [Discussions](https://github.com/zhanguser13-CTRL/Claude-code-/discussions)
