#!/usr/bin/env python3
"""
Speech Recognizer integration tests using unittest framework
Tests speech recognition functionality across multiple engines with fallback
"""

import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock

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
    
    @patch('speech_recognition.Recognizer.listen')
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_mock_speech_recognition_google(self, mock_recognize, mock_listen):
        """Test speech recognition with mocked Google engine."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        # Mock audio data
        mock_audio = MagicMock()
        mock_listen.return_value = mock_audio
        mock_recognize.return_value = "hello world test"
        
        try:
            recognizer = SpeechRecognizer()
            success, text = recognizer.listen_for_speech(timeout=1, phrase_timeout=1)
            
            self.assertTrue(success)
            self.assertEqual(text, "hello world test")
            print(f"✅ Mock Google recognition successful: '{text}'")
            
            # Verify mocks were called
            mock_listen.assert_called_once()
            mock_recognize.assert_called_once_with(mock_audio)
            
        except Exception as e:
            self.fail(f"Mock Google recognition test failed: {e}")
    
    @patch('speech_recognition.Recognizer.listen')
    @patch('speech_recognition.Recognizer.recognize_sphinx')
    def test_mock_speech_recognition_sphinx(self, mock_recognize, mock_listen):
        """Test speech recognition with mocked Sphinx engine."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        # Mock audio data
        mock_audio = MagicMock()
        mock_listen.return_value = mock_audio
        mock_recognize.return_value = "sphinx recognition test"
        
        try:
            # Force sphinx engine by modifying recognition_engines
            recognizer = SpeechRecognizer()
            original_engines = recognizer.recognition_engines
            recognizer.recognition_engines = ['sphinx']
            
            success, text = recognizer.listen_for_speech(timeout=1, phrase_timeout=1)
            
            # Restore original engines
            recognizer.recognition_engines = original_engines
            
            self.assertTrue(success)
            self.assertEqual(text, "sphinx recognition test")
            print(f"✅ Mock Sphinx recognition successful: '{text}'")
            
            # Verify mocks were called
            mock_listen.assert_called_once()
            mock_recognize.assert_called_once_with(mock_audio)
            
        except Exception as e:
            self.fail(f"Mock Sphinx recognition test failed: {e}")
    
    @patch('speech_recognition.Recognizer.listen')
    def test_mock_recognition_fallback(self, mock_listen):
        """Test speech recognition engine fallback behavior."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        # Mock audio data
        mock_audio = MagicMock()
        mock_listen.return_value = mock_audio
        
        try:
            recognizer = SpeechRecognizer()
            
            # Mock first engine to fail, second to succeed
            with patch('speech_recognition.Recognizer.recognize_google') as mock_google, \
                 patch('speech_recognition.Recognizer.recognize_sphinx') as mock_sphinx:
                
                # First engine fails
                mock_google.side_effect = Exception("Google API error")
                
                # Second engine succeeds
                mock_sphinx.return_value = "fallback successful"
                
                # Set engines to test fallback
                original_engines = recognizer.recognition_engines
                recognizer.recognition_engines = ['google', 'sphinx']
                
                success, text = recognizer.listen_for_speech(timeout=1, phrase_timeout=1)
                
                # Restore original engines
                recognizer.recognition_engines = original_engines
                
                self.assertTrue(success)
                self.assertEqual(text, "fallback successful")
                print(f"✅ Engine fallback successful: '{text}'")
                
                # Verify both engines were attempted
                mock_google.assert_called_once()
                mock_sphinx.assert_called_once()
            
        except Exception as e:
            self.fail(f"Engine fallback test failed: {e}")
    
    @patch('speech_recognition.Recognizer.listen')
    def test_mock_recognition_timeout(self, mock_listen):
        """Test speech recognition timeout handling."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        # Mock timeout exception
        import speech_recognition as sr
        mock_listen.side_effect = sr.WaitTimeoutError("Timeout")
        
        try:
            recognizer = SpeechRecognizer()
            success, text = recognizer.listen_for_speech(timeout=1, phrase_timeout=1)
            
            self.assertFalse(success)
            self.assertIsNone(text)
            print(f"✅ Timeout handling successful: success={success}, text={text}")
            
        except Exception as e:
            self.fail(f"Timeout handling test failed: {e}")
    
    @patch('speech_recognition.Recognizer.listen')
    def test_mock_recognition_no_speech(self, mock_listen):
        """Test handling when no speech is detected."""
        if not self.recognizer_available:
            self.skipTest("Speech recognizer not available")
        
        # Mock no speech detected
        import speech_recognition as sr
        mock_audio = MagicMock()
        mock_listen.return_value = mock_audio
        
        try:
            with patch('speech_recognition.Recognizer.recognize_google') as mock_recognize:
                mock_recognize.side_effect = sr.UnknownValueError("No speech detected")
                
                recognizer = SpeechRecognizer()
                success, text = recognizer.listen_for_speech(timeout=1, phrase_timeout=1)
                
                self.assertFalse(success)
                self.assertIsNone(text)
                print(f"✅ No speech handling successful: success={success}, text={text}")
            
        except Exception as e:
            self.fail(f"No speech handling test failed: {e}")
    
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