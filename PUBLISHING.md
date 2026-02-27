# Publishing Guide

This guide explains how to publish the Claude Code Pet Companion plugin for others to install.

## Publishing Options

### Option 1: PyPI (Recommended for pip install)

#### Prerequisites
- PyPI account at https://pypi.org
- API token for trusted publishing or authentication

#### Steps

1. **Register the package name on PyPI**
   - Go to https://pypi.org
   - Sign up / Log in
   - Verify the package name `claude-pet-companion` is available

2. **Configure GitHub Actions for Trusted Publishing**
   - Go to repository Settings → Secrets and variables → Actions
   - No secrets needed for trusted publishing!

3. **Create and push a release tag**
   ```bash
   # Update version in setup.py and .claude-plugin/plugin.json
   git add setup.py .claude-plugin/plugin.json
   git commit -m "Bump version to 1.0.0"

   # Create and push tag
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. **GitHub Actions automatically publishes to PyPI**
   - Check the Actions tab for progress
   - Package appears at https://pypi.org/project/claude-pet-companion/

5. **Users can now install**
   ```bash
   pip install claude-pet-companion
   ```

#### Manual PyPI Upload (Alternative)
```bash
# Build the package
python -m build

# Upload with twine
twine upload dist/*
```

### Option 2: Homebrew (macOS/Linux)

Create a formula file:

```ruby
# claude-pet-companion.rb
class ClaudePetCompanion < Formula
  include Language::Python::Virtualenv

  desc "Pixel-art virtual pet plugin for Claude Code"
  homepage "https://github.com/your-repo/claude-pet-companion"
  url "https://github.com/your-repo/claude-pet-companion/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "your-sha256-hash"

  depends_on "python@3.10"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "pet-companion", "status"
  end
end
```

### Option 3: Direct Download / Git Clone

Provide simple instructions in README:

```bash
# Clone the repository
git clone https://github.com/your-repo/claude-pet-companion.git
cd claude-pet-companion

# Run installer
python install.py
```

### Option 4: Claude Code Plugin Registry (Future)

When Claude Code establishes a plugin registry:

```bash
claude plugin install claude-pet-companion
```

## Pre-Release Checklist

- [ ] Version numbers updated in:
  - [ ] `setup.py`
  - [ ] `pyproject.toml`
  - [ ] `.claude-plugin/plugin.json`
  - [ ] `claude_pet_companion/__init__.py`
- [ ] Changelog updated in `RELEASE.md`
- [ ] README.md is complete and accurate
- [ ] INSTALL.md has clear instructions
- [ ] All files included in `MANIFEST.in`
- [ ] License file present
- [ ] Tested clean install on fresh system
- [ ] GitHub Actions workflow configured
- [ ] Tagged release commit

## Post-Release

1. **Announce the release**
   - GitHub Release with notes
   - Social media (Twitter, Reddit, etc.)
   - Claude Code community forums

2. **Monitor for issues**
   - Check GitHub Issues
   - Respond to user questions

3. **Gather feedback**
   - What features do users want?
   - Any bugs to fix?

## Version Bumping

For semantic versioning (MAJOR.MINOR.PATCH):

```bash
# Patch release (bug fixes)
git tag v1.0.1

# Minor release (new features)
git tag v1.1.0

# Major release (breaking changes)
git tag v2.0.0
```

## Testing Before Release

```bash
# Test build
python -m build

# Test install in virtual environment
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows
pip install dist/claude_pet_companion-1.0.0-py3-none-any.whl
pet-companion status

# Test all commands
pet-companion feed
pet-companion play
pet-companion sleep
pet-companion status
```
