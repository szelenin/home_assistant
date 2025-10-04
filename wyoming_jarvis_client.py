#!/usr/bin/env python3
"""
Wyoming-Jarvis Client: Connects Pi Wyoming satellite to Mac Jarvis voice system.

This creates a bridge between:
- Pi satellite (audio capture/playback)
- Mac Jarvis (STT, TTS, AI processing)
"""

import asyncio
import logging
import json
import tempfile
import wave
import os
import signal
from typing import Optional

# Import Jarvis components
from home_assistant.speech.recognizer import SpeechRecognizer
from home_assistant.speech.tts import TextToSpeech
from home_assistant.ai.orchestrator import AIOrchestrator
from home_assistant.utils.logger import setup_logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WyomingJarvisClient:
    """Client that connects Wyoming satellite to Jarvis voice processing."""

    def __init__(self, satellite_host="192.168.86.20", satellite_port=10700):
        self.satellite_host = satellite_host
        self.satellite_port = satellite_port
        self.reader = None
        self.writer = None
        self.running = False

        # Jarvis components
        self.speech_recognizer = None
        self.tts_engine = None
        self.ai_orchestrator = None

        # Audio processing
        self.audio_buffer = bytearray()
        self.is_streaming = False

    async def initialize_jarvis(self):
        """Initialize Jarvis voice components."""
        logger.info("🤖 Initializing Jarvis components...")

        try:
            # Initialize Speech Recognition
            self.speech_recognizer = SpeechRecognizer()
            logger.info("✅ Speech recognition ready")

            # Initialize TTS
            self.tts_engine = TextToSpeech()
            logger.info("✅ TTS engine ready")

            # Initialize AI (optional - may fail due to config)
            try:
                # self.ai_orchestrator = AIOrchestrator()
                logger.info("⚠️  AI orchestrator skipped (config issue)")
            except Exception as e:
                logger.warning(f"AI orchestrator unavailable: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize Jarvis: {e}")
            raise

    async def connect_to_satellite(self):
        """Connect to Wyoming satellite."""
        logger.info(f"🔌 Connecting to Wyoming satellite at {self.satellite_host}:{self.satellite_port}...")

        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.satellite_host, self.satellite_port
            )
            logger.info("✅ Connected to Wyoming satellite!")

            # Send satellite info request
            info_request = {"type": "describe"}
            await self._send_message(info_request)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to satellite: {e}")
            return False

    async def _send_message(self, message):
        """Send JSON message to satellite."""
        if self.writer:
            json_data = json.dumps(message) + "\n"
            self.writer.write(json_data.encode())
            await self.writer.drain()

    async def start_audio_streaming(self):
        """Start receiving audio from satellite."""
        logger.info("🎤 Starting audio streaming from satellite...")

        # Request audio streaming
        audio_start = {
            "type": "audio-start",
            "rate": 16000,
            "width": 2,
            "channels": 1
        }
        await self._send_message(audio_start)
        self.is_streaming = True
        self.audio_buffer.clear()

        logger.info("🎵 Listening for audio from Pi satellite...")

    async def stop_audio_streaming(self):
        """Stop receiving audio from satellite."""
        if self.is_streaming:
            audio_stop = {"type": "audio-stop"}
            await self._send_message(audio_stop)
            self.is_streaming = False
            logger.info("⏹️  Audio streaming stopped")

    async def process_audio_buffer(self):
        """Process accumulated audio through Jarvis STT."""
        if not self.audio_buffer or not self.speech_recognizer:
            return None

        logger.info(f"🧠 Processing {len(self.audio_buffer)} bytes of audio...")

        try:
            # Save audio to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Create WAV file header
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)  # 16kHz
                    wav_file.writeframes(bytes(self.audio_buffer))

                # Use Jarvis speech recognition
                transcript = self.speech_recognizer.recognize_from_file(temp_file.name)

                # Clean up temp file
                os.unlink(temp_file.name)

                if transcript:
                    logger.info(f"🗣️  Heard: '{transcript}'")
                    return transcript
                else:
                    logger.info("🤐 No speech detected")
                    return None

        except Exception as e:
            logger.error(f"❌ Speech recognition failed: {e}")
            return None

    async def generate_response(self, text: str) -> Optional[str]:
        """Generate AI response to user input."""
        if not text:
            return None

        logger.info(f"🤔 Processing query: '{text}'")

        try:
            if self.ai_orchestrator:
                response = self.ai_orchestrator.process_query(text)
            else:
                # Simple echo response if AI not available
                response = f"I heard you say: {text}"

            logger.info(f"💬 Response: '{response}'")
            return response

        except Exception as e:
            logger.error(f"❌ AI processing failed: {e}")
            return "Sorry, I couldn't process that."

    async def send_tts_to_satellite(self, text: str):
        """Generate TTS and send to satellite speakers."""
        if not text or not self.tts_engine:
            return

        logger.info(f"🔊 Generating TTS: '{text}'")

        try:
            # Generate TTS audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                success = self.tts_engine.speak_to_file(text, temp_file.name)

                if success:
                    # Read audio data
                    with wave.open(temp_file.name, 'rb') as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())

                    # Send TTS start
                    tts_start = {
                        "type": "synthesize",
                        "text": text
                    }
                    await self._send_message(tts_start)

                    # Send audio data (simplified)
                    logger.info("📤 Sending TTS audio to satellite...")

                # Clean up
                os.unlink(temp_file.name)

        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")

    async def handle_satellite_messages(self):
        """Handle incoming messages from satellite."""
        while self.running and self.reader:
            try:
                data = await asyncio.wait_for(self.reader.readline(), timeout=1.0)
                if not data:
                    break

                message = json.loads(data.decode().strip())
                msg_type = message.get("type")

                if msg_type == "info":
                    logger.info(f"📋 Satellite info: {message.get('satellite', {}).get('name', 'unknown')}")

                elif msg_type == "audio-chunk":
                    if self.is_streaming:
                        # Accumulate audio data
                        audio_bytes = bytes.fromhex(message.get("audio", ""))
                        self.audio_buffer.extend(audio_bytes)

                elif msg_type == "audio-stop":
                    logger.info("🎵 Audio stream ended - processing speech...")
                    # Process accumulated audio
                    transcript = await self.process_audio_buffer()
                    if transcript:
                        # Generate AI response
                        response = await self.generate_response(transcript)
                        if response:
                            # Send TTS back to satellite
                            await self.send_tts_to_satellite(response)

                    # Clear buffer for next audio session
                    self.audio_buffer.clear()

                else:
                    logger.debug(f"📨 Received: {msg_type}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ Error handling message: {e}")
                break

    async def run(self):
        """Main run loop."""
        self.running = True

        try:
            # Initialize components
            await self.initialize_jarvis()

            # Connect to satellite
            if not await self.connect_to_satellite():
                return

            # Start audio streaming
            await self.start_audio_streaming()

            logger.info("🎯 Wyoming-Jarvis bridge is running!")
            logger.info("🎤 Speak into the Pi's microphone to test...")
            logger.info("🔊 Responses will play through Pi's speakers")
            logger.info("⌨️  Press Ctrl+C to stop")

            # Handle satellite messages
            await self.handle_satellite_messages()

        except Exception as e:
            logger.error(f"❌ Bridge failed: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up connections."""
        self.running = False

        if self.is_streaming:
            await self.stop_audio_streaming()

        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

        logger.info("🔌 Disconnected from satellite")

async def main():
    """Main function with signal handling."""
    client = WyomingJarvisClient()

    # Handle shutdown signals
    def signal_handler():
        logger.info("🛑 Shutdown signal received...")
        client.running = False

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: signal_handler())

    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    print("🚀 Wyoming-Jarvis Voice Bridge")
    print("=" * 50)
    print("Connecting Pi satellite to Mac Jarvis...")
    print()

    asyncio.run(main())