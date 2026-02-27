#!/usr/bin/env python3
"""
launch_panel.py - Launch the Pet Companion webview panel

This script creates and shows the pet companion webview panel in VS Code.
"""
import sys
import os
import json
from pathlib import Path

# Add skills directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'pet-core', 'scripts'))

from pet_state import PetState, get_state


def get_webview_content():
    """Get the HTML content for the webview."""
    html_file = Path(__file__).parent.parent / 'webview' / 'index.html'

    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return f"<html><body><h1>Pet Companion</h1><p>Webview file not found: {html_file}</p></body></html>"


def print_webview_instructions():
    """Print instructions for launching the webview."""
    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
    webview_path = Path(plugin_root) / 'webview' / 'index.html' if plugin_root else 'webview/index.html'

    print("=" * 60)
    print("Claude Code Pet Companion")
    print("=" * 60)
    print()
    print("To launch the pet panel in VS Code:")
    print()
    print("1. Using the command palette:")
    print("   - Press Ctrl+Shift+P (Cmd+Shift+P on Mac)")
    print("   - Type 'Pet Companion: Show Panel'")
    print()
    print("2. Using the integrated terminal:")
    print("   - Run: code --open-webview " + str(webview_path))
    print()
    print("3. Status Commands:")
    print("   - /pet:status - Check pet status")
    print("   - /pet:feed - Feed your pet")
    print("   - /pet:play - Play with your pet")
    print("   - /pet:sleep - Toggle sleep mode")
    print()
    print("=" * 60)


def show_pet_status():
    """Show the current pet status."""
    state = get_state()
    print(state.get_summary())


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Launch Pet Companion Panel')
    parser.add_argument('--status', action='store_true', help='Show pet status')
    parser.add_argument('--webview', action='store_true', help='Print webview HTML')
    parser.add_argument('--json', action='store_true', help='Output state as JSON')

    args = parser.parse_args()

    if args.status:
        show_pet_status()
    elif args.webview:
        print(get_webview_content())
    elif args.json:
        state = get_state()
        print(json.dumps(state.to_dict(), indent=2, default=str))
    else:
        print_webview_instructions()
        show_pet_status()


if __name__ == "__main__":
    main()
