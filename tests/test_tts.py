#!/usr/bin/env python3
"""
Simple test script to verify TTS functionality
"""

import sys
import os

# Add src directory to Python path (from tests directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_path)

# Import using the full path
sys.path.insert(0, os.path.join(current_dir, '..'))
from src.speech.tts import TextToSpeech

def test_tts():
    print("Testing TTS functionality...")
    
    tts = TextToSpeech()
    
    # Test the exact message from main.py
    test_message = "Hello! I'm your new Home Assistant. I need you to give me a name so I know when you're talking to me."
    
    print(f"Speaking: {test_message}")
    success = tts.speak(test_message)
    
    if success:
        print("✅ TTS test completed successfully")
    else:
        print("❌ TTS test failed")

if __name__ == "__main__":
    test_tts()