#!/usr/bin/env python3
"""
Test TTS volume and clarity
"""

import sys
import os
import time

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from home_assistant.speech.tts import TextToSpeech

def test_tts_volume():
    """Test TTS with different volume levels."""
    print("🔊 Testing TTS Volume and Clarity")
    print("=" * 40)
    
    tts = TextToSpeech()
    
    # Test with maximum volume
    print("🔊 Setting volume to maximum...")
    tts.set_volume(1.0)
    
    phrases = [
        "This is a test at maximum volume.",
        "Can you hear me clearly now?",
        "What's the weather like today?"
    ]
    
    for i, phrase in enumerate(phrases, 1):
        print(f"\n🔊 Speaking phrase {i}/{len(phrases)}: '{phrase}'")
        print("   (This should be very loud and clear)")
        
        success = tts.speak(phrase)
        
        if success:
            print("✅ Phrase spoken successfully")
        else:
            print("❌ Failed to speak phrase")
        
        # Pause between phrases
        if i < len(phrases):
            print("   Waiting 2 seconds...")
            time.sleep(2)
    
    print("\n🎉 Volume test completed!")
    print("Did you hear all phrases clearly and loudly?")

if __name__ == "__main__":
    test_tts_volume() 