#!/usr/bin/env python3
"""
Test script to isolate TTS hanging issue.
"""

import sys
import os
import time

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from home_assistant.speech.tts import TextToSpeech

def test_tts_simple():
    """Test TTS with a simple message."""
    print("Testing TTS with simple message...")

    try:
        # Create TTS instance
        tts = TextToSpeech()

        if not tts.is_available():
            print("❌ TTS not available")
            return False

        print("✅ TTS initialized")

        # Test 1: Simple short message
        print("\n🔍 Test 1: Speaking simple message")
        start_time = time.time()
        success = tts.speak("Test message")
        duration = time.time() - start_time
        print(f"Result: success={success}, duration={duration:.1f}s")

        # Test 2: Another message to see if it hangs
        print("\n🔍 Test 2: Speaking second message")
        start_time = time.time()
        success = tts.speak("Second test")
        duration = time.time() - start_time
        print(f"Result: success={success}, duration={duration:.1f}s")

        print("\n✅ TTS tests completed!")
        return True

    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tts_simple()
    sys.exit(0 if success else 1)