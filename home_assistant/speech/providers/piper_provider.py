import subprocess
import platform
import shutil
import os
import tempfile
from typing import Dict, Any, List, Optional
from ..base_tts_provider import BaseTTSProvider, TTSConfigurationError, TTSProviderUnavailableError


class PiperTTSProvider(BaseTTSProvider):
    """TTS provider using Piper neural text-to-speech."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Piper TTS provider."""
        self.piper_cmd = None
        self.platform = platform.system().lower()
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate Piper-specific configuration."""
        # Set defaults if not provided
        if 'model' not in self.config:
            self.config['model'] = 'en_US-lessac-medium'
        if 'rate' not in self.config:
            self.config['rate'] = 1.0
        if 'volume' not in self.config:
            self.config['volume'] = 1.0
        if 'speaker_id' not in self.config:
            self.config['speaker_id'] = None
        if 'output_raw' not in self.config:
            self.config['output_raw'] = False
        
        # Validate rate (speed multiplier: 0.25-4.0)
        if not isinstance(self.config['rate'], (int, float)) or self.config['rate'] < 0.25 or self.config['rate'] > 4.0:
            raise TTSConfigurationError("Rate must be between 0.25 and 4.0")
        
        # Validate volume (0.0-2.0)
        if not isinstance(self.config['volume'], (int, float)) or self.config['volume'] < 0.0 or self.config['volume'] > 2.0:
            raise TTSConfigurationError("Volume must be between 0.0 and 2.0")
        
        # Validate speaker_id if provided
        if self.config['speaker_id'] is not None:
            if not isinstance(self.config['speaker_id'], int) or self.config['speaker_id'] < 0:
                raise TTSConfigurationError("Speaker ID must be a non-negative integer")
    
    def _initialize_provider(self) -> None:
        """Initialize the Piper TTS provider."""
        # Try to find piper command
        if shutil.which('piper'):
            self.piper_cmd = 'piper'
        else:
            # Try Python module import
            try:
                import piper
                self.piper_cmd = 'python-piper'
                self.logger.info("Using Piper Python module")
            except ImportError:
                raise TTSProviderUnavailableError(
                    "Piper TTS not found. Install with: pip install piper-tts or download from https://github.com/rhasspy/piper"
                )
        
        if self.piper_cmd == 'piper':
            self.logger.info(f"Using Piper command: {self.piper_cmd}")
            
            # Test Piper functionality
            try:
                result = subprocess.run([self.piper_cmd, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    self.logger.info(f"Piper version: {version_info}")
                else:
                    # Some versions don't have --version, try --help
                    result = subprocess.run([self.piper_cmd, '--help'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        raise TTSProviderUnavailableError("Piper command failed")
            except subprocess.TimeoutExpired:
                raise TTSProviderUnavailableError("Piper command timed out")
            except Exception as e:
                raise TTSProviderUnavailableError(f"Failed to test Piper: {e}")
    
    def is_available(self) -> bool:
        """Check if Piper TTS is available."""
        # Check for command line tool
        if shutil.which('piper'):
            try:
                result = subprocess.run(['piper', '--help'], 
                                      capture_output=True, timeout=5)
                return result.returncode == 0
            except Exception:
                pass
        
        # Check for Python module
        try:
            import piper
            return True
        except ImportError:
            pass
        
        return False
    
    def speak(self, text: str) -> bool:
        """Speak the given text using Piper TTS."""
        if not self._validate_text_input(text):
            return False
        
        if not self.piper_cmd:
            self.logger.warning(f"Piper not available, would say: {text}")
            return False
        
        try:
            self._log_speech_attempt(text)
            
            if self.piper_cmd == 'python-piper':
                return self._speak_with_python_module(text)
            else:
                return self._speak_with_command(text)
                
        except Exception as e:
            self.logger.error(f"Failed to speak text with Piper: {e}")
            return False
    
    def _speak_with_command(self, text: str) -> bool:
        """Speak using Piper command line tool."""
        try:
            # Check if model exists by trying to run piper with --help first
            # This is a workaround since piper doesn't have easy model detection
            model_path = self.config['model']
            
            # Create temporary files for input and output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as text_file:
                text_file.write(text)
                text_file_path = text_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
                audio_file_path = audio_file.name
            
            try:
                # Build Piper command
                cmd = [
                    self.piper_cmd,
                    '--model', model_path,
                    '--output_file', audio_file_path
                ]
                
                # Add optional parameters
                if self.config['speaker_id'] is not None:
                    cmd.extend(['--speaker', str(self.config['speaker_id'])])
                
                if self.config['output_raw']:
                    cmd.append('--output_raw')
                
                self.logger.debug(f"Running Piper command: {' '.join(cmd)}")
                
                # Execute Piper with text input
                with open(text_file_path, 'r') as f:
                    result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    if "Unable to find voice" in result.stderr:
                        self.logger.error(f"Piper model '{model_path}' not found. Download it first or use a different model.")
                        self.logger.info("Available models can be downloaded from: https://github.com/rhasspy/piper/releases")
                    else:
                        self.logger.error(f"Piper failed with return code {result.returncode}: {result.stderr}")
                    return False
                
                # Play the generated audio file
                return self._play_audio_file(audio_file_path)
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(text_file_path)
                    os.unlink(audio_file_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            self.logger.error("Piper command timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to execute Piper command: {e}")
            return False
    
    def _speak_with_python_module(self, text: str) -> bool:
        """Speak using Piper Python module."""
        try:
            import piper
            import io
            import wave
            import sounddevice as sd
            import numpy as np
            
            # Create Piper voice
            voice = piper.PiperVoice.load(self.config['model'])
            
            # Generate audio
            with io.BytesIO() as wav_io:
                voice.synthesize(text, wav_io, speaker_id=self.config['speaker_id'])
                wav_io.seek(0)
                
                # Read WAV data
                with wave.open(wav_io, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    sample_rate = wav_file.getframerate()
                    
                    # Convert to numpy array
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    
                    # Apply volume scaling
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    audio_data *= self.config['volume']
                    
                    # Play audio
                    sd.play(audio_data, samplerate=sample_rate)
                    sd.wait()
            
            self.logger.info("Piper TTS completed successfully")
            return True
            
        except ImportError:
            self.logger.error("Piper Python module not available")
            return False
        except Exception as e:
            self.logger.error(f"Failed to use Piper Python module: {e}")
            return False
    
    def _play_audio_file(self, audio_file_path: str) -> bool:
        """Play audio file using system command or sounddevice."""
        try:
            # Try different audio players based on platform
            if self.platform == 'darwin':  # macOS
                subprocess.run(['afplay', audio_file_path], check=True, timeout=30)
            elif self.platform == 'linux':  # Linux
                players = ['aplay', 'paplay', 'play']
                for player in players:
                    if shutil.which(player):
                        subprocess.run([player, audio_file_path], check=True, timeout=30)
                        break
                else:
                    # Fallback to sounddevice
                    return self._play_with_sounddevice(audio_file_path)
            else:  # Windows or other
                return self._play_with_sounddevice(audio_file_path)
            
            self.logger.info("Piper audio playback completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio playback failed: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Audio playback timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to play audio: {e}")
            return False
    
    def _play_with_sounddevice(self, audio_file_path: str) -> bool:
        """Play audio file using sounddevice."""
        try:
            import sounddevice as sd
            import soundfile as sf
            
            data, samplerate = sf.read(audio_file_path)
            
            # Apply volume scaling
            data *= self.config['volume']
            
            sd.play(data, samplerate)
            sd.wait()
            
            return True
        except ImportError:
            self.logger.error("sounddevice or soundfile not available for audio playback")
            return False
        except Exception as e:
            self.logger.error(f"Failed to play with sounddevice: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available Piper models/voices."""
        # Piper voices are model files, so we return common models
        # In a real implementation, you might scan for .onnx model files
        common_models = [
            {'id': 'en_US-lessac-medium', 'name': 'English US (Lessac Medium)', 'language': 'en-US', 'gender': 'female'},
            {'id': 'en_US-ljspeech-medium', 'name': 'English US (LJ Speech Medium)', 'language': 'en-US', 'gender': 'female'},
            {'id': 'en_US-amy-medium', 'name': 'English US (Amy Medium)', 'language': 'en-US', 'gender': 'female'},
            {'id': 'en_US-danny-low', 'name': 'English US (Danny Low)', 'language': 'en-US', 'gender': 'male'},
            {'id': 'en_GB-alan-medium', 'name': 'English GB (Alan Medium)', 'language': 'en-GB', 'gender': 'male'},
            {'id': 'de_DE-thorsten-medium', 'name': 'German (Thorsten Medium)', 'language': 'de-DE', 'gender': 'male'},
            {'id': 'es_ES-mls_9972-low', 'name': 'Spanish (MLS 9972 Low)', 'language': 'es-ES', 'gender': 'female'},
            {'id': 'fr_FR-mls_1840-low', 'name': 'French (MLS 1840 Low)', 'language': 'fr-FR', 'gender': 'male'},
            {'id': 'it_IT-riccardo-x_low', 'name': 'Italian (Riccardo X-Low)', 'language': 'it-IT', 'gender': 'male'},
        ]
        
        return common_models
    
    def set_voice(self, voice_id: str) -> bool:
        """Set Piper model/voice."""
        try:
            # Validate voice exists in available models
            available_voices = self.get_available_voices()
            voice_ids = [v['id'] for v in available_voices]
            
            if voice_id not in voice_ids:
                self.logger.warning(f"Model '{voice_id}' not in known models. Available: {voice_ids}")
                # Still allow it in case user has custom models
            
            self.config['model'] = voice_id
            self.logger.info(f"Piper model set to: {voice_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set voice: {e}")
            return False
    
    def set_rate(self, rate: int) -> bool:
        """Set Piper speech rate (converted from WPM to speed multiplier)."""
        try:
            # Convert WPM to approximate speed multiplier
            # Assuming baseline of 175 WPM = 1.0 speed
            speed = rate / 175.0
            speed = max(0.25, min(4.0, speed))
            
            self.config['rate'] = speed
            self.logger.info(f"Piper rate set to: {speed} (from {rate} WPM)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set rate: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set Piper volume."""
        try:
            # Convert from 0.0-1.0 to Piper's 0.0-2.0 scale
            piper_volume = volume * 2.0
            piper_volume = max(0.0, min(2.0, piper_volume))
            
            self.config['volume'] = piper_volume
            self.logger.info(f"Piper volume set to: {piper_volume} (from {volume})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set volume: {e}")
            return False
    
    def set_speaker_id(self, speaker_id: Optional[int]) -> bool:
        """Set Piper speaker ID for multi-speaker models."""
        try:
            if speaker_id is not None and (not isinstance(speaker_id, int) or speaker_id < 0):
                self.logger.error("Speaker ID must be a non-negative integer or None")
                return False
            
            self.config['speaker_id'] = speaker_id
            self.logger.info(f"Piper speaker ID set to: {speaker_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set speaker ID: {e}")
            return False