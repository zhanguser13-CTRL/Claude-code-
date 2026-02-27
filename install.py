#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Pet Companion - Installer

Run this script to install the plugin:
    python install.py

Or install directly with:
    pip install claude-pet-companion
"""
import os
import sys
import shutil
import json
import subprocess
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class PetCompanionInstaller:
    """Installer for Claude Code Pet Companion plugin."""

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.install_dir = self.get_claude_plugin_dir()
        self.plugin_name = "claude-pet-companion"
        # 数据目录（用户保存数据）
        self.data_dir = Path.home() / '.claude-pet-companion'

    def get_claude_plugin_dir(self):
        """Get the Claude Code plugins directory."""
        # Check for CLAUDE_PLUGINS_PATH environment variable
        env_path = os.environ.get('CLAUDE_PLUGINS_PATH')
        if env_path:
            return Path(env_path)

        # Default locations based on platform
        home = Path.home()

        if sys.platform == "darwin":  # macOS
            return home / ".claude" / "plugins"
        elif sys.platform == "win32":  # Windows
            return home / "AppData" / "Roaming" / "Claude" / "plugins"
        else:  # Linux
            return home / ".claude" / "plugins"

    def check_dependencies(self):
        """Check if required dependencies are installed."""
        print("Checking dependencies...")

        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ is required")
            return False

        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")

        # Check if Claude Code is available
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ Claude Code: {result.stdout.strip()}")
            else:
                print("⚠ Claude Code not found in PATH")
                print("  Please install Claude Code first")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠ Claude Code not found in PATH")
            print("  Plugin will be installed but may not work until Claude Code is installed")

        return True

    def create_install_dir(self):
        """Create the plugin installation directory."""
        self.install_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Install directory: {self.install_dir}")

    def copy_plugin_files(self):
        """Copy plugin files to installation directory."""
        dest_dir = self.install_dir / self.plugin_name

        # Validate destination path to prevent path traversal
        try:
            dest_dir_resolved = dest_dir.resolve()
            install_dir_resolved = self.install_dir.resolve()
            if not str(dest_dir_resolved).startswith(str(install_dir_resolved)):
                raise ValueError("Invalid installation directory")
        except (ValueError, RuntimeError) as e:
            print(f"✗ Invalid installation path: {e}")
            return None

        # Remove existing installation
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
            print(f"✓ Removed existing installation")

        # Copy all files
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Copy directories
        dirs_to_copy = [
            '.claude-plugin',
            'skills',
            'agents',
            'hooks',
            'webview',
            'scripts',
            'data'
        ]

        for dir_name in dirs_to_copy:
            src = self.script_dir / dir_name
            dst = dest_dir / dir_name
            if src.exists():
                shutil.copytree(src, dst)
                print(f"✓ Copied {dir_name}/")

        # Copy README
        readme_src = self.script_dir / 'README.md'
        if readme_src.exists():
            shutil.copy2(readme_src, dest_dir / 'README.md')
            print(f"✓ Copied README.md")

        # Copy setup script if exists
        setup_src = self.script_dir / 'setup.py'
        if setup_src.exists():
            shutil.copy2(setup_src, dest_dir / 'setup.py')

        return dest_dir

    def create_data_files(self):
        """Create initial data files if they don't exist."""
        data_dir = self.install_dir / self.plugin_name / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)

        state_file = data_dir / 'pet_state.json'
        if not state_file.exists():
            default_state = data_dir / 'default_state.json'
            if default_state.exists():
                shutil.copy2(default_state, state_file)
                print(f"✓ Created pet state file")

    def verify_installation(self, dest_dir):
        """Verify the installation was successful."""
        print("\nVerifying installation...")

        checks = [
            (dest_dir / '.claude-plugin' / 'plugin.json', 'Plugin manifest'),
            (dest_dir / 'skills' / 'pet-core' / 'scripts' / 'pet_state.py', 'Core state module'),
            (dest_dir / 'webview' / 'index.html', 'Webview interface'),
            (dest_dir / 'hooks' / 'hooks.json', 'Hook configuration'),
        ]

        all_ok = True
        for path, name in checks:
            if path.exists():
                print(f"✓ {name}")
            else:
                print(f"✗ {name} - MISSING")
                all_ok = False

        return all_ok

    def print_completion(self, dest_dir):
        """Print installation completion message."""
        print("\n" + "=" * 60)
        print("🎉 Claude Code Pet Companion installed successfully!")
        print("=" * 60)
        print()
        print("Plugin location: " + str(dest_dir))
        print()
        print("Getting Started:")
        print("  1. Restart Claude Code")
        print("  2. Check pet status: /pet:status")
        print("  3. Feed your pet: /pet:feed")
        print("  4. Play with your pet: /pet:play")
        print()
        print("Commands:")
        print("  /pet:status - View pet stats")
        print("  /pet:feed   - Feed your pet")
        print("  /pet:play   - Play with your pet")
        print("  /pet:sleep  - Toggle sleep mode")
        print()
        print("For more info, see: " + str(dest_dir / 'README.md'))
        print("=" * 60)

    def install(self):
        """Run the installation."""
        print("=" * 60)
        print("Claude Code Pet Companion - Installer")
        print("=" * 60)
        print()

        if not self.check_dependencies():
            print("\n❌ Installation failed: Missing dependencies")
            return False

        self.create_install_dir()
        dest_dir = self.copy_plugin_files()
        self.create_data_files()

        if self.verify_installation(dest_dir):
            self.print_completion(dest_dir)
            return True
        else:
            print("\n❌ Installation verification failed")
            return False

    def check_installed(self):
        """检查插件是否已安装"""
        dest_dir = self.install_dir / self.plugin_name
        return dest_dir.exists()

    def uninstall(self, remove_data=False, remove_pip=False):
        """Uninstall the plugin."""
        dest_dir = self.install_dir / self.plugin_name

        # Validate path to prevent accidental deletion
        try:
            dest_dir_resolved = dest_dir.resolve()
            install_dir_resolved = self.install_dir.resolve()
            if not str(dest_dir_resolved).startswith(str(install_dir_resolved)):
                print("✗ Invalid uninstall path")
                return
        except (ValueError, RuntimeError):
            print("✗ Invalid uninstall path")
            return

        if not dest_dir.exists() and not self.data_dir.exists():
            print("Plugin is not installed")
            return

        print("\nUninstalling...")

        # Remove plugin files
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
            print(f"✓ Removed plugin: {dest_dir}")

        # Remove user data if requested
        if remove_data and self.data_dir.exists():
            shutil.rmtree(self.data_dir)
            print(f"✓ Removed user data: {self.data_dir}")
        elif self.data_dir.exists():
            print(f"  User data preserved at: {self.data_dir}")

        # Remove pip package if requested
        if remove_pip:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", "claude-pet-companion"],
                    capture_output=True
                )
                print("✓ Removed pip package")
            except Exception:
                pass

        print("\nUninstallation complete!")


