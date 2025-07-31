#!/usr/bin/env python3
"""
Test TTS only (without speech recognition interference)
"""

import sys
import os
import time

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from home_assistant.speech.tts import TextToSpeech

def test_tts_only():
    """Test TTS without speech recognition interference."""
    print("🎤 Testing TTS Only (No Speech Recognition)")
    print("=" * 50)
    
    tts = TextToSpeech()
    
    # Test the exact phrases from the integration test
    phrases = [
        "Hello, how are you?",
        "What's the weather like?",
        "Turn on the lights"
    ]
    
    for i, phrase in enumerate(phrases, 1):
        print(f"\n🎤 Speaking phrase {i}/{len(phrases)}: '{phrase}'")
        print("   (You should hear this clearly)")
        
        success = tts.speak(phrase)
        
        if success:
            print("✅ Phrase spoken successfully")
        else:
            print("❌ Failed to speak phrase")
        
        # Pause between phrases (like in integration test)
        if i < len(phrases):
            print("   Waiting 3 seconds before next phrase...")
            time.sleep(3)
    
    print("\n🎉 TTS-only test completed!")
    print("Did you hear all 3 phrases clearly?")

if __name__ == "__main__":
    test_tts_only() 