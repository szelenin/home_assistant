from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..utils.logger import setup_logging


class TTSConfigurationError(Exception):
    """Raised when TTS provider configuration is invalid."""
    pass


class TTSProviderUnavailableError(Exception):
    """Raised when TTS provider is not available on the current system."""
    pass


class BaseTTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the TTS provider.
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config
        self.logger = setup_logging(f"home_assistant.tts.{self.__class__.__name__.lower()}")
        self._validate_config()
        self._initialize_provider()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate provider-specific configuration.
        
        Raises:
            TTSConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def _initialize_provider(self) -> None:
        """
        Initialize the TTS provider.
        
        Raises:
            TTSProviderUnavailableError: If provider cannot be initialized
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this TTS provider is available on the current system.
        
        Returns:
            bool: True if provider is available, False otherwise
        """
        pass
    
    @abstractmethod
    def speak(self, text: str) -> bool:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices for this provider.
        
        Returns:
            List of voice dictionaries with keys: id, name, language, gender
        """
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the voice to use for speech synthesis.
        
        Args:
            voice_id: Voice identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def set_rate(self, rate: int) -> bool:
        """
        Set speech rate in words per minute.
        
        Args:
            rate: Speech rate (typically 50-400 WPM)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def set_volume(self, volume: float) -> bool:
        """
        Set speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the name of this TTS provider."""
        return self.__class__.__name__.replace("TTSProvider", "").lower()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this TTS provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            "name": self.get_provider_name(),
            "available": self.is_available(),
            "voices": len(self.get_available_voices()),
            "config": self.config
        }
    
    def _validate_text_input(self, text: str) -> bool:
        """
        Validate text input for TTS.
        
        Args:
            text: Text to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not text or not isinstance(text, str):
            self.logger.warning("Invalid text input: must be non-empty string")
            return False
        
        if not text.strip():
            self.logger.warning("Empty or whitespace-only text provided")
            return False
        
        return True
    
    def _log_speech_attempt(self, text: str) -> None:
        """Log speech attempt for debugging."""
        self.logger.info(f"Speaking with {self.get_provider_name()}: {text[:50]}{'...' if len(text) > 50 else ''}")