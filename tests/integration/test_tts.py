#!/usr/bin/env python3
"""
Enhanced TTS integration tests using unittest framework
Tests multiple TTS providers: pyttsx, espeak, piper
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

from home_assistant.speech.tts import TextToSpeech
from home_assistant.speech.base_tts_provider import TTSProviderUnavailableError


class TestTTS(unittest.TestCase):
    """Test cases for Text-to-Speech functionality across multiple providers."""
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Test with default provider (pyttsx)
        self.tts = TextToSpeech()
        
        # Get available providers for testing
        self.available_providers = self.tts.get_available_providers()
        print(f"\nAvailable TTS providers: {self.available_providers}")
    
    def test_basic_tts_functionality_pyttsx(self):
        """Test basic TTS functionality with pyttsx provider."""
        if not self.available_providers.get('pyttsx', False):
            self.skipTest("pyttsx provider not available")
        
        print("\n🎤 Testing Basic TTS Functionality (pyttsx)")
        print("=" * 50)
        
        tts = TextToSpeech('pyttsx')
        test_message = "Hello! Testing pyttsx TTS provider functionality."
        
        print(f"Speaking with pyttsx: {test_message}")
        success = tts.speak(test_message)
        
        self.assertTrue(success, "pyttsx TTS should complete successfully")
        print("✅ pyttsx TTS test completed successfully")
    
    def test_basic_tts_functionality_espeak(self):
        """Test basic TTS functionality with espeak provider."""
        if not self.available_providers.get('espeak', False):
            self.skipTest("espeak provider not available")
        
        print("\n🎤 Testing Basic TTS Functionality (espeak)")
        print("=" * 50)
        
        tts = TextToSpeech('espeak')
        test_message = "Hello! Testing espeak TTS provider functionality."
        
        print(f"Speaking with espeak: {test_message}")
        success = tts.speak(test_message)
        
        self.assertTrue(success, "espeak TTS should complete successfully")
        print("✅ espeak TTS test completed successfully")
    
    def test_basic_tts_functionality_piper(self):
        """Test basic TTS functionality with piper provider."""
        if not self.available_providers.get('piper', False):
            self.skipTest("piper provider not available")
        
        print("\n🎤 Testing Basic TTS Functionality (piper)")
        print("=" * 50)
        
        tts = TextToSpeech('piper')
        test_message = "Hello! Testing piper neural TTS provider functionality."
        
        print(f"Speaking with piper: {test_message}")
        success = tts.speak(test_message)
        
        self.assertTrue(success, "piper TTS should complete successfully")
        print("✅ piper TTS test completed successfully")
    
    def test_tts_provider_availability(self):
        """Test TTS provider availability and configuration."""
        print("\n🔧 Testing TTS Provider Availability")
        print("=" * 45)
        
        available_providers = self.tts.get_available_providers()
        self.assertIsInstance(available_providers, dict, "Should return provider availability dict")
        
        # Test each provider
        for provider_name, is_available in available_providers.items():
            print(f"  {provider_name}: {'✅ Available' if is_available else '❌ Not available'}")
            
            if is_available:
                try:
                    tts = TextToSpeech(provider_name)
                    self.assertTrue(tts.is_available(), f"{provider_name} should be available")
                    
                    # Test provider info
                    info = tts.get_provider_info()
                    self.assertIsInstance(info, dict, "Provider info should be a dict")
                    self.assertIn('name', info, "Provider info should include name")
                    self.assertIn('available', info, "Provider info should include availability")
                    
                    print(f"    {provider_name} info: {info}")
                except Exception as e:
                    self.fail(f"Failed to initialize {provider_name} provider: {e}")
        
        print("✅ TTS provider availability test passed")
    
    def test_multiple_phrases_pyttsx(self):
        """Test pyttsx provider with multiple phrases."""
        if not self.available_providers.get('pyttsx', False):
            self.skipTest("pyttsx provider not available")
        
        print("\n🎵 Testing Multiple Phrases (pyttsx)")
        print("=" * 42)
        
        tts = TextToSpeech('pyttsx')
        test_phrases = [
            "Welcome to pyttsx testing.",
            "This is phrase number two.",
            "Final test phrase for pyttsx."
        ]
        
        self._test_multiple_phrases(tts, test_phrases, 'pyttsx')
    
    def test_multiple_phrases_espeak(self):
        """Test espeak provider with multiple phrases."""
        if not self.available_providers.get('espeak', False):
            self.skipTest("espeak provider not available")
        
        print("\n🎵 Testing Multiple Phrases (espeak)")
        print("=" * 42)
        
        tts = TextToSpeech('espeak')
        test_phrases = [
            "Welcome to espeak testing.",
            "This is phrase number two.",
            "Final test phrase for espeak."
        ]
        
        self._test_multiple_phrases(tts, test_phrases, 'espeak')
    
    def test_multiple_phrases_piper(self):
        """Test piper provider with multiple phrases."""
        if not self.available_providers.get('piper', False):
            self.skipTest("piper provider not available")
        
        print("\n🎵 Testing Multiple Phrases (piper)")
        print("=" * 41)
        
        tts = TextToSpeech('piper')
        test_phrases = [
            "Welcome to piper neural TTS testing.",
            "This is phrase number two with piper.",
            "Final test phrase for piper neural TTS."
        ]
        
        self._test_multiple_phrases(tts, test_phrases, 'piper')
    
    def _test_multiple_phrases(self, tts, phrases, provider_name):
        """Helper method to test multiple phrases with a TTS provider."""
        success_count = 0
        total_phrases = len(phrases)
        
        for i, phrase in enumerate(phrases, 1):
            print(f"🔊 {provider_name} phrase {i}/{total_phrases}: {phrase}")
            
            success = tts.speak(phrase)
            self.assertTrue(success, f"{provider_name} phrase {i} should complete successfully")
            
            if success:
                success_count += 1
                print(f"✅ {provider_name} phrase {i} completed")
            else:
                print(f"❌ {provider_name} phrase {i} failed")
            
            # Brief delay between phrases
            if i < total_phrases:
                time.sleep(1)
        
        print(f"📊 {provider_name} Results: {success_count}/{total_phrases} phrases successful")
        self.assertEqual(success_count, total_phrases, f"All {provider_name} phrases should complete successfully")
        print(f"✅ {provider_name} multiple phrases test passed!")
    
    def test_voice_listing_pyttsx(self):
        """Test voice listing functionality for pyttsx."""
        if not self.available_providers.get('pyttsx', False):
            self.skipTest("pyttsx provider not available")
        
        print("\n🗣️ Testing Voice Listing (pyttsx)")
        print("=" * 39)
        
        tts = TextToSpeech('pyttsx')
        voices = tts.get_available_voices()
        
        self.assertIsInstance(voices, list, "Voices should be returned as a list")
        if voices:
            print(f"Found {len(voices)} pyttsx voices:")
            for voice in voices[:3]:  # Show first 3 voices
                print(f"  - {voice['name']} ({voice['id']})")
        else:
            print("No pyttsx voices found")
        
        print("✅ pyttsx voice listing test completed")
    
    def test_voice_listing_espeak(self):
        """Test voice listing functionality for espeak."""
        if not self.available_providers.get('espeak', False):
            self.skipTest("espeak provider not available")
        
        print("\n🗣️ Testing Voice Listing (espeak)")
        print("=" * 39)
        
        tts = TextToSpeech('espeak')
        voices = tts.get_available_voices()
        
        self.assertIsInstance(voices, list, "Voices should be returned as a list")
        if voices:
            print(f"Found {len(voices)} espeak voices:")
            for voice in voices[:3]:  # Show first 3 voices
                print(f"  - {voice['name']} ({voice['id']})")
        else:
            print("No espeak voices found")
        
        print("✅ espeak voice listing test completed")
    
    def test_voice_listing_piper(self):
        """Test voice listing functionality for piper."""
        if not self.available_providers.get('piper', False):
            self.skipTest("piper provider not available")
        
        print("\n🗣️ Testing Voice Listing (piper)")
        print("=" * 38)
        
        tts = TextToSpeech('piper')
        voices = tts.get_available_voices()
        
        self.assertIsInstance(voices, list, "Voices should be returned as a list")
        if voices:
            print(f"Found {len(voices)} piper models:")
            for voice in voices[:3]:  # Show first 3 models
                print(f"  - {voice['name']} ({voice['id']})")
        else:
            print("No piper models found")
        
        print("✅ piper voice listing test completed")
    
    def test_invalid_input_handling_all_providers(self):
        """Test invalid input handling across all available providers."""
        print("\n⚠️  Testing Invalid Input Handling (All Providers)")
        print("=" * 55)
        
        test_cases = [
            ("", "empty string"),
            ("   ", "whitespace-only string"),
        ]
        
        for provider_name, is_available in self.available_providers.items():
            if not is_available:
                print(f"⏭️  Skipping {provider_name} (not available)")
                continue
            
            print(f"\n🧪 Testing {provider_name} invalid input handling")
            tts = TextToSpeech(provider_name)
            
            for test_input, description in test_cases:
                success = tts.speak(test_input)
                self.assertFalse(success, f"{provider_name}: {description} should return False")
                print(f"  ✅ {provider_name}: {description} handled correctly")
        
        print("✅ All providers handle invalid input correctly")
    
    def test_configuration_methods_pyttsx(self):
        """Test configuration methods for pyttsx provider."""
        if not self.available_providers.get('pyttsx', False):
            self.skipTest("pyttsx provider not available")
        
        print("\n⚙️ Testing Configuration Methods (pyttsx)")
        print("=" * 44)
        
        tts = TextToSpeech('pyttsx')
        self._test_configuration_methods(tts, 'pyttsx')
    
    def test_configuration_methods_espeak(self):
        """Test configuration methods for espeak provider."""
        if not self.available_providers.get('espeak', False):
            self.skipTest("espeak provider not available")
        
        print("\n⚙️ Testing Configuration Methods (espeak)")
        print("=" * 44)
        
        tts = TextToSpeech('espeak')
        self._test_configuration_methods(tts, 'espeak')
    
    def test_configuration_methods_piper(self):
        """Test configuration methods for piper provider."""
        if not self.available_providers.get('piper', False):
            self.skipTest("piper provider not available")
        
        print("\n⚙️ Testing Configuration Methods (piper)")
        print("=" * 43)
        
        tts = TextToSpeech('piper')
        self._test_configuration_methods(tts, 'piper')
    
    def _test_configuration_methods(self, tts, provider_name):
        """Helper method to test configuration methods."""
        # Test rate setting
        success = tts.set_rate(200)
        self.assertIsInstance(success, bool, f"{provider_name}: set_rate should return boolean")
        print(f"✅ {provider_name}: Rate setting method works")
        
        # Test volume setting
        success = tts.set_volume(0.8)
        self.assertIsInstance(success, bool, f"{provider_name}: set_volume should return boolean")
        print(f"✅ {provider_name}: Volume setting method works")
        
        # Test voice setting (if voices are available)
        voices = tts.get_available_voices()
        if voices:
            test_voice = voices[0]['id']
            success = tts.set_voice(test_voice)
            self.assertIsInstance(success, bool, f"{provider_name}: set_voice should return boolean")
            print(f"✅ {provider_name}: Voice setting method works")
        else:
            print(f"ℹ️  {provider_name}: No voices available to test voice setting")


def run_tts_tests():
    """Run the TTS test suite and return success status."""
    print("🎤🎵 TTS Multi-Provider Integration Test Suite")
    print("=" * 60)
    print("Testing TTS providers: pyttsx, espeak, piper")
    print("Each provider will be tested independently with specific test methods")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTTS)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*20} Test Summary {'='*20}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 All TTS multi-provider tests passed!")
        print("✅ All available TTS providers working correctly")
    else:
        print("\n⚠️  Some TTS tests failed.")
        if result.failures:
            print("\nFailures:")
            for test, failure in result.failures:
                print(f"  - {test}: {failure}")
        if result.errors:
            print("\nErrors:")
            for test, error in result.errors:
                print(f"  - {test}: {error}")
        print("\nNote: Tests may be skipped if TTS providers are not available on this system")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🎤 TTS Multi-Provider Test Suite")
    print("This test suite will check all available TTS providers:")
    print("  - pyttsx (pyttsx3 with eSpeak-NG backend)")
    print("  - espeak (direct eSpeak-NG subprocess)")
    print("  - piper (neural TTS)")
    print("\nTests will be skipped automatically if providers are not available.\n")
    
    # Handle different execution modes
    if len(sys.argv) > 1 and 'unittest' in sys.argv[0]:
        # Running via unittest module discovery (python -m unittest discover)
        unittest.main()
    elif len(sys.argv) > 1 and sys.argv[1] == 'unittest':
        # Remove custom argument to avoid confusing unittest
        sys.argv.pop(1)
        unittest.main()
    else:
        # Run with custom output (direct execution)
        run_tts_tests()