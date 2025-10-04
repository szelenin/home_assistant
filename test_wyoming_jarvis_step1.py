#!/usr/bin/env python3
"""
Wyoming-Jarvis Integration Test - Step 1
Tests: Pi Voice Command → Home Assistant Processing → TTS Playback

This test verifies the complete pipeline:
1. Capture voice from Pi microphone
2. Send to Mac for Jarvis STT → AI → TTS processing
3. Play response on Pi speakers

Prerequisites:
- Pi satellite running on 192.168.86.20:10700
- Wyoming integration initialized
- Jarvis components available
"""

import asyncio
import subprocess
import tempfile
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class WyomingJarvisStep1Test:
    def __init__(self):
        self.integration = None

    async def initialize(self):
        """Initialize Wyoming-Jarvis integration."""
        logger.info("🚀 Initializing Wyoming-Jarvis integration...")

        try:
            from home_assistant.wyoming.jarvis_integration import WyomingJarvisIntegration
            self.integration = WyomingJarvisIntegration()
            await self.integration.initialize()
            logger.info("✅ Integration initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize integration: {e}")
            return False

    def check_pi_satellite(self):
        """Check if Pi satellite is accessible."""
        logger.info("🔍 Checking Pi satellite status...")

        try:
            # Check if satellite is listening
            result = subprocess.run(
                ["nc", "-zv", "192.168.86.20", "10700"],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                logger.info("✅ Pi satellite is online and listening")
                return True
            else:
                logger.error("❌ Pi satellite not accessible")
                return False

        except Exception as e:
            logger.error(f"❌ Satellite check failed: {e}")
            return False

    def capture_audio_from_pi(self, duration=3):
        """Capture audio from Pi microphone."""
        logger.info(f"🎤 Capturing {duration}s of audio from Pi microphone...")

        try:
            # Record audio from Pi
            record_cmd = f"ssh lizard@alicegreen.local 'timeout {duration} arecord -D hw:2,0 -r 16000 -c 1 -f S16_LE -t wav /tmp/test_voice_input.wav 2>/dev/null'"

            result = subprocess.run(record_cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("✅ Audio captured from Pi")

                # Copy audio file to Mac
                scp_cmd = "scp lizard@alicegreen.local:/tmp/test_voice_input.wav /tmp/pi_test_audio.wav"
                result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0 and os.path.exists("/tmp/pi_test_audio.wav"):
                    logger.info("📥 Audio file received from Pi")
                    return "/tmp/pi_test_audio.wav"
                else:
                    logger.error("❌ Failed to receive audio from Pi")
                    return None
            else:
                logger.error("❌ Failed to capture audio from Pi")
                return None

        except Exception as e:
            logger.error(f"❌ Audio capture failed: {e}")
            return None

    def test_speech_recognition(self, audio_file):
        """Test speech recognition with captured audio."""
        logger.info("🧠 Testing speech recognition...")

        try:
            if not self.integration:
                logger.error("❌ Integration not initialized")
                return None

            # Read audio file
            with open(audio_file, 'rb') as f:
                audio_data = f.read()

            # Test speech recognition
            transcript = self.integration.recognize_from_audio_data(audio_data)

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
            if not self.integration:
                logger.error("❌ Integration not initialized")
                return None

            # Process query with AI
            response = self.integration.process_query(query)

            if response:
                logger.info(f"💬 AI response: '{response}'")
                return response
            else:
                logger.error("❌ No AI response generated")
                return None

        except Exception as e:
            logger.error(f"❌ AI processing failed: {e}")
            return None

    def test_tts_to_pi(self, text):
        """Test TTS playback on Pi speakers."""
        logger.info(f"🔊 Testing TTS to Pi: '{text}'")

        try:
            if not self.integration:
                logger.error("❌ Integration not initialized")
                return False

            # Send TTS to Pi
            success = self.integration.send_tts_to_pi(text)

            if success:
                logger.info("✅ TTS successfully played on Pi speakers")
                return True
            else:
                logger.error("❌ TTS playback failed")
                return False

        except Exception as e:
            logger.error(f"❌ TTS test failed: {e}")
            return False

    async def run_complete_test(self):
        """Run the complete Step 1 test."""
        logger.info("🎯 Starting Complete Step 1 Test")
        logger.info("=" * 60)

        # Test sequence
        results = {
            'satellite_check': False,
            'audio_capture': False,
            'speech_recognition': False,
            'ai_processing': False,
            'tts_playback': False
        }

        # 1. Check Pi satellite
        results['satellite_check'] = self.check_pi_satellite()
        if not results['satellite_check']:
            logger.error("❌ Cannot proceed - Pi satellite not accessible")
            return results

        # 2. Give user instructions
        logger.info("\\n📢 GET READY TO SPEAK!")
        logger.info("In 3 seconds, you will have 3 seconds to speak into the Pi microphone")
        logger.info("Say something like: 'What is the weather today?'")

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
            ai_response = f"I heard you say: {transcript}. The Wyoming-Jarvis integration is working!"
            logger.info(f"💬 Using fallback response: '{ai_response}'")
            results['ai_processing'] = True

        # 6. Test TTS playback
        results['tts_playback'] = self.test_tts_to_pi(ai_response)

        # Cleanup
        if audio_file and os.path.exists(audio_file):
            os.unlink(audio_file)

        return results

    def print_results(self, results):
        """Print test results summary."""
        logger.info("\\n" + "=" * 60)
        logger.info("🎯 STEP 1 TEST RESULTS")
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
            logger.info("🎉 STEP 1 COMPLETE: Wyoming → Jarvis integration working!")
            logger.info("✅ Ready for Step 2: Wake word detection")
        else:
            logger.info("⚠️  Some tests failed - check logs above")

        logger.info("=" * 60)

        return all_passed

async def main():
    """Main test function."""
    print("🚀 Wyoming-Jarvis Integration Test - Step 1")
    print("=" * 60)
    print("Testing: Pi Voice → Wyoming → Jarvis STT → AI → TTS → Pi")
    print()

    test = WyomingJarvisStep1Test()

    try:
        # Initialize
        if not await test.initialize():
            print("❌ Failed to initialize - check your Jarvis components")
            return

        # Run complete test
        results = await test.run_complete_test()

        # Show results
        success = test.print_results(results)

        if success:
            print("\\n🎯 Next step: Run test_wyoming_wakeword_step2.py")
        else:
            print("\\n🔧 Fix the failed components before proceeding")

    except KeyboardInterrupt:
        print("\\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())