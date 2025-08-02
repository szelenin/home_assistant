#!/usr/bin/env python3
"""
Test script for speech recognizer functionality
"""

import sys
import os
import time

# Add project root to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from home_assistant.speech.recognizer import SpeechRecognizer


def test_microphone_initialization():
    """Test microphone initialization."""
    print("🎤 Testing microphone initialization...")
    
    try:
        recognizer = SpeechRecognizer()
        
        if recognizer.is_available():
            print("✅ Microphone initialized successfully")
            print(f"   Microphone available: {recognizer.microphone is not None}")
            print(f"   Recognizer available: {recognizer.recognizer is not None}")
            return True
        else:
            print("❌ Microphone not available")
            print("   This might be due to:")
            print("   - Missing PyAudio (install with: pip install pyaudio)")
            print("   - No microphone connected")
            print("   - Microphone permissions not granted")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing microphone: {e}")
        return False


def test_ambient_noise_adjustment():
    """Test ambient noise adjustment."""
    print("\n🔊 Testing ambient noise adjustment...")
    
    try:
        recognizer = SpeechRecognizer()
        
        if recognizer.is_available():
            print("✅ Ambient noise adjustment completed")
            print("   The recognizer should now be calibrated for your environment")
            return True
        else:
            print("❌ Cannot test ambient noise adjustment - microphone not available")
            return False
            
    except Exception as e:
        print(f"❌ Error during ambient noise adjustment: {e}")
        return False


def test_listen_for_speech(timeout=5):
    """Test listening for speech."""
    print(f"\n🎧 Testing speech recognition (timeout: {timeout}s)...")
    print("   Please speak something when prompted...")
    
    try:
        recognizer = SpeechRecognizer()
        
        if not recognizer.is_available():
            print("❌ Cannot test speech recognition - microphone not available")
            return False
        
        print("   Starting to listen in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("🎤 SPEAK NOW!")
        success, text = recognizer.listen_for_speech(timeout=timeout, phrase_timeout=3)
        
        if success:
            print(f"✅ Speech recognized successfully!")
            print(f"   Text: '{text}'")
            return True
        else:
            print("❌ Speech recognition failed")
            print("   Possible reasons:")
            print("   - No speech detected")
            print("   - Speech too quiet")
            print("   - Network issues (for Google Speech Recognition)")
            print("   - Microphone permissions")
            return False
            
    except Exception as e:
        print(f"❌ Error during speech recognition test: {e}")
        return False


def test_continuous_listening():
    """Test continuous listening mode."""
    print("\n🔄 Testing continuous listening mode...")
    print("   This will listen for multiple phrases. Say 'stop' to end.")
    
    try:
        recognizer = SpeechRecognizer()
        
        if not recognizer.is_available():
            print("❌ Cannot test continuous listening - microphone not available")
            return False
        
        print("   Starting continuous listening in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        phrase_count = 0
        max_phrases = 5
        
        while phrase_count < max_phrases:
            print(f"\n🎤 Listening for phrase {phrase_count + 1}/{max_phrases}...")
            success, text = recognizer.listen_for_speech(timeout=5, phrase_timeout=3)
            
            if success:
                phrase_count += 1
                print(f"✅ Phrase {phrase_count}: '{text}'")
                
                if text and text.lower().strip() == 'stop':
                    print("   Stop command detected, ending test.")
                    break
            else:
                print("   No speech detected, trying again...")
        
        print(f"✅ Continuous listening test completed. Recognized {phrase_count} phrases.")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return True
    except Exception as e:
        print(f"❌ Error during continuous listening test: {e}")
        return False


def test_microphone_info():
    """Display microphone information."""
    print("\n📋 Microphone Information:")
    
    try:
        import speech_recognition as sr
        
        # List available microphones
        print("   Available microphones:")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"     {index}: {name}")
        
        # Test default microphone
        try:
            mic = sr.Microphone()
            print(f"   Default microphone: {mic.device_index}")
        except Exception as e:
            print(f"   Error accessing default microphone: {e}")
            
    except ImportError:
        print("   SpeechRecognition not available")
    except Exception as e:
        print(f"   Error getting microphone info: {e}")


def main():
    """Run all speech recognizer tests."""
    print("🎤 Speech Recognizer Test Suite")
    print("=" * 40)
    
    # Test microphone information
    test_microphone_info()
    
    # Test basic functionality
    tests = [
        ("Microphone Initialization", test_microphone_initialization),
        ("Ambient Noise Adjustment", test_ambient_noise_adjustment),
        ("Single Speech Recognition", lambda: test_listen_for_speech(5)),
        ("Continuous Listening", test_continuous_listening),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*20} Test Summary {'='*20}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Speech recognizer is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\n💡 Troubleshooting tips:")
        print("   - Install PyAudio: pip install pyaudio")
        print("   - Check microphone permissions")
        print("   - Ensure microphone is connected and working")
        print("   - Test microphone in system settings")


if __name__ == "__main__":
    main() 