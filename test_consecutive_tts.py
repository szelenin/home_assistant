#!/usr/bin/env python3
"""
Test consecutive TTS calls to verify the fix
"""

import sys
import os
import time

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from home_assistant.speech.tts import TextToSpeech

def test_consecutive_tts():
    """Test consecutive TTS calls."""
    print("🎤 Testing Consecutive TTS Calls")
    print("=" * 40)
    
    tts = TextToSpeech()
    
    # Test phrases that should be spoken consecutively
    phrases = [
        "First phrase: Hello, this is a test.",
        "Second phrase: Can you hear me speaking?",
        "Third phrase: What's the weather like today?",
        "Fourth phrase: Turn on the lights please.",
        "Fifth phrase: Set temperature to 72 degrees."
    ]
    
    for i, phrase in enumerate(phrases, 1):
        print(f"\n🎤 Speaking phrase {i}/{len(phrases)}: '{phrase}'")
        print("   (You should hear this clearly)")
        
        success = tts.speak(phrase)
        
        if success:
            print("✅ Phrase spoken successfully")
        else:
            print("❌ Failed to speak phrase")
        
        # Short pause between phrases
        if i < len(phrases):
            print("   Waiting 1 second before next phrase...")
            time.sleep(1)
    
    print("\n🎉 Consecutive TTS test completed!")
    print("Did you hear all 5 phrases clearly?")

if __name__ == "__main__":
    test_consecutive_tts() 