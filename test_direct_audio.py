#!/usr/bin/env python3
"""
Direct audio test: Test Jarvis TTS by sending audio directly to Pi speakers.
This bypasses Wyoming protocol to test the basic audio pipeline.
"""

import subprocess
import tempfile
import os
from home_assistant.speech.tts import TextToSpeech

def test_tts_to_pi():
    """Test TTS by generating audio and playing it on Pi speakers."""
    print("🔊 Testing TTS pipeline to Pi speakers...")

    try:
        # Initialize TTS
        print("🤖 Initializing TTS engine...")
        tts = TextToSpeech()

        # Generate test message
        test_message = "Hello from your Wyoming satellite! The voice pipeline is working."
        print(f"💬 Generating: '{test_message}'")

        # Create temporary file for TTS audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

        # Generate TTS audio
        success = tts.speak_to_file(test_message, temp_path)

        if success:
            print("✅ TTS audio generated successfully")

            # Copy audio to Pi and play it
            print("📤 Sending audio to Pi...")

            # Copy file to Pi
            scp_cmd = f"scp {temp_path} lizard@alicegreen.local:/tmp/test_tts.wav"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Audio copied to Pi")

                # Play audio on Pi
                print("🔊 Playing audio on Pi speakers...")
                play_cmd = "ssh lizard@alicegreen.local 'aplay -D hw:2,0 /tmp/test_tts.wav'"
                result = subprocess.run(play_cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    print("✅ Audio played successfully!")
                    print("🎉 TTS pipeline to Pi speakers is working!")
                else:
                    print(f"❌ Audio playback failed: {result.stderr}")
            else:
                print(f"❌ File copy failed: {result.stderr}")
        else:
            print("❌ TTS generation failed")

        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_microphone_capture():
    """Test capturing audio from Pi microphone."""
    print("\n🎤 Testing microphone capture from Pi...")

    try:
        print("🎙️  Recording 3 seconds of audio from Pi microphone...")
        print("👄 Please speak into the Pi's microphone now!")

        # Record audio on Pi
        record_cmd = """ssh lizard@alicegreen.local '
            timeout 3 arecord -D hw:2,0 -r 16000 -c 1 -f S16_LE -t wav /tmp/test_record.wav 2>/dev/null ||
            echo "Recording completed (or device busy - that\\'s expected if Wyoming is running)"
        '"""

        result = subprocess.run(record_cmd, shell=True, capture_output=True, text=True)
        print(f"📊 Recording result: {result.stdout.strip()}")

        # Check if file was created
        check_cmd = "ssh lizard@alicegreen.local 'ls -lh /tmp/test_record.wav 2>/dev/null || echo \"No file created\"'"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        print(f"📁 File status: {result.stdout.strip()}")

        if "test_record.wav" in result.stdout:
            print("✅ Audio capture working!")

            # Play back the recorded audio
            print("🔄 Playing back recorded audio...")
            playback_cmd = "ssh lizard@alicegreen.local 'aplay -D hw:2,0 /tmp/test_record.wav'"
            subprocess.run(playback_cmd, shell=True)
            print("✅ Playback completed!")
        else:
            print("ℹ️  No recording created (expected if Wyoming satellite is using microphone)")

    except Exception as e:
        print(f"❌ Microphone test failed: {e}")

if __name__ == "__main__":
    print("🧪 Direct Audio Pipeline Test")
    print("=" * 50)
    print("Testing audio pipeline without Wyoming protocol...")
    print()

    # Test TTS to Pi speakers
    test_tts_to_pi()

    # Test microphone capture
    test_microphone_capture()

    print("\n" + "=" * 50)
    print("🎯 This test shows if the basic audio pipeline works.")
    print("🔧 If TTS works but Wyoming doesn't, it's a protocol issue.")
    print("🎤 If microphone is 'busy', Wyoming satellite is working correctly.")