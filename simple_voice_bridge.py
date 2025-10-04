#!/usr/bin/env python3
"""
Simple Voice Bridge: Connects Pi microphone to Mac voice processing.
When you speak into Pi mic, Mac processes it and sends TTS back to Pi speakers.
"""

import asyncio
import logging
import tempfile
import os
import subprocess
from home_assistant.speech.recognizer import SpeechRecognizer
from home_assistant.speech.tts import TextToSpeech

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleVoiceBridge:
    def __init__(self):
        self.speech_recognizer = None
        self.tts_engine = None
        self.running = False

    async def initialize(self):
        """Initialize voice components."""
        logger.info("🤖 Initializing voice processing...")

        try:
            # Initialize speech recognition
            self.speech_recognizer = SpeechRecognizer()
            logger.info("✅ Speech recognition ready")

            # Initialize TTS
            self.tts_engine = TextToSpeech()
            logger.info("✅ TTS engine ready")

            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    def process_audio_from_pi(self):
        """Capture audio from Pi microphone and process it."""
        logger.info("🎤 Capturing audio from Pi microphone...")

        try:
            # Record 3 seconds of audio from Pi
            record_cmd = """ssh lizard@alicegreen.local '
                timeout 3 arecord -D hw:2,0 -r 16000 -c 1 -f S16_LE -t wav /tmp/voice_input.wav 2>/dev/null
            '"""

            result = subprocess.run(record_cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Audio captured from Pi")

                # Copy audio file to Mac
                scp_cmd = "scp lizard@alicegreen.local:/tmp/voice_input.wav /tmp/pi_audio.wav"
                result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0 and os.path.exists("/tmp/pi_audio.wav"):
                    logger.info("📥 Audio file received from Pi")

                    # Process with speech recognition
                    transcript = self.speech_recognizer.recognize_from_file("/tmp/pi_audio.wav")

                    if transcript:
                        logger.info(f"🗣️  Heard: '{transcript}'")

                        # Generate response
                        response = f"I heard you say: {transcript}. Voice system working!"
                        logger.info(f"💬 Responding: '{response}'")

                        # Send TTS response to Pi
                        self.send_tts_to_pi(response)

                        return transcript
                    else:
                        logger.info("🤐 No speech detected")
                        self.send_tts_to_pi("I didn't hear anything. Please speak louder.")
                        return None
                else:
                    logger.error("❌ Failed to receive audio from Pi")
                    return None
            else:
                logger.error("❌ Failed to capture audio from Pi")
                return None

        except Exception as e:
            logger.error(f"❌ Audio processing failed: {e}")
            return None

    def send_tts_to_pi(self, text):
        """Send TTS response to Pi speakers."""
        logger.info(f"🔊 Sending TTS to Pi: '{text}'")

        try:
            # Generate TTS audio using macOS say
            say_cmd = f'say "{text}" -o /tmp/mac_response.aiff'
            result = subprocess.run(say_cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                # Convert to wav
                convert_cmd = "afconvert /tmp/mac_response.aiff -o /tmp/mac_response.wav -f WAVE -d LEI16@22050"
                result = subprocess.run(convert_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    # Send to Pi and play
                    scp_cmd = "scp /tmp/mac_response.wav lizard@alicegreen.local:/tmp/tts_response.wav"
                    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

                    if result.returncode == 0:
                        # Play on Pi speakers
                        play_cmd = "ssh lizard@alicegreen.local 'aplay -D hw:2,0 /tmp/tts_response.wav'"
                        subprocess.run(play_cmd, shell=True)
                        logger.info("✅ TTS played on Pi speakers")
                    else:
                        logger.error("❌ Failed to send TTS to Pi")
                else:
                    logger.error("❌ Audio conversion failed")
            else:
                logger.error("❌ TTS generation failed")

        except Exception as e:
            logger.error(f"❌ TTS to Pi failed: {e}")

    async def run_voice_loop(self):
        """Run the voice processing loop."""
        logger.info("🎯 Voice bridge running!")
        logger.info("🎤 Speak into the Pi microphone...")
        logger.info("⌨️  Press Ctrl+C to stop")

        self.running = True

        while self.running:
            try:
                logger.info("\n👂 Listening for voice input...")

                # Process audio from Pi
                transcript = self.process_audio_from_pi()

                if transcript:
                    logger.info(f"✅ Successfully processed: '{transcript}'")
                else:
                    logger.info("ℹ️  No speech detected, trying again...")

                # Wait a bit before next capture
                await asyncio.sleep(2)

            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping voice bridge...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Voice loop error: {e}")
                await asyncio.sleep(1)

async def main():
    """Main function."""
    bridge = SimpleVoiceBridge()

    print("🚀 Simple Voice Bridge")
    print("=" * 50)
    print("Connecting Pi microphone to Mac voice processing...")
    print()

    # Initialize components
    if not await bridge.initialize():
        print("❌ Failed to initialize voice components")
        return

    print("✅ Voice bridge ready!")
    print("\n🎤 NOW SPEAK INTO THE PI MICROPHONE!")
    print("The system will:")
    print("  1. 🎤 Capture your voice from Pi")
    print("  2. 🧠 Process speech on Mac")
    print("  3. 🔊 Respond through Pi speakers")
    print()

    try:
        await bridge.run_voice_loop()
    except KeyboardInterrupt:
        print("\n👋 Voice bridge stopped")

if __name__ == "__main__":
    asyncio.run(main())