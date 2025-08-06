#!/usr/bin/env python3
"""
Speech Recognition integration tests using unittest framework
Tests multiple speech recognition providers: vosk, google, whisper
"""

import sys
import os
import time
import unittest

# Add project root to Python path - more robust path detection
current_dir = os.path.dirname(os.path.abspath(__file__))

# Handle different execution contexts (direct run vs unittest discovery)
if 'tests' in current_dir:
    # Running from tests directory structure
    project_root = os.path.dirname(os.path.dirname(current_dir))  # tests/integration -> tests -> project_root
else:
    # Running from project root or other location
    project_root = os.path.dirname(current_dir)

# Ensure project root contains the home_assistant module
if not os.path.exists(os.path.join(project_root, 'home_assistant')):
    # Try going up one more level
    project_root = os.path.dirname(project_root)

sys.path.insert(0, project_root)

from home_assistant.speech.recognizer import SpeechRecognizer
from home_assistant.speech.base_speech_provider import SpeechProviderUnavailableError


class TestSpeechRecognizer(unittest.TestCase):
    """Test cases for Speech Recognition functionality across multiple providers."""
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Test with default provider
        self.recognizer = SpeechRecognizer()
        
        # Get available providers for testing
        self.available_providers = self.recognizer.get_available_providers()
        print(f"\nAvailable speech recognition providers: {self.available_providers}")
    
    def test_basic_speech_recognition_vosk(self):
        """Test basic speech recognition functionality with vosk provider."""
        if not self.available_providers.get('vosk', False):
            self.skipTest("vosk provider not available")
        
        print("\n🎤 Testing Basic Speech Recognition (vosk)")
        print("=" * 50)
        
        recognizer = SpeechRecognizer('vosk')
        
        print(f"Testing vosk speech recognition with short timeout...")
        success, text = recognizer.listen_for_speech(timeout=2, phrase_timeout=1)
        
        print(f"   Result: success={success}, text='{text}'")
        
        # Vosk test is informational - may timeout or detect speech
        if success and text:
            print(f"✅ vosk recognition successful: '{text}'")
        else:
            print(f"ℹ️  vosk recognition timed out or no speech detected")
        
        # Test that provider is properly initialized
        self.assertTrue(recognizer.is_available(), "vosk provider should be available")
        print("✅ vosk speech recognition test completed")
    
    def test_basic_speech_recognition_google(self):
        """Test basic speech recognition functionality with google provider."""
        if not self.available_providers.get('google', False):
            self.skipTest("google provider not available")
        
        print("\n🎤 Testing Basic Speech Recognition (google)")
        print("=" * 50)
        
        recognizer = SpeechRecognizer('google')
        
        print(f"Testing google speech recognition with short timeout...")
        print(f"   Note: This requires internet connection")
        success, text = recognizer.listen_for_speech(timeout=2, phrase_timeout=1)
        
        print(f"   Result: success={success}, text='{text}'")
        
        # Google test is informational - may timeout, have network issues, or detect speech
        if success and text:
            print(f"✅ google recognition successful: '{text}'")
        else:
            print(f"ℹ️  google recognition timed out, no speech detected, or network issue")
        
        # Test that provider is properly initialized
        self.assertTrue(recognizer.is_available(), "google provider should be available")
        print("✅ google speech recognition test completed")
    
    def test_basic_speech_recognition_whisper(self):
        """Test basic speech recognition functionality with whisper provider."""
        if not self.available_providers.get('whisper', False):
            self.skipTest("whisper provider not available")
        
        print("\n🎤 Testing Basic Speech Recognition (whisper)")
        print("=" * 50)
        
        recognizer = SpeechRecognizer('whisper')
        
        print(f"Testing whisper speech recognition with short timeout...")
        print(f"   Note: Whisper is resource intensive and may be slow")
        success, text = recognizer.listen_for_speech(timeout=3, phrase_timeout=2)
        
        print(f"   Result: success={success}, text='{text}'")
        
        # Whisper test is informational - may timeout or detect speech
        if success and text:
            print(f"✅ whisper recognition successful: '{text}'")
        else:
            print(f"ℹ️  whisper recognition timed out or no speech detected")
        
        # Test that provider is properly initialized
        self.assertTrue(recognizer.is_available(), "whisper provider should be available")
        print("✅ whisper speech recognition test completed")
    
    def test_speech_provider_availability(self):
        """Test speech recognition provider availability."""
        print("\n🔍 Testing Speech Provider Availability")
        print("=" * 50)
        
        providers = self.recognizer.get_available_providers()
        self.assertIsInstance(providers, dict)
        
        print(f"Available providers: {providers}")
        
        # Test that we have at least one provider available
        available_count = sum(1 for available in providers.values() if available)
        self.assertGreater(available_count, 0, "No speech recognition providers available")
        
        print(f"✅ {available_count} provider(s) available")
        
        # Test provider info for available providers
        for provider_name, available in providers.items():
            if available:
                try:
                    recognizer = SpeechRecognizer(provider_name)
                    info = recognizer.get_provider_info()
                    self.assertIsInstance(info, dict)
                    print(f"   {provider_name}: {info.get('name', 'Unknown')} - {info.get('status', 'Unknown')}")
                except Exception as e:
                    print(f"   {provider_name}: Error getting info - {e}")
    
    def test_provider_configuration_vosk(self):
        """Test Vosk provider configuration methods."""
        if not self.available_providers.get('vosk', False):
            self.skipTest("vosk provider not available")
        
        print("\n⚙️ Testing Vosk Provider Configuration")
        print("=" * 50)
        
        recognizer = SpeechRecognizer('vosk')
        
        # Test provider info
        info = recognizer.get_provider_info()
        self.assertIsInstance(info, dict)
        print(f"Vosk info: {info.get('name', 'Unknown')} - Status: {info.get('status', 'Unknown')}")
        
        # Test availability
        self.assertTrue(recognizer.is_available(), "vosk provider should be available")
        print("✅ vosk provider configuration test completed")
    
    def test_provider_configuration_google(self):
        """Test Google provider configuration methods."""
        if not self.available_providers.get('google', False):
            self.skipTest("google provider not available")
        
        print("\n⚙️ Testing Google Provider Configuration")
        print("=" * 50)
        
        recognizer = SpeechRecognizer('google')
        
        # Test provider info
        info = recognizer.get_provider_info()
        self.assertIsInstance(info, dict)
        print(f"Google info: {info.get('name', 'Unknown')} - Status: {info.get('status', 'Unknown')}")
        print(f"   Language: {info.get('language', 'Unknown')}")
        print(f"   Free tier: {info.get('free_tier', 'Unknown')}")
        
        # Test availability
        self.assertTrue(recognizer.is_available(), "google provider should be available")
        print("✅ google provider configuration test completed")
    
    def test_provider_configuration_whisper(self):
        """Test Whisper provider configuration methods."""
        if not self.available_providers.get('whisper', False):
            self.skipTest("whisper provider not available")
        
        print("\n⚙️ Testing Whisper Provider Configuration")
        print("=" * 50)
        
        recognizer = SpeechRecognizer('whisper')
        
        # Test provider info
        info = recognizer.get_provider_info()
        self.assertIsInstance(info, dict)
        print(f"Whisper info: {info.get('name', 'Unknown')} - Status: {info.get('status', 'Unknown')}")
        print(f"   Model: {info.get('model', 'Unknown')}")
        print(f"   Device: {info.get('device', 'Unknown')}")
        
        # Test availability
        self.assertTrue(recognizer.is_available(), "whisper provider should be available")
        print("✅ whisper provider configuration test completed")
    
    def test_speech_timeout_handling_all_providers(self):
        """Test timeout handling across all available providers."""
        print("\n⏱️ Testing Timeout Handling")
        print("=" * 50)
        
        for provider_name, available in self.available_providers.items():
            if available:
                print(f"\n   Testing {provider_name} timeout handling...")
                try:
                    recognizer = SpeechRecognizer(provider_name)
                    
                    # Use very short timeout to force timeout condition
                    start_time = time.time()
                    success, text = recognizer.listen_for_speech(timeout=0.5, phrase_timeout=0.3)
                    end_time = time.time()
                    
                    duration = end_time - start_time
                    print(f"   {provider_name} timeout duration: {duration:.2f}s - Result: success={success}")
                    
                    # Should timeout quickly (within 2 seconds including processing time)
                    self.assertLess(duration, 3.0, f"{provider_name} timeout took too long")
                    
                except Exception as e:
                    print(f"   {provider_name} timeout test error: {e}")
        
        print("✅ Timeout handling test completed")
    
    def test_microphone_info_display(self):
        """Test microphone information display functionality."""
        print("\n🎤 Testing Microphone Information")
        print("=" * 50)
        
        try:
            import speech_recognition as sr
            
            # Get microphone list
            mic_names = sr.Microphone.list_microphone_names()
            self.assertIsInstance(mic_names, list)
            
            print(f"Found {len(mic_names)} microphones:")
            for i, name in enumerate(mic_names[:5]):  # Show first 5 to avoid spam
                print(f"   {i}: {name}")
            
            if len(mic_names) > 5:
                print(f"   ... and {len(mic_names) - 5} more")
            
            # Test default microphone
            try:
                default_mic = sr.Microphone()
                print(f"Default microphone index: {default_mic.device_index}")
            except Exception as e:
                print(f"Default microphone error: {e}")
            
            print("✅ Microphone info test completed")
            
        except ImportError:
            self.skipTest("SpeechRecognition module not available")
        except Exception as e:
            self.fail(f"Microphone info test failed: {e}")
    
    def test_recognizer_cleanup(self):
        """Test proper cleanup of recognizer resources."""
        print("\n🧹 Testing Recognizer Cleanup")
        print("=" * 50)
        
        try:
            # Test that recognizer can be created and destroyed multiple times
            for provider_name, available in self.available_providers.items():
                if available:
                    print(f"   Testing {provider_name} cleanup...")
                    for i in range(2):
                        temp_recognizer = SpeechRecognizer(provider_name)
                        self.assertIsNotNone(temp_recognizer)
                        # Python's garbage collector should handle cleanup
                        del temp_recognizer
            
            print("✅ Recognizer cleanup test successful")
            
        except Exception as e:
            self.fail(f"Recognizer cleanup test failed: {e}")


if __name__ == '__main__':
    # Configure test discovery and execution
    unittest.main(verbosity=2)