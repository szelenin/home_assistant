#!/usr/bin/env python3
"""
Speech Recognizer Test with Auto-Stop Options

This test provides automatic stopping options for microphone tests.
"""

import sys
import os
import time

# Add src directory to Python path (from tests directory)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_path)

# Import using the full path
sys.path.insert(0, os.path.join(current_dir, '..'))

from src.speech.recognizer import SpeechRecognizer
from src.utils.logger import setup_logging


def test_auto_stop_single_recognition(timeout=3, auto_stop=True):
    """
    Test single speech recognition with auto-stop option.
    
    Args:
        timeout: Maximum time to wait for speech (seconds)
        auto_stop: If True, automatically stops after timeout
    """
    logger = setup_logging("home_assistant.test_auto_stop")
    
    print(f"🎤 Auto-Stop Single Recognition Test (timeout: {timeout}s)")
    print("=" * 50)
    
    try:
        recognizer = SpeechRecognizer()
        
        if not recognizer.is_available():
            print("❌ Microphone not available")
            return False
        
        print("🎤 Listening for speech...")
        print(f"   Will {'auto-stop' if auto_stop else 'wait indefinitely'} after {timeout} seconds")
        
        success, text = recognizer.listen_for_speech(timeout=timeout, phrase_timeout=timeout//2)
        
        if success and text:
            print(f"✅ Recognized: '{text}'")
            return True
        else:
            if auto_stop:
                print(f"⏰ Auto-stopped after {timeout} seconds (no speech detected)")
            else:
                print("❌ No speech recognized")
            return False
            
    except Exception as e:
        logger.error(f"Auto-stop test failed: {e}")
        print(f"❌ Test failed: {e}")
        return False


def test_auto_stop_continuous_recognition(max_phrases=3, timeout_per_phrase=3):
    """
    Test continuous speech recognition with automatic stopping.
    
    Args:
        max_phrases: Maximum number of phrases to recognize
        timeout_per_phrase: Timeout for each phrase (seconds)
    """
    logger = setup_logging("home_assistant.test_auto_continuous")
    
    print(f"🔄 Auto-Stop Continuous Recognition Test")
    print(f"   Max phrases: {max_phrases}, Timeout per phrase: {timeout_per_phrase}s")
    print("=" * 50)
    
    try:
        recognizer = SpeechRecognizer()
        
        if not recognizer.is_available():
            print("❌ Microphone not available")
            return False
        
        phrase_count = 0
        successful_phrases = []
        
        print("🎤 Starting continuous listening...")
        print("   Will auto-stop after max phrases or timeouts")
        
        for i in range(max_phrases):
            print(f"\n🎤 Listening for phrase {i+1}/{max_phrases}...")
            
            success, text = recognizer.listen_for_speech(
                timeout=timeout_per_phrase, 
                phrase_timeout=timeout_per_phrase//2
            )
            
            if success and text:
                phrase_count += 1
                successful_phrases.append(text)
                print(f"✅ Phrase {phrase_count}: '{text}'")
                
                # Auto-stop if user says "stop"
                if text.lower().strip() == 'stop':
                    print("🛑 Stop command detected, ending test.")
                    break
            else:
                print(f"⏰ Timeout for phrase {i+1} (no speech detected)")
                # Continue to next phrase instead of stopping
        
        print(f"\n✅ Continuous test completed!")
        print(f"   Successful phrases: {phrase_count}/{max_phrases}")
        if successful_phrases:
            print(f"   Recognized: {', '.join(successful_phrases)}")
        
        return phrase_count > 0  # Success if at least one phrase recognized
        
    except Exception as e:
        logger.error(f"Auto-stop continuous test failed: {e}")
        print(f"❌ Test failed: {e}")
        return False


def test_quick_demo():
    """Quick demo with very short timeouts for testing."""
    print("⚡ Quick Demo Test (Fast Auto-Stop)")
    print("=" * 40)
    
    # Test 1: Single recognition with 2-second timeout
    print("\n1️⃣ Single Recognition (2s timeout):")
    result1 = test_auto_stop_single_recognition(timeout=2, auto_stop=True)
    
    # Test 2: Continuous recognition with 2 phrases, 2s each
    print("\n2️⃣ Continuous Recognition (2 phrases, 2s each):")
    result2 = test_auto_stop_continuous_recognition(max_phrases=2, timeout_per_phrase=2)
    
    # Summary
    print(f"\n{'='*20} Quick Demo Summary {'='*20}")
    if result1 and result2:
        print("🎉 All quick tests passed!")
    elif result1 or result2:
        print("⚠️  Some tests passed")
    else:
        print("❌ No tests passed")
    
    return result1 and result2


def main():
    """Run auto-stop tests with different configurations."""
    logger = setup_logging("home_assistant.test_auto_main")
    
    print("🎤 Speech Recognizer Auto-Stop Test Suite")
    print("=" * 50)
    
    # Test configurations
    tests = [
        ("Quick Demo (2s timeout)", lambda: test_auto_stop_single_recognition(2, True)),
        ("Short Recognition (3s timeout)", lambda: test_auto_stop_single_recognition(3, True)),
        ("Continuous (3 phrases, 3s each)", lambda: test_auto_stop_continuous_recognition(3, 3)),
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
    print(f"\n{'='*20} Auto-Stop Test Summary {'='*20}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All auto-stop tests passed!")
    else:
        print("⚠️  Some auto-stop tests failed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Auto-stop tests interrupted by user")
    except Exception as e:
        logger = setup_logging("home_assistant.test_auto_main")
        logger.critical(f"Fatal error in auto-stop tests: {e}")
        print(f"�� Fatal error: {e}") 