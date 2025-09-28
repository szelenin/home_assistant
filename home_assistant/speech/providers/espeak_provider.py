import subprocess
import platform
import shutil
import os
import yaml
from typing import Dict, Any, List, Optional
from ..base_tts_provider import BaseTTSProvider, TTSConfigurationError, TTSProviderUnavailableError


class EspeakTTSProvider(BaseTTSProvider):
    """TTS provider using eSpeak-NG directly via subprocess."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the eSpeak-NG TTS provider."""
        self.espeak_cmd = None
        self.platform = platform.system().lower()
        self.output_device = None
        super().__init__(config)

        # Load audio configuration for output device
        self._load_audio_config()

    def _load_audio_config(self):
        """Load audio configuration from main config file."""
        try:
            # Load main config.yaml from project root
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    main_config = yaml.safe_load(f)

                audio_config = main_config.get('audio', {})
                self.output_device = audio_config.get('output_device')

                if self.output_device:
                    self.logger.info(f"Using configured output device: {self.output_device}")
                else:
                    self.logger.debug("No output device specified, using default")
            else:
                self.logger.warning("config.yaml not found, using default audio device")

        except Exception as e:
            self.logger.warning(f"Error loading audio config: {e}, using default audio device")

    def _validate_config(self) -> None:
        """Validate eSpeak-specific configuration."""
        # Set defaults if not provided
        if 'voice' not in self.config:
            self.config['voice'] = 'en'
        if 'rate' not in self.config:
            self.config['rate'] = 175
        if 'volume' not in self.config:
            self.config['volume'] = 80
        if 'pitch' not in self.config:
            self.config['pitch'] = 50
        if 'gap' not in self.config:
            self.config['gap'] = 0
        
        # Validate rate (words per minute: 80-450)
        if not isinstance(self.config['rate'], (int, float)) or self.config['rate'] < 80 or self.config['rate'] > 450:
            raise TTSConfigurationError("Rate must be between 80 and 450 WPM")
        
        # Validate volume (0-200, where 100 is normal)
        if not isinstance(self.config['volume'], (int, float)) or self.config['volume'] < 0 or self.config['volume'] > 200:
            raise TTSConfigurationError("Volume must be between 0 and 200")
        
        # Validate pitch (0-99)
        if not isinstance(self.config['pitch'], (int, float)) or self.config['pitch'] < 0 or self.config['pitch'] > 99:
            raise TTSConfigurationError("Pitch must be between 0 and 99")
        
        # Validate gap (pause between words in 10ms units)
        if not isinstance(self.config['gap'], (int, float)) or self.config['gap'] < 0:
            raise TTSConfigurationError("Gap must be >= 0")
    
    def _initialize_provider(self) -> None:
        """Initialize the eSpeak-NG provider."""
        # Find eSpeak executable
        possible_commands = ['espeak-ng', 'espeak']
        
        for cmd in possible_commands:
            if shutil.which(cmd):
                self.espeak_cmd = cmd
                break
        
        if not self.espeak_cmd:
            raise TTSProviderUnavailableError("eSpeak-NG not found. Install with: brew install espeak-ng (macOS) or apt install espeak-ng (Linux)")
        
        self.logger.info(f"Using eSpeak command: {self.espeak_cmd}")
        
        # Test eSpeak functionality
        try:
            result = subprocess.run([self.espeak_cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_info = result.stdout.strip()
                self.logger.info(f"eSpeak version: {version_info}")
            else:
                raise TTSProviderUnavailableError("eSpeak command failed")
        except subprocess.TimeoutExpired:
            raise TTSProviderUnavailableError("eSpeak command timed out")
        except Exception as e:
            raise TTSProviderUnavailableError(f"Failed to test eSpeak: {e}")
    
    def is_available(self) -> bool:
        """Check if eSpeak-NG is available."""
        if not self.espeak_cmd:
            return False
        
        try:
            result = subprocess.run([self.espeak_cmd, '--version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def speak(self, text: str) -> bool:
        """Speak the given text using eSpeak-NG."""
        if not self._validate_text_input(text):
            return False
        
        if not self.espeak_cmd:
            self.logger.warning(f"eSpeak not available, would say: {text}")
            return False
        
        try:
            self._log_speech_attempt(text)
            
            # Build eSpeak command with parameters
            if self.output_device and self.platform == 'linux':
                # On Linux, check if we should use PulseAudio or ALSA
                # First, try to detect if PulseAudio is running
                pulse_running = subprocess.run(['pactl', 'info'], capture_output=True, timeout=1).returncode == 0

                if pulse_running:
                    # Use PulseAudio - pipe to paplay with specific device
                    espeak_cmd = [
                        self.espeak_cmd,
                        '-v', str(self.config['voice']),
                        '-s', str(self.config['rate']),
                        '-a', str(self.config['volume']),
                        '-p', str(self.config['pitch']),
                        '-g', str(self.config['gap']),
                        '--stdout',  # Output WAV to stdout
                        text
                    ]

                    # Convert ALSA device to PulseAudio sink
                    if 'plughw:2,0' in self.output_device or 'hw:2' in self.output_device:
                        # Try to find USB audio sink in PulseAudio
                        sink_result = subprocess.run(['pactl', 'list', 'short', 'sinks'],
                                                   capture_output=True, text=True, timeout=1)
                        usb_sink = None
                        for line in sink_result.stdout.splitlines():
                            if 'usb' in line.lower() or 'logitech' in line.lower():
                                usb_sink = line.split()[1]  # Get sink name
                                break

                        if usb_sink:
                            paplay_cmd = ['paplay', '--device=' + usb_sink]
                            self.logger.debug(f"Using PulseAudio USB sink: {usb_sink}")
                        else:
                            paplay_cmd = ['paplay']
                            self.logger.debug("USB sink not found, using default PulseAudio sink")
                    else:
                        paplay_cmd = ['paplay']

                    self.logger.debug(f"Running eSpeak | paplay: {' '.join(espeak_cmd)} | {' '.join(paplay_cmd)}")

                    # Pipe eSpeak output to paplay
                    espeak_process = subprocess.Popen(espeak_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    paplay_process = subprocess.Popen(paplay_cmd, stdin=espeak_process.stdout,
                                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    espeak_process.stdout.close()
                    paplay_output, paplay_error = paplay_process.communicate(timeout=30)
                    espeak_process.wait()

                    result_code = paplay_process.returncode
                else:
                    # PulseAudio not running, use ALSA
                    espeak_cmd = [
                        self.espeak_cmd,
                        '-v', str(self.config['voice']),
                        '-s', str(self.config['rate']),
                        '-a', str(self.config['volume']),
                        '-p', str(self.config['pitch']),
                        '-g', str(self.config['gap']),
                        '--stdout',  # Output WAV to stdout
                        text
                    ]
                    aplay_cmd = ['aplay', '-D', self.output_device]

                    self.logger.debug(f"Running eSpeak | aplay: {' '.join(espeak_cmd)} | {' '.join(aplay_cmd)}")
                    self.logger.debug(f"Using ALSA output device: {self.output_device}")

                    # Pipe eSpeak output to aplay
                    espeak_process = subprocess.Popen(espeak_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    aplay_process = subprocess.Popen(aplay_cmd, stdin=espeak_process.stdout,
                                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    espeak_process.stdout.close()
                    aplay_output, aplay_error = aplay_process.communicate(timeout=30)
                    espeak_process.wait()

                    result_code = aplay_process.returncode
            else:
                # Default behavior for other platforms or when no output device specified
                cmd = [
                    self.espeak_cmd,
                    '-v', str(self.config['voice']),
                    '-s', str(self.config['rate']),
                    '-a', str(self.config['volume']),
                    '-p', str(self.config['pitch']),
                    '-g', str(self.config['gap']),
                    text
                ]

                self.logger.debug(f"Running eSpeak command: {' '.join(cmd)}")

                # Execute eSpeak normally
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                result_code = result.returncode
            
            if result_code == 0:
                self.logger.info("eSpeak TTS completed successfully")
                return True
            else:
                self.logger.error(f"eSpeak failed with return code {result_code}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("eSpeak command timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to speak text with eSpeak: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available eSpeak voices."""
        if not self.espeak_cmd:
            return []
        
        try:
            result = subprocess.run([self.espeak_cmd, '--voices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.logger.error("Failed to get eSpeak voices")
                return []
            
            voices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 4:
                    # eSpeak voice format: Ptyp Language Age/Gender VoiceName File Other Lang
                    voice_info = {
                        'id': parts[3],  # VoiceName
                        'name': parts[3],  # VoiceName
                        'language': parts[1],  # Language
                        'gender': self._parse_gender(parts[2]) if len(parts) > 2 else 'unknown'
                    }
                    voices.append(voice_info)
            
            return voices
        except Exception as e:
            self.logger.error(f"Failed to get available voices: {e}")
            return []
    
    def _parse_gender(self, age_gender: str) -> str:
        """Parse gender from eSpeak age/gender field."""
        if 'F' in age_gender.upper():
            return 'female'
        elif 'M' in age_gender.upper():
            return 'male'
        else:
            return 'unknown'
    
    def set_voice(self, voice_id: str) -> bool:
        """Set eSpeak voice."""
        try:
            # Validate voice exists
            available_voices = self.get_available_voices()
            voice_ids = [v['id'] for v in available_voices]
            
            if voice_id not in voice_ids:
                self.logger.warning(f"Voice '{voice_id}' not found. Available voices: {voice_ids}")
                return False
            
            self.config['voice'] = voice_id
            self.logger.info(f"eSpeak voice set to: {voice_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set voice: {e}")
            return False
    
    def set_rate(self, rate: int) -> bool:
        """Set eSpeak speech rate."""
        try:
            if rate < 80 or rate > 450:
                self.logger.error("Rate must be between 80 and 450 WPM")
                return False
            
            self.config['rate'] = rate
            self.logger.info(f"eSpeak speech rate set to: {rate} WPM")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set rate: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set eSpeak volume (converted from 0.0-1.0 to 0-200)."""
        try:
            # Convert from 0.0-1.0 to eSpeak's 0-200 scale
            espeak_volume = int(volume * 200)
            espeak_volume = max(0, min(200, espeak_volume))
            
            self.config['volume'] = espeak_volume
            self.logger.info(f"eSpeak volume set to: {espeak_volume} (from {volume})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set volume: {e}")
            return False
    
    def set_pitch(self, pitch: int) -> bool:
        """Set eSpeak pitch (0-99)."""
        try:
            if pitch < 0 or pitch > 99:
                self.logger.error("Pitch must be between 0 and 99")
                return False
            
            self.config['pitch'] = pitch
            self.logger.info(f"eSpeak pitch set to: {pitch}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set pitch: {e}")
            return False
    
    def set_gap(self, gap: int) -> bool:
        """Set eSpeak gap between words (in 10ms units)."""
        try:
            if gap < 0:
                self.logger.error("Gap must be >= 0")
                return False

            self.config['gap'] = gap
            self.logger.info(f"eSpeak gap set to: {gap} (10ms units)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set gap: {e}")
            return False

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages for eSpeak.

        eSpeak supports a wide range of languages.
        """
        # eSpeak supports many languages, here are the most common ones
        # Language codes based on eSpeak --voices output
        return [
            'af', 'an', 'bg', 'bs', 'ca', 'cs', 'cy', 'da', 'de',
            'el', 'en', 'eo', 'es', 'et', 'fa', 'fi', 'fr', 'ga',
            'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'ka',
            'kn', 'ko', 'ku', 'la', 'lt', 'lv', 'mk', 'ml', 'ms',
            'ne', 'nl', 'no', 'pa', 'pl', 'pt', 'ro', 'ru', 'sk',
            'sq', 'sr', 'sv', 'sw', 'ta', 'te', 'tr', 'uk', 'vi',
            'zh'
        ]