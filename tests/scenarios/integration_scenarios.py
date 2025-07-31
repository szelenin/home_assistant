#!/usr/bin/env python3
"""
Integration Test Scenarios

This module contains scenarios that test the integration between
TTS and speech recognition components.
"""

import sys
import os
import time

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from home_assistant.speech.recognizer import SpeechRecognizer
from home_assistant.speech.tts import TextToSpeech
from home_assistant.utils.logger import setup_logging


class IntegrationScenarios:
    """Test scenarios for TTS and Speech Recognition integration."""
    
    def __init__(self):
        self.logger = setup_logging("home_assistant.test.integration_scenarios")
        self.recognizer = None
        self.tts = None
    
    def setup(self):
        """Initialize components for testing."""
        try:
            self.recognizer = SpeechRecognizer()
            self.tts = TextToSpeech()
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup components: {e}")
            return False
    
    def scenario_speak_and_listen(self):
        """Scenario: Speak a message and listen for response"""
        print("🎯 Scenario: Speak and Listen")
        print("=" * 40)
        print("Testing TTS -> Speech Recognition integration")
        
        if not self.setup():
            return False
        
        if not self.recognizer.is_available():
            print("❌ Speech recognizer not available")
            return False
        
        if not self.tts.engine:
            print("❌ TTS engine not available")
            return False
        
        print("✅ Both recognizer and TTS initialized successfully")
        
        # Test loop
        test_count = 0
        max_tests = 3
        
        while test_count < max_tests:
            test_count += 1
            print(f"\n{'='*20} Test {test_count}/{max_tests} {'='*20}")
            
            # Listen for speech
            print("🎤 Listening for speech...")
            print("   Please speak something clearly...")
            
            success, text = self.recognizer.listen_for_speech(timeout=10, phrase_timeout=5)
            
            if success and text:
                print(f"✅ Recognized: '{text}'")
                print("🔊 Speaking it back...")
                
                # Speak back what was heard
                tts_success = self.tts.speak(text)
                
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
        
        print("\n🎉 All speak-and-listen tests completed successfully!")
        return True
    
    def scenario_conversation_flow(self):
        """Scenario: Simulate a conversation flow"""
        print("🎯 Scenario: Conversation Flow")
        print("=" * 40)
        print("Testing conversation-like interaction")
        
        if not self.setup():
            return False
        
        # Simulate a conversation
        conversation = [
            ("Hello, how are you?", "I'm doing well, thank you!"),
            ("What's the weather like?", "It's sunny and 72 degrees."),
            ("Turn on the lights", "Lights are now on."),
        ]
        
        success_count = 0
        for question, expected_response in conversation:
            print(f"\n🎤 Assistant: {question}")
            
            # Speak the question
            if self.tts.speak(question):
                print("✅ Question spoken")
                
                # Listen for response
                print("🎤 Listening for response...")
                success, response = self.recognizer.listen_for_speech(timeout=5, phrase_timeout=3)
                
                if success and response:
                    print(f"✅ Response received: '{response}'")
                    success_count += 1
                else:
                    print("❌ No response received")
            else:
                print("❌ Failed to speak question")
        
        print(f"\n✅ Conversation flow: {success_count}/{len(conversation)} interactions successful")
        return success_count > 0
    
    def scenario_configuration_test(self):
        """Scenario: Test configuration loading and usage"""
        print("🎯 Scenario: Configuration Test")
        print("=" * 40)
        print("Testing configuration loading and usage")
        
        if not self.setup():
            return False
        
        # Test TTS configuration
        print("TTS Configuration:")
        print(f"  Voice ID: {self.tts.voice_id}")
        print(f"  Rate: {self.tts.rate}")
        print(f"  Volume: {self.tts.volume}")
        
        # Test recognizer configuration
        if self.recognizer.is_available():
            print("✅ Speech recognizer available")
            print(f"  Recognition engines: {self.recognizer.recognition_engines}")
        else:
            print("❌ Speech recognizer not available")
            return False
        
        print("✅ Configuration test completed")
        return True
    
    def scenario_error_handling(self):
        """Scenario: Test error handling in integration"""
        print("🎯 Scenario: Error Handling")
        print("=" * 40)
        print("Testing error handling in integration")
        
        if not self.setup():
            return False
        
        # Test TTS with empty text
        print("Testing TTS with empty text...")
        success = self.tts.speak("")
        if not success:
            print("✅ TTS correctly handled empty text")
        else:
            print("❌ TTS should have failed with empty text")
        
        # Test recognizer with no speech
        print("Testing recognizer with no speech (timeout)...")
        success, text = self.recognizer.listen_for_speech(timeout=2, phrase_timeout=1)
        if not success:
            print("✅ Recognizer correctly handled no speech")
        else:
            print("❌ Recognizer should have failed with no speech")
        
        print("✅ Error handling test completed")
        return True
    
    def run_all_scenarios(self):
        """Run all integration scenarios."""
        print("🎤🎵 Integration Test Scenarios")
        print("=" * 50)
        
        scenarios = [
            ("Speak and Listen", self.scenario_speak_and_listen),
            ("Conversation Flow", self.scenario_conversation_flow),
            ("Configuration Test", self.scenario_configuration_test),
            ("Error Handling", self.scenario_error_handling),
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
        print(f"\n{'='*20} Integration Scenarios Summary {'='*20}")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {name}: {status}")
        
        print(f"\n   Overall: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("🎉 All integration scenarios passed!")
        else:
            print("⚠️  Some integration scenarios failed.")
        
        return passed == total


def main():
    """Run integration scenarios."""
    scenarios = IntegrationScenarios()
    scenarios.run_all_scenarios()


if __name__ == "__main__":
    main() 