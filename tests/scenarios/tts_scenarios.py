#!/usr/bin/env python3
"""
TTS (Text-to-Speech) Test Scenarios

This module contains scenarios for testing TTS functionality.
"""

import sys
import os

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from home_assistant.speech.tts import TextToSpeech
from home_assistant.utils.logger import setup_logging


class TTSScenarios:
    """Test scenarios for Text-to-Speech functionality."""
    
    def __init__(self):
        self.logger = setup_logging("home_assistant.test.tts_scenarios")
        self.tts = None
    
    def setup(self):
        """Initialize TTS for testing."""
        try:
            self.tts = TextToSpeech()
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup TTS: {e}")
            return False
    
    def scenario_welcome_message(self):
        """Scenario: Welcome message from main.py"""
        print("🎯 Scenario: Welcome Message")
        print("=" * 40)
        print("Testing the exact welcome message from main.py")
        
        if not self.setup():
            return False
        
        message = "Hello! I'm your new Home Assistant. I need you to give me a name so I know when you're talking to me."
        
        print(f"Speaking: {message}")
        success = self.tts.speak(message)
        
        if success:
            print("✅ Welcome message scenario passed")
            return True
        else:
            print("❌ Welcome message scenario failed")
            return False
    
    def scenario_voice_configuration(self):
        """Scenario: Voice configuration and settings"""
        print("🎯 Scenario: Voice Configuration")
        print("=" * 40)
        print("Testing voice configuration and settings")
        
        if not self.setup():
            return False
        
        # Test voice listing
        print("Listing available voices...")
        self.tts.list_voices()
        
        # Test rate setting
        print("Testing speech rate...")
        success = self.tts.set_rate(150)
        if success:
            print("✅ Rate setting passed")
        else:
            print("❌ Rate setting failed")
            return False
        
        # Test volume setting
        print("Testing volume setting...")
        success = self.tts.set_volume(0.8)
        if success:
            print("✅ Volume setting passed")
        else:
            print("❌ Volume setting failed")
            return False
        
        print("✅ Voice configuration scenario passed")
        return True
    
    def scenario_short_phrases(self):
        """Scenario: Short phrases and commands"""
        print("🎯 Scenario: Short Phrases")
        print("=" * 40)
        print("Testing short phrases and commands")
        
        if not self.setup():
            return False
        
        phrases = [
            "Hello",
            "Good morning",
            "Turn on the lights",
            "What's the weather?",
            "Set temperature to 72 degrees"
        ]
        
        success_count = 0
        for phrase in phrases:
            print(f"Speaking: '{phrase}'")
            success = self.tts.speak(phrase)
            if success:
                success_count += 1
                print("✅ Phrase spoken successfully")
            else:
                print("❌ Phrase failed")
        
        print(f"✅ Short phrases scenario: {success_count}/{len(phrases)} passed")
        return success_count == len(phrases)
    
    def scenario_long_text(self):
        """Scenario: Long text and paragraphs"""
        print("🎯 Scenario: Long Text")
        print("=" * 40)
        print("Testing long text and paragraphs")
        
        if not self.setup():
            return False
        
        long_text = """
        This is a longer piece of text to test how the TTS system handles 
        extended speech. It should be able to process and speak longer 
        paragraphs without issues. This scenario tests the robustness of 
        the text-to-speech engine when dealing with substantial amounts of text.
        """
        
        print("Speaking long text...")
        success = self.tts.speak(long_text.strip())
        
        if success:
            print("✅ Long text scenario passed")
            return True
        else:
            print("❌ Long text scenario failed")
            return False
    
    def run_all_scenarios(self):
        """Run all TTS scenarios."""
        print("🎤 TTS Test Scenarios")
        print("=" * 50)
        
        scenarios = [
            ("Welcome Message", self.scenario_welcome_message),
            ("Voice Configuration", self.scenario_voice_configuration),
            ("Short Phrases", self.scenario_short_phrases),
            ("Long Text", self.scenario_long_text),
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
        print(f"\n{'='*20} TTS Scenarios Summary {'='*20}")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {name}: {status}")
        
        print(f"\n   Overall: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("🎉 All TTS scenarios passed!")
        else:
            print("⚠️  Some TTS scenarios failed.")
        
        return passed == total


def main():
    """Run TTS scenarios."""
    scenarios = TTSScenarios()
    scenarios.run_all_scenarios()


if __name__ == "__main__":
    main() 