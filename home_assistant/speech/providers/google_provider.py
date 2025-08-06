import speech_recognition as sr
from typing import Dict, Any, Optional, Tuple
from ..base_speech_provider import BaseSpeechProvider, SpeechConfigurationError, SpeechProviderUnavailableError


class GoogleSpeechProvider(BaseSpeechProvider):
    """Speech recognition provider using Google Speech Recognition."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Google speech provider."""
        self.recognizer = None
        self.microphone = None
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate Google-specific configuration."""
        # Set defaults if not provided
        if 'language' not in self.config:
            self.config['language'] = 'en-US'
        
        if 'show_all' not in self.config:
            self.config['show_all'] = False
        
        # Validate language code format
        language = self.config['language']
        if not isinstance(language, str) or len(language) < 2:
            raise SpeechConfigurationError(f"Invalid language code: {language}")
        
        # Basic validation for language code format (e.g., 'en-US', 'fr-FR')
        if '-' in language and len(language.split('-')) != 2:
            raise SpeechConfigurationError(f"Language code should be in format 'xx-XX': {language}")
    
    def _initialize_provider(self) -> None:
        """Initialize the Google speech recognition provider."""
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            self.logger.info("Google Speech Recognition initialized")
            
        except Exception as e:
            raise SpeechProviderUnavailableError(f"Failed to initialize Google Speech: {e}")
    
    def listen_for_speech(self, timeout: int = 10, phrase_timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """Listen for speech using Google Speech Recognition."""
        self._validate_timeout_params(timeout, phrase_timeout)
        self._log_speech_attempt(timeout, phrase_timeout)
        
        if not self.is_available():
            self.logger.error("Google provider not available")
            return False, None
        
        try:
            # Capture audio
            with self.microphone as source:
                self.logger.debug("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_timeout)
            
            # Recognize speech using Google
            self.logger.debug(f"Sending audio to Google Speech API (language: {self.config['language']})")
            
            text = self.recognizer.recognize_google(
                audio, 
                language=self.config['language'],
                show_all=self.config['show_all']
            )
            
            if isinstance(text, str) and text.strip():
                text = text.strip()
                self._log_speech_result(True, text)
                return True, text
            elif isinstance(text, dict) and self.config['show_all']:
                # When show_all=True, Google returns a dict with alternatives
                alternatives = text.get('alternative', [])
                if alternatives and len(alternatives) > 0:
                    best_text = alternatives[0].get('transcript', '').strip()
                    confidence = alternatives[0].get('confidence', 0.0)
                    
                    if best_text:
                        self._log_speech_result(True, best_text)
                        self.logger.debug(f"Google confidence: {confidence:.2f}")
                        return True, best_text
            
            self.logger.warning("Google returned empty or invalid result")
            self._log_speech_result(False, None)
            return False, None
            
        except sr.UnknownValueError:
            self.logger.warning("Google could not understand the audio")
            self._log_speech_result(False, None)
            return False, None
        except sr.RequestError as e:
            self.logger.error(f"Google Speech API request failed: {e}")
            self._log_speech_result(False, None)
            return False, None
        except sr.WaitTimeoutError:
            self.logger.warning("Speech recognition timed out")
            self._log_speech_result(False, None)
            return False, None
        except Exception as e:
            self.logger.error(f"Google speech recognition failed: {e}")
            self._log_speech_result(False, None)
            return False, None
    
    def is_available(self) -> bool:
        """Check if Google provider is available."""
        return (self.recognizer is not None and self.microphone is not None)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the Google engine."""
        info = {
            'name': 'Google Speech Recognition',
            'type': 'online',
            'language_support': 'excellent (100+ languages)',
            'accuracy': 'excellent (95%+)',
            'latency': 'moderate (300-800ms)',
            'privacy': 'limited (audio sent to Google)',
            'resource_usage': 'minimal (cloud-based)',
            'free_tier': '60 minutes/month'
        }
        
        if self.is_available():
            info.update({
                'language': self.config['language'],
                'show_all': self.config['show_all'],
                'status': 'ready'
            })
        else:
            info['status'] = 'unavailable'
        
        return info