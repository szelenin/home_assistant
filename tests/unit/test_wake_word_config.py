#!/usr/bin/env python3
"""
Wake Word Configuration Unit Tests

Tests for wake word detection configuration management.
"""

import sys
import os
import unittest
import tempfile
import yaml

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from home_assistant.utils.config import ConfigManager


class WakeWordConfigTests(unittest.TestCase):
    """Unit tests for wake word configuration management."""

    def setUp(self):
        """Set up test with temporary config file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False)
        self.temp_file.close()
        self.config_path = self.temp_file.name
        # Remove the empty file so ConfigManager will create default config
        os.unlink(self.config_path)

    def tearDown(self):
        """Clean up temporary config file."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    def test_default_wake_word_detection_config(self):
        """Test that default config includes wake word detection settings."""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.get_config()
        
        # Check wake word section exists
        self.assertIn('wake_word', config)
        wake_word_config = config['wake_word']
        
        # Check detection subsection exists
        self.assertIn('detection', wake_word_config)
        detection_config = wake_word_config['detection']
        
        # Check default provider is set
        self.assertIn('provider', detection_config)
        self.assertEqual(detection_config['provider'], 'openwakeword')
        
        # Check providers configuration exists
        self.assertIn('providers', detection_config)
        providers = detection_config['providers']
        
        # Check all expected providers are configured
        self.assertIn('openwakeword', providers)
        self.assertIn('porcupine', providers)
        self.assertIn('pocketsphinx', providers)
        
        # Check OpenWakeWord provider settings
        oww_config = providers['openwakeword']
        self.assertIn('model_path', oww_config)
        self.assertIn('threshold', oww_config)
        self.assertIn('inference_framework', oww_config)
        
        # Check Porcupine provider settings
        porcupine_config = providers['porcupine']
        self.assertIn('access_key', porcupine_config)
        self.assertIn('keyword_path', porcupine_config)
        
        # Check PocketSphinx provider settings
        ps_config = providers['pocketsphinx']
        self.assertIn('hmm_path', ps_config)
        self.assertIn('dict_path', ps_config)
        self.assertIn('keyphrase_threshold', ps_config)

    def test_get_wake_word_detection_config(self):
        """Test getting wake word detection configuration."""
        config_manager = ConfigManager(self.config_path)
        
        detection_config = config_manager.get_wake_word_detection_config()
        
        self.assertIsInstance(detection_config, dict)
        self.assertIn('provider', detection_config)
        self.assertIn('providers', detection_config)

    def test_get_wake_word_provider(self):
        """Test getting configured wake word provider."""
        config_manager = ConfigManager(self.config_path)
        
        provider = config_manager.get_wake_word_provider()
        
        self.assertEqual(provider, 'openwakeword')

    def test_set_wake_word_provider(self):
        """Test setting wake word provider."""
        config_manager = ConfigManager(self.config_path)
        
        # Set to different provider
        config_manager.set_wake_word_provider('porcupine')
        
        # Verify it was set
        provider = config_manager.get_wake_word_provider()
        self.assertEqual(provider, 'porcupine')
        
        # Verify it persists
        new_config_manager = ConfigManager(self.config_path)
        provider = new_config_manager.get_wake_word_provider()
        self.assertEqual(provider, 'porcupine')

    def test_wake_word_provider_validation(self):
        """Test that valid providers can be set."""
        config_manager = ConfigManager(self.config_path)
        
        # Test valid providers
        valid_providers = ['openwakeword', 'porcupine', 'pocketsphinx']
        
        for provider in valid_providers:
            config_manager.set_wake_word_provider(provider)
            self.assertEqual(config_manager.get_wake_word_provider(), provider)

    def test_wake_word_detection_config_persistence(self):
        """Test that wake word detection config is saved to file."""
        config_manager = ConfigManager(self.config_path)
        
        # Modify provider
        config_manager.set_wake_word_provider('porcupine')
        
        # Read config file directly
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Verify the change is in the file
        self.assertEqual(
            config_data['wake_word']['detection']['provider'], 
            'porcupine'
        )

    def test_wake_word_detection_config_structure(self):
        """Test the structure of wake word detection configuration."""
        config_manager = ConfigManager(self.config_path)
        detection_config = config_manager.get_wake_word_detection_config()
        
        # Test structure
        self.assertIn('provider', detection_config)
        self.assertIn('providers', detection_config)
        
        providers = detection_config['providers']
        
        # Test OpenWakeWord config structure
        self.assertIn('openwakeword', providers)
        oww_config = providers['openwakeword']
        required_oww_keys = ['model_path', 'threshold', 'inference_framework']
        for key in required_oww_keys:
            self.assertIn(key, oww_config)
        
        # Test Porcupine config structure  
        self.assertIn('porcupine', providers)
        porcupine_config = providers['porcupine']
        required_porcupine_keys = ['access_key', 'keyword_path']
        for key in required_porcupine_keys:
            self.assertIn(key, porcupine_config)
        
        # Test PocketSphinx config structure
        self.assertIn('pocketsphinx', providers)
        ps_config = providers['pocketsphinx']
        required_ps_keys = ['hmm_path', 'dict_path', 'keyphrase_threshold']
        for key in required_ps_keys:
            self.assertIn(key, ps_config)

    def test_wake_word_detection_config_defaults(self):
        """Test default values in wake word detection configuration."""
        config_manager = ConfigManager(self.config_path)
        detection_config = config_manager.get_wake_word_detection_config()
        
        # Test default provider
        self.assertEqual(detection_config['provider'], 'openwakeword')
        
        # Test default OpenWakeWord settings
        oww_config = detection_config['providers']['openwakeword']
        self.assertEqual(oww_config['model_path'], './openwakeword_models')
        self.assertEqual(oww_config['threshold'], 0.5)
        self.assertEqual(oww_config['inference_framework'], 'onnx')
        
        # Test default Porcupine settings
        porcupine_config = detection_config['providers']['porcupine']
        self.assertEqual(porcupine_config['access_key'], 'your-picovoice-key-here')
        self.assertIsNone(porcupine_config['keyword_path'])
        
        # Test default PocketSphinx settings
        ps_config = detection_config['providers']['pocketsphinx']
        self.assertIsNone(ps_config['hmm_path'])
        self.assertIsNone(ps_config['dict_path'])
        self.assertEqual(ps_config['keyphrase_threshold'], 1e-20)

    def test_wake_word_detection_config_with_missing_section(self):
        """Test handling of missing wake word detection section."""
        # Create config without detection section
        config_data = {
            'wake_word': {
                'name': 'TestAssistant',
                'sensitivity': 0.5
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        config_manager = ConfigManager(self.config_path)
        
        # Should return empty dict for missing detection config
        detection_config = config_manager.get_wake_word_detection_config()
        self.assertEqual(detection_config, {})
        
        # Should return default provider
        provider = config_manager.get_wake_word_provider()
        self.assertEqual(provider, 'openwakeword')

    def test_wake_word_detection_integration_with_existing_config(self):
        """Test that wake word detection config integrates with existing wake word settings."""
        config_manager = ConfigManager(self.config_path)
        
        # Set wake word name (existing functionality)
        config_manager.set_wake_word('MyAssistant')
        
        # Set wake word provider (new functionality)
        config_manager.set_wake_word_provider('porcupine')
        
        # Verify both work together
        wake_word = config_manager.get_wake_word()
        provider = config_manager.get_wake_word_provider()
        
        self.assertEqual(wake_word, 'MyAssistant')
        self.assertEqual(provider, 'porcupine')
        
        # Verify in config structure
        config = config_manager.get_config()
        self.assertEqual(config['wake_word']['name'], 'MyAssistant')
        self.assertEqual(config['wake_word']['detection']['provider'], 'porcupine')


if __name__ == '__main__':
    print("🔧 Wake Word Configuration Unit Tests")
    print("=" * 50)
    print()
    
    # Run tests with detailed output
    unittest.main(verbosity=2)