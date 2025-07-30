import pyttsx3
import sounddevice as sd
import yaml
import os
from typing import Optional
from ..utils.logger import setup_logging


class TextToSpeech:
    def __init__(self, voice_id=None, rate=None, volume=None):
        self.engine = None
        self.logger = setup_logging("home_assistant.tts")
        
        # Load configuration from config.yaml
        self.config = self._load_config()
        
        # Use provided parameters or fall back to config values
        self.voice_id = voice_id or self.config.get('tts', {}).get('voice_id', "com.apple.voice.compact.en-US.Samantha")
        self.rate = rate or self.config.get('tts', {}).get('rate', 150)
        self.volume = volume or self.config.get('tts', {}).get('volume', 1.0)
        
        # Debug output
        self.logger.debug(f"TTS Config loaded - Voice ID: {self.voice_id}, Rate: {self.rate}, Volume: {self.volume}")
        
        self._check_audio_devices()
        self._initialize_engine()
    
    def _load_config(self):
        """Load configuration from config.yaml file."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.warning(f"Could not load config.yaml: {e}. Using default TTS settings")
            return {}
    
    def _check_audio_devices(self):
        """Check and display available audio devices."""
        try:
            devices = sd.query_devices()
            self.logger.info(f"Found {len(devices)} audio devices")
            
            output_devices = []
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    output_devices.append((i, device))
                    self.logger.debug(f"Output {i}: {device['name']} (channels: {device['max_output_channels']})")
            
            # Try to set default device like in test_tts_detailed.py
            try:
                sd.default.device = None  # Use system default
                self.logger.info("Audio device configuration successful")
            except Exception as e:
                self.logger.warning(f"Audio device configuration warning: {e}")
                
        except Exception as e:
            self.logger.error(f"Audio device check failed: {e}")
    
    def _initialize_engine(self):
        """Initialize the TTS engine."""
        try:
            self.engine = pyttsx3.init()
            self._configure_voice()
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def _configure_voice(self):
        """Configure voice properties."""
        if not self.engine:
            return
        
        try:
            # Set rate and volume BEFORE voice selection
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Get all available voices first
            voices = self.engine.getProperty('voices')
            if voices:
                self.logger.info(f"Found {len(voices)} available voices")
                for i, voice in enumerate(voices):
                    gender = voice.gender if hasattr(voice, 'gender') else 'Unknown'
                    languages = voice.languages if hasattr(voice, 'languages') else []
                    self.logger.debug(f"Voice {i}: {voice.name} (ID: {voice.id}, Gender: {gender}, Languages: {languages})")
                
                # Use specified voice or default selection
                if self.voice_id:
                    # Try to find the specified voice
                    voice_found = False
                    for voice in voices:
                        if voice.id == self.voice_id:
                            self.engine.setProperty('voice', voice.id)
                            self.logger.info(f"Using specified voice: {voice.name}")
                            voice_found = True
                            break
                    
                    if not voice_found:
                        self.logger.warning(f"Specified voice ID '{self.voice_id}' not found, using default")
                        self._select_default_voice(voices)
                else:
                    self._select_default_voice(voices)
            
            # Set rate and volume AGAIN after voice selection
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Double-check and force the rate again
            current_rate = self.engine.getProperty('rate')
            if current_rate != self.rate:
                self.logger.warning(f"Rate mismatch: expected {self.rate}, got {current_rate}, forcing...")
                self.engine.setProperty('rate', self.rate)
                # Try one more time
                if self.engine.getProperty('rate') != self.rate:
                    self.logger.warning("Rate still not set correctly. This is a known pyttsx3 limitation on macOS.")
                    
            # Print current settings for debugging
            final_rate = self.engine.getProperty('rate')
            final_volume = self.engine.getProperty('volume')
            self.logger.info(f"TTS configured - Rate: {final_rate}, Volume: {final_volume}")
            
        except Exception as e:
            self.logger.error(f"Failed to configure voice: {e}")
    
    def _select_default_voice(self, voices):
        """Select default voice based on preferences."""
        # Prefer female voice if available, otherwise use first available
        for voice in voices:
            if hasattr(voice, 'gender') and voice.gender and 'female' in voice.gender.lower():
                self.engine.setProperty('voice', voice.id)
                self.logger.info(f"Using female voice: {voice.name}")
                return
        
        # If no female voice found, use the first available
        if voices:
            self.engine.setProperty('voice', voices[0].id)
            self.logger.info(f"Using default voice: {voices[0].name}")
    
    def list_voices(self):
        """List all available voices with details."""
        if not self.engine:
            self.logger.error("TTS engine not available")
            return
        
        voices = self.engine.getProperty('voices')
        if voices:
            self.logger.info(f"Available Voices ({len(voices)} total)")
            for i, voice in enumerate(voices):
                gender = voice.gender if hasattr(voice, 'gender') else 'Unknown'
                languages = voice.languages if hasattr(voice, 'languages') else []
                self.logger.info(f"Voice {i+1}: {voice.name} (ID: {voice.id}, Gender: {gender}, Languages: {languages})")
        else:
            self.logger.error("No voices found")
    
    def set_voice(self, voice_id):
        """Set a specific voice by ID."""
        if not self.engine:
            self.logger.error("TTS engine not available")
            return False
        
        try:
            self.engine.setProperty('voice', voice_id)
            self.logger.info(f"Voice set to: {voice_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set voice: {e}")
            return False
    
    def set_rate(self, rate):
        """Set speech rate (words per minute)."""
        if not self.engine:
            self.logger.error("TTS engine not available")
            return False
        
        try:
            self.engine.setProperty('rate', rate)
            self.logger.info(f"Speech rate set to: {rate} WPM")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set rate: {e}")
            return False
    
    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)."""
        if not self.engine:
            self.logger.error("TTS engine not available")
            return False
        
        try:
            self.engine.setProperty('volume', volume)
            self.logger.info(f"Volume set to: {volume}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set volume: {e}")
            return False
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text.
        
        Args:
            text: The text to speak
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.engine:
            self.logger.warning(f"TTS not available, would say: {text}")
            return False
        
        try:
            # Preprocess text like in working version
            text = text.replace(",", "")
            
            self.logger.info(f"Speaking: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
            # Add engine.stop() like in working version
            self.engine.stop()
            self.logger.info("TTS completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to speak text: {e}")
            return False