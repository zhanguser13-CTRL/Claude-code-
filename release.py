#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Release Script for Claude Pet Companion

This script helps you:
1. Bump version in all files
2. Commit changes
3. Create and push tag
4. Trigger GitHub Actions for PyPI/GitHub release

Usage:
    python release.py patch    # 2.3.1 -> 2.3.2
    python release.py minor    # 2.3.1 -> 2.4.0
    python release.py major    # 2.3.1 -> 3.0.0
    python release.py 2.5.0    # Set specific version
"""
import re
import subprocess
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Files that contain version numbers
VERSION_FILES = {
    "pyproject.toml": r'version = "([^"]+)"',
    "setup.py": r'VERSION = "([^"]+)"',
    ".claude-plugin/plugin.json": r'"version":\s*"([^"]+)"',
    "claude_pet_companion/__init__.py": r'__version__ = "([^"]+)"',
}


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject = Path(__file__).parent / "pyproject.toml"
    content = pyproject.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    return "2.3.1"


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type."""
    parts = current.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        # Custom version
        return bump_type

    return f"{major}.{minor}.{patch}"


def update_version(new_version: str) -> None:
    """Update version in all files."""
    files_updated = []

    for file_path, pattern in VERSION_FILES.items():
        path = Path(__file__).parent / file_path
        if not path.exists():
            print(f"  ⚠ Skipping {file_path} (not found)")
            continue

        content = path.read_text()
        match = re.search(pattern, content)
        if not match:
            print(f"  ⚠ Skipping {file_path} (pattern not found)")
            continue

        old_version = match.group(1)
        new_content = re.sub(pattern, f'version = "{new_version}"', content)
        # Handle different file formats
        if "plugin.json" in file_path:
            new_content = re.sub(r'"version":\s*"[^"]+"', f'"version": "{new_version}"', content)
        elif "__init__.py" in file_path:
            new_content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)

        path.write_text(new_content)
        files_updated.append(file_path)
        print(f"  ✓ {file_path}: {old_version} → {new_version}")

    return files_updated


def run_git_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run git command."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check
    )
    return result


def main():
    """Main release workflow."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCurrent version:", get_current_version())
        sys.exit(1)

    bump_type = sys.argv[1]
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)

    print("=" * 60)
    print(f"🚀 Claude Pet Companion Release")
    print("=" * 60)
    print(f"\nCurrent version: {current_version}")
    print(f"New version: {new_version}")
    print()

    # Check for uncommitted changes
    result = run_git_command(["git", "status", "--porcelain"], check=False)
    if result.returncode != 0:
        print("❌ Not a git repository")
        sys.exit(1)

    if result.stdout.strip():
        print("⚠️  You have uncommitted changes:")
        print(result.stdout)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(1)

    # Update version files
    print("Updating version numbers...")
    files_updated = update_version(new_version)

    if not files_updated:
        print("❌ No files were updated!")
        sys.exit(1)

    # Commit changes
    print("\nCommitting changes...")
    run_git_command(["git", "add"] + files_updated)
    run_git_command(["git", "commit", "-m", f"Bump version to {new_version}"])

    # Create tag
    tag_name = f"v{new_version}"
    print(f"\nCreating tag {tag_name}...")
    run_git_command(["git", "tag", "-a", tag_name, "-m", f"Release {new_version}"])

    # Push to GitHub
    print("\nPushing to GitHub...")
    print("  This will trigger the release workflow:")
    print("  - GitHub Release creation")
    print("  - PyPI publication")
    print()

    response = input("Push to GitHub? (Y/n): ")
    if response.lower() == 'n':
        print("\nTo push manually:")
        print(f"  git push origin main")
        print(f"  git push origin {tag_name}")
        sys.exit(0)

    try:
        run_git_command(["git", "push", "origin", "main"])
        run_git_command(["git", "push", "origin", tag_name])
    except subprocess.CalledProcessError as e:
        print(f"❌ Push failed: {e}")
        print("\nTo push manually:")
        print(f"  git push origin main")
        print(f"  git push origin {tag_name}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Release triggered successfully!")
    print("=" * 60)
    print(f"\nTrack progress at:")
    print(f"  https://github.com/zhanguser13-CTRL/Claude-code-/actions")
    print(f"\nAfter completion:")
    print(f"  GitHub Release: https://github.com/zhanguser13-CTRL/Claude-code-/releases/tag/{tag_name}")
    print(f"  PyPI: https://pypi.org/project/claude-pet-companion/{new_version}/")


if __name__ == "__main__":
    main()
