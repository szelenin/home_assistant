import tempfile
import os
import wave
import speech_recognition as sr
from typing import Dict, Any, Optional, Tuple
from ..base_speech_provider import BaseSpeechProvider, SpeechConfigurationError, SpeechProviderUnavailableError


class WhisperSpeechProvider(BaseSpeechProvider):
    """Speech recognition provider using OpenAI Whisper."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Whisper speech provider."""
        self.whisper_model = None
        self.recognizer = None
        self.microphone = None
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate Whisper-specific configuration."""
        # Set defaults if not provided
        if 'model' not in self.config:
            self.config['model'] = 'base'
        
        if 'language' not in self.config:
            self.config['language'] = None  # Auto-detect
        
        if 'device' not in self.config:
            self.config['device'] = 'cpu'
        
        if 'temperature' not in self.config:
            self.config['temperature'] = 0.0
        
        # Validate model name
        valid_models = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
        if self.config['model'] not in valid_models:
            raise SpeechConfigurationError(
                f"Invalid Whisper model '{self.config['model']}'. "
                f"Valid options: {valid_models}"
            )
        
        # Validate device
        valid_devices = ['cpu', 'cuda']
        if self.config['device'] not in valid_devices:
            raise SpeechConfigurationError(
                f"Invalid device '{self.config['device']}'. Valid options: {valid_devices}"
            )
        
        # Validate temperature
        if not isinstance(self.config['temperature'], (int, float)):
            raise SpeechConfigurationError("Temperature must be a number")
        
        if not 0.0 <= self.config['temperature'] <= 1.0:
            raise SpeechConfigurationError("Temperature must be between 0.0 and 1.0")
        
        # Validate language code if provided
        if self.config['language'] is not None:
            if not isinstance(self.config['language'], str) or len(self.config['language']) < 2:
                raise SpeechConfigurationError(f"Invalid language code: {self.config['language']}")
    
    def _initialize_provider(self) -> None:
        """Initialize the Whisper speech recognition provider."""
        # Check if Whisper is available
        try:
            import whisper
        except ImportError:
            raise SpeechProviderUnavailableError(
                "OpenAI Whisper not installed. Install with: pip install openai-whisper"
            )
        
        # Load Whisper model
        try:
            self.logger.info(f"Loading Whisper model '{self.config['model']}' on {self.config['device']}...")
            self.whisper_model = whisper.load_model(
                self.config['model'], 
                device=self.config['device']
            )
            self.logger.info(f"Whisper model '{self.config['model']}' loaded successfully")
            
        except Exception as e:
            raise SpeechProviderUnavailableError(f"Failed to load Whisper model: {e}")
        
        # Initialize microphone
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
        except Exception as e:
            raise SpeechProviderUnavailableError(f"Failed to initialize microphone: {e}")
    
    def listen_for_speech(self, timeout: int = 10, phrase_timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """Listen for speech using Whisper recognition."""
        self._validate_timeout_params(timeout, phrase_timeout)
        self._log_speech_attempt(timeout, phrase_timeout)
        
        if not self.is_available():
            self.logger.error("Whisper provider not available")
            return False, None
        
        try:
            # Capture audio
            with self.microphone as source:
                self.logger.debug("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_timeout)
            
            # Convert audio to WAV file for Whisper
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
                
                # Write audio data to WAV file
                with wave.open(temp_audio_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(audio.sample_width)
                    wav_file.setframerate(audio.sample_rate)
                    wav_file.writeframes(audio.frame_data)
            
            try:
                # Process with Whisper
                self.logger.debug("Processing audio with Whisper...")
                
                transcribe_options = {
                    'temperature': self.config['temperature'],
                    'fp16': self.config['device'] == 'cuda'  # Use FP16 on GPU
                }
                
                if self.config['language']:
                    transcribe_options['language'] = self.config['language']
                
                result = self.whisper_model.transcribe(temp_audio_path, **transcribe_options)
                
                text = result.get('text', '').strip()
                
                if text:
                    self._log_speech_result(True, text)
                    # Log additional Whisper info if available
                    if 'language' in result:
                        self.logger.debug(f"Detected language: {result['language']}")
                    return True, text
                else:
                    self.logger.warning("Whisper returned empty text")
                    self._log_speech_result(False, None)
                    return False, None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_audio_path)
                except OSError:
                    pass
                
        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timed out")
            self._log_speech_result(False, None)
            return False, None
        except Exception as e:
            self.logger.error(f"Whisper speech recognition failed: {e}")
            self._log_speech_result(False, None)
            return False, None
    
    def is_available(self) -> bool:
        """Check if Whisper provider is available."""
        return (self.whisper_model is not None and 
                self.recognizer is not None and 
                self.microphone is not None)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the Whisper engine."""
        info = {
            'name': 'OpenAI Whisper',
            'type': 'offline',
            'language_support': 'excellent (99+ languages with auto-detection)',
            'accuracy': 'excellent (90-95%)',
            'latency': 'high (2-10+ seconds)',
            'privacy': 'excellent (fully offline)',
            'resource_usage': 'high (CPU/GPU intensive)',
            'best_for': 'batch processing, high accuracy needs'
        }
        
        if self.is_available():
            info.update({
                'model': self.config['model'],
                'language': self.config['language'] or 'auto-detect',
                'device': self.config['device'],
                'temperature': self.config['temperature'],
                'status': 'ready'
            })
        else:
            info['status'] = 'unavailable'
        
        return info