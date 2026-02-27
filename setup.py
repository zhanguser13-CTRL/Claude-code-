"""
Claude Code Pet Companion - Setup Script

For installation via pip:
    pip install claude-pet-companion

After installation, install the Claude Code plugin:
    claude-pet install

Or launch the desktop pet directly:
    claude-pet
    pet-companion
"""
from setuptools import setup, find_packages
from pathlib import Path


# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Version - Direct specification (2.3.3)
VERSION = "2.4.0"


setup(
    name="claude-pet-companion",
    version=VERSION,
    description="A 3D virtual pet plugin for Claude Code with 10 evolution stages and 5 paths",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Claude Code Community",
    author_email="noreply@example.com",
    url="https://github.com/anthropics/claude-pet-companion",
    license="MIT",
    keywords="claude-code plugin pet companion evolution gamification",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "claude_pet_companion": [
            "webview/**/*",
            "data/**/*",
            ".claude-plugin/**/*",
            "hooks/**/*",
            "hooks/*.json",
            "agents/*.md",
            "skills/**/*",
            "skills/**/**/*",
            "render/**/*",
            "items/**/*",
            "memories/**/*",
            "*.py",
        ],
    },
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "claude-pet=claude_pet_companion.cli:main",
            "pet-companion=claude_pet_companion.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/anthropics/claude-pet-companion/issues",
        "Source": "https://github.com/anthropics/claude-pet-companion",
        "Documentation": "https://github.com/anthropics/claude-pet-companion/blob/main/README.md",
    },
)
