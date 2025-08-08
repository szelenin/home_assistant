"""
PocketSphinx Provider

Implementation of wake word detection using CMU PocketSphinx.
Free offline speech recognition that can be used for keyword spotting.
"""

import os
import sys
import threading
import time
from typing import Dict, Any, Tuple, Optional
import tempfile

from ..base_wake_word_provider import BaseWakeWordProvider, WakeWordConfigurationError, WakeWordProviderUnavailableError


class PocketSphinxProvider(BaseWakeWordProvider):
    """
    PocketSphinx implementation for wake word detection.
    
    Uses CMU PocketSphinx for keyword spotting:
    - Free and open source
    - Works with any keyphrase
    - Lower accuracy than commercial solutions
    - Good for basic wake word functionality
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PocketSphinx provider.
        
        Args:
            config: Configuration dictionary containing:
                - hmm_path: Path to acoustic model (optional, uses default)
                - dict_path: Path to dictionary (optional, uses default)
                - keyphrase_threshold: Detection threshold (default: 1e-20)
        """
        super().__init__(config)
        
        self.hmm_path = config.get('hmm_path')  # Acoustic model
        self.dict_path = config.get('dict_path')  # Dictionary
        self.keyphrase_threshold = config.get('keyphrase_threshold', 1e-20)
        
        # PocketSphinx components (initialized lazily)
        self.decoder = None
        
        # Audio processing
        self.sample_rate = 16000
        self.chunk_size = 1024
        
        # State management
        self._current_keyphrase = None
        
        self.logger.debug(f"PocketSphinx provider initialized with threshold: {self.keyphrase_threshold}")
    
    def _initialize_pocketsphinx(self, wake_word: str):
        """Initialize PocketSphinx decoder with the specified wake word."""
        if self.decoder is not None and self._current_keyphrase == wake_word:
            return
        
        try:
            from pocketsphinx import Config, Decoder
            
            # Create PocketSphinx configuration
            config = Config()
            
            # Set sample rate
            config.set_string('-samprate', str(self.sample_rate))
            
            # Set acoustic model (HMM)
            if self.hmm_path and os.path.exists(self.hmm_path):
                config.set_string('-hmm', self.hmm_path)
            # else: use default model from pocketsphinx
            
            # Set dictionary
            if self.dict_path and os.path.exists(self.dict_path):
                config.set_string('-dict', self.dict_path)
            # else: use default dictionary from pocketsphinx
            
            # Configure for keyphrase spotting
            config.set_string('-keyphrase', wake_word)
            config.set_float('-kws_threshold', self.keyphrase_threshold)
            
            # Disable unnecessary components for efficiency
            config.set_string('-lm', None)  # Disable language model
            config.set_string('-bestpath', 'no')  # Disable best path search
            config.set_string('-maxwpf', '1')  # Max words per frame
            
            # Create decoder
            self.decoder = Decoder(config)
            self._current_keyphrase = wake_word
            
            self.logger.info(f"PocketSphinx decoder initialized for keyphrase: '{wake_word}'")
            
        except ImportError as e:
            raise WakeWordProviderUnavailableError(
                f"PocketSphinx library not available. Install with: pip install pocketsphinx. Error: {e}"
            )
        except Exception as e:
            raise WakeWordConfigurationError(f"Failed to initialize PocketSphinx: {e}")
    
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
                frames_per_buffer=self.chunk_size
            )
            
            self.logger.debug("Audio stream setup complete for PocketSphinx")
            
        except ImportError:
            raise WakeWordProviderUnavailableError(
                "PyAudio not available. Install with: pip install pyaudio"
            )
    
    def listen_for_wake_word(self, wake_word: str, timeout: Optional[int] = None) -> Tuple[bool, float]:
        """
        Listen for the wake word using PocketSphinx.
        
        Args:
            wake_word: The wake word to listen for
            timeout: Optional timeout in seconds (None for indefinite listening)
            
        Returns:
            Tuple[bool, float]: (detected, confidence_score)
        """
        if not self.is_available():
            raise WakeWordProviderUnavailableError("PocketSphinx provider is not available")
        
        self._initialize_pocketsphinx(wake_word)
        self._setup_audio()
        
        try:
            self.logger.info(f"Listening for wake word with PocketSphinx: '{wake_word}'")
            
            # Start utterance
            self.decoder.start_utt()
            start_time = time.time()
            
            while True:
                # Check timeout
                if timeout and time.time() - start_time > timeout:
                    self.logger.debug("PocketSphinx wake word detection timed out")
                    return False, 0.0
                
                # Read audio data
                try:
                    audio_data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Process audio with PocketSphinx
                    self.decoder.process_raw(audio_data, False, False)
                    
                    # Check for hypothesis (detected keyphrase)
                    hypothesis = self.decoder.hyp()
                    if hypothesis is not None:
                        detected_text = hypothesis.hypstr
                        confidence = hypothesis.best_score
                        
                        self.logger.info(f"PocketSphinx detected: '{detected_text}' (score: {confidence})")
                        
                        # Check if detected text matches our wake word (case insensitive)
                        if wake_word.lower() in detected_text.lower():
                            # Convert score to confidence (PocketSphinx scores are negative log probabilities)
                            # Higher (less negative) scores indicate higher confidence
                            confidence_score = min(1.0, max(0.0, (confidence + 10000) / 10000))
                            
                            return True, confidence_score
                        else:
                            # Restart utterance for continuous listening
                            self.decoder.end_utt()
                            self.decoder.start_utt()
                    
                except Exception as e:
                    self.logger.warning(f"Error processing audio with PocketSphinx: {e}")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("PocketSphinx wake word detection interrupted by user")
            return False, 0.0
        except Exception as e:
            self.logger.error(f"Error during PocketSphinx wake word detection: {e}")
            raise WakeWordProviderUnavailableError(f"PocketSphinx wake word detection failed: {e}")
        finally:
            # Clean up
            if self.decoder:
                self.decoder.end_utt()
            if hasattr(self, 'audio_stream') and self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            if hasattr(self, 'audio'):
                self.audio.terminate()
    
    def is_available(self) -> bool:
        """
        Check if PocketSphinx provider is available.
        
        Returns:
            bool: True if PocketSphinx is available and properly configured
        """
        try:
            # Check if PocketSphinx is installed
            from pocketsphinx import Config, Decoder
            
            # Check if PyAudio is available
            import pyaudio
            
            # Try to create a minimal decoder to test functionality
            try:
                config = Config()
                config.set_string('-samprate', '16000')
                config.set_string('-keyphrase', 'test')
                config.set_float('-kws_threshold', 1e-20)
                config.set_string('-lm', None)
                
                test_decoder = Decoder(config)
                # If we get here, PocketSphinx is working
                return True
                
            except Exception as e:
                self.logger.debug(f"PocketSphinx test initialization failed: {e}")
                return False
            
        except ImportError as e:
            self.logger.debug(f"PocketSphinx not available: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"PocketSphinx availability check failed: {e}")
            return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the PocketSphinx engine.
        
        Returns:
            Dict[str, Any]: Engine information
        """
        info = {
            'name': 'CMU PocketSphinx',
            'description': 'Free offline speech recognition for keyword spotting',
            'supported_languages': ['English (extensible with custom models)'],
            'accuracy': 'Fair (70-85% depending on conditions and threshold)',
            'latency': 'Medium (200-500ms)',
            'resource_usage': 'Low-Medium (lightweight but may use CPU for processing)',
            'licensing': 'BSD (Free)',
            'offline': True,
            'custom_words': True,
            'hmm_path': self.hmm_path,
            'dict_path': self.dict_path,
            'keyphrase_threshold': self.keyphrase_threshold
        }
        
        try:
            import pocketsphinx
            info['version'] = getattr(pocketsphinx, '__version__', 'Unknown')
        except ImportError:
            info['version'] = 'Not installed'
        
        return info
    
    def validate_wake_word(self, wake_word: str) -> bool:
        """
        Validate wake word for PocketSphinx.
        
        PocketSphinx can work with any phrase, but some work better than others.
        
        Args:
            wake_word: The wake word to validate
            
        Returns:
            bool: True if valid for PocketSphinx
        """
        if not super().validate_wake_word(wake_word):
            return False
        
        # PocketSphinx specific validation
        wake_word = wake_word.strip().lower()
        
        # Should be 1-5 words for best performance
        words = wake_word.split()
        if len(words) > 5:
            self.logger.warning(f"Wake word may be too long (>5 words) for PocketSphinx: '{wake_word}'")
            return False
        
        # Avoid very short single character words
        for word in words:
            if len(word) < 2:
                self.logger.warning(f"Very short word in wake phrase: '{word}' in '{wake_word}'")
                return False
        
        # PocketSphinx works better with common English words
        # but we'll accept any reasonable phrase
        return True
    
    def get_supported_wake_words(self) -> Optional[list]:
        """
        Get list of supported wake words.
        
        Returns:
            None: PocketSphinx supports any keyphrase (custom words)
        """
        # PocketSphinx supports arbitrary keyphrases
        return None
    
    def cleanup(self):
        """Clean up PocketSphinx resources."""
        try:
            if hasattr(self, 'audio_stream') and self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            if hasattr(self, 'audio'):
                self.audio.terminate()
            
            if self.decoder:
                # PocketSphinx decoder doesn't have explicit cleanup
                self.decoder = None
                self._current_keyphrase = None
            
            self.logger.debug("PocketSphinx provider cleaned up")
            
        except Exception as e:
            self.logger.warning(f"Error during PocketSphinx cleanup: {e}")