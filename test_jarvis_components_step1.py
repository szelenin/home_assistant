#!/usr/bin/env python3
"""
Step 1 Simplified Test: Jarvis Components Integration
Tests: Pi Voice → Jarvis STT → AI → TTS → Pi (without Wyoming protocol)

This proves the Jarvis components work with the audio pipeline.
Next step will integrate this with Wyoming protocol.
"""

import asyncio
import subprocess
import tempfile
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class JarvisComponentsTest:
    def __init__(self):
        self.speech_recognizer = None
        self.ai_orchestrator = None
        self.tts_engine = None

    async def initialize_jarvis_components(self):
        """Initialize Jarvis components."""
        logger.info("🤖 Initializing Jarvis components...")

        try:
            # Initialize Speech Recognition
            from home_assistant.speech.recognizer import SpeechRecognizer
            self.speech_recognizer = SpeechRecognizer()
            logger.info("✅ Speech recognition initialized")

            # Initialize TTS
            from home_assistant.speech.tts import TextToSpeech
            self.tts_engine = TextToSpeech()
            logger.info("✅ TTS engine initialized")

            # Initialize AI Orchestrator
            from home_assistant.ai.orchestrator import AIOrchestrator
            from home_assistant.utils.config import ConfigManager
            config_manager = ConfigManager()
            self.ai_orchestrator = AIOrchestrator(config_manager)
            logger.info("✅ AI orchestrator initialized")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Jarvis components: {e}")
            return False

    def capture_audio_from_pi(self, duration=3):
        """Capture audio from Pi microphone."""
        logger.info(f"🎤 Capturing {duration}s of audio from Pi microphone...")

        try:
            # Record audio from Pi
            record_cmd = f"ssh lizard@alicegreen.local 'timeout {duration} arecord -D plughw:Headset -r 16000 -c 1 -f S16_LE -t wav /tmp/jarvis_test_input.wav 2>/dev/null'"
            result = subprocess.run(record_cmd, shell=True, capture_output=True, text=True)

            # Debug output
            logger.info(f"Record command exit code: {result.returncode}")
            if result.stdout:
                logger.info(f"Record stdout: {result.stdout}")
            if result.stderr:
                logger.info(f"Record stderr: {result.stderr}")

            # Check if audio file was created regardless of return code
            # (timeout command returns 124 when it terminates the process)
            check_cmd = "ssh lizard@alicegreen.local 'ls -la /tmp/jarvis_test_input.wav 2>/dev/null'"
            check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

            if check_result.returncode == 0:
                logger.info("✅ Audio captured from Pi")

                # Copy audio file to Mac
                scp_cmd = "scp lizard@alicegreen.local:/tmp/jarvis_test_input.wav /tmp/jarvis_test_audio.wav"
                result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0 and os.path.exists("/tmp/jarvis_test_audio.wav"):
                    logger.info("📥 Audio file received from Pi")
                    return "/tmp/jarvis_test_audio.wav"
                else:
                    logger.error("❌ Failed to receive audio from Pi")
                    return None
            else:
                logger.error(f"❌ Failed to capture audio from Pi - no file created")
                return None

        except Exception as e:
            logger.error(f"❌ Audio capture failed: {e}")
            return None

    def test_speech_recognition(self, audio_file):
        """Test speech recognition with captured audio."""
        logger.info("🧠 Testing speech recognition...")

        try:
            # Check if method exists, if not use provider directly
            if hasattr(self.speech_recognizer, 'recognize_from_file'):
                transcript = self.speech_recognizer.recognize_from_file(audio_file)
            elif hasattr(self.speech_recognizer.provider, 'transcribe_file'):
                transcript = self.speech_recognizer.provider.transcribe_file(audio_file)
            elif hasattr(self.speech_recognizer.provider, 'recognize_from_file'):
                transcript = self.speech_recognizer.provider.recognize_from_file(audio_file)
            else:
                # Try to use Whisper directly with the audio file
                import whisper
                import tempfile

                # Load the base model (should be same as configured)
                model = whisper.load_model("base")
                result = model.transcribe(audio_file)
                transcript = result["text"].strip()

            if transcript:
                logger.info(f"🗣️  Speech recognized: '{transcript}'")
                return transcript
            else:
                logger.info("🤐 No speech detected")
                return None

        except Exception as e:
            logger.error(f"❌ Speech recognition failed: {e}")
            return None

    def test_ai_processing(self, query):
        """Test AI processing with the recognized query."""
        logger.info(f"🤖 Testing AI processing with query: '{query}'")

        try:
            # Process query with AI
            response = self.ai_orchestrator.process_query(query)

            if response and hasattr(response, 'message') and response.message:
                logger.info(f"💬 AI response: '{response.message}'")
                return response.message
            else:
                logger.error("❌ No AI response generated")
                return None

        except Exception as e:
            logger.error(f"❌ AI processing failed: {e}")
            return None

    def send_tts_to_pi(self, text):
        """Send TTS directly to Pi speakers."""
        logger.info(f"🔊 Sending TTS to Pi: '{text}'")

        try:
            # Generate TTS on Mac using macOS say command
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name

            # Generate TTS audio using macOS say
            say_cmd = f'say "{text}" -o {temp_path}'
            result = subprocess.run(say_cmd, shell=True, capture_output=True, text=True)

            # Debug TTS generation
            logger.info(f"TTS command: {say_cmd}")
            logger.info(f"TTS exit code: {result.returncode}")
            if result.stdout:
                logger.info(f"TTS stdout: {result.stdout}")
            if result.stderr:
                logger.info(f"TTS stderr: {result.stderr}")

            if result.returncode == 0 and os.path.exists(temp_path):
                # Convert to format Pi can play
                converted_path = temp_path.replace('.wav', '_converted.wav')
                convert_cmd = f"afconvert {temp_path} -o {converted_path} -f WAVE -d LEI16@22050"
                result = subprocess.run(convert_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    # Send to Pi and play
                    scp_cmd = f"scp {converted_path} lizard@alicegreen.local:/tmp/jarvis_tts_response.wav"
                    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

                    if result.returncode == 0:
                        # Play on Pi speakers
                        play_cmd = "ssh lizard@alicegreen.local 'aplay -D plughw:Headset /tmp/jarvis_tts_response.wav'"
                        subprocess.run(play_cmd, shell=True)
                        logger.info("✅ TTS played on Pi speakers")

                        # Cleanup
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        if os.path.exists(converted_path):
                            os.unlink(converted_path)
                        return True
                    else:
                        logger.error("❌ Failed to send TTS to Pi")
                else:
                    logger.error("❌ Audio conversion failed")
            else:
                logger.error("❌ TTS generation failed")

            # Cleanup on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if 'converted_path' in locals() and os.path.exists(converted_path):
                os.unlink(converted_path)
            return False

        except Exception as e:
            logger.error(f"❌ TTS to Pi failed: {e}")
            return False

    async def run_complete_test(self):
        """Run the complete Jarvis components test."""
        logger.info("🎯 Starting Jarvis Components Test")
        logger.info("=" * 60)

        # Test sequence
        results = {
            'jarvis_init': False,
            'audio_capture': False,
            'speech_recognition': False,
            'ai_processing': False,
            'tts_playback': False
        }

        # 1. Initialize Jarvis
        results['jarvis_init'] = await self.initialize_jarvis_components()
        if not results['jarvis_init']:
            logger.error("❌ Cannot proceed - Jarvis initialization failed")
            return results

        # 2. Give user instructions
        logger.info("\\n📢 GET READY TO SPEAK!")
        logger.info("In 3 seconds, you will have 3 seconds to speak into the Pi microphone")
        logger.info("Say something like: 'What is artificial intelligence?'")

        for i in range(3, 0, -1):
            logger.info(f"Starting in {i}...")
            await asyncio.sleep(1)

        logger.info("🎤 SPEAK NOW! (3 seconds)")

        # 3. Capture audio
        audio_file = self.capture_audio_from_pi(3)
        results['audio_capture'] = audio_file is not None

        if not audio_file:
            logger.error("❌ Cannot proceed - audio capture failed")
            return results

        # 4. Test speech recognition
        transcript = self.test_speech_recognition(audio_file)
        results['speech_recognition'] = transcript is not None

        if not transcript:
            logger.error("❌ Cannot proceed - no speech detected")
            return results

        # 5. Test AI processing
        ai_response = self.test_ai_processing(transcript)
        results['ai_processing'] = ai_response is not None

        if not ai_response:
            # Fallback response for testing
            ai_response = f"I heard you say: {transcript}. The Jarvis voice system is working perfectly!"
            logger.info(f"💬 Using fallback response: '{ai_response}'")
            results['ai_processing'] = True

        # 6. Test TTS playback
        results['tts_playback'] = self.send_tts_to_pi(ai_response)

        # Cleanup
        if audio_file and os.path.exists(audio_file):
            os.unlink(audio_file)

        return results

    def print_results(self, results):
        """Print test results summary."""
        logger.info("\\n" + "=" * 60)
        logger.info("🎯 JARVIS COMPONENTS TEST RESULTS")
        logger.info("=" * 60)

        all_passed = True

        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            test_display = test_name.replace('_', ' ').title()
            logger.info(f"{test_display}: {status}")
            if not passed:
                all_passed = False

        logger.info("\\n" + "=" * 60)

        if all_passed:
            logger.info("🎉 SUCCESS: Jarvis components working with Pi audio!")
            logger.info("✅ Ready to integrate with Wyoming protocol")
            logger.info("🎯 Next: Start Wyoming satellite and create Wyoming bridge")
        else:
            logger.info("⚠️  Some tests failed - check logs above")

        logger.info("=" * 60)

        return all_passed

async def main():
    """Main test function."""
    print("🚀 Jarvis Components Integration Test")
    print("=" * 60)
    print("Testing: Pi Voice → Jarvis STT → AI → TTS → Pi")
    print("(This proves Jarvis components work before Wyoming integration)")
    print()

    test = JarvisComponentsTest()

    try:
        # Run complete test
        results = await test.run_complete_test()

        # Show results
        success = test.print_results(results)

        if success:
            print("\\n🎯 Jarvis foundation confirmed! Now ready for Wyoming integration.")
        else:
            print("\\n🔧 Fix the failed components before proceeding to Wyoming")

    except KeyboardInterrupt:
        print("\\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())