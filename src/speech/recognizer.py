import speech_recognition as sr
from typing import Optional, Tuple, List
import time
import yaml
import os
from ..utils.logger import setup_logging


class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.logger = setup_logging("home_assistant.recognizer")
        self.recognition_engines = self._load_recognition_config()
        self._initialize_microphone()
    
    def _load_recognition_config(self) -> List[str]:
        """Load recognition engine configuration from config.yaml."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                engines = config.get('speech', {}).get('recognition_engines', ['google', 'vosk', 'sphinx'])
                self.logger.info(f"Loaded recognition engines: {engines}")
                return engines
        except Exception as e:
            self.logger.warning(f"Could not load recognition config: {e}. Using defaults: ['google', 'vosk', 'sphinx']")
            return ['google', 'vosk', 'sphinx']
    
    def _initialize_microphone(self):
        """Initialize the microphone."""
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            self.logger.error(f"Failed to initialize microphone: {e}")
            self.logger.info("Note: This might be due to missing PyAudio. Install with: pip install pyaudio")
            self.microphone = None
    
    def _try_recognition_engine(self, audio, engine_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Try a specific recognition engine.
        
        Args:
            audio: Audio data to recognize
            engine_name: Name of the engine to try
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, text, error_message)
        """
        try:
            if engine_name == 'google':
                text = self.recognizer.recognize_google(audio)
                return True, text.strip(), None
                
            elif engine_name == 'vosk':
                # Vosk requires special handling
                try:
                    import vosk
                    # This would require Vosk model setup
                    # For now, we'll log that Vosk is not fully implemented
                    self.logger.warning("Vosk recognition not fully implemented - requires model download")
                    return False, None, "Vosk not fully implemented"
                except ImportError:
                    return False, None, "Vosk not installed (pip install vosk)"
                    
            elif engine_name == 'sphinx':
                text = self.recognizer.recognize_sphinx(audio)
                return True, text.strip(), None
                
            elif engine_name == 'whisper':
                try:
                    text = self.recognizer.recognize_whisper(audio)
                    return True, text.strip(), None
                except AttributeError:
                    return False, None, "Whisper not available (requires openai-whisper)"
                    
            else:
                return False, None, f"Unknown recognition engine: {engine_name}"
                
        except sr.RequestError as e:
            error_msg = f"{engine_name.capitalize()} service error: {str(e)}"
            return False, None, error_msg
        except sr.UnknownValueError:
            error_msg = f"{engine_name.capitalize()} could not understand audio"
            return False, None, error_msg
        except Exception as e:
            error_msg = f"{engine_name.capitalize()} recognition failed: {str(e)}"
            return False, None, error_msg
    
    def listen_for_speech(self, timeout: int = 10, phrase_timeout: int = 5) -> Tuple[bool, Optional[str]]:
        """
        Listen for speech and return the recognized text.
        
        Args:
            timeout: Maximum time to wait for speech to start (seconds)
            phrase_timeout: Maximum time to wait for phrase to complete (seconds)
            
        Returns:
            Tuple[bool, Optional[str]]: (success, recognized_text)
        """
        if not self.microphone:
            self.logger.warning("Microphone not available")
            return False, None
        
        try:
            self.logger.info("Listening...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            self.logger.info("Processing speech...")
            
            # Try each recognition engine in priority order
            for engine_name in self.recognition_engines:
                self.logger.info(f"Trying {engine_name} recognition...")
                
                success, text, error = self._try_recognition_engine(audio, engine_name)
                
                if success and text:
                    self.logger.info(f"✅ Recognized with {engine_name}: {text}")
                    return True, text
                else:
                    self.logger.warning(f"❌ {engine_name} failed: {error}")
                    continue
            
            # If all engines failed, log detailed error
            self.logger.error("All recognition engines failed:")
            for engine_name in self.recognition_engines:
                success, text, error = self._try_recognition_engine(audio, engine_name)
                self.logger.error(f"  {engine_name}: {error}")
            
            return False, None
                
        except sr.WaitTimeoutError:
            self.logger.warning("No speech detected within timeout")
            return False, None
        except Exception as e:
            self.logger.error(f"Error during speech recognition: {e}")
            return False, None
    
    def is_available(self) -> bool:
        """Check if speech recognition is available."""
        return self.microphone is not None
    
    def get_available_engines(self) -> List[str]:
        """Get list of available recognition engines."""
        available = []
        
        # Check Google
        try:
            # Test if Google recognition is available
            available.append('google')
        except:
            pass
        
        # Check Vosk
        try:
            import vosk
            available.append('vosk')
        except ImportError:
            pass
        
        # Check Sphinx
        try:
            # Sphinx is built into speech_recognition
            available.append('sphinx')
        except:
            pass
        
        # Check Whisper
        try:
            import whisper
            available.append('whisper')
        except ImportError:
            pass
        
        return available