import yaml
import os
from typing import Dict, Any, Optional
from .logger import setup_logging


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.logger = setup_logging("home_assistant.config")
        self._config = self._load_config()
        self._ai_config = self._load_ai_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file, create default if not exists."""
        if not os.path.exists(self.config_path):
            self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file) or {}
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            'wake_word': {
                'name': None,
                'sensitivity': 0.5,
                'detection': {
                    'provider': 'openwakeword',  # Options: openwakeword, porcupine, pocketsphinx
                    'providers': {
                        'openwakeword': {
                            'model_path': './openwakeword_models',
                            'threshold': 0.5,
                            'inference_framework': 'onnx'
                        },
                        'porcupine': {
                            'access_key': 'your-picovoice-key-here',
                            'keyword_path': None
                        },
                        'pocketsphinx': {
                            'hmm_path': None,
                            'dict_path': None,
                            'keyphrase_threshold': 1e-20
                        }
                    }
                }
            },
            'speech': {
                'provider': 'vosk',
                'language': 'en-US'
            },
            'audio': {
                'sample_rate': 16000,
                'chunk_size': 512
            }
        }
        
        self.save_config(default_config)
    
    def get_wake_word(self) -> Optional[str]:
        """Get the configured wake word name."""
        return self._config.get('wake_word', {}).get('name')
    
    def set_wake_word(self, name: str):
        """Set the wake word name and save to config."""
        if 'wake_word' not in self._config:
            self._config['wake_word'] = {}
        
        self._config['wake_word']['name'] = name
        self.save_config(self._config)
    
    def get_wake_word_detection_config(self) -> Dict[str, Any]:
        """Get the wake word detection configuration."""
        return self._config.get('wake_word', {}).get('detection', {})
    
    def get_wake_word_provider(self) -> str:
        """Get the configured wake word detection provider."""
        detection_config = self.get_wake_word_detection_config()
        return detection_config.get('provider', 'openwakeword')
    
    def set_wake_word_provider(self, provider: str):
        """Set the wake word detection provider and save to config."""
        if 'wake_word' not in self._config:
            self._config['wake_word'] = {}
        if 'detection' not in self._config['wake_word']:
            self._config['wake_word']['detection'] = {}
        
        self._config['wake_word']['detection']['provider'] = provider
        self.save_config(self._config)
    
    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration."""
        return self._config.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to YAML file."""
        if config is None:
            config = self._config
        
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, indent=2)
            self._config = config
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def _load_ai_config(self) -> Dict[str, Any]:
        """Load AI configuration from separate file."""
        ai_config_file = self._config.get('ai', {}).get('config_file', 'ai_config.yaml')
        
        if not os.path.exists(ai_config_file):
            self.logger.warning(f"AI config file not found: {ai_config_file}")
            self.logger.info("Create ai_config.yaml from ai_config.example.yaml template")
            return {}
        
        try:
            with open(ai_config_file, 'r') as file:
                ai_config = yaml.safe_load(file) or {}
                self.logger.info(f"Loaded AI configuration from {ai_config_file}")
                return ai_config
        except Exception as e:
            self.logger.error(f"Error loading AI config from {ai_config_file}: {e}")
            return {}
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get the AI configuration with provider-specific settings."""
        if not self._ai_config:
            return {}
        
        # Get current provider
        provider = self._config.get('ai', {}).get('provider', 'anthropic')
        
        # Merge provider-specific config with API keys
        ai_config = {
            'provider': provider,
            'anthropic_api_key': self._ai_config.get('anthropic_api_key'),
            'openai_api_key': self._ai_config.get('openai_api_key')
        }
        
        # Add provider-specific settings
        if provider in self._ai_config:
            ai_config.update(self._ai_config[provider])
        
        return ai_config
    
    def reload_ai_config(self):
        """Reload AI configuration from file."""
        self._ai_config = self._load_ai_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Property to access the main configuration."""
        return self._config