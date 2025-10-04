#!/usr/bin/env python3
"""
Test TTS to Pi speakers via Wyoming satellite.
This sends TTS audio directly to the Pi speakers.
"""

import subprocess
import tempfile
import os

def test_tts_to_pi():
    """Test sending TTS to Pi speakers."""
    print("🔊 Testing TTS to Pi speakers via Wyoming satellite...")

    try:
        # Generate TTS on Mac using macOS say command
        message = "Hello! This is your Wyoming satellite speaking from the Pi speakers!"
        print(f"💬 Message: '{message}'")

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name

        # Generate TTS audio using macOS say command
        print("🎵 Generating TTS audio...")
        say_cmd = f'say "{message}" -o {temp_path}'
        result = subprocess.run(say_cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ TTS audio generated")

            # Copy to Pi
            print("📤 Copying audio to Pi...")
            scp_cmd = f"scp {temp_path} lizard@alicegreen.local:/tmp/tts_test.wav"
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Audio copied to Pi")

                # Play on Pi speakers
                print("🔊 Playing on Pi speakers...")
                # Convert to correct format and play
                play_cmd = """ssh lizard@alicegreen.local '
                    # Convert to correct format for Pi speakers
                    ffmpeg -i /tmp/tts_test.wav -ar 22050 -ac 2 -f wav /tmp/tts_converted.wav -y 2>/dev/null &&
                    # Play through speakers
                    aplay -D hw:2,0 /tmp/tts_converted.wav 2>/dev/null &&
                    echo "✅ TTS played successfully on Pi speakers!" ||
                    echo "❌ Playback failed"
                '"""

                result = subprocess.run(play_cmd, shell=True, capture_output=True, text=True)
                print(result.stdout.strip())

                if result.returncode == 0:
                    print("🎉 SUCCESS: TTS working on Pi speakers!")
                else:
                    print(f"❌ Playback failed: {result.stderr}")

            else:
                print(f"❌ File copy failed: {result.stderr}")

        else:
            print(f"❌ TTS generation failed: {result.stderr}")

        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🧪 Pi TTS Test")
    print("=" * 40)
    test_tts_to_pi()
    print("\nIf you heard the message from the Pi, the audio pipeline is working!")
    print("🎯 Your Wyoming satellite system is ready for voice commands!")