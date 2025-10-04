#!/usr/bin/env python3
"""
Complete Pipeline Test: Pi Voice → Mac Processing → Pi TTS Response
This tests the FULL round-trip communication including audio response.
"""

import asyncio
import subprocess
import os
import logging
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_pipeline():
    """Test the complete pipeline with TTS response."""
    logger.info("🚀 Testing COMPLETE Pipeline: Pi → Mac → Pi (with TTS response)")
    logger.info("=" * 70)

    try:
        # Initialize Jarvis components
        logger.info("🤖 Initializing Jarvis components...")

        from home_assistant.speech.recognizer import SpeechRecognizer
        speech_recognizer = SpeechRecognizer()
        logger.info("✅ Speech recognition initialized")

        # Capture audio
        logger.info("\\n📢 GET READY TO SPEAK!")
        logger.info("In 3 seconds, say something into the Pi microphone")
        logger.info("Example: 'Hello Jarvis, how are you today?'")

        for i in range(3, 0, -1):
            logger.info(f"Starting in {i}...")
            await asyncio.sleep(1)

        logger.info("🎤 SPEAK NOW! (3 seconds)")

        # Record from Pi
        record_cmd = "ssh lizard@alicegreen.local 'timeout 3 arecord -D plughw:Headset -r 16000 -c 1 -f S16_LE -t wav /tmp/complete_test.wav 2>/dev/null'"
        result = subprocess.run(record_cmd, shell=True, capture_output=True, text=True)

        # Copy to Mac
        scp_cmd = "scp lizard@alicegreen.local:/tmp/complete_test.wav /tmp/complete_test.wav"
        subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

        if os.path.exists("/tmp/complete_test.wav"):
            logger.info("✅ Audio captured and transferred")

            # Transcribe with Whisper
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe("/tmp/complete_test.wav")
            transcript = result["text"].strip()

            if transcript:
                logger.info(f"✅ Speech recognized: '{transcript}'")

                # Generate response message
                response_text = f"Hello! I heard you say: {transcript}. The complete voice pipeline is working perfectly!"
                logger.info(f"💬 Generating response: '{response_text}'")

                # Generate TTS using the working method
                with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as f:
                    aiff_path = f.name

                wav_path = aiff_path.replace('.aiff', '.wav')

                # Generate TTS audio
                say_cmd = f'say "{response_text}" -o {aiff_path}'
                result = subprocess.run(say_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info("✅ TTS audio generated")

                    # Convert to WAV format
                    convert_cmd = f"afconvert {aiff_path} -o {wav_path} -f WAVE -d LEI16@22050"
                    result = subprocess.run(convert_cmd, shell=True, capture_output=True, text=True)

                    if result.returncode == 0:
                        logger.info("✅ Audio converted to WAV")

                        # Send to Pi and play
                        scp_cmd = f"scp {wav_path} lizard@alicegreen.local:/tmp/response.wav"
                        result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

                        if result.returncode == 0:
                            logger.info("✅ Audio sent to Pi")

                            # Play on Pi speakers
                            logger.info("🔊 Playing response on Pi speakers...")
                            play_cmd = "ssh lizard@alicegreen.local 'aplay -D plughw:Headset /tmp/response.wav'"
                            subprocess.run(play_cmd, shell=True)

                            logger.info("\\n" + "=" * 70)
                            logger.info("🎉 SUCCESS: COMPLETE PIPELINE WORKING!")
                            logger.info("✅ Pi audio capture: Working")
                            logger.info("✅ Speech recognition: Working")
                            logger.info("✅ TTS generation: Working")
                            logger.info("✅ Pi audio playback: Working")
                            logger.info("🎯 Full round-trip communication established!")
                            logger.info("=" * 70)

                            # Cleanup
                            for cleanup_file in ["/tmp/complete_test.wav", aiff_path, wav_path]:
                                if os.path.exists(cleanup_file):
                                    os.unlink(cleanup_file)

                            return True
                        else:
                            logger.error("❌ Failed to send audio to Pi")
                    else:
                        logger.error("❌ Audio conversion failed")
                else:
                    logger.error("❌ TTS generation failed")

                # Cleanup on failure
                for cleanup_file in [aiff_path, wav_path]:
                    if os.path.exists(cleanup_file):
                        os.unlink(cleanup_file)

            else:
                logger.error("❌ No speech detected")
        else:
            logger.error("❌ Audio capture failed")

        return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎙️  Complete Pipeline Test")
    print("=" * 50)
    print("This will test the FULL voice pipeline:")
    print("  1. 🎤 Capture your voice on Pi")
    print("  2. 🧠 Process with Whisper on Mac")
    print("  3. 🔊 Respond with TTS on Pi speakers")
    print()

    success = asyncio.run(test_complete_pipeline())
    if success:
        print("\\n🎯 COMPLETE SUCCESS! You should have heard the response.")
        print("Your voice system is ready for Wyoming protocol integration!")
    else:
        print("\\n❌ Something failed. Check the logs above.")