import yaml
import os
from typing import Optional, Dict, Any
from ..utils.logger import setup_logging
from .base_tts_provider import BaseTTSProvider, TTSConfigurationError, TTSProviderUnavailableError
from .providers.pyttsx_provider import PyttsxTTSProvider
from .providers.espeak_provider import EspeakTTSProvider
from .providers.piper_provider import PiperTTSProvider


class TextToSpeech:
    """Factory-based Text-to-Speech system supporting multiple TTS providers."""
    
    def __init__(self, provider_name: Optional[str] = None):
        self.logger = setup_logging("home_assistant.tts")
        self.config = self._load_config()
        
        # Determine which provider to use
        self.provider_name = provider_name or self.config.get('tts', {}).get('provider', 'pyttsx')
        
        # Initialize the TTS provider
        self.provider = self._create_provider()
        
        self.logger.info(f"TTS initialized with {self.provider_name} provider")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml file."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.warning(f"Could not load config.yaml: {e}. Using default TTS settings")
            return {}
    
    def _create_provider(self) -> BaseTTSProvider:
        """Create TTS provider based on configuration."""
        provider_config = self.config.get('tts', {}).get('providers', {}).get(self.provider_name, {})
        
        try:
            if self.provider_name == 'pyttsx':
                return PyttsxTTSProvider(provider_config)
            elif self.provider_name == 'espeak':
                return EspeakTTSProvider(provider_config)
            elif self.provider_name == 'piper':
                return PiperTTSProvider(provider_config)
            else:
                self.logger.warning(f"Unknown TTS provider '{self.provider_name}', falling back to pyttsx")
                return PyttsxTTSProvider(provider_config)
        except (TTSConfigurationError, TTSProviderUnavailableError) as e:
            self.logger.error(f"Failed to initialize {self.provider_name} provider: {e}")
            # Try to fallback to pyttsx if it's not already the current provider
            if self.provider_name != 'pyttsx':
                self.logger.info("Attempting fallback to pyttsx provider...")
                try:
                    fallback_config = self.config.get('tts', {}).get('providers', {}).get('pyttsx', {})
                    return PyttsxTTSProvider(fallback_config)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback to pyttsx also failed: {fallback_error}")
            raise e
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get list of available TTS providers and their availability status."""
        providers = {
            'pyttsx': False,
            'espeak': False,
            'piper': False
        }
        
        # Test each provider
        try:
            provider = PyttsxTTSProvider({})
            providers['pyttsx'] = provider.is_available()
        except Exception:
            pass
        
        try:
            provider = EspeakTTSProvider({})
            providers['espeak'] = provider.is_available()
        except Exception:
            pass
        
        try:
            provider = PiperTTSProvider({})
            providers['piper'] = provider.is_available()
        except Exception:
            pass
        
        return providers
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current TTS provider."""
        return self.provider.get_provider_info()
    
    def get_available_voices(self):
        """Get list of available voices from current provider."""
        return self.provider.get_available_voices()
    
    def is_available(self) -> bool:
        """Check if current TTS provider is available."""
        return self.provider.is_available()
    
    def list_voices(self):
        """List all available voices with details."""
        voices = self.provider.get_available_voices()
        if voices:
            self.logger.info(f"Available Voices for {self.provider_name} ({len(voices)} total)")
            for i, voice in enumerate(voices):
                self.logger.info(f"Voice {i+1}: {voice['name']} (ID: {voice['id']}, Language: {voice['language']}, Gender: {voice['gender']})")
        else:
            self.logger.error(f"No voices found for {self.provider_name} provider")
    
    def set_voice(self, voice_id: str) -> bool:
        """Set a specific voice by ID."""
        return self.provider.set_voice(voice_id)
    
    def set_rate(self, rate: int) -> bool:
        """Set speech rate (words per minute)."""
        return self.provider.set_rate(rate)
    
    def set_volume(self, volume: float) -> bool:
        """Set volume (0.0 to 1.0)."""
        return self.provider.set_volume(volume)
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text using the current TTS provider.
        
        Args:
            text: The text to speak
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.provider.speak(text)