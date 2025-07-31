import yaml
import os
from typing import Dict, Any, Optional
from .logger import setup_logging


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.logger = setup_logging("home_assistant.config")
        self._config = self._load_config()
    
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
                'sensitivity': 0.5
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
    
    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration."""
        return self._config.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to YAML file."""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, indent=2)
            self._config = config
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")