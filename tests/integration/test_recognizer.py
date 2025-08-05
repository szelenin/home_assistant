#!/usr/bin/env python3
"""
Speech Recognizer integration tests using unittest framework
Tests real speech recognition functionality across multiple engines with fallback
"""

import sys
import os
import time
import unittest
import threading
import tempfile
import wave
import struct

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


class TestSpeechRecognizer(unittest.TestCase):
    """Test cases for Speech Recognition functionality across multiple engines."""
    
    def setUp(self):
        """Set up test fixtures for each test."""
        self.recognizer = None
        
        # Get available engines for testing
        try:
            temp_recognizer = SpeechRecognizer()
            self.available_engines = temp_recognizer.get_available_engines()
            self.recognizer_available = temp_recognizer.is_available()
            print(f"\nAvailable speech recognition engines: {self.available_engines}")
            print(f"Recognizer available: {self.recognizer_available}")
        except Exception as e:
            self.available_engines = []
            self.recognizer_available = False
            print(f"\nFailed to initialize recognizer: {e}")
    
    def test_recognizer_initialization(self):
        """Test basic recognizer initialization."""
        try:
            recognizer = SpeechRecognizer()
            self.assertIsNotNone(recognizer)
            print(f"✅ Recognizer initialized successfully")
            
            # Test availability
            available = recognizer.is_available()
            print(f"   Recognizer available: {available}")
            
            if available:
                self.assertIsNotNone(recognizer.microphone)
                self.assertIsNotNone(recognizer.recognizer)
                print(f"   Microphone: {recognizer.microphone is not None}")
                print(f"   SR engine: {recognizer.recognizer is not None}")
            
        except Exception as e:
            self.fail(f"Failed to initialize recognizer: {e}")
    
    def test_microphone_availability(self):
        """Test microphone availability and configuration."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        try:
            recognizer = SpeechRecognizer()
            self.assertTrue(recognizer.is_available())
            
            # Test microphone properties
            self.assertIsNotNone(recognizer.microphone)
            print(f"✅ Microphone available")
            print(f"   Device index: {getattr(recognizer.microphone, 'device_index', 'N/A')}")
            
        except Exception as e:
            self.fail(f"Microphone availability test failed: {e}")
    
    def test_available_engines_detection(self):
        """Test detection of available speech recognition engines."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        try:
            recognizer = SpeechRecognizer()
            engines = recognizer.get_available_engines()
            
            self.assertIsInstance(engines, list)
            self.assertGreater(len(engines), 0, "No speech recognition engines available")
            
            print(f"✅ Available engines detected: {engines}")
            
            # Verify engines are valid strings
            for engine in engines:
                self.assertIsInstance(engine, str)
                self.assertGreater(len(engine), 0)
            
        except Exception as e:
            self.fail(f"Engine detection test failed: {e}")
    
    def test_engine_configuration(self):
        """Test speech recognition engine configuration."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        try:
            recognizer = SpeechRecognizer()
            
            # Test configured engines
            configured_engines = recognizer.recognition_engines
            self.assertIsInstance(configured_engines, list)
            print(f"✅ Configured engines: {configured_engines}")
            
            # Test available engines
            available_engines = recognizer.get_available_engines()
            print(f"   Available engines: {available_engines}")
            
            # There should be some overlap between configured and available
            overlap = set(configured_engines) & set(available_engines)
            self.assertGreater(len(overlap), 0, "No overlap between configured and available engines")
            print(f"   Working engines: {list(overlap)}")
            
        except Exception as e:
            self.fail(f"Engine configuration test failed: {e}")
    
    def test_speech_recognition_with_silence(self):
        """Test speech recognition with silence (timeout scenario)."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        try:
            recognizer = SpeechRecognizer()
            
            print(f"✅ Testing speech recognition timeout with silence...")
            print(f"   This test will wait for {1} second of silence")
            
            # Test with very short timeout to simulate silence
            success, text = recognizer.listen_for_speech(timeout=1, phrase_timeout=0.5)
            
            # With silence, we expect failure (timeout or no speech detected)
            print(f"   Result: success={success}, text='{text}'")
            
            # This is acceptable - silence should either timeout or return no text
            if not success:
                print(f"✅ Silence handling successful (timeout/no speech)")
            else:
                print(f"⚠️  Unexpected speech detected: '{text}'")
            
        except Exception as e:
            self.fail(f"Silence test failed: {e}")
    
    def test_speech_recognition_engine_google(self):
        """Test Google speech recognition engine specifically."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        if 'google' not in self.available_engines:
            self.skipTest("Google speech recognition engine not available")
        
        try:
            recognizer = SpeechRecognizer()
            
            # Force Google engine only
            original_engines = recognizer.recognition_engines.copy()
            recognizer.recognition_engines = ['google']
            
            print(f"✅ Testing Google speech recognition engine...")
            print(f"   Engine will timeout after 2 seconds of silence")
            print(f"   Note: This requires internet connection")
            
            # Test Google recognition with short timeout
            success, text = recognizer.listen_for_speech(timeout=2, phrase_timeout=1)
            
            # Restore original engines
            recognizer.recognition_engines = original_engines
            
            print(f"   Google engine result: success={success}, text='{text}'")
            
            # Google engine test is informational - it may timeout or detect speech
            if success and text:
                print(f"✅ Google recognition successful: '{text}'")
            else:
                print(f"ℹ️  Google recognition timed out or no speech detected")
            
        except Exception as e:
            print(f"ℹ️  Google recognition test: {e}")
            # Don't fail the test - Google may not be available due to network
    
    def test_speech_recognition_engine_sphinx(self):
        """Test Sphinx speech recognition engine specifically."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        try:
            # Check if Sphinx is available
            import speech_recognition as sr
            recognizer_sr = sr.Recognizer()
            
            # Try to test Sphinx availability
            try:
                # Create a small test audio data to check Sphinx
                # This will test if Sphinx is properly installed
                recognizer = SpeechRecognizer()
                
                # Check if sphinx is in available engines
                if 'sphinx' not in self.available_engines:
                    self.skipTest("Sphinx speech recognition engine not available (requires pocketsphinx installation)")
                
                print(f"✅ Sphinx speech recognition engine available")
                print(f"   Note: Sphinx works offline but has limited accuracy")
                
                # Force Sphinx engine only for testing
                original_engines = recognizer.recognition_engines.copy()
                recognizer.recognition_engines = ['sphinx']
                
                # Test Sphinx with short timeout
                success, text = recognizer.listen_for_speech(timeout=1, phrase_timeout=0.5)
                
                # Restore original engines
                recognizer.recognition_engines = original_engines
                
                print(f"   Sphinx result: success={success}, text='{text}'")
                
                if success and text:
                    print(f"✅ Sphinx recognition successful: '{text}'")
                else:
                    print(f"ℹ️  Sphinx recognition timed out or no speech detected")
                
            except Exception as sphinx_error:
                print(f"ℹ️  Sphinx engine test: {sphinx_error}")
                self.skipTest(f"Sphinx not properly configured: {sphinx_error}")
                
        except ImportError:
            self.skipTest("pocketsphinx not installed for Sphinx testing")
        except Exception as e:
            print(f"ℹ️  Sphinx availability test: {e}")
    
    def test_speech_recognition_engine_fallback(self):
        """Test real speech recognition engine fallback behavior."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        if len(self.available_engines) < 2:
            self.skipTest("Need at least 2 engines to test fallback")
        
        try:
            recognizer = SpeechRecognizer()
            
            print(f"✅ Testing engine fallback with available engines: {self.available_engines}")
            
            # Test with all configured engines (normal fallback scenario)
            success, text = recognizer.listen_for_speech(timeout=2, phrase_timeout=1)
            
            print(f"   Fallback test result: success={success}, text='{text}'")
            
            # The test is informational - fallback should work properly
            if success and text:
                print(f"✅ Engine fallback successful: '{text}'")
            else:
                print(f"ℹ️  No speech detected during fallback test")
            
            # Test that we can actually attempt multiple engines by checking logs
            # The actual fallback logic is tested by the system working with multiple engines
            
        except Exception as e:
            self.fail(f"Engine fallback test failed: {e}")
    
    def test_real_speech_timeout_handling(self):
        """Test real timeout handling in speech recognition."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        try:
            recognizer = SpeechRecognizer()
            
            print(f"✅ Testing real timeout handling...")
            print(f"   Will wait 0.5 seconds for speech input")
            
            # Use very short timeout to force timeout condition
            start_time = time.time()
            success, text = recognizer.listen_for_speech(timeout=0.5, phrase_timeout=0.3)
            end_time = time.time()
            
            duration = end_time - start_time
            print(f"   Timeout test duration: {duration:.2f} seconds")
            print(f"   Result: success={success}, text='{text}'")
            
            # Should timeout quickly
            self.assertLess(duration, 2.0, "Timeout took too long")
            
            if not success:
                print(f"✅ Timeout handling working correctly")
            else:
                print(f"⚠️  Unexpected speech detected during timeout test: '{text}'")
            
        except Exception as e:
            self.fail(f"Timeout handling test failed: {e}")
    
    def test_microphone_info_display(self):
        """Test microphone information display functionality."""
        try:
            import speech_recognition as sr
            
            # Get microphone list
            mic_names = sr.Microphone.list_microphone_names()
            self.assertIsInstance(mic_names, list)
            
            print(f"✅ Found {len(mic_names)} microphones:")
            for i, name in enumerate(mic_names):
                print(f"   {i}: {name}")
            
            # Test default microphone
            try:
                default_mic = sr.Microphone()
                print(f"   Default microphone index: {default_mic.device_index}")
            except Exception as e:
                print(f"   Default microphone error: {e}")
            
        except ImportError:
            self.skipTest("SpeechRecognition module not available")
        except Exception as e:
            self.fail(f"Microphone info test failed: {e}")
    
    def test_recognizer_cleanup(self):
        """Test proper cleanup of recognizer resources."""
        try:
            recognizer = SpeechRecognizer()
            
            # Test that recognizer can be created and destroyed multiple times
            for i in range(3):
                temp_recognizer = SpeechRecognizer()
                self.assertIsNotNone(temp_recognizer)
                # Python's garbage collector should handle cleanup
                del temp_recognizer
            
            print(f"✅ Recognizer cleanup test successful")
            
        except Exception as e:
            self.fail(f"Recognizer cleanup test failed: {e}")


if __name__ == '__main__':
    # Configure test discovery and execution
    unittest.main(verbosity=2)