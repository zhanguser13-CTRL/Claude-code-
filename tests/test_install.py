"""
Unit tests for install.py

Tests the installation script functionality including:
- check_installed() method
- create_install_dir() method
- copy_plugin_files() method
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from install import PetCompanionInstaller


class TestPetCompanionInstaller(unittest.TestCase):
    """Test cases for PetCompanionInstaller class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_home = tempfile.mkdtemp()

        # Create mock plugin structure in temp dir
        self.plugin_dir = Path(self.temp_dir)
        (self.plugin_dir / ".claude-plugin").mkdir()
        (self.plugin_dir / ".claude-plugin" / "plugin.json").write_text('{"name": "test"}')
        (self.plugin_dir / "skills").mkdir()
        (self.plugin_dir / "agents").mkdir()
        (self.plugin_dir / "hooks").mkdir()
        (self.plugin_dir / "webview").mkdir()
        (self.plugin_dir / "scripts").mkdir()
        (self.plugin_dir / "data").mkdir()
        (self.plugin_dir / "README.md").write_text("# Test README")

    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        if Path(self.temp_home).exists():
            shutil.rmtree(self.temp_home)

    @patch('install.Path.home')
    def test_init_creates_data_dir(self, mock_home):
        """Test that __init__ initializes data_dir attribute."""
        mock_home.return_value = Path(self.temp_home)

        installer = PetCompanionInstaller()

        self.assertIsNotNone(installer.data_dir)
        self.assertEqual(installer.data_dir, Path(self.temp_home) / '.claude-pet-companion')

    @patch('install.Path.home')
    def test_check_installed_returns_true_when_installed(self, mock_home):
        """Test check_installed() returns True when plugin is installed."""
        mock_home.return_value = Path(self.temp_home)

        # Create mock install directory with plugin
        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        install_dir.mkdir(parents=True)
        plugin_dir = install_dir / "claude-pet-companion"
        plugin_dir.mkdir()

        installer = PetCompanionInstaller()
        installer.install_dir = install_dir

        self.assertTrue(installer.check_installed())

    @patch('install.Path.home')
    def test_check_installed_returns_false_when_not_installed(self, mock_home):
        """Test check_installed() returns False when plugin is not installed."""
        mock_home.return_value = Path(self.temp_home)

        # Create install directory but no plugin
        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        install_dir.mkdir(parents=True)

        installer = PetCompanionInstaller()
        installer.install_dir = install_dir

        self.assertFalse(installer.check_installed())

    @patch('install.Path.home')
    def test_create_install_dir_creates_directory(self, mock_home):
        """Test create_install_dir() creates the install directory."""
        mock_home.return_value = Path(self.temp_home)

        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        installer = PetCompanionInstaller()
        installer.install_dir = install_dir

        installer.create_install_dir()

        self.assertTrue(install_dir.exists())
        self.assertTrue(install_dir.is_dir())

    @patch('install.Path.home')
    def test_create_install_dir_handles_existing_directory(self, mock_home):
        """Test create_install_dir() handles existing directory."""
        mock_home.return_value = Path(self.temp_home)

        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        install_dir.mkdir(parents=True)

        installer = PetCompanionInstaller()
        installer.install_dir = install_dir

        # Should not raise an error
        installer.create_install_dir()

        self.assertTrue(install_dir.exists())

    @patch('install.Path.home')
    def test_copy_plugin_files_copies_all_directories(self, mock_home):
        """Test copy_plugin_files() copies all required directories."""
        mock_home.return_value = Path(self.temp_home)

        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        install_dir.mkdir(parents=True)

        # Mock script_dir to point to our test directory
        installer = PetCompanionInstaller()
        installer.script_dir = Path(self.temp_dir)
        installer.install_dir = install_dir

        dest_dir = installer.copy_plugin_files()

        # Check destination exists
        self.assertTrue(dest_dir.exists())

        # Check all directories were copied
        expected_dirs = [
            '.claude-plugin',
            'skills',
            'agents',
            'hooks',
            'webview',
            'scripts',
            'data',
        ]

        for dir_name in expected_dirs:
            self.assertTrue((dest_dir / dir_name).exists(),
                          f"Directory {dir_name} was not copied")

        # Check README was copied
        self.assertTrue((dest_dir / 'README.md').exists())

    @patch('install.Path.home')
    def test_copy_plugin_files_removes_existing_installation(self, mock_home):
        """Test copy_plugin_files() removes existing installation."""
        mock_home.return_value = Path(self.temp_home)

        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        install_dir.mkdir(parents=True)

        # Create existing installation
        dest_dir = install_dir / "claude-pet-companion"
        dest_dir.mkdir(parents=True)
        (dest_dir / "old_file.txt").write_text("old content")

        installer = PetCompanionInstaller()
        installer.script_dir = Path(self.temp_dir)
        installer.install_dir = install_dir

        installer.copy_plugin_files()

        # Old file should be gone
        self.assertFalse((dest_dir / "old_file.txt").exists())
        # New files should exist
        self.assertTrue((dest_dir / "README.md").exists())

    @patch('install.Path.home')
    def test_get_claude_plugin_dir_windows(self, mock_home):
        """Test get_claude_plugin_dir() on Windows."""
        mock_home.return_value = Path(self.temp_home)

        with patch('install.sys.platform', 'win32'):
            installer = PetCompanionInstaller()
            expected = Path(self.temp_home) / "AppData" / "Roaming" / "Claude" / "plugins"
            self.assertEqual(installer.install_dir, expected)

    @patch('install.Path.home')
    def test_get_claude_plugin_dir_macos(self, mock_home):
        """Test get_claude_plugin_dir() on macOS."""
        mock_home.return_value = Path(self.temp_home)

        with patch('install.sys.platform', 'darwin'):
            installer = PetCompanionInstaller()
            expected = Path(self.temp_home) / ".claude" / "plugins"
            self.assertEqual(installer.install_dir, expected)

    @patch('install.Path.home')
    def test_get_claude_plugin_dir_linux(self, mock_home):
        """Test get_claude_plugin_dir() on Linux."""
        mock_home.return_value = Path(self.temp_home)

        with patch('install.sys.platform', 'linux'):
            installer = PetCompanionInstaller()
            expected = Path(self.temp_home) / ".claude" / "plugins"
            self.assertEqual(installer.install_dir, expected)

    @patch('install.Path.home')
    def test_uninstall_removes_plugin(self, mock_home):
        """Test uninstall() removes plugin directory."""
        mock_home.return_value = Path(self.temp_home)

        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        install_dir.mkdir(parents=True)

        # Create plugin directory
        plugin_dir = install_dir / "claude-pet-companion"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "test.txt").write_text("test")

        installer = PetCompanionInstaller()
        installer.install_dir = install_dir

        installer.uninstall(remove_data=False, remove_pip=False)

        self.assertFalse(plugin_dir.exists())
        self.assertTrue(install_dir.exists())  # Parent should remain

    @patch('install.Path.home')
    def test_uninstall_with_remove_data(self, mock_home):
        """Test uninstall() with remove_data=True removes data directory."""
        mock_home.return_value = Path(self.temp_home)

        install_dir = Path(self.temp_home) / ".claude" / "plugins"
        install_dir.mkdir(parents=True)

        # Create plugin and data directories
        plugin_dir = install_dir / "claude-pet-companion"
        plugin_dir.mkdir(parents=True)

        data_dir = Path(self.temp_home) / ".claude-pet-companion"
        data_dir.mkdir(parents=True)
        (data_dir / "save.json").write_text("{}")

        installer = PetCompanionInstaller()
        installer.install_dir = install_dir

        installer.uninstall(remove_data=True, remove_pip=False)

        self.assertFalse(plugin_dir.exists())
        self.assertFalse(data_dir.exists())


if __name__ == '__main__':
    unittest.main()
