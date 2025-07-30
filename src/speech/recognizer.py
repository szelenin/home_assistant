import speech_recognition as sr
from typing import Optional, Tuple
import time
from ..utils.logger import setup_logging


class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.logger = setup_logging("home_assistant.recognizer")
        self._initialize_microphone()
    
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
            try:
                # Try Google Speech Recognition first (requires internet)
                text = self.recognizer.recognize_google(audio)
                self.logger.info(f"Recognized: {text}")
                return True, text.strip()
            except sr.RequestError:
                # Fall back to offline recognition if available
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    self.logger.info(f"Recognized (offline): {text}")
                    return True, text.strip()
                except sr.RequestError:
                    self.logger.error("Speech recognition service unavailable")
                    return False, None
            except sr.UnknownValueError:
                self.logger.warning("Could not understand audio")
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