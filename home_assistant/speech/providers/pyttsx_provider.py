import pyttsx3
import sounddevice as sd
import platform
import time
import threading
from typing import Dict, Any, List, Optional
from ..base_tts_provider import BaseTTSProvider, TTSConfigurationError, TTSProviderUnavailableError


class PyttsxTTSProvider(BaseTTSProvider):
    """TTS provider using pyttsx3 with eSpeak-NG backend."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the pyttsx3 TTS provider."""
        self.engine = None
        self.platform = platform.system().lower()
        self._engine_usage_count = 0  # Track engine usage
        self._max_usage_before_reinit = 1  # Reinitialize after every use on macOS (engine degrades quickly)

        # Threading support for non-blocking TTS
        self._tts_thread = None
        self._speaking = False
        self._stop_requested = False
        self._tts_lock = threading.Lock()

        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate pyttsx3-specific configuration."""
        # Set defaults if not provided
        if 'voice_id' not in self.config:
            self.config['voice_id'] = "com.apple.voice.compact.en-US.Samantha"
        if 'rate' not in self.config:
            self.config['rate'] = 150
        if 'volume' not in self.config:
            self.config['volume'] = 0.5
        
        # Validate rate
        if not isinstance(self.config['rate'], (int, float)) or self.config['rate'] < 50 or self.config['rate'] > 400:
            raise TTSConfigurationError("Rate must be between 50 and 400 WPM")
        
        # Validate volume
        if not isinstance(self.config['volume'], (int, float)) or self.config['volume'] < 0.0 or self.config['volume'] > 1.0:
            raise TTSConfigurationError("Volume must be between 0.0 and 1.0")
    
    def _initialize_provider(self) -> None:
        """Initialize the pyttsx3 engine."""
        try:
            # Properly cleanup any existing engine first
            if self.engine is not None:
                try:
                    self.engine.stop()
                    if hasattr(self.engine, 'endLoop'):
                        self.engine.endLoop()
                except Exception:
                    pass  # Ignore cleanup errors
                self.engine = None

            # Create fresh engine instance
            self.engine = pyttsx3.init()
            self._check_audio_devices()
            self._configure_voice()

            # Reset usage counter after successful initialization
            self._engine_usage_count = 0

        except Exception as e:
            raise TTSProviderUnavailableError(f"Failed to initialize pyttsx3: {e}")
    
    def _check_audio_devices(self):
        """Check and configure audio devices."""
        try:
            devices = sd.query_devices()
            self.logger.info(f"Found {len(devices)} audio devices")
            
            output_devices = []
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    output_devices.append((i, device))
                    self.logger.debug(f"Output {i}: {device['name']} (channels: {device['max_output_channels']})")
            
            # Configure default device
            try:
                sd.default.device = None  # Use system default
                self.logger.info("Audio device configuration successful")
            except Exception as e:
                self.logger.warning(f"Audio device configuration warning: {e}")
                
        except Exception as e:
            self.logger.error(f"Audio device check failed: {e}")
        
        # Ensure system volume is adequate for TTS (macOS only)
        if self.platform == 'darwin':
            self._ensure_system_volume()
    
    def _ensure_system_volume(self):
        """Ensure system volume is adequate for TTS (macOS only)."""
        try:
            import subprocess
            result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], 
                                  capture_output=True, text=True)
            current_volume = int(result.stdout.strip())
            
            if current_volume < 50:
                subprocess.run(['osascript', '-e', 'set volume output volume 75'], 
                              capture_output=True)
                self.logger.info(f"System volume was {current_volume}%, increased to 75% for TTS")
            
        except Exception as e:
            self.logger.warning(f"Could not adjust system volume: {e}")
    
    def _configure_voice(self):
        """Configure voice properties."""
        if not self.engine:
            return
        
        try:
            # Get all available voices
            voices = self.engine.getProperty('voices')
            if voices:
                self.logger.info(f"Found {len(voices)} available voices")
                
                # Use specified voice or default selection
                if self.config.get('voice_id'):
                    voice_found = False
                    for voice in voices:
                        if voice.id == self.config['voice_id']:
                            self.engine.setProperty('voice', voice.id)
                            self.logger.info(f"Using specified voice: {voice.name}")
                            voice_found = True
                            break
                    
                    if not voice_found:
                        self.logger.warning(f"Specified voice ID '{self.config['voice_id']}' not found, using default")
                        self._select_default_voice(voices)
                else:
                    self._select_default_voice(voices)
            
            # Set rate and volume
            self.engine.setProperty('rate', self.config['rate'])
            self.engine.setProperty('volume', self.config['volume'])
            
            # Verify settings
            final_rate = self.engine.getProperty('rate')
            final_volume = self.engine.getProperty('volume')
            self.logger.info(f"TTS configured - Rate: {final_rate}, Volume: {final_volume}")
            
        except Exception as e:
            self.logger.error(f"Failed to configure voice: {e}")
    
    def _select_default_voice(self, voices):
        """Select default voice based on preferences."""
        # Prefer female voice if available
        for voice in voices:
            if hasattr(voice, 'gender') and voice.gender and 'female' in voice.gender.lower():
                self.engine.setProperty('voice', voice.id)
                self.logger.info(f"Using female voice: {voice.name}")
                return
        
        # Use first available voice
        if voices:
            self.engine.setProperty('voice', voices[0].id)
            self.logger.info(f"Using default voice: {voices[0].name}")
    
    def is_available(self) -> bool:
        """Check if pyttsx3 is available."""
        try:
            test_engine = pyttsx3.init()
            test_engine.stop()
            return True
        except Exception:
            return False
    
    def speak(self, text: str) -> bool:
        """Speak the given text using pyttsx3."""
        if not self._validate_text_input(text):
            return False
        
        if not self.engine:
            self.logger.warning(f"TTS not available, would say: {text}")
            return False
        
        try:
            self._log_speech_attempt(text)
            
            # Smart engine management - initialize if needed or after usage threshold
            needs_reinit = False
            if not self.engine:
                needs_reinit = True
                self.logger.debug("Initializing engine (first time)")
            elif self.platform == 'darwin' and self._engine_usage_count >= self._max_usage_before_reinit:
                needs_reinit = True
                self.logger.debug(f"Reinitializing engine after {self._engine_usage_count} uses on macOS")
                self._engine_usage_count = 0

            if needs_reinit:
                self._initialize_provider()
                if not self.engine:
                    self.logger.error("Failed to initialize TTS engine")
                    return False

                self._configure_voice()

                # macOS-specific settling time
                if self.platform == 'darwin':
                    time.sleep(0.1)

                # Apply settings with retries for macOS consistency
                for attempt in range(3):
                    self.engine.setProperty('rate', self.config['rate'])
                    self.engine.setProperty('volume', self.config['volume'])

                    actual_rate = self.engine.getProperty('rate')
                    actual_volume = self.engine.getProperty('volume')

                    if abs(actual_rate - self.config['rate']) < 1 and abs(actual_volume - self.config['volume']) < 0.1:
                        break

                    if attempt < 2:
                        time.sleep(0.05)
            
            # Verify final settings
            if self.engine:
                actual_rate = self.engine.getProperty('rate')
                actual_volume = self.engine.getProperty('volume')
                self.logger.debug(f"Final settings: Rate={actual_rate}, Volume={actual_volume}")
            
            # Speak the text
            start_time = time.time()
            self.engine.say(text)
            self.engine.runAndWait()
            duration = time.time() - start_time

            # Check for TTS degradation (too fast = no audio output)
            if duration < 0.1 and len(text) > 10:  # Short duration for long text = problem
                self.logger.warning(f"TTS completed too quickly ({duration:.2f}s for {len(text)} chars) - forcing reinitialization")
                self._engine_usage_count = self._max_usage_before_reinit  # Force reinit on next call
            else:
                # Track usage for smart reinitialization
                self._engine_usage_count += 1

            self.logger.info("TTS completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to speak text: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            if not voices:
                return []
            
            voice_list = []
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'language': getattr(voice, 'languages', ['unknown'])[0] if hasattr(voice, 'languages') else 'unknown',
                    'gender': getattr(voice, 'gender', 'unknown')
                }
                voice_list.append(voice_info)
            
            return voice_list
        except Exception as e:
            self.logger.error(f"Failed to get available voices: {e}")
            return []
    
    def set_voice(self, voice_id: str) -> bool:
        """Set a specific voice by ID."""
        if not self.engine:
            return False
        
        try:
            self.engine.setProperty('voice', voice_id)
            self.config['voice_id'] = voice_id
            self.logger.info(f"Voice set to: {voice_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set voice: {e}")
            return False
    
    def set_rate(self, rate: int) -> bool:
        """Set speech rate."""
        if not self.engine:
            return False
        
        try:
            self.engine.setProperty('rate', rate)
            self.config['rate'] = rate
            self.logger.info(f"Speech rate set to: {rate} WPM")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set rate: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set volume level."""
        if not self.engine:
            return False

        try:
            self.engine.setProperty('volume', volume)
            self.config['volume'] = volume
            self.logger.info(f"Volume set to: {volume}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set volume: {e}")
            return False

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages for pyttsx.

        Returns languages based on available system voices.
        """
        languages = set()

        try:
            # Get all available voices
            voices = self.get_available_voices()

            # Extract unique language codes from voices
            for voice in voices:
                language = voice.get('language', '')
                if language:
                    # Extract base language code (e.g., 'en' from 'en-US')
                    base_lang = language.split('-')[0].split('_')[0].lower()
                    if base_lang:
                        languages.add(base_lang)
        except Exception as e:
            self.logger.warning(f"Failed to get supported languages: {e}")
            # Return default English if unable to get voices
            return ['en']

        # Convert to sorted list
        return sorted(list(languages))

    def _tts_worker(self, text: str) -> None:
        """Worker method for non-blocking TTS execution."""
        try:
            with self._tts_lock:
                if self._stop_requested:
                    return

                self._speaking = True

                # Smart engine management - same as regular speak method
                needs_reinit = False
                if not self.engine:
                    needs_reinit = True
                    self.logger.debug("Initializing engine (first time)")
                elif self.platform == 'darwin' and self._engine_usage_count >= self._max_usage_before_reinit:
                    needs_reinit = True
                    self.logger.debug(f"Reinitializing engine after {self._engine_usage_count} uses on macOS")
                    self._engine_usage_count = 0

                if needs_reinit:
                    self._initialize_provider()
                    if not self.engine:
                        self.logger.error("Failed to initialize TTS engine")
                        return

                    self._configure_voice()

                    # macOS-specific settling time
                    if self.platform == 'darwin':
                        time.sleep(0.1)

                    # Apply settings with retries for macOS consistency
                    for attempt in range(3):
                        self.engine.setProperty('rate', self.config['rate'])
                        self.engine.setProperty('volume', self.config['volume'])

                        actual_rate = self.engine.getProperty('rate')
                        actual_volume = self.engine.getProperty('volume')

                        if abs(actual_rate - self.config['rate']) < 1 and abs(actual_volume - self.config['volume']) < 0.1:
                            break

                        if attempt < 2:
                            time.sleep(0.05)

                # Check for stop request before speaking
                if self._stop_requested:
                    return

                # Speak the text
                start_time = time.time()
                self.engine.say(text)

                # Use simple runAndWait for macOS compatibility
                # Based on research: startLoop/endLoop can cause issues on macOS
                self.engine.runAndWait()

                duration = time.time() - start_time

                # Check for TTS degradation (too fast = no audio output)
                if duration < 0.1 and len(text) > 10:  # Short duration for long text = problem
                    self.logger.warning(f"Async TTS completed too quickly ({duration:.2f}s for {len(text)} chars) - forcing reinitialization")
                    self._engine_usage_count = self._max_usage_before_reinit  # Force reinit on next call
                else:
                    # Track usage for smart reinitialization
                    self._engine_usage_count += 1

        except Exception as e:
            self.logger.error(f"TTS worker error: {e}")
        finally:
            with self._tts_lock:
                self._speaking = False
                self._stop_requested = False

    def start_speaking_async(self, text: str) -> bool:
        """
        Start speaking text asynchronously (non-blocking).

        Args:
            text: Text to speak

        Returns:
            bool: True if started successfully
        """
        if not self._validate_text_input(text):
            return False

        if not self.engine:
            self.logger.warning(f"TTS not available, would say: {text}")
            return False

        # Stop any current speech
        self.stop_speaking()

        try:
            self._log_speech_attempt(text)

            # Start TTS in separate thread
            self._tts_thread = threading.Thread(target=self._tts_worker, args=(text,))
            self._tts_thread.daemon = True
            self._tts_thread.start()

            self.logger.debug("Non-blocking TTS started")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start async TTS: {e}")
            return False

    def stop_speaking(self) -> bool:
        """
        Stop current TTS operation.

        Returns:
            bool: True if stopped successfully
        """
        try:
            with self._tts_lock:
                if self._speaking:
                    self._stop_requested = True
                    if self.engine and hasattr(self.engine, 'stop'):
                        self.engine.stop()

                    self.logger.debug("TTS stop requested")

            # Wait for thread to finish (with timeout)
            if self._tts_thread and self._tts_thread.is_alive():
                self._tts_thread.join(timeout=2.0)

            return True

        except Exception as e:
            self.logger.error(f"Failed to stop TTS: {e}")
            return False

    def is_speaking(self) -> bool:
        """
        Check if TTS is currently speaking.

        Returns:
            bool: True if currently speaking
        """
        with self._tts_lock:
            return self._speaking

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for current TTS to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if completed normally, False if timeout
        """
        if self._tts_thread and self._tts_thread.is_alive():
            self._tts_thread.join(timeout=timeout)
            return not self._tts_thread.is_alive()
        return True