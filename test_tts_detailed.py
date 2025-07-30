#!/usr/bin/env python3
"""
Detailed TTS test matching the working sttts.py pattern
"""

import pyttsx3
import sounddevice as sd

def print_neutral(text):
    print(f"\033[35m[*] {text}\033[0m")

def test_tts_direct():
    """Test TTS using the same pattern as sttts.py"""
    print_neutral("Testing TTS with direct pyttsx3 usage...")
    
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        
        # Test message
        text = "Hello! I'm your new Home Assistant. I need you to give me a name so I know when you're talking to me."
        text = text.replace(",", "")
        
        print_neutral(f"Speaking: {text}")
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        
        print_neutral("✅ Direct TTS test completed")
        
    except Exception as e:
        print(f"❌ Direct TTS test failed: {e}")

def test_audio_devices():
    """Test audio device configuration"""
    print_neutral("Checking audio devices...")
    
    try:
        devices = sd.query_devices()
        print_neutral(f"Found {len(devices)} audio devices:")
        
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                print_neutral(f"  Output {i}: {device['name']} (channels: {device['max_output_channels']})")
        
        # Try to set default device like in sttts.py
        try:
            sd.default.device = None  # Use system default
            print_neutral("✅ Audio device configuration successful")
        except Exception as e:
            print_neutral(f"⚠️ Audio device configuration warning: {e}")
            
    except Exception as e:
        print(f"❌ Audio device check failed: {e}")

if __name__ == "__main__":
    test_audio_devices()
    test_tts_direct() 