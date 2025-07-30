import unittest
import tempfile
import os
import yaml
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')
    
    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
    
    def test_create_default_config(self):
        """Test that default config is created when file doesn't exist."""
        config_manager = ConfigManager(self.config_path)
        
        self.assertTrue(os.path.exists(self.config_path))
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.assertIn('wake_word', config)
        self.assertIn('speech', config)
        self.assertIn('audio', config)
        self.assertIsNone(config['wake_word']['name'])
    
    def test_get_wake_word_none(self):
        """Test getting wake word when not set."""
        config_manager = ConfigManager(self.config_path)
        wake_word = config_manager.get_wake_word()
        self.assertIsNone(wake_word)
    
    def test_set_and_get_wake_word(self):
        """Test setting and getting wake word."""
        config_manager = ConfigManager(self.config_path)
        test_name = "Jarvis"
        
        config_manager.set_wake_word(test_name)
        wake_word = config_manager.get_wake_word()
        
        self.assertEqual(wake_word, test_name)
    
    def test_wake_word_persisted(self):
        """Test that wake word is saved to file."""
        config_manager = ConfigManager(self.config_path)
        test_name = "Alexa"
        
        config_manager.set_wake_word(test_name)
        
        # Create new config manager to test persistence
        new_config_manager = ConfigManager(self.config_path)
        wake_word = new_config_manager.get_wake_word()
        
        self.assertEqual(wake_word, test_name)
    
    def test_get_full_config(self):
        """Test getting the full configuration."""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.get_config()
        
        self.assertIsInstance(config, dict)
        self.assertIn('wake_word', config)
        self.assertIn('speech', config)
        self.assertIn('audio', config)
    
    @patch('builtins.open', side_effect=IOError("File error"))
    @patch('builtins.print')
    def test_error_handling_load(self, mock_print, mock_open):
        """Test error handling when loading config fails."""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.get_config()
        
        # Should return empty dict on error
        self.assertEqual(config, {})
        mock_print.assert_called()
    
    @patch('yaml.dump', side_effect=IOError("Write error"))
    @patch('builtins.print')
    def test_error_handling_save(self, mock_print, mock_dump):
        """Test error handling when saving config fails."""
        config_manager = ConfigManager(self.config_path)
        config_manager.set_wake_word("test")
        
        mock_print.assert_called()


if __name__ == '__main__':
    unittest.main()