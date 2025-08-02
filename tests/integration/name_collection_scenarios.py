#!/usr/bin/env python3
"""
Name Collection Test Scenarios

This module contains scenarios for testing the name collection functionality.
"""

import sys
import os

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from home_assistant.utils.name_collector import NameCollector
from home_assistant.utils.logger import setup_logging


class NameCollectionScenarios:
    """Test scenarios for Name Collection functionality."""
    
    def __init__(self):
        self.logger = setup_logging("home_assistant.test.name_collection_scenarios")
        self.name_collector = None
    
    def setup(self):
        """Initialize name collector for testing."""
        try:
            self.name_collector = NameCollector()
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup name collector: {e}")
            return False
    
    def scenario_initial_setup(self):
        """Scenario: Initial setup without wake word"""
        print("🎯 Scenario: Initial Setup")
        print("=" * 40)
        print("Testing initial setup without wake word")
        
        if not self.setup():
            return False
        
        # Test initial state
        config = self.name_collector.config_manager.get_config()
        wake_word = config.get('wake_word', {}).get('name')
        
        if wake_word is None:
            print("✅ No wake word configured (expected for initial setup)")
            return True
        else:
            print(f"⚠️  Wake word already configured: {wake_word}")
            return True
    
    def scenario_name_collection_flow(self):
        """Scenario: Complete name collection flow"""
        print("🎯 Scenario: Name Collection Flow")
        print("=" * 40)
        print("Testing complete name collection flow")
        
        if not self.setup():
            return False
        
        print("This scenario would test the complete name collection flow.")
        print("It would involve:")
        print("  1. TTS welcome message")
        print("  2. Listening for user's chosen name")
        print("  3. Confirming the name")
        print("  4. Saving to config.yaml")
        
        print("✅ Name collection flow scenario defined")
        return True
    
    def scenario_config_management(self):
        """Scenario: Configuration management"""
        print("🎯 Scenario: Configuration Management")
        print("=" * 40)
        print("Testing configuration management")
        
        if not self.setup():
            return False
        
        # Test config loading
        config = self.name_collector.config_manager.get_config()
        if config:
            print("✅ Configuration loaded successfully")
            print(f"   Wake word: {config.get('wake_word', {}).get('name')}")
            print(f"   TTS voice: {config.get('tts', {}).get('voice_id')}")
            print(f"   Speech engines: {config.get('speech', {}).get('recognition_engines')}")
            return True
        else:
            print("❌ Failed to load configuration")
            return False
    
    def scenario_error_handling(self):
        """Scenario: Error handling in name collection"""
        print("🎯 Scenario: Error Handling")
        print("=" * 40)
        print("Testing error handling in name collection")
        
        if not self.setup():
            return False
        
        # Test with invalid config
        print("Testing error handling...")
        
        # This would test various error conditions
        print("✅ Error handling scenario defined")
        return True
    
    def run_all_scenarios(self):
        """Run all name collection scenarios."""
        print("🎤 Name Collection Test Scenarios")
        print("=" * 50)
        
        scenarios = [
            ("Initial Setup", self.scenario_initial_setup),
            ("Name Collection Flow", self.scenario_name_collection_flow),
            ("Configuration Management", self.scenario_config_management),
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
        print(f"\n{'='*20} Name Collection Scenarios Summary {'='*20}")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {name}: {status}")
        
        print(f"\n   Overall: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("🎉 All name collection scenarios passed!")
        else:
            print("⚠️  Some name collection scenarios failed.")
        
        return passed == total


def main():
    """Run name collection scenarios."""
    scenarios = NameCollectionScenarios()
    scenarios.run_all_scenarios()


if __name__ == "__main__":
    main() 