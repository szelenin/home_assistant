#!/usr/bin/env python3
"""
Test audio focus and system audio settings
"""

import sys
import os
import time
import subprocess

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from home_assistant.speech.tts import TextToSpeech

def check_system_audio():
    """Check system audio settings."""
    print("🔊 Checking System Audio Settings")
    print("=" * 40)
    
    try:
        # Check system volume
        result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], 
                              capture_output=True, text=True)
        system_volume = result.stdout.strip()
        print(f"System Volume: {system_volume}")
        
        # Check if system is muted
        result = subprocess.run(['osascript', '-e', 'output muted of (get volume settings)'], 
                              capture_output=True, text=True)
        system_muted = result.stdout.strip()
        print(f"System Muted: {system_muted}")
        
        # Check audio output device
        result = subprocess.run(['osascript', '-e', 'name of (get volume settings)'], 
                              capture_output=True, text=True)
        audio_device = result.stdout.strip()
        print(f"Audio Device: {audio_device}")
        
    except Exception as e:
        print(f"Could not check system audio: {e}")

def test_audio_focus():
    """Test audio focus with TTS."""
    print("\n🎤 Testing Audio Focus")
    print("=" * 40)
    
    # Check system audio first
    check_system_audio()
    
    tts = TextToSpeech()
    
    # Test with system volume check before each call
    phrases = [
        "First test: Can you hear this clearly?",
        "Second test: This should be audible.",
        "Third test: This is the final test."
    ]
    
    for i, phrase in enumerate(phrases, 1):
        print(f"\n🎤 Test {i}: '{phrase}'")
        
        # Check system audio before speaking
        check_system_audio()
        
        success = tts.speak(phrase)
        print(f"✅ TTS Success: {success}")
        
        if i < len(phrases):
            print("   Waiting 3 seconds...")
            time.sleep(3)
    
    print("\n🎉 Audio focus test completed!")

if __name__ == "__main__":
    test_audio_focus() 