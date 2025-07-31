#!/usr/bin/env python3
"""
Speech Recognizer Test Scenarios

This module contains scenarios for testing speech recognition functionality.
"""

import sys
import os
import time

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from home_assistant.speech.recognizer import SpeechRecognizer
from home_assistant.utils.logger import setup_logging


class RecognizerScenarios:
    """Test scenarios for Speech Recognition functionality."""
    
    def __init__(self):
        self.logger = setup_logging("home_assistant.test.recognizer_scenarios")
        self.recognizer = None
    
    def setup(self):
        """Initialize recognizer for testing."""
        try:
            self.recognizer = SpeechRecognizer()
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup recognizer: {e}")
            return False
    
    def scenario_microphone_initialization(self):
        """Scenario: Microphone initialization and availability"""
        print("🎯 Scenario: Microphone Initialization")
        print("=" * 40)
        print("Testing microphone initialization and availability")
        
        if not self.setup():
            return False
        
        if self.recognizer.is_available():
            print("✅ Microphone initialized successfully")
            print(f"   Microphone available: {self.recognizer.microphone is not None}")
            print(f"   Recognizer available: {self.recognizer.recognizer is not None}")
            return True
        else:
            print("❌ Microphone not available")
            print("   This might be due to:")
            print("   - Missing PyAudio (install with: pip install pyaudio)")
            print("   - No microphone connected")
            print("   - Microphone permissions not granted")
            return False
    
    def scenario_ambient_noise_adjustment(self):
        """Scenario: Ambient noise adjustment"""
        print("🎯 Scenario: Ambient Noise Adjustment")
        print("=" * 40)
        print("Testing ambient noise adjustment")
        
        if not self.setup():
            return False
        
        if self.recognizer.is_available():
            print("✅ Ambient noise adjustment completed")
            print("   The recognizer should now be calibrated for your environment")
            return True
        else:
            print("❌ Cannot test ambient noise adjustment - microphone not available")
            return False
    
    def scenario_single_speech_recognition(self, timeout=5):
        """Scenario: Single speech recognition"""
        print(f"🎯 Scenario: Single Speech Recognition (timeout: {timeout}s)")
        print("=" * 40)
        print("Testing single speech recognition")
        
        if not self.setup():
            return False
        
        if not self.recognizer.is_available():
            print("❌ Cannot test speech recognition - microphone not available")
            return False
        
        print("   Starting to listen in 3 seconds...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("🎤 SPEAK NOW!")
        success, text = self.recognizer.listen_for_speech(timeout=timeout, phrase_timeout=3)
        
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
    
    def scenario_continuous_recognition(self, max_phrases=3, timeout_per_phrase=3):
        """Scenario: Continuous speech recognition"""
        print(f"🎯 Scenario: Continuous Recognition ({max_phrases} phrases, {timeout_per_phrase}s each)")
        print("=" * 40)
        print("Testing continuous speech recognition")
        
        if not self.setup():
            return False
        
        if not self.recognizer.is_available():
            print("❌ Cannot test continuous recognition - microphone not available")
            return False
        
        phrase_count = 0
        successful_phrases = []
        
        print("🎤 Starting continuous listening...")
        
        for i in range(max_phrases):
            print(f"\n🎤 Listening for phrase {i+1}/{max_phrases}...")
            
            success, text = self.recognizer.listen_for_speech(
                timeout=timeout_per_phrase, 
                phrase_timeout=timeout_per_phrase//2
            )
            
            if success and text:
                phrase_count += 1
                successful_phrases.append(text)
                print(f"✅ Phrase {phrase_count}: '{text}'")
                
                if text.lower().strip() == 'stop':
                    print("🛑 Stop command detected, ending test.")
                    break
            else:
                print(f"⏰ Timeout for phrase {i+1} (no speech detected)")
        
        print(f"\n✅ Continuous recognition completed!")
        print(f"   Successful phrases: {phrase_count}/{max_phrases}")
        if successful_phrases:
            print(f"   Recognized: {', '.join(successful_phrases)}")
        
        return phrase_count > 0
    
    def scenario_engine_fallback(self):
        """Scenario: Engine fallback testing"""
        print("🎯 Scenario: Engine Fallback Testing")
        print("=" * 40)
        print("Testing speech recognition engine fallback")
        
        if not self.setup():
            return False
        
        # Test available engines
        available_engines = self.recognizer.get_available_engines()
        print(f"Available engines: {available_engines}")
        
        # Test configured engines
        configured_engines = self.recognizer.recognition_engines
        print(f"Configured engines: {configured_engines}")
        
        # Check if we have at least one working engine
        if available_engines:
            print("✅ At least one speech recognition engine is available")
            return True
        else:
            print("❌ No speech recognition engines available")
            return False
    
    def run_all_scenarios(self):
        """Run all recognizer scenarios."""
        print("🎤 Speech Recognizer Test Scenarios")
        print("=" * 50)
        
        scenarios = [
            ("Microphone Initialization", self.scenario_microphone_initialization),
            ("Ambient Noise Adjustment", self.scenario_ambient_noise_adjustment),
            ("Single Speech Recognition", lambda: self.scenario_single_speech_recognition(5)),
            ("Continuous Recognition", lambda: self.scenario_continuous_recognition(3, 3)),
            ("Engine Fallback", self.scenario_engine_fallback),
        ]
        
        results = []
        for name, scenario in scenarios:
            print(f"\n{'='*20} {name} {'='*20}")
            try:
                result = scenario()
                results.append((name, result))
            except Exception as e:
                self.logger.error(f"Scenario {name} failed with exception: {e}")
                results.append((name, False))
        
        # Summary
        print(f"\n{'='*20} Recognizer Scenarios Summary {'='*20}")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {name}: {status}")
        
        print(f"\n   Overall: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("🎉 All recognizer scenarios passed!")
        else:
            print("⚠️  Some recognizer scenarios failed.")
        
        return passed == total


def main():
    """Run recognizer scenarios."""
    scenarios = RecognizerScenarios()
    scenarios.run_all_scenarios()


if __name__ == "__main__":
    main() 