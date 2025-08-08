"""
Wake Word Detector

Factory-based wake word detector that follows the same pattern as SpeechRecognizer.
Supports multiple wake word detection providers with single provider operation.
"""

from typing import Dict, Any, Optional, Tuple
import logging

from .base_wake_word_provider import BaseWakeWordProvider, WakeWordConfigurationError, WakeWordProviderUnavailableError
from ..utils.config import ConfigManager


class WakeWordDetector:
    """
    Factory-based wake word detector that manages different wake word detection providers.
    
    Similar to SpeechRecognizer, this class uses a factory pattern to create and manage
    wake word detection providers based on configuration.
    """
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize the wake word detector with a specific provider.
        
        Args:
            provider_name: Name of the provider to use. If None, uses config default.
        """
        self.logger = logging.getLogger("home_assistant.wake_word.detector")
        self.config_manager = ConfigManager()
        
        # Determine provider name
        if provider_name:
            self.provider_name = provider_name
        else:
            wake_word_config = self.config_manager.get_config().get('wake_word', {})
            detection_config = wake_word_config.get('detection', {})
            self.provider_name = detection_config.get('provider', 'openwakeword')
        
        # Create the provider
        self.provider = self._create_provider()
        
        self.logger.info(f"Wake word detector initialized with provider: {self.provider_name}")
    
    def _create_provider(self) -> BaseWakeWordProvider:
        """
        Create the wake word provider based on the configured provider name.
        
        Returns:
            BaseWakeWordProvider: The configured wake word provider
            
        Raises:
            WakeWordConfigurationError: If the provider is unknown or configuration is invalid
        """
        # Get provider-specific configuration
        wake_word_config = self.config_manager.get_config().get('wake_word', {})
        detection_config = wake_word_config.get('detection', {})
        providers_config = detection_config.get('providers', {})
        provider_config = providers_config.get(self.provider_name, {})
        
        # Add common configuration
        provider_config['provider_name'] = self.provider_name
        
        try:
            if self.provider_name == 'openwakeword':
                from .providers.openwakeword_provider import OpenWakeWordProvider
                return OpenWakeWordProvider(provider_config)
            elif self.provider_name == 'porcupine':
                from .providers.porcupine_provider import PorcupineProvider
                return PorcupineProvider(provider_config)
            elif self.provider_name == 'pocketsphinx':
                from .providers.pocketsphinx_provider import PocketSphinxProvider
                return PocketSphinxProvider(provider_config)
            else:
                raise WakeWordConfigurationError(
                    f"Unknown wake word provider '{self.provider_name}'. "
                    f"Valid options: openwakeword, porcupine, pocketsphinx"
                )
        except ImportError as e:
            raise WakeWordProviderUnavailableError(
                f"Wake word provider '{self.provider_name}' is not available. "
                f"Missing dependency: {e}"
            )
    
    def listen_for_wake_word(self, wake_word: Optional[str] = None, timeout: Optional[int] = None) -> Tuple[bool, float]:
        """
        Listen for the wake word using the configured provider.
        
        Args:
            wake_word: The wake word to listen for. If None, uses configured wake word.
            timeout: Optional timeout in seconds (None for indefinite listening)
            
        Returns:
            Tuple[bool, float]: (detected, confidence_score)
                - detected: True if wake word was detected, False if timeout
                - confidence_score: Confidence score (0.0-1.0) if detected, 0.0 if timeout
        """
        if not self.is_available():
            self.logger.error(f"Wake word provider '{self.provider_name}' is not available")
            return False, 0.0
        
        # Get wake word from config if not provided
        if wake_word is None:
            wake_word = self.config_manager.get_wake_word()
            if not wake_word:
                self.logger.error("No wake word configured")
                return False, 0.0
        
        # Validate wake word
        if not self.provider.validate_wake_word(wake_word):
            self.logger.error(f"Invalid wake word: '{wake_word}'")
            return False, 0.0
        
        try:
            self.logger.debug(f"Listening for wake word: '{wake_word}' with timeout: {timeout}")
            return self.provider.listen_for_wake_word(wake_word, timeout)
        except Exception as e:
            self.logger.error(f"Error during wake word detection: {e}")
            return False, 0.0
    
    def is_available(self) -> bool:
        """
        Check if the wake word detector is available.
        
        Returns:
            bool: True if the provider is available and ready to use
        """
        try:
            return self.provider.is_available()
        except:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current wake word provider.
        
        Returns:
            Dict[str, Any]: Provider information including engine details
        """
        try:
            info = self.provider.get_engine_info()
            info['provider_name'] = self.provider_name
            info['is_available'] = self.is_available()
            return info
        except:
            return {
                'provider_name': self.provider_name,
                'is_available': False,
                'error': 'Failed to get provider info'
            }
    
    def get_available_providers(self) -> Dict[str, bool]:
        """
        Get the availability status of all wake word providers.
        
        Returns:
            Dict[str, bool]: Dictionary mapping provider names to availability status
        """
        providers = {}
        provider_list = ['openwakeword', 'porcupine', 'pocketsphinx']
        
        for provider_name in provider_list:
            try:
                # Try to create a temporary instance to check availability
                temp_detector = WakeWordDetector(provider_name)
                providers[provider_name] = temp_detector.is_available()
            except:
                providers[provider_name] = False
        
        return providers
    
    def cleanup(self):
        """
        Clean up the wake word detector and its provider.
        """
        try:
            if self.provider:
                self.provider.cleanup()
                self.logger.debug("Wake word detector cleaned up")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()