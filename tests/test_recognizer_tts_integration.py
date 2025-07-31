#!/usr/bin/env python3
"""
Integration test for speech recognizer and TTS

This test listens for speech and then speaks it back using
configurations from the YAML file.
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
from src.speech.tts import TextToSpeech
from src.utils.logger import setup_logging


def test_recognizer_tts_integration():
    """Test speech recognition and TTS integration."""
    logger = setup_logging("home_assistant.test_integration")
    
    print("🎤🎵 Speech Recognition + TTS Integration Test")
    print("=" * 50)
    print("This test will:")
    print("1. Listen for your speech")
    print("2. Speak back what it heard using TTS")
    print("3. Use configurations from config.yaml")
    print()
    
    # Initialize components
    try:
        recognizer = SpeechRecognizer()
        tts = TextToSpeech()
        
        if not recognizer.is_available():
            print("❌ Speech recognizer not available")
            print("   Please check microphone permissions and PyAudio installation")
            return False
        
        if not tts.engine:
            print("❌ TTS engine not available")
            print("   Please check pyttsx3 installation")
            return False
        
        print("✅ Both recognizer and TTS initialized successfully")
        print()
        
        # Test loop
        test_count = 0
        max_tests = 3
        
        while test_count < max_tests:
            test_count += 1
            print(f"\n{'='*20} Test {test_count}/{max_tests} {'='*20}")
            
            # Listen for speech
            print("🎤 Listening for speech...")
            print("   Please speak something clearly...")
            
            success, text = recognizer.listen_for_speech(timeout=10, phrase_timeout=5)
            
            if success and text:
                print(f"✅ Recognized: '{text}'")
                print("🔊 Speaking it back...")
                
                # Speak back what was heard
                tts_success = tts.speak(text)
                
                if tts_success:
                    print("✅ TTS completed successfully")
                else:
                    print("❌ TTS failed")
                    return False
                    
            else:
                print("❌ No speech recognized")
                if test_count < max_tests:
                    print("   Trying again...")
                    continue
                else:
                    print("   Max tests reached")
                    return False
            
            # Ask if user wants to continue
            if test_count < max_tests:
                print("\nPress Enter to continue to next test, or 'q' to quit...")
                try:
                    user_input = input().strip().lower()
                    if user_input == 'q':
                        print("👋 Test stopped by user")
                        return True
                except KeyboardInterrupt:
                    print("\n👋 Test interrupted by user")
                    return True
        
        print("\n🎉 All integration tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"❌ Integration test failed: {e}")
        return False


def test_configuration_loading():
    """Test that configurations are loaded from YAML."""
    logger = setup_logging("home_assistant.test_config")
    
    print("\n🔧 Testing Configuration Loading")
    print("=" * 30)
    
    try:
        # Test TTS configuration
        tts = TextToSpeech()
        
        print(f"TTS Configuration:")
        print(f"  Voice ID: {tts.voice_id}")
        print(f"  Rate: {tts.rate}")
        print(f"  Volume: {tts.volume}")
        
        # Test recognizer configuration
        recognizer = SpeechRecognizer()
        
        if recognizer.is_available():
            print("✅ Speech recognizer available")
        else:
            print("❌ Speech recognizer not available")
        
        print("✅ Configuration loading test completed")
        return True
        
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """Run the integration tests."""
    logger = setup_logging("home_assistant.test_main")
    
    print("🎤🎵 Speech Recognition + TTS Integration Test Suite")
    print("=" * 60)
    
    # Test configuration loading first
    config_success = test_configuration_loading()
    
    if not config_success:
        print("❌ Configuration test failed. Stopping.")
        return
    
    # Test integration
    integration_success = test_recognizer_tts_integration()
    
    # Summary
    print(f"\n{'='*20} Test Summary {'='*20}")
    
    if config_success and integration_success:
        print("🎉 All tests passed!")
        print("✅ Configuration loading: PASS")
        print("✅ Speech recognition + TTS integration: PASS")
        print("\n💡 The system is working correctly with YAML configurations.")
    else:
        print("⚠️  Some tests failed:")
        if not config_success:
            print("❌ Configuration loading: FAIL")
        if not integration_success:
            print("❌ Speech recognition + TTS integration: FAIL")
        print("\n🔧 Please check:")
        print("   - Microphone permissions")
        print("   - PyAudio installation")
        print("   - pyttsx3 installation")
        print("   - config.yaml file")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        logger = setup_logging("home_assistant.test_main")
        logger.critical(f"Fatal error in test: {e}")
        print(f"�� Fatal error: {e}") 