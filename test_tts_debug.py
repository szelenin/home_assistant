#!/usr/bin/env python3
"""
Debug test for TTS 3rd call issue
"""

import sys
import os
import time

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from home_assistant.speech.tts import TextToSpeech

def test_tts_debug():
    """Debug test for TTS 3rd call issue."""
    print("🔍 Debugging TTS 3rd Call Issue")
    print("=" * 40)
    
    # Test 1: Simple consecutive calls
    print("\n🎤 Test 1: Simple consecutive calls")
    tts1 = TextToSpeech()
    
    for i in range(1, 4):
        phrase = f"Test {i}: This is phrase number {i}"
        print(f"\n🎤 Speaking: '{phrase}'")
        
        success = tts1.speak(phrase)
        print(f"✅ Success: {success}")
        
        if i < 3:
            print("   Waiting 2 seconds...")
            time.sleep(2)
    
    # Test 2: Recreate TTS for each call
    print("\n🎤 Test 2: Recreate TTS for each call")
    
    for i in range(1, 4):
        tts2 = TextToSpeech()  # New instance each time
        phrase = f"Fresh Test {i}: This is phrase number {i}"
        print(f"\n🎤 Speaking: '{phrase}'")
        
        success = tts2.speak(phrase)
        print(f"✅ Success: {success}")
        
        if i < 3:
            print("   Waiting 2 seconds...")
            time.sleep(2)
    
    # Test 3: Force engine cleanup
    print("\n🎤 Test 3: Force engine cleanup")
    tts3 = TextToSpeech()
    
    for i in range(1, 4):
        phrase = f"Clean Test {i}: This is phrase number {i}"
        print(f"\n🎤 Speaking: '{phrase}'")
        
        # Force engine stop before speaking
        try:
            tts3.engine.stop()
        except:
            pass
        
        success = tts3.speak(phrase)
        print(f"✅ Success: {success}")
        
        if i < 3:
            print("   Waiting 2 seconds...")
            time.sleep(2)
    
    print("\n🎉 Debug test completed!")
    print("Which test(s) did you hear all 3 phrases?")

if __name__ == "__main__":
    test_tts_debug() 