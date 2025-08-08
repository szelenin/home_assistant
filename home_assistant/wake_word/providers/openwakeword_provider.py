"""
OpenWakeWord Provider

Implementation of wake word detection using OpenWakeWord library.
This is the default provider offering custom wake word training and offline operation.
"""

import os
import sys
import numpy as np
from typing import Dict, Any, Tuple, Optional
import threading
import time

from ..base_wake_word_provider import BaseWakeWordProvider, WakeWordConfigurationError, WakeWordProviderUnavailableError


class OpenWakeWordProvider(BaseWakeWordProvider):
    """
    OpenWakeWord implementation for wake word detection.
    
    Supports custom wake words with offline operation and good accuracy.
    Best for privacy-focused deployments and custom wake word requirements.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenWakeWord provider.
        
        Args:
            config: Configuration dictionary containing:
                - model_path: Path to OpenWakeWord models directory
                - threshold: Detection threshold (0.0-1.0, default 0.5)
                - inference_framework: Framework to use ('onnx' or 'tflite', default 'onnx')
        """
        super().__init__(config)
        
        self.model_path = config.get('model_path', './openwakeword_models')
        self.threshold = config.get('threshold', 0.5)
        self.inference_framework = config.get('inference_framework', 'onnx')
        
        # OpenWakeWord components (initialized lazily)
        self.oww_model = None
        self.audio_format = None
        
        # Audio processing
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        
        # State management
        self._stop_listening = False
        self._listening_thread = None
        
        self.logger.debug(f"OpenWakeWord provider initialized with model_path: {self.model_path}")
    
    def _initialize_openwakeword(self):
        """Initialize OpenWakeWord components if not already done."""
        if self.oww_model is not None:
            return
        
        try:
            import openwakeword
            from openwakeword import Model
            
            # Initialize the model with proper file paths
            if os.path.isdir(self.model_path):
                # Load specific wake word models from directory
                wake_word_models = []
                model_extension = '.onnx' if self.inference_framework == 'onnx' else '.tflite'
                
                for filename in os.listdir(self.model_path):
                    if (filename.endswith(model_extension) and 
                        not filename.startswith(('embedding_', 'melspectrogram', 'silero_'))):
                        wake_word_models.append(os.path.join(self.model_path, filename))
                
                if wake_word_models:
                    self.logger.debug(f"Loading wake word models: {wake_word_models}")
                    self.oww_model = Model(
                        wakeword_models=wake_word_models,
                        inference_framework=self.inference_framework
                    )
                else:
                    # Fallback: load all available pre-trained models
                    self.logger.debug("No specific models found, loading all pre-trained models")
                    self.oww_model = Model(inference_framework=self.inference_framework)
                    
            elif os.path.isfile(self.model_path):
                # Single model file
                self.oww_model = Model(
                    wakeword_models=[self.model_path],
                    inference_framework=self.inference_framework
                )
            else:
                # Default: load all available pre-trained models
                self.logger.debug("Model path not found, using default pre-trained models")
                self.oww_model = Model(inference_framework=self.inference_framework)
            
            self.logger.info(f"OpenWakeWord model loaded with {self.inference_framework} framework from: {self.model_path}")
            
        except ImportError as e:
            raise WakeWordProviderUnavailableError(
                f"OpenWakeWord library not available. Install with: pip install openwakeword. Error: {e}"
            )
        except Exception as e:
            raise WakeWordConfigurationError(
                f"Failed to initialize OpenWakeWord model: {e}"
            )
    
    def _setup_audio(self):
        """Set up audio recording for wake word detection."""
        try:
            import pyaudio
            
            self.audio_format = pyaudio.paInt16
            self.logger.debug("Audio setup complete")
            
        except ImportError:
            raise WakeWordProviderUnavailableError(
                "PyAudio not available. Install with: pip install pyaudio"
            )
    
    def listen_for_wake_word(self, wake_word: str, timeout: Optional[int] = None) -> Tuple[bool, float]:
        """
        Listen for the wake word using OpenWakeWord.
        
        Args:
            wake_word: The wake word to listen for
            timeout: Optional timeout in seconds (None for indefinite listening)
            
        Returns:
            Tuple[bool, float]: (detected, confidence_score)
        """
        if not self.is_available():
            raise WakeWordProviderUnavailableError("OpenWakeWord provider is not available")
        
        self._initialize_openwakeword()
        self._setup_audio()
        
        try:
            import pyaudio
            
            # Create audio stream
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.logger.info(f"Listening for wake word: '{wake_word}'")
            start_time = time.time()
            
            try:
                while True:
                    # Check timeout
                    if timeout and time.time() - start_time > timeout:
                        self.logger.debug("Wake word detection timed out")
                        return False, 0.0
                    
                    # Read audio data
                    try:
                        audio_data = stream.read(self.chunk_size, exception_on_overflow=False)
                        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                        
                        # Get predictions from OpenWakeWord
                        prediction = self.oww_model.predict(audio_array)
                        
                        # Check for wake word detection
                        for model_name, score in prediction.items():
                            if score > self.threshold:
                                self.logger.info(f"Wake word detected! Model: {model_name}, Score: {score:.3f}")
                                return True, float(score)
                    
                    except Exception as e:
                        self.logger.warning(f"Error processing audio chunk: {e}")
                        continue
                    
            finally:
                # Clean up audio resources
                stream.stop_stream()
                stream.close()
                audio.terminate()
                
        except KeyboardInterrupt:
            self.logger.info("Wake word detection interrupted by user")
            return False, 0.0
        except Exception as e:
            self.logger.error(f"Error during wake word detection: {e}")
            raise WakeWordProviderUnavailableError(f"Wake word detection failed: {e}")
    
    def is_available(self) -> bool:
        """
        Check if OpenWakeWord provider is available.
        
        Returns:
            bool: True if OpenWakeWord is available and properly configured
        """
        try:
            # Check if OpenWakeWord is installed
            import openwakeword
            
            # Check if PyAudio is available
            import pyaudio
            
            # Check if model path exists
            if not os.path.exists(self.model_path):
                self.logger.warning(f"OpenWakeWord model path not found: {self.model_path}")
                return False
            
            # Check if there are any model files in the path
            if os.path.isdir(self.model_path):
                model_files = [f for f in os.listdir(self.model_path) if f.endswith('.onnx')]
                if not model_files:
                    self.logger.warning(f"No .onnx model files found in: {self.model_path}")
                    return False
            elif os.path.isfile(self.model_path):
                if not self.model_path.endswith('.onnx'):
                    self.logger.warning(f"Model file doesn't appear to be .onnx format: {self.model_path}")
                    return False
            
            return True
            
        except ImportError as e:
            self.logger.debug(f"OpenWakeWord not available: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"OpenWakeWord availability check failed: {e}")
            return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the OpenWakeWord engine.
        
        Returns:
            Dict[str, Any]: Engine information
        """
        info = {
            'name': 'OpenWakeWord',
            'description': 'Free offline wake word detection with custom word support',
            'supported_languages': ['English (custom words supported)'],
            'accuracy': 'Good (85-95% depending on model and training)',
            'latency': 'Low-Medium (100-300ms)',
            'resource_usage': 'Medium (requires model files, moderate CPU)',
            'licensing': 'Apache 2.0 (Free)',
            'offline': True,
            'custom_words': True,
            'model_path': self.model_path,
            'threshold': self.threshold,
            'inference_framework': self.inference_framework
        }
        
        try:
            import openwakeword
            info['version'] = getattr(openwakeword, '__version__', 'Unknown')
        except ImportError:
            info['version'] = 'Not installed'
        
        return info
    
    def validate_wake_word(self, wake_word: str) -> bool:
        """
        Validate wake word for OpenWakeWord.
        
        OpenWakeWord supports custom wake words but requires pre-trained models.
        
        Args:
            wake_word: The wake word to validate
            
        Returns:
            bool: True if valid (basic validation, actual model availability checked separately)
        """
        if not super().validate_wake_word(wake_word):
            return False
        
        # OpenWakeWord specific validation
        wake_word = wake_word.strip().lower()
        
        # Should be 1-4 words
        words = wake_word.split()
        if len(words) > 4:
            self.logger.warning(f"Wake word too long (>4 words): '{wake_word}'")
            return False
        
        # Each word should be reasonable length
        for word in words:
            if len(word) < 2 or len(word) > 15:
                self.logger.warning(f"Word length invalid: '{word}' in '{wake_word}'")
                return False
        
        return True
    
    def get_supported_wake_words(self) -> Optional[list]:
        """
        Get list of available pre-trained wake words.
        
        Returns:
            list: List of available wake word models, or empty list if none found
        """
        if not os.path.exists(self.model_path):
            return []
        
        wake_words = []
        
        try:
            if os.path.isdir(self.model_path):
                # Directory of models - extract names from .onnx files
                for filename in os.listdir(self.model_path):
                    if filename.endswith('.onnx'):
                        # Extract wake word name from filename
                        name = filename.replace('.onnx', '').replace('_', ' ').title()
                        wake_words.append(name)
            elif os.path.isfile(self.model_path) and self.model_path.endswith('.onnx'):
                # Single model file
                filename = os.path.basename(self.model_path)
                name = filename.replace('.onnx', '').replace('_', ' ').title()
                wake_words.append(name)
                
        except Exception as e:
            self.logger.warning(f"Error scanning wake word models: {e}")
        
        return wake_words
    
    def cleanup(self):
        """Clean up OpenWakeWord resources."""
        try:
            self._stop_listening = True
            if self._listening_thread and self._listening_thread.is_alive():
                self._listening_thread.join(timeout=1.0)
            
            if self.oww_model:
                # OpenWakeWord doesn't have explicit cleanup, but we can clear the reference
                self.oww_model = None
            
            self.logger.debug("OpenWakeWord provider cleaned up")
            
        except Exception as e:
            self.logger.warning(f"Error during OpenWakeWord cleanup: {e}")