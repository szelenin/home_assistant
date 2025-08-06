import json
import os
import speech_recognition as sr
from typing import Dict, Any, Optional, Tuple
from ..base_speech_provider import BaseSpeechProvider, SpeechConfigurationError, SpeechProviderUnavailableError


class VoskSpeechProvider(BaseSpeechProvider):
    """Speech recognition provider using Vosk offline engine."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Vosk speech provider."""
        self.vosk_model = None
        self.vosk_recognizer = None
        self.microphone = None
        self.sr_recognizer = None
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate Vosk-specific configuration."""
        # Set defaults if not provided
        if 'model_path' not in self.config:
            self.config['model_path'] = './vosk-model-en-us-0.22'
        
        if 'confidence_threshold' not in self.config:
            self.config['confidence_threshold'] = 0.8
        
        if 'sample_rate' not in self.config:
            self.config['sample_rate'] = 16000
        
        # Validate confidence threshold
        if not isinstance(self.config['confidence_threshold'], (int, float)):
            raise SpeechConfigurationError("Confidence threshold must be a number")
        
        if not 0.0 <= self.config['confidence_threshold'] <= 1.0:
            raise SpeechConfigurationError("Confidence threshold must be between 0.0 and 1.0")
        
        # Validate sample rate
        if not isinstance(self.config['sample_rate'], int) or self.config['sample_rate'] <= 0:
            raise SpeechConfigurationError("Sample rate must be a positive integer")
    
    def _initialize_provider(self) -> None:
        """Initialize the Vosk speech recognition provider."""
        # Check if Vosk is available
        try:
            import vosk
        except ImportError:
            raise SpeechProviderUnavailableError(
                "Vosk not installed. Install with: pip install vosk"
            )
        
        # Check if model path exists
        model_path = self.config['model_path']
        if not os.path.exists(model_path):
            raise SpeechProviderUnavailableError(
                f"Vosk model not found at: {model_path}. "
                f"Download a model from https://alphacephei.com/vosk/models"
            )
        
        # Validate model directory structure
        if not os.path.isdir(model_path):
            raise SpeechProviderUnavailableError(
                f"Vosk model path must be a directory: {model_path}"
            )
        
        # Check for required model files
        # Different Vosk models have different graph files: HCLG.fst (large) or HCLr.fst+Gr.fst (small)
        required_basic_files = ['am/final.mdl', 'conf/mfcc.conf']
        for file_path in required_basic_files:
            full_path = os.path.join(model_path, file_path)
            if not os.path.exists(full_path):
                raise SpeechProviderUnavailableError(
                    f"Invalid Vosk model: missing {file_path} in {model_path}"
                )
        
        # Check for either HCLG.fst (large models) or HCLr.fst+Gr.fst (small models)
        hclg_path = os.path.join(model_path, 'graph/HCLG.fst')
        hclr_path = os.path.join(model_path, 'graph/HCLr.fst')
        gr_path = os.path.join(model_path, 'graph/Gr.fst')
        
        if not os.path.exists(hclg_path) and not (os.path.exists(hclr_path) and os.path.exists(gr_path)):
            raise SpeechProviderUnavailableError(
                f"Invalid Vosk model: missing graph files in {model_path}. "
                f"Expected either 'graph/HCLG.fst' or 'graph/HCLr.fst' + 'graph/Gr.fst'"
            )
        
        # Initialize Vosk model
        try:
            # Disable Vosk logging (it's very verbose)
            vosk.SetLogLevel(-1)
            
            self.vosk_model = vosk.Model(model_path)
            self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, self.config['sample_rate'])
            self.vosk_recognizer.SetWords(True)  # Enable word-level timestamps
            
            self.logger.info(f"Vosk model loaded from: {model_path}")
            
        except Exception as e:
            raise SpeechProviderUnavailableError(f"Failed to load Vosk model: {e}")
        
        # Initialize microphone
        try:
            self.sr_recognizer = sr.Recognizer()
            self.microphone = sr.Microphone(sample_rate=self.config['sample_rate'])
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Adjusting for ambient noise...")
                self.sr_recognizer.adjust_for_ambient_noise(source, duration=1)
                
        except Exception as e:
            raise SpeechProviderUnavailableError(f"Failed to initialize microphone: {e}")
    
    def listen_for_speech(self, timeout: int = 10, phrase_timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """Listen for speech using Vosk recognition."""
        self._validate_timeout_params(timeout, phrase_timeout)
        self._log_speech_attempt(timeout, phrase_timeout)
        
        if not self.is_available():
            self.logger.error("Vosk provider not available")
            return False, None
        
        try:
            # Capture audio
            with self.microphone as source:
                self.logger.debug("Listening for speech...")
                audio = self.sr_recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_timeout)
            
            # Convert audio to raw data for Vosk
            raw_data = audio.get_raw_data(convert_rate=self.config['sample_rate'], convert_width=2)
            
            # Process with Vosk
            if self.vosk_recognizer.AcceptWaveform(raw_data):
                result = json.loads(self.vosk_recognizer.Result())
            else:
                result = json.loads(self.vosk_recognizer.FinalResult())
            
            # Extract text and confidence
            text = result.get('text', '').strip()
            confidence = result.get('confidence', 0.0)
            
            if text and confidence >= self.config['confidence_threshold']:
                self._log_speech_result(True, text)
                self.logger.debug(f"Vosk confidence: {confidence:.2f}")
                return True, text
            else:
                if text:
                    self.logger.warning(f"Low confidence: {confidence:.2f} < {self.config['confidence_threshold']}")
                else:
                    self.logger.warning("No text recognized by Vosk")
                self._log_speech_result(False, None)
                return False, None
                
        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timed out")
            self._log_speech_result(False, None)
            return False, None
        except Exception as e:
            self.logger.error(f"Vosk speech recognition failed: {e}")
            self._log_speech_result(False, None)
            return False, None
    
    def is_available(self) -> bool:
        """Check if Vosk provider is available."""
        return (self.vosk_model is not None and 
                self.vosk_recognizer is not None and 
                self.microphone is not None)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the Vosk engine."""
        info = {
            'name': 'Vosk',
            'type': 'offline',
            'language_support': 'model-dependent',
            'accuracy': 'good (85-92%)',
            'latency': 'low (200-400ms)',
            'privacy': 'excellent (fully offline)',
            'resource_usage': 'moderate'
        }
        
        if self.is_available():
            info.update({
                'model_path': self.config['model_path'],
                'confidence_threshold': self.config['confidence_threshold'],
                'sample_rate': self.config['sample_rate'],
                'status': 'ready'
            })
        else:
            info['status'] = 'unavailable'
        
        return info