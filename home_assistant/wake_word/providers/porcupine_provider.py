"""
Porcupine Provider

Implementation of wake word detection using Picovoice Porcupine.
Commercial provider offering high accuracy and low latency detection.
"""

import os
import sys
import numpy as np
from typing import Dict, Any, Tuple, Optional
import time

from ..base_wake_word_provider import BaseWakeWordProvider, WakeWordConfigurationError, WakeWordProviderUnavailableError


class PorcupineProvider(BaseWakeWordProvider):
    """
    Porcupine implementation for wake word detection.
    
    Commercial wake word detection service by Picovoice offering:
    - High accuracy and low latency
    - Pre-built keyword models
    - Custom keyword creation capability
    - Requires Picovoice account and access key
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Porcupine provider.
        
        Args:
            config: Configuration dictionary containing:
                - access_key: Picovoice access key (required)
                - keyword_path: Path to custom .ppn keyword file (optional)
        """
        super().__init__(config)
        
        self.access_key = config.get('access_key', 'your-picovoice-key-here')
        self.keyword_path = config.get('keyword_path')
        
        # Porcupine components (initialized lazily)
        self.porcupine = None
        self.audio_stream = None
        
        # Audio processing settings
        self.sample_rate = 16000
        self.frame_length = 512  # Porcupine requires specific frame length
        
        # State management
        self._keywords = []
        
        self.logger.debug(f"Porcupine provider initialized with access_key: {'***' if self.access_key != 'your-picovoice-key-here' else 'NOT SET'}")
    
    def _initialize_porcupine(self, wake_word: str):
        """Initialize Porcupine with the specified wake word."""
        if self.porcupine is not None:
            return
        
        try:
            import pvporcupine
            
            # Determine keyword to use
            keyword_names = []
            keyword_paths = []
            
            if self.keyword_path and os.path.exists(self.keyword_path):
                # Use custom keyword file
                keyword_paths.append(self.keyword_path)
                self.logger.info(f"Using custom Porcupine keyword: {self.keyword_path}")
            else:
                # Try to use built-in keywords
                wake_word_lower = wake_word.lower()
                
                # Map common wake words to Porcupine built-in keywords
                builtin_keywords = {
                    'alexa': 'alexa',
                    'computer': 'computer',
                    'jarvis': 'jarvis',
                    'smart mirror': 'smart mirror',
                    'hey google': 'hey google',
                    'hey siri': 'hey siri',
                    'bumblebee': 'bumblebee',
                    'grasshopper': 'grasshopper',
                    'picovoice': 'picovoice',
                    'terminator': 'terminator'
                }
                
                if wake_word_lower in builtin_keywords:
                    keyword_names.append(builtin_keywords[wake_word_lower])
                    self.logger.info(f"Using built-in Porcupine keyword: {builtin_keywords[wake_word_lower]}")
                else:
                    # No suitable keyword found
                    raise WakeWordConfigurationError(
                        f"Wake word '{wake_word}' not supported by Porcupine built-in keywords. "
                        f"Available keywords: {', '.join(builtin_keywords.keys())}. "
                        f"To use custom wake words, provide a .ppn file path in keyword_path config."
                    )
            
            # Initialize Porcupine
            if keyword_paths:
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=keyword_paths
                )
            else:
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=keyword_names
                )
            
            # Verify sample rate
            expected_sample_rate = self.porcupine.sample_rate
            if self.sample_rate != expected_sample_rate:
                self.logger.warning(f"Adjusting sample rate from {self.sample_rate} to {expected_sample_rate}")
                self.sample_rate = expected_sample_rate
            
            # Verify frame length
            expected_frame_length = self.porcupine.frame_length
            if self.frame_length != expected_frame_length:
                self.logger.warning(f"Adjusting frame length from {self.frame_length} to {expected_frame_length}")
                self.frame_length = expected_frame_length
            
            self.logger.info("Porcupine initialized successfully")
            
        except ImportError as e:
            raise WakeWordProviderUnavailableError(
                f"Porcupine library not available. Install with: pip install pvporcupine. Error: {e}"
            )
        except Exception as e:
            if "invalid access key" in str(e).lower():
                raise WakeWordConfigurationError(
                    f"Invalid Porcupine access key. Get your key from: https://console.picovoice.ai/"
                )
            else:
                raise WakeWordConfigurationError(f"Failed to initialize Porcupine: {e}")
    
    def _setup_audio(self):
        """Set up audio recording for wake word detection."""
        try:
            import pyaudio
            
            self.audio = pyaudio.PyAudio()
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.frame_length
            )
            
            self.logger.debug("Audio stream setup complete")
            
        except ImportError:
            raise WakeWordProviderUnavailableError(
                "PyAudio not available. Install with: pip install pyaudio"
            )
    
    def listen_for_wake_word(self, wake_word: str, timeout: Optional[int] = None) -> Tuple[bool, float]:
        """
        Listen for the wake word using Porcupine.
        
        Args:
            wake_word: The wake word to listen for
            timeout: Optional timeout in seconds (None for indefinite listening)
            
        Returns:
            Tuple[bool, float]: (detected, confidence_score)
        """
        if not self.is_available():
            raise WakeWordProviderUnavailableError("Porcupine provider is not available")
        
        self._initialize_porcupine(wake_word)
        self._setup_audio()
        
        try:
            self.logger.info(f"Listening for wake word with Porcupine: '{wake_word}'")
            start_time = time.time()
            
            while True:
                # Check timeout
                if timeout and time.time() - start_time > timeout:
                    self.logger.debug("Porcupine wake word detection timed out")
                    return False, 0.0
                
                # Read audio data
                try:
                    audio_data = self.audio_stream.read(self.frame_length, exception_on_overflow=False)
                    pcm = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Process with Porcupine
                    keyword_index = self.porcupine.process(pcm)
                    
                    if keyword_index >= 0:
                        self.logger.info(f"Wake word detected by Porcupine! Keyword index: {keyword_index}")
                        return True, 1.0  # Porcupine doesn't provide confidence scores
                    
                except Exception as e:
                    self.logger.warning(f"Error processing audio with Porcupine: {e}")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("Porcupine wake word detection interrupted by user")
            return False, 0.0
        except Exception as e:
            self.logger.error(f"Error during Porcupine wake word detection: {e}")
            raise WakeWordProviderUnavailableError(f"Porcupine wake word detection failed: {e}")
        finally:
            # Clean up audio resources
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            if hasattr(self, 'audio'):
                self.audio.terminate()
    
    def is_available(self) -> bool:
        """
        Check if Porcupine provider is available.
        
        Returns:
            bool: True if Porcupine is available and properly configured
        """
        try:
            # Check if Porcupine is installed
            import pvporcupine
            
            # Check if PyAudio is available
            import pyaudio
            
            # Check if access key is configured
            if self.access_key == 'your-picovoice-key-here':
                self.logger.debug("Porcupine access key not configured")
                return False
            
            # Try to create a minimal Porcupine instance to validate key
            try:
                test_porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=['alexa']  # Use built-in keyword for testing
                )
                test_porcupine.delete()
                return True
                
            except Exception as e:
                if "invalid access key" in str(e).lower():
                    self.logger.debug(f"Invalid Porcupine access key")
                    return False
                else:
                    self.logger.debug(f"Porcupine availability test failed: {e}")
                    return False
            
        except ImportError as e:
            self.logger.debug(f"Porcupine not available: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Porcupine availability check failed: {e}")
            return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the Porcupine engine.
        
        Returns:
            Dict[str, Any]: Engine information
        """
        info = {
            'name': 'Picovoice Porcupine',
            'description': 'Commercial high-accuracy wake word detection with low latency',
            'supported_languages': ['English (built-in keywords and custom models)'],
            'accuracy': 'Excellent (95%+ with optimized models)',
            'latency': 'Very Low (~30ms)',
            'resource_usage': 'Low (optimized for edge devices)',
            'licensing': 'Commercial (requires Picovoice account)',
            'offline': True,
            'custom_words': True,
            'access_key_configured': self.access_key != 'your-picovoice-key-here',
            'keyword_path': self.keyword_path
        }
        
        try:
            import pvporcupine
            info['version'] = pvporcupine.PORCUPINE_VERSION
        except ImportError:
            info['version'] = 'Not installed'
        
        return info
    
    def validate_wake_word(self, wake_word: str) -> bool:
        """
        Validate wake word for Porcupine.
        
        Args:
            wake_word: The wake word to validate
            
        Returns:
            bool: True if valid for Porcupine
        """
        if not super().validate_wake_word(wake_word):
            return False
        
        wake_word_lower = wake_word.lower()
        
        # If custom keyword path is provided, any valid word is acceptable
        if self.keyword_path and os.path.exists(self.keyword_path):
            return True
        
        # Check against built-in keywords
        builtin_keywords = [
            'alexa', 'computer', 'jarvis', 'smart mirror', 'hey google', 
            'hey siri', 'bumblebee', 'grasshopper', 'picovoice', 'terminator'
        ]
        
        if wake_word_lower in builtin_keywords:
            return True
        
        self.logger.warning(f"Wake word '{wake_word}' not in Porcupine built-in keywords")
        return False
    
    def get_supported_wake_words(self) -> Optional[list]:
        """
        Get list of supported wake words.
        
        Returns:
            list: List of built-in wake words supported by Porcupine
        """
        if self.keyword_path and os.path.exists(self.keyword_path):
            # Custom keyword file - extract name from filename
            filename = os.path.basename(self.keyword_path)
            name = filename.replace('.ppn', '').replace('_', ' ').title()
            return [name]
        
        # Return built-in keywords
        return [
            'Alexa', 'Computer', 'Jarvis', 'Smart Mirror', 'Hey Google',
            'Hey Siri', 'Bumblebee', 'Grasshopper', 'Picovoice', 'Terminator'
        ]
    
    def cleanup(self):
        """Clean up Porcupine resources."""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            if hasattr(self, 'audio'):
                self.audio.terminate()
            
            if self.porcupine:
                self.porcupine.delete()
                self.porcupine = None
            
            self.logger.debug("Porcupine provider cleaned up")
            
        except Exception as e:
            self.logger.warning(f"Error during Porcupine cleanup: {e}")