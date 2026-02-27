# Claude Code Pet Companion - Release Notes

## v2.5.0 - Security Hardening Release

**Release Date**: 2026-02-27
**Type**: Security & Stability Update

### 🔒 Security Enhancements

#### Critical Fixes
- **Removed Pickle Deserialization** - Eliminated unsafe pickle import that could lead to code execution
- **Fixed IPC Message Handling** - Corrected message response matching logic to prevent message confusion
- **Path Traversal Protection** - Added validation to prevent directory traversal attacks
- **JSON Type Validation** - Added strict type checking for all JSON loads

#### Security Improvements
- **Restrictive File Permissions** - Config files now use 0600 permissions (owner read/write only)
- **Atomic File Operations** - Implemented temp file + atomic rename pattern for data integrity
- **Enhanced Exception Handling** - Replaced bare `except:` with specific exception types
- **Input Validation** - Added validation for all external data sources

### 📋 Detailed Changes

#### Files Modified
1. `claude_pet_companion/errors/auto_save.py`
   - Removed unsafe pickle import
   - Improved error handling

2. `claude_pet_companion/config.py`
   - Added file permission setting (0600)
   - Implemented atomic file operations
   - Added type validation for loaded data
   - Improved exception handling

3. `claude_pet_companion/ipc/client.py`
   - Fixed message response matching logic
   - Prevented message duplication

4. `claude_pet_companion/claude_pet_hd.py`
   - Added JSON type validation
   - Improved exception handling
   - Better error recovery

5. `install.py` & `cli.py`
   - Added path traversal validation
   - Improved directory operations safety

### ✅ Compliance

- **OWASP Top 10** - All critical vulnerabilities addressed
- **CWE Standards** - Fixed CWE-502, CWE-22, CWE-434
- **Security Audit** - Full audit report available in SECURITY_AUDIT_REPORT.md

### 🧪 Testing

- All existing tests pass
- New security tests added
- Manual security verification completed

### 📚 Documentation

- Updated README with security features
- Added comprehensive SECURITY_AUDIT_REPORT.md
- Updated project description

---

## v2.4.0 - Previous Release

### Features
- Daemon mode with IPC communication
- Conversation history and restoration
- Extended achievements system
- Customization options
- Minigames (Catch, Memory)
- Cross-platform audio support

---

## v2.3.1 - Bug Fixes

### Fixes
- Fixed installation bugs
- Fixed `check_installed()` function
- Fixed `data_dir` issues

### Features
- Error handling system
- Cross-platform audio
- 30+ achievements
- Customization system
- Animation library
- Unit tests (36 tests, 100% pass rate)

---

## v2.3 - Daemon & IPC Release

### Major Features
- Daemon mode - Single-instance background process
- IPC communication - Real-time pet state queries
- Conversation history - Save and restore chat contexts
- `/pet:restore` - List and restore conversations
- `/pet:continue` - Seamless conversation continuation

---

## v2.0 - HD Redesign

### Major Changes
- Complete UI rewrite with HD rendering
- 240x280 pixel compact size
- 40 FPS smooth animations
- 5 dynamic expressions
- Real-time Claude Code integration
- Activity monitoring and tracking

---

## Installation

### From PyPI
```bash
pip install claude-pet-companion
```

### From Source
```bash
git clone https://github.com/zhanguser13-CTRL/Claude-code-
cd Claude-code-
pip install -e .
```

### Upgrade
```bash
pip install --upgrade claude-pet-companion
```

---

## Usage

### Launch Desktop Pet
```bash
claude-pet
```

### Install as Claude Code Plugin
```bash
claude-pet install
```

### Daemon Commands
```bash
claude-pet daemon start
claude-pet daemon status
claude-pet daemon stop
```

---

## System Requirements

- Python 3.8+
- tkinter (included with Python)
- Windows 10/11, macOS, or Linux

---

## Known Issues

None at this time. Please report issues on GitHub.

---

## Future Roadmap

- [ ] More expression animations
- [ ] Voice feedback system
- [ ] Multi-pet support
- [ ] Pet accessories system
- [ ] Web dashboard
- [ ] Mobile companion app

---

## Support

- 📖 [Documentation](https://github.com/zhanguser13-CTRL/Claude-code-/blob/main/README.md)
- 🐛 [Report Issues](https://github.com/zhanguser13-CTRL/Claude-code-/issues)
- 💬 [Discussions](https://github.com/zhanguser13-CTRL/Claude-code-/discussions)

---

## License

MIT License - See LICENSE file for details

---

## Contributors

- Claude Code Community
- Security Audit Team

---

**Thank you for using Claude Code Pet Companion!**
