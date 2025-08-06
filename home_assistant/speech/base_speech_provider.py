from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from ..utils.logger import setup_logging


class SpeechConfigurationError(Exception):
    """Raised when speech recognition provider configuration is invalid."""
    pass


class SpeechProviderUnavailableError(Exception):
    """Raised when speech recognition provider is not available on the current system."""
    pass


class BaseSpeechProvider(ABC):
    """Abstract base class for Speech Recognition providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the speech recognition provider.
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config
        self.logger = setup_logging(f"home_assistant.speech.{self.__class__.__name__.lower()}")
        self._validate_config()
        self._initialize_provider()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate provider-specific configuration.
        
        Raises:
            SpeechConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def _initialize_provider(self) -> None:
        """
        Initialize the speech recognition provider.
        
        Raises:
            SpeechProviderUnavailableError: If provider cannot be initialized
        """
        pass
    
    @abstractmethod
    def listen_for_speech(self, timeout: int = 10, phrase_timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Listen for speech and return the recognized text.
        
        Args:
            timeout: Maximum time to wait for speech to start (seconds)
            phrase_timeout: Maximum time to wait for phrase to complete (seconds)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, recognized_text)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the speech recognition provider is available.
        
        Returns:
            bool: True if provider is available and working, False otherwise
        """
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the speech recognition engine.
        
        Returns:
            Dict[str, Any]: Engine information including name, version, capabilities
        """
        pass
    
    def _validate_timeout_params(self, timeout: int, phrase_timeout: int) -> None:
        """
        Validate timeout parameters.
        
        Args:
            timeout: Speech detection timeout
            phrase_timeout: Phrase completion timeout
            
        Raises:
            SpeechConfigurationError: If timeout values are invalid
        """
        if not isinstance(timeout, int) or timeout <= 0:
            raise SpeechConfigurationError(f"Timeout must be a positive integer, got: {timeout}")
        
        if not isinstance(phrase_timeout, int) or phrase_timeout <= 0:
            raise SpeechConfigurationError(f"Phrase timeout must be a positive integer, got: {phrase_timeout}")
        
        if timeout < phrase_timeout:
            raise SpeechConfigurationError(f"Timeout ({timeout}) must be >= phrase_timeout ({phrase_timeout})")
    
    def _log_speech_attempt(self, timeout: int, phrase_timeout: int) -> None:
        """Log speech recognition attempt."""
        self.logger.info(f"Listening for speech (timeout: {timeout}s, phrase_timeout: {phrase_timeout}s)")
    
    def _log_speech_result(self, success: bool, text: Optional[str]) -> None:
        """Log speech recognition result."""
        if success and text:
            self.logger.info(f"Speech recognized: '{text}'")
        elif success and not text:
            self.logger.warning("Speech detection succeeded but no text recognized")
        else:
            self.logger.warning("Speech recognition failed or timed out")