#!/usr/bin/env python3
"""
Test script to isolate the welcome message TTS hanging issue.
"""

import sys
import os
import time

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from home_assistant.speech.tts import TextToSpeech

def test_welcome_message():
    """Test TTS with the exact welcome message."""
    print("Testing TTS with exact welcome message...")

    try:
        # Create TTS instance
        tts = TextToSpeech()

        if not tts.is_available():
            print("❌ TTS not available")
            return False

        print("✅ TTS initialized")

        # Test with the exact welcome message
        welcome_message = "Hello! I'm jarvis, your Home Assistant. I'm ready to help!"
        print(f"\n🔍 Testing with welcome message: '{welcome_message}'")

        start_time = time.time()
        success = tts.speak(welcome_message)
        duration = time.time() - start_time
        print(f"Result: success={success}, duration={duration:.1f}s")

        if success:
            print("✅ Welcome message TTS completed successfully!")
        else:
            print("❌ Welcome message TTS failed!")

        return success

    except Exception as e:
        print(f"❌ Welcome message test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_welcome_message()
    sys.exit(0 if success else 1)