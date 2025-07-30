import pyttsx3
import sounddevice as sd
from typing import Optional


class TextToSpeech:
    def __init__(self):
        self.engine = None
        self._check_audio_devices()
        self._initialize_engine()
    
    def _check_audio_devices(self):
        """Check and display available audio devices."""
        try:
            devices = sd.query_devices()
            print(f"🎵 Found {len(devices)} audio devices:")
            
            output_devices = []
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    output_devices.append((i, device))
                    print(f"  🔊 Output {i}: {device['name']} (channels: {device['max_output_channels']})")
            
            # Try to set default device like in test_tts_detailed.py
            try:
                sd.default.device = None  # Use system default
                print("✅ Audio device configuration successful")
            except Exception as e:
                print(f"⚠️ Audio device configuration warning: {e}")
                
        except Exception as e:
            print(f"❌ Audio device check failed: {e}")
    
    def _initialize_engine(self):
        """Initialize the TTS engine."""
        try:
            self.engine = pyttsx3.init()
            self._configure_voice()
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def _configure_voice(self):
        """Configure voice properties."""
        if not self.engine:
            return
        
        try:
            # Set speech rate (words per minute) - matching working version
            self.engine.setProperty('rate', 150)
            
            # Set volume to maximum for testing
            self.engine.setProperty('volume', 1.0)
            
            # Try to use a more natural voice if available
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voice if available, otherwise use first available
                for voice in voices:
                    if voice.gender and 'female' in voice.gender.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    self.engine.setProperty('voice', voices[0].id)
                    
            # Print current settings for debugging
            print(f"TTS configured - Rate: {self.engine.getProperty('rate')}, Volume: {self.engine.getProperty('volume')}")
            
        except Exception as e:
            print(f"Failed to configure voice: {e}")
    
    def speak(self, text: str) -> bool:
        """
        Speak the given text.
        
        Args:
            text: The text to speak
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.engine:
            print(f"TTS not available, would say: {text}")
            return False
        
        try:
            # Preprocess text like in working version
            text = text.replace(",", "")
            
            print(f"🔊 Speaking: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
            # Add engine.stop() like in working version
            self.engine.stop()
            print("✅ TTS completed successfully")
            return True
        except Exception as e:
            print(f"Failed to speak text: {e}")
            return False