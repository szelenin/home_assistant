"""Integration module connecting Wyoming protocol to Jarvis.

This module creates the bridge between Wyoming satellite communications
and the existing Jarvis voice assistant system.
"""

import asyncio
import logging
import yaml
import os
from typing import Optional, Dict, Any
import numpy as np
import io
import tempfile

from ..utils.logger import setup_logging
from ..speech.recognizer import SpeechRecognizer
from ..speech.tts import TextToSpeech
from ..ai.orchestrator import AIOrchestrator
from .server import WyomingServer
from .event_bridge import EventBridge


class WyomingJarvisIntegration:
    """Integrates Wyoming protocol with existing Jarvis system."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Wyoming-Jarvis integration.

        Args:
            config_path: Path to Wyoming configuration file
        """
        self.logger = setup_logging("wyoming.jarvis")

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize Wyoming components
        self.server = None
        self.event_bridge = EventBridge()

        # Initialize Jarvis components
        self.speech_recognition = None
        self.tts_engine = None
        self.ai_orchestrator = None

        # Audio conversion settings
        self.stt_rate = self.config['audio']['input']['rate']
        self.tts_rate = self.config['audio']['output']['rate']

        self.logger.info("Wyoming-Jarvis integration initialized")

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """Load Wyoming configuration.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        if not config_path:
            # Use default config path
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config',
                'wyoming.yaml'
            )

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('wyoming', {})
        except Exception as e:
            self.logger.warning(f"Could not load Wyoming config: {e}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default Wyoming configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            'server': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 10700
            },
            'audio': {
                'input': {'rate': 16000, 'width': 2, 'channels': 1},
                'output': {'rate': 22050, 'width': 2, 'channels': 1}
            },
            'integration': {
                'use_existing_stt': True,
                'use_existing_tts': True,
                'use_existing_ai': True
            }
        }

    async def initialize(self) -> None:
        """Initialize all components."""
        try:
            # Initialize Jarvis components
            await self._initialize_jarvis_components()

            # Initialize Wyoming server
            await self._initialize_wyoming_server()

            # Connect components via event bridge
            self._connect_components()

            self.logger.info("Wyoming-Jarvis integration initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize integration: {e}")
            raise

    async def _initialize_jarvis_components(self) -> None:
        """Initialize Jarvis voice assistant components."""
        self.logger.info("Initializing Jarvis components...")

        # Initialize Speech Recognition
        if self.config['integration'].get('use_existing_stt', True):
            try:
                from ..speech.recognizer import SpeechRecognizer
                self.speech_recognition = SpeechRecognizer()
                self.logger.info("Speech recognition initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize speech recognition: {e}")

        # Initialize TTS
        if self.config['integration'].get('use_existing_tts', True):
            try:
                from ..speech.tts import TextToSpeech
                self.tts_engine = TextToSpeech()
                self.logger.info("TTS engine initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize TTS: {e}")

        # Initialize AI Orchestrator
        if self.config['integration'].get('use_existing_ai', True):
            try:
                from ..ai.orchestrator import AIOrchestrator
                self.ai_orchestrator = AIOrchestrator()
                self.logger.info("AI orchestrator initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize AI orchestrator: {e}")

    async def _initialize_wyoming_server(self) -> None:
        """Initialize Wyoming protocol server."""
        if not self.config['server'].get('enabled', True):
            self.logger.info("Wyoming server disabled in configuration")
            return

        host = self.config['server'].get('host', '0.0.0.0')
        port = self.config['server'].get('port', 10700)

        self.server = WyomingServer(host, port)
        self.logger.info(f"Wyoming server configured for {host}:{port}")

    def _connect_components(self) -> None:
        """Connect Wyoming and Jarvis components via event bridge."""
        # Set Home Assistant components in the event bridge
        self.event_bridge.set_home_assistant_components(
            speech_recognizer=self,  # Use this class as adapter
            tts_engine=self,
            ai_orchestrator=self,
            wake_word_detector=None  # Wake word handled by satellites
        )

        # Set event bridge in server
        if self.server:
            self.server.event_bridge = self.event_bridge

        self.logger.info("Components connected via event bridge")

    # Adapter methods for event bridge

    def recognize_from_audio_data(self, audio_data: bytes) -> Optional[str]:
        """Adapter method for speech recognition.

        Args:
            audio_data: WAV audio data

        Returns:
            Transcribed text or None
        """
        if not self.speech_recognition:
            return None

        try:
            # Save audio to temporary file (Whisper needs a file)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                # Use Whisper to transcribe
                result = self.speech_recognition.recognize_from_file(temp_path)
                return result
            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except Exception as e:
            self.logger.error(f"Speech recognition failed: {e}")
            return None

    def process_query(self, query: str) -> Optional[str]:
        """Adapter method for AI processing.

        Args:
            query: User query text

        Returns:
            AI response or None
        """
        if not self.ai_orchestrator:
            return None

        try:
            # Process with AI orchestrator
            response = self.ai_orchestrator.process_query(query)
            return response
        except Exception as e:
            self.logger.error(f"AI processing failed: {e}")
            return None

    def generate_tts_audio(self, text: str, rate: int = 22050) -> Optional[bytes]:
        """Generate TTS audio data.

        Args:
            text: Text to synthesize
            rate: Target sample rate

        Returns:
            Raw audio data or None
        """
        if not self.tts_engine:
            return None

        try:
            # Generate speech with TTS engine
            # This is a simplified version - you'll need to adapt to your TTS implementation
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name

            # Use your TTS to generate audio file
            success = self.tts_engine.speak_to_file(text, temp_path)

            if success:
                # Read the audio file and extract raw data
                import wave
                with wave.open(temp_path, 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())

                os.unlink(temp_path)
                return audio_data
            else:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None

        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            return None

    async def start(self) -> None:
        """Start the Wyoming-Jarvis integration."""
        try:
            # Initialize components if not already done
            if not self.server and self.config['server'].get('enabled', True):
                await self.initialize()

            # Start Wyoming server
            if self.server:
                self.logger.info("Starting Wyoming server...")

                # Run server in background task
                server_task = asyncio.create_task(self.server.start())

                # Store task reference
                self._server_task = server_task

                self.logger.info("Wyoming-Jarvis integration started")
            else:
                self.logger.info("Wyoming server not enabled")

        except Exception as e:
            self.logger.error(f"Failed to start integration: {e}")
            raise

    async def stop(self) -> None:
        """Stop the Wyoming-Jarvis integration."""
        try:
            # Stop Wyoming server
            if self.server:
                await self.server.stop()

            # Cancel server task
            if hasattr(self, '_server_task'):
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Wyoming-Jarvis integration stopped")

        except Exception as e:
            self.logger.error(f"Error stopping integration: {e}")

    def get_status(self) -> dict:
        """Get status of the integration.

        Returns:
            Status dictionary
        """
        status = {
            'running': False,
            'server': None,
            'satellites': {},
            'components': {
                'stt': self.speech_recognition is not None,
                'tts': self.tts_engine is not None,
                'ai': self.ai_orchestrator is not None
            }
        }

        if self.server:
            status['running'] = self.server._running
            status['server'] = {
                'host': self.server.host,
                'port': self.server.port,
                'clients': len(self.server.clients)
            }

            # Get satellite information
            for client_id, client in self.server.clients.items():
                status['satellites'][client_id] = {
                    'name': client.satellite_name,
                    'streaming': client.is_streaming,
                    'connected': True
                }

        return status


async def main():
    """Main function for testing the integration."""
    import signal

    # Create integration
    integration = WyomingJarvisIntegration()

    # Handle shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("\nShutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize and start
        await integration.initialize()
        await integration.start()

        print("Wyoming-Jarvis integration running. Press Ctrl+C to stop.")

        # Wait for shutdown
        await shutdown_event.wait()

    finally:
        # Clean shutdown
        await integration.stop()


if __name__ == "__main__":
    asyncio.run(main())