def main():
    """Main entry point."""
    installer = PetCompanionInstaller()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'uninstall':
            remove_data = '--all' in sys.argv or '--data' in sys.argv
            remove_pip = '--pip' in sys.argv

            print("=" * 60)
            print("Claude Code Pet Companion - Uninstaller")
            print("=" * 60)
            print()

            if not installer.check_installed():
                print("\nPlugin is not installed.")
                return

            if remove_data:
                print("\n⚠️  WARNING: This will delete all save data!")
                response = input("\nType 'yes' to confirm: ")
                if response.lower() != 'yes':
                    print("Uninstall cancelled.")
                    return
            else:
                response = input("\nUninstall plugin? (y/N): ")
                if response.lower() != 'y':
                    print("Uninstall cancelled.")
                    return

            installer.uninstall(remove_data=remove_data, remove_pip=remove_pip)
            return

        elif cmd == '--help' or cmd == '-h':
            print("Claude Code Pet Companion - Installer")
            print()
            print("Usage: python install.py [command] [options]")
            print()
            print("Commands:")
            print("  (none)   Install the plugin")
            print("  uninstall  Uninstall the plugin")
            print()
            print("Options for uninstall:")
            print("  --all     Remove all data including saves")
            print("  --pip     Also uninstall pip package")
            print()
            print("Examples:")
            print("  python install.py              # Install")
            print("  python install.py uninstall    # Uninstall plugin only")
            print("  python install.py uninstall --all    # Uninstall everything")
            return

    # Default: install
    success = installer.install()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
