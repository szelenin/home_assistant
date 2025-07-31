#!/usr/bin/env python3
"""
Test with forced system volume
"""

import sys
import os
import time
import subprocess

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from home_assistant.speech.tts import TextToSpeech

def set_system_volume(volume_percent):
    """Set system volume."""
    try:
        subprocess.run(['osascript', '-e', f'set volume output volume {volume_percent}'], 
                      capture_output=True)
        print(f"🔊 Set system volume to {volume_percent}%")
    except Exception as e:
        print(f"Could not set system volume: {e}")

def test_with_volume_fix():
    """Test TTS with forced system volume."""
    print("🔊 Testing TTS with Volume Fix")
    print("=" * 40)
    
    # Set system volume to maximum
    print("🔊 Setting system volume to maximum...")
    set_system_volume(100)
    
    tts = TextToSpeech()
    
    # Test phrases
    phrases = [
        "Volume test 1: Can you hear this at full volume?",
        "Volume test 2: This should be very loud.",
        "Volume test 3: This is the final volume test."
    ]
    
    for i, phrase in enumerate(phrases, 1):
        print(f"\n🎤 Test {i}: '{phrase}'")
        print("   (This should be very loud and clear)")
        
        success = tts.speak(phrase)
        print(f"✅ TTS Success: {success}")
        
        if i < len(phrases):
            print("   Waiting 2 seconds...")
            time.sleep(2)
    
    print("\n🎉 Volume fix test completed!")
    print("Did you hear all 3 phrases at full volume?")

if __name__ == "__main__":
    test_with_volume_fix() 