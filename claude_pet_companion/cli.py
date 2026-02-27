#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Pet Companion - CLI

Command-line interface for the pet companion.
"""
import sys
import os
import shutil
import json
from pathlib import Path


class PetPluginInstaller:
    """Handle Claude Code plugin installation."""

    def __init__(self):
        self.package_dir = Path(__file__).parent
        self.plugin_dir = self.get_claude_plugin_dir()

    def get_claude_plugin_dir(self):
        """Get the Claude Code plugins directory."""
        env_path = os.environ.get('CLAUDE_PLUGINS_PATH')
        if env_path:
            return Path(env_path)

        home = Path.home()
        # Claude Code uses ~/.claude/plugins on all platforms
        return home / ".claude" / "plugins"

    def install_plugin(self):
        """Install plugin to Claude Code plugins directory."""
        print("Installing Claude Code Pet Companion plugin...")

        # Create plugin directory
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        dest_dir = self.plugin_dir / "claude-pet-companion"

        # Validate destination path
        try:
            dest_dir_resolved = dest_dir.resolve()
            plugin_dir_resolved = self.plugin_dir.resolve()
            if not str(dest_dir_resolved).startswith(str(plugin_dir_resolved)):
                print("✗ Invalid plugin directory")
                return False
        except (ValueError, RuntimeError):
            print("✗ Invalid plugin directory")
            return False

        # Remove existing
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy plugin components
        items_to_copy = [
            ('.claude-plugin', '.claude-plugin'),
            ('skills', 'skills'),
            ('agents', 'agents'),
            ('hooks', 'hooks'),
            ('render', 'render'),
            ('items', 'items'),
            ('memories', 'memories'),
            ('ipc', 'ipc'),
            ('daemon', 'daemon'),
            ('scripts', 'scripts'),
            ('webview', 'webview'),
            ('data', 'data'),
        ]

        for src_name, dst_name in items_to_copy:
            src = self.package_dir / src_name
            dst = dest_dir / dst_name
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
                else:
                    shutil.copy2(src, dst)
                print(f"  [OK] Copied {src_name}")

        # Copy main module files
        for py_file in ['config.py', 'themes.py', 'claude_pet_hd.py', '__init__.py', 'cli.py']:
            src = self.package_dir / py_file
            if src.exists():
                shutil.copy2(src, dest_dir / py_file)
                print(f"  [OK] Copied {py_file}")

        print(f"\n[OK] Plugin installed to: {dest_dir}")
        print("\nPlease restart Claude Code to use the plugin.")
        print("\nAvailable commands:")
        print("  /pet:status  - Check pet status")
        print("  /pet:feed    - Feed your pet")
        print("  /pet:play    - Play with your pet")
        print("  /pet:sleep   - Toggle sleep mode")
        print("  /pet:restore - Restore conversation context")
        print("  /pet:continue - Continue a conversation")

        return True

    def uninstall_plugin(self):
        """Uninstall plugin from Claude Code."""
        dest_dir = self.plugin_dir / "claude-pet-companion"
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
            print(f"[OK] Plugin uninstalled from: {dest_dir}")
            return True
        else:
            print("Plugin is not installed.")
            return False


class PetState:
    """宠物状态类"""
    def __init__(self):
        self.name = 'Claude'
        self.mood = 'happy'
        self.hunger = 100
        self.happiness = 100
        self.energy = 100
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100

    def print_status(self):
        """打印状态"""
        print(f"""
🤖 {self.name} - Level {self.level}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Mood: {self.mood}
   Hunger: {self.hunger}/100
   Happiness: {self.happiness}/100
   Energy: {self.energy}/100
   XP: {self.xp}/{self.xp_to_next}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def print_status():
    """打印宠物状态"""
    state = PetState()
    state.print_status()
    return 0


def launch_desktop_pet():
    """启动桌面宠物"""
    try:
        from claude_pet_companion.claude_pet_hd import ClaudeCodePetHD
        print("Starting Claude Code Pet HD Enhanced...")
        pet = ClaudeCodePetHD()
        pet.run()
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install tkinter (usually included with Python)")


def daemon_start():
    """启动守护进程"""
    from claude_pet_companion.daemon import get_daemon_manager
    from claude_pet_companion.ipc import check_server_running

    manager = get_daemon_manager()

    # 检查是否已运行
    if manager.is_running():
        print("Daemon is already running")
        from claude_pet_companion.daemon.daemon_manager import print_status
        print_status()
        return 1

    # 检查端口是否被占用
    if check_server_running(manager.ipc_host, manager.ipc_port):
        print(f"Error: Port {manager.ipc_port} is already in use")
        print("Another process may be using the IPC port.")
        return 1

    # 启动守护进程（实际上是启动桌面宠物）
    print("Starting Claude Pet Daemon...")
    if manager.start():
        print("Daemon started successfully")
        print("Launching desktop pet...")
        launch_desktop_pet()
        return 0
    else:
        print("Failed to start daemon")
        return 1


def daemon_stop():
    """停止守护进程"""
    from claude_pet_companion.daemon import get_daemon_manager

    manager = get_daemon_manager()
    if manager.stop():
        print("Daemon stopped successfully")
        return 0
    else:
        print("Failed to stop daemon")
        return 1


def daemon_status():
    """显示守护进程状态"""
    from claude_pet_companion.daemon.daemon_manager import print_status
    print_status()
    return 0


def daemon_restart():
    """重启守护进程"""
    from claude_pet_companion.daemon import get_daemon_manager

    manager = get_daemon_manager()
    if manager.restart():
        print("Daemon restarted successfully")
        return 0
    else:
        print("Failed to restart daemon")
        return 1


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Code Pet Companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  (none)       Launch the desktop pet
  status       Show pet status
  install      Install Claude Code plugin
  uninstall    Uninstall Claude Code plugin

Daemon Commands:
  daemon start    Start the pet daemon
  daemon stop     Stop the pet daemon
  daemon restart  Restart the pet daemon
  daemon status   Show daemon status

Examples:
  claude-pet              # Launch desktop pet
  claude-pet install      # Install Claude Code plugin
  claude-pet status       # Show status
  claude-pet daemon start # Start daemon
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['launch', 'status', 'install', 'uninstall', 'daemon'],
        default='launch',
        help='Command to run'
    )

    parser.add_argument(
        'subcommand',
        nargs='?',
        choices=['start', 'stop', 'restart', 'status'],
        help='Daemon subcommand'
    )

    args = parser.parse_args()

    if args.command == 'launch' or args.command == 'status':
        if args.command == 'status':
            return print_status() or 0
        else:
            launch_desktop_pet()
    elif args.command == 'install':
        installer = PetPluginInstaller()
        return 0 if installer.install_plugin() else 1
    elif args.command == 'uninstall':
        installer = PetPluginInstaller()
        return 0 if installer.uninstall_plugin() else 1
    elif args.command == 'daemon':
        if not args.subcommand:
            print("Error: daemon requires a subcommand (start, stop, restart, status)")
            return 1

        if args.subcommand == 'start':
            return daemon_start()
        elif args.subcommand == 'stop':
            return daemon_stop()
        elif args.subcommand == 'status':
            return daemon_status()
        elif args.subcommand == 'restart':
            return daemon_restart()

    return 0


if __name__ == "__main__":
    main()
