#!/usr/bin/env python3
"""
Wake Word Detector Integration Tests

Tests each wake word provider individually, following the same pattern as speech recognition tests.
Each provider is tested in isolation to avoid interference and provide clear failure messages.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from home_assistant.wake_word.detector import WakeWordDetector
from home_assistant.wake_word.base_wake_word_provider import WakeWordProviderUnavailableError, WakeWordConfigurationError


class WakeWordDetectorIntegrationTests(unittest.TestCase):
    """Integration tests for wake word detection providers."""

    def setUp(self):
        """Set up test configuration."""
        # Create a test wake word
        self.test_wake_word = "TestAssistant"
        
    def test_openwakeword_provider_initialization(self):
        """Test OpenWakeWord provider initialization and availability."""
        try:
            detector = WakeWordDetector('openwakeword')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.fail(f"Failed to initialize OpenWakeWord provider: {e}")
        
        # Check provider info
        info = detector.get_provider_info()
        self.assertIsNotNone(info)
        self.assertEqual(info['provider_name'], 'openwakeword')
        self.assertIn('name', info)
        self.assertEqual(info['name'], 'OpenWakeWord')
        
        # Check if provider reports availability correctly
        is_available = detector.is_available()
        self.assertIsInstance(is_available, bool)
        
        if not is_available:
            print("ℹ️  OpenWakeWord not available - likely missing models or dependencies")
        else:
            print("✅ OpenWakeWord provider available")
        
        detector.cleanup()

    def test_openwakeword_wake_word_validation(self):
        """Test OpenWakeWord wake word validation."""
        try:
            detector = WakeWordDetector('openwakeword')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.skipTest(f"OpenWakeWord provider not available: {e}")
        
        # Valid wake words
        self.assertTrue(detector.provider.validate_wake_word("TestAssistant"))
        self.assertTrue(detector.provider.validate_wake_word("Hey Computer"))
        self.assertTrue(detector.provider.validate_wake_word("Alexa"))
        
        # Invalid wake words
        self.assertFalse(detector.provider.validate_wake_word(""))
        self.assertFalse(detector.provider.validate_wake_word("A"))  # Too short
        self.assertFalse(detector.provider.validate_wake_word("This is way too long for a wake word"))
        
        detector.cleanup()

    def test_openwakeword_detection_functionality(self):
        """Test OpenWakeWord detection functionality."""
        try:
            detector = WakeWordDetector('openwakeword')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.skipTest(f"OpenWakeWord provider not available: {e}")
        
        if not detector.is_available():
            self.skipTest("OpenWakeWord provider not available - missing models or dependencies")
        
        print("🎤 Testing OpenWakeWord detection (this test requires working audio)")
        print(f"   Try saying the wake word: '{self.test_wake_word}' within 5 seconds...")
        
        try:
            # Test with short timeout for CI/automated testing
            detected, confidence = detector.listen_for_wake_word(self.test_wake_word, timeout=5)
            
            print(f"   Detection result: {detected}, Confidence: {confidence:.3f}")
            
            # The test passes if it doesn't crash - actual detection depends on audio environment
            self.assertIsInstance(detected, bool)
            self.assertIsInstance(confidence, (int, float))
            
            if detected:
                print("✅ Wake word detected successfully!")
                self.assertGreater(confidence, 0.0)
            else:
                print("ℹ️  No wake word detected (expected in automated testing)")
                
        except Exception as e:
            self.fail(f"OpenWakeWord detection failed with error: {e}")
        
        detector.cleanup()

    def test_porcupine_provider_initialization(self):
        """Test Porcupine provider initialization and availability."""
        try:
            detector = WakeWordDetector('porcupine')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.skipTest(f"Porcupine provider not available: {e}")
        
        # Check provider info
        info = detector.get_provider_info()
        self.assertIsNotNone(info)
        self.assertEqual(info['provider_name'], 'porcupine')
        self.assertIn('name', info)
        
        # Check if provider reports availability correctly
        is_available = detector.is_available()
        self.assertIsInstance(is_available, bool)
        
        if not is_available:
            print("ℹ️  Porcupine not available - likely missing access key or dependencies")
        else:
            print("✅ Porcupine provider available")
        
        detector.cleanup()

    def test_porcupine_detection_functionality(self):
        """Test Porcupine detection functionality."""
        try:
            detector = WakeWordDetector('porcupine')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.skipTest(f"Porcupine provider not available: {e}")
        
        if not detector.is_available():
            self.skipTest("Porcupine provider not available - missing access key or dependencies")
        
        print("🎤 Testing Porcupine detection (this test requires working audio and API key)")
        print(f"   Try saying the wake word: '{self.test_wake_word}' within 5 seconds...")
        
        try:
            # Test with short timeout for CI/automated testing
            detected, confidence = detector.listen_for_wake_word(self.test_wake_word, timeout=5)
            
            print(f"   Detection result: {detected}, Confidence: {confidence:.3f}")
            
            # The test passes if it doesn't crash - actual detection depends on audio environment
            self.assertIsInstance(detected, bool)
            self.assertIsInstance(confidence, (int, float))
            
            if detected:
                print("✅ Wake word detected successfully!")
                self.assertGreater(confidence, 0.0)
            else:
                print("ℹ️  No wake word detected (expected in automated testing)")
                
        except Exception as e:
            self.fail(f"Porcupine detection failed with error: {e}")
        
        detector.cleanup()

    def test_pocketsphinx_provider_initialization(self):
        """Test PocketSphinx provider initialization and availability."""
        try:
            detector = WakeWordDetector('pocketsphinx')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.skipTest(f"PocketSphinx provider not available: {e}")
        
        # Check provider info
        info = detector.get_provider_info()
        self.assertIsNotNone(info)
        self.assertEqual(info['provider_name'], 'pocketsphinx')
        self.assertIn('name', info)
        
        # Check if provider reports availability correctly
        is_available = detector.is_available()
        self.assertIsInstance(is_available, bool)
        
        if not is_available:
            print("ℹ️  PocketSphinx not available - likely missing models or dependencies")
        else:
            print("✅ PocketSphinx provider available")
        
        detector.cleanup()

    def test_pocketsphinx_detection_functionality(self):
        """Test PocketSphinx detection functionality."""
        try:
            detector = WakeWordDetector('pocketsphinx')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.skipTest(f"PocketSphinx provider not available: {e}")
        
        if not detector.is_available():
            self.skipTest("PocketSphinx provider not available - missing models or dependencies")
        
        print("🎤 Testing PocketSphinx detection (this test requires working audio)")
        print(f"   Try saying the wake word: '{self.test_wake_word}' within 5 seconds...")
        
        try:
            # Test with short timeout for CI/automated testing
            detected, confidence = detector.listen_for_wake_word(self.test_wake_word, timeout=5)
            
            print(f"   Detection result: {detected}, Confidence: {confidence:.3f}")
            
            # The test passes if it doesn't crash - actual detection depends on audio environment
            self.assertIsInstance(detected, bool)
            self.assertIsInstance(confidence, (int, float))
            
            if detected:
                print("✅ Wake word detected successfully!")
                self.assertGreater(confidence, 0.0)
            else:
                print("ℹ️  No wake word detected (expected in automated testing)")
                
        except Exception as e:
            self.fail(f"PocketSphinx detection failed with error: {e}")
        
        detector.cleanup()

    def test_provider_availability(self):
        """Test availability detection for all providers."""
        try:
            detector = WakeWordDetector()  # Use default provider
            available_providers = detector.get_available_providers()
            
            self.assertIsInstance(available_providers, dict)
            self.assertIn('openwakeword', available_providers)
            self.assertIn('porcupine', available_providers)
            self.assertIn('pocketsphinx', available_providers)
            
            print("Wake word provider availability:")
            for provider, available in available_providers.items():
                status = "✅ Available" if available else "❌ Not available"
                print(f"  {provider}: {status}")
            
            # At least one provider should be testable (even if not fully functional)
            has_any_provider = any(available_providers.values())
            if not has_any_provider:
                print("⚠️  No wake word providers available - this may indicate missing dependencies")
            
        except Exception as e:
            self.fail(f"Provider availability check failed: {e}")

    def test_invalid_provider(self):
        """Test handling of invalid provider name."""
        with self.assertRaises((WakeWordConfigurationError, ValueError)):
            WakeWordDetector('nonexistent_provider')

    def test_wake_word_detection_timeout(self):
        """Test wake word detection timeout functionality."""
        try:
            detector = WakeWordDetector('openwakeword')
        except (ImportError, WakeWordProviderUnavailableError) as e:
            self.skipTest(f"OpenWakeWord provider not available: {e}")
        
        if not detector.is_available():
            self.skipTest("OpenWakeWord provider not available")
        
        print("⏱️  Testing wake word detection timeout (should complete in ~2 seconds)")
        
        import time
        start_time = time.time()
        
        # Test timeout functionality - should return False, 0.0 after timeout
        detected, confidence = detector.listen_for_wake_word(self.test_wake_word, timeout=2)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should have timed out
        self.assertFalse(detected)
        self.assertEqual(confidence, 0.0)
        
        # Should have taken approximately the timeout duration (with some tolerance)
        self.assertGreaterEqual(elapsed, 1.8)  # At least 1.8 seconds
        self.assertLessEqual(elapsed, 3.0)     # No more than 3 seconds
        
        print(f"✅ Timeout test completed in {elapsed:.1f} seconds")
        
        detector.cleanup()


if __name__ == '__main__':
    print("🎤 Wake Word Detector Integration Tests")
    print("=" * 50)
    print()
    
    # Run tests with detailed output
    unittest.main(verbosity=2, buffer=True)