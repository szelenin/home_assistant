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

        # Audio processing - load from main config
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_device_index = None
        self.input_device = None

        # Load audio configuration
        self._load_audio_config()

        # State management
        self._current_keyphrase = None

        self.logger.debug(f"PocketSphinx provider initialized with threshold: {self.keyphrase_threshold}")

    def _load_audio_config(self):
        """Load audio configuration from main config file."""
        try:
            import yaml
            import os

            # Load main config.yaml from project root
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    main_config = yaml.safe_load(f)

                audio_config = main_config.get('audio', {})
                self.input_device = audio_config.get('input_device')
                self.device_patterns = audio_config.get('device_patterns', [])

                if self.input_device:
                    self.logger.info(f"Using configured input device: {self.input_device}")
                    # Convert device string like "hw:2,0" to PyAudio device index
                    self._find_device_index()
                else:
                    self.logger.debug("No input device specified, using default")

            else:
                self.logger.warning("config.yaml not found, using default audio device")

        except Exception as e:
            self.logger.warning(f"Error loading audio config: {e}, using default audio device")

    def _find_device_index(self):
        """Find PyAudio device index for the configured input device."""
        try:
            import pyaudio

            audio = pyaudio.PyAudio()

            # For hw:X,Y format, try to find device by name or index
            if self.input_device.startswith('hw:'):
                # Extract card number from hw:X,Y
                try:
                    card_num = int(self.input_device.split(':')[1].split(',')[0])

                    # Find device by checking device info
                    for i in range(audio.get_device_count()):
                        device_info = audio.get_device_info_by_index(i)

                        # Check if this is an input device and matches configured patterns
                        if device_info['maxInputChannels'] > 0:
                            # Check if device name matches any configured patterns
                            device_matches = any(pattern.lower() in device_info['name'].lower()
                                               for pattern in self.device_patterns) if self.device_patterns else False

                            if device_matches:
                                self.audio_device_index = i
                                self.logger.info(f"Found configured audio device at index {i}: {device_info['name']}")
                                break

                except (ValueError, IndexError):
                    pass

            audio.terminate()

        except Exception as e:
            self.logger.warning(f"Error finding device index: {e}")

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

            # Use configured audio device index if available
            audio_kwargs = {
                'format': pyaudio.paInt16,
                'channels': 1,
                'rate': self.sample_rate,
                'input': True,
                'frames_per_buffer': self.chunk_size
            }

            if self.audio_device_index is not None:
                audio_kwargs['input_device_index'] = self.audio_device_index
                self.logger.info(f"Opening audio stream with device index: {self.audio_device_index}")
            else:
                self.logger.debug("Using default audio device for PocketSphinx")

            self.audio_stream = self.audio.open(**audio_kwargs)

            self.logger.debug("Audio stream setup complete for PocketSphinx")

        except ImportError:
            raise WakeWordProviderUnavailableError(
                "PyAudio not available. Install with: pip install pyaudio"
            )
        except Exception as e:
            # If specific device fails, try default
            if self.audio_device_index is not None:
                self.logger.warning(f"Failed to open configured device {self.audio_device_index}, trying default: {e}")
                try:
                    self.audio_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=self.sample_rate,
                        input=True,
                        frames_per_buffer=self.chunk_size
                    )
                    self.logger.info("Using default audio device as fallback")
                except Exception as e2:
                    raise WakeWordProviderUnavailableError(f"Audio setup failed: {e2}")
            else:
                raise WakeWordProviderUnavailableError(f"Audio setup failed: {e}")
    
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

        # Only setup audio if not already setup
        if not hasattr(self, 'audio_stream') or not self.audio_stream:
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
            # Clean up decoder state but keep audio stream for reuse
            if self.decoder:
                self.decoder.end_utt()
            # Note: Keep audio stream open for reuse in subsequent calls
    
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
    
    def pause_audio_stream(self):
        """Pause the audio stream to avoid conflicts with TTS."""
        try:
            if hasattr(self, 'audio_stream') and self.audio_stream:
                self.logger.debug("⏸️ [AUDIO PAUSE] Pausing PocketSphinx audio stream for TTS")
                self.audio_stream.stop_stream()
                return True
        except Exception as e:
            self.logger.warning(f"Failed to pause PocketSphinx audio stream: {e}")
        return False

    def resume_audio_stream(self):
        """Resume the audio stream after TTS is complete."""
        try:
            if hasattr(self, 'audio_stream') and self.audio_stream:
                self.logger.debug("▶️ [AUDIO RESUME] Resuming PocketSphinx audio stream after TTS")
                self.audio_stream.start_stream()
                return True
        except Exception as e:
            self.logger.warning(f"Failed to resume PocketSphinx audio stream: {e}")
        return False

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