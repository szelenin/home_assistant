"""
Base Wake Word Provider

Abstract base class for all wake word detection providers.
Follows the same pattern as BaseSpeechProvider for consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import logging


class WakeWordConfigurationError(Exception):
    """Raised when there's a configuration error with the wake word provider."""
    pass


class WakeWordProviderUnavailableError(Exception):
    """Raised when the wake word provider is not available."""
    pass


class WakeWordDetectedError(Exception):
    """Raised when wake word is detected (used as signal)."""
    pass


class BaseWakeWordProvider(ABC):
    """
    Abstract base class for wake word detection providers.
    
    All wake word providers must implement this interface to ensure
    consistent behavior across different wake word detection engines.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the wake word provider.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"home_assistant.wake_word.{self.__class__.__name__.lower()}")
        
    @abstractmethod
    def listen_for_wake_word(self, wake_word: str, timeout: Optional[int] = None) -> Tuple[bool, float]:
        """
        Listen for the wake word and return when detected or timeout reached.
        
        Args:
            wake_word: The wake word to listen for
            timeout: Optional timeout in seconds (None for indefinite listening)
            
        Returns:
            Tuple[bool, float]: (detected, confidence_score)
                - detected: True if wake word was detected, False if timeout
                - confidence_score: Confidence score (0.0-1.0) if detected, 0.0 if timeout
                
        Raises:
            WakeWordProviderUnavailableError: If the provider is not available
            WakeWordConfigurationError: If there's a configuration issue
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the wake word provider is available and properly configured.
        
        Returns:
            bool: True if the provider is ready to use, False otherwise
        """
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the wake word detection engine.
        
        Returns:
            Dict[str, Any]: Dictionary containing engine information:
                - name: Engine name
                - version: Engine version if available
                - description: Brief description
                - supported_languages: List of supported languages
                - accuracy: Expected accuracy description
                - latency: Expected latency description
                - resource_usage: Expected resource usage description
        """
        pass
    
    def cleanup(self):
        """
        Clean up any resources used by the provider.
        Called when the provider is no longer needed.
        """
        pass
    
    def validate_wake_word(self, wake_word: str) -> bool:
        """
        Validate that the wake word is suitable for this provider.
        
        Args:
            wake_word: The wake word to validate
            
        Returns:
            bool: True if the wake word is valid for this provider
        """
        if not wake_word or not isinstance(wake_word, str):
            return False
        
        # Basic validation - can be overridden by providers
        wake_word = wake_word.strip()
        if len(wake_word) < 2:
            return False
        
        # Should contain only letters, numbers, and basic punctuation
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', wake_word):
            return False
        
        return True
    
    def get_supported_wake_words(self) -> Optional[list]:
        """
        Get list of pre-defined wake words supported by this provider.
        
        Returns:
            Optional[list]: List of supported wake words, or None if custom words are supported
        """
        # Default implementation - providers can override
        return None