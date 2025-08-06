import yaml
import os
from typing import Optional, Dict, Any, Tuple
from ..utils.logger import setup_logging
from .base_speech_provider import BaseSpeechProvider, SpeechConfigurationError, SpeechProviderUnavailableError
from .providers.vosk_provider import VoskSpeechProvider
from .providers.google_provider import GoogleSpeechProvider
from .providers.whisper_provider import WhisperSpeechProvider


class SpeechRecognizer:
    """Factory-based Speech Recognition system supporting multiple speech providers."""
    
    def __init__(self, provider_name: Optional[str] = None):
        self.logger = setup_logging("home_assistant.speech.recognizer")
        self.config = self._load_config()
        
        # Determine which provider to use
        self.provider_name = provider_name or self.config.get('speech', {}).get('provider', 'vosk')
        
        # Initialize the speech recognition provider
        self.provider = self._create_provider()
        
        self.logger.info(f"Speech Recognition initialized with {self.provider_name} provider")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml file."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.warning(f"Could not load config.yaml: {e}. Using default speech recognition settings")
            return {}
    
    def _create_provider(self) -> BaseSpeechProvider:
        """Create speech recognition provider based on configuration."""
        # Get provider-specific configuration
        provider_config = self.config.get('speech', {}).get('providers', {}).get(self.provider_name, {})
        
        # Add global language setting if not specified in provider config
        global_language = self.config.get('speech', {}).get('language', 'en-US')
        if 'language' not in provider_config and self.provider_name in ['google', 'whisper']:
            provider_config['language'] = global_language
        
        try:
            if self.provider_name == 'vosk':
                return VoskSpeechProvider(provider_config)
            elif self.provider_name == 'google':
                return GoogleSpeechProvider(provider_config)
            elif self.provider_name == 'whisper':
                return WhisperSpeechProvider(provider_config)
            else:
                raise SpeechConfigurationError(f"Unknown speech provider '{self.provider_name}'. Valid options: vosk, google, whisper")
        except (SpeechConfigurationError, SpeechProviderUnavailableError) as e:
            self.logger.error(f"Failed to initialize {self.provider_name} provider: {e}")
            raise e
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get list of available speech recognition providers and their availability status."""
        providers = {
            'vosk': False,
            'google': False,
            'whisper': False
        }
        
        # Test each provider
        try:
            provider = VoskSpeechProvider({})
            providers['vosk'] = provider.is_available()
        except Exception:
            pass
        
        try:
            provider = GoogleSpeechProvider({})
            providers['google'] = provider.is_available()
        except Exception:
            pass
        
        try:
            provider = WhisperSpeechProvider({})
            providers['whisper'] = provider.is_available()
        except Exception:
            pass
        
        return providers
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        if self.provider:
            return self.provider.get_engine_info()
        return {'status': 'not_initialized'}
    
    def listen_for_speech(self, timeout: int = 10, phrase_timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Listen for speech and return the recognized text using the configured provider.
        
        Args:
            timeout: Maximum time to wait for speech to start (seconds)
            phrase_timeout: Maximum time to wait for phrase to complete (seconds)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, recognized_text)
        """
        if not self.provider:
            self.logger.error("No speech recognition provider available")
            return False, None
        
        return self.provider.listen_for_speech(timeout, phrase_timeout)
    
    def is_available(self) -> bool:
        """Check if speech recognition is available."""
        return self.provider is not None and self.provider.is_available()
    
    def get_available_engines(self):
        """Legacy method for compatibility - returns list of available provider names."""
        available_providers = self.get_available_providers()
        return [name for name, available in available_providers.items() if available]