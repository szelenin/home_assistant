import subprocess
import platform
import shutil
from typing import Dict, Any, List, Optional
from ..base_tts_provider import BaseTTSProvider, TTSConfigurationError, TTSProviderUnavailableError


class EspeakTTSProvider(BaseTTSProvider):
    """TTS provider using eSpeak-NG directly via subprocess."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the eSpeak-NG TTS provider."""
        self.espeak_cmd = None
        self.platform = platform.system().lower()
        super().__init__(config)
    
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
            
            # Execute eSpeak
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("eSpeak TTS completed successfully")
                return True
            else:
                self.logger.error(f"eSpeak failed with return code {result.returncode}: {result.stderr}")
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