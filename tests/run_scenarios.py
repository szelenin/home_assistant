#!/usr/bin/env python3
"""
Main Test Runner for Home Assistant Scenarios

This script runs all test scenarios in a standardized way.
"""

import sys
import os
import argparse

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from integration.tts_scenarios import TTSScenarios
from integration.recognizer_scenarios import RecognizerScenarios
from integration.integration_scenarios import IntegrationScenarios
from integration.name_collection_scenarios import NameCollectionScenarios


def run_all_scenarios():
    """Run all test scenarios."""
    print("🏠 Home Assistant Test Scenarios")
    print("=" * 60)
    
    scenario_classes = [
        ("TTS Scenarios", TTSScenarios),
        ("Recognizer Scenarios", RecognizerScenarios),
        ("Integration Scenarios", IntegrationScenarios),
        ("Name Collection Scenarios", NameCollectionScenarios),
    ]
    
    all_results = []
    
    for name, scenario_class in scenario_classes:
        print(f"\n{'='*25} {name} {'='*25}")
        try:
            scenarios = scenario_class()
            result = scenarios.run_all_scenarios()
            all_results.append((name, result))
        except Exception as e:
            print(f"❌ Failed to run {name}: {e}")
            all_results.append((name, False))
    
    # Final Summary
    print(f"\n{'='*25} FINAL SUMMARY {'='*25}")
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    
    for name, result in all_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\n   Overall: {passed}/{total} scenario categories passed")
    
    if passed == total:
        print("🎉 All scenario categories passed!")
        return True
    else:
        print("⚠️  Some scenario categories failed.")
        return False


def run_specific_scenario(scenario_name):
    """Run a specific scenario category."""
    scenario_map = {
        'tts': TTSScenarios,
        'recognizer': RecognizerScenarios,
        'integration': IntegrationScenarios,
        'name_collection': NameCollectionScenarios,
    }
    
    if scenario_name not in scenario_map:
        print(f"❌ Unknown scenario: {scenario_name}")
        print(f"Available scenarios: {', '.join(scenario_map.keys())}")
        return False
    
    scenario_class = scenario_map[scenario_name]
    scenarios = scenario_class()
    return scenarios.run_all_scenarios()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Home Assistant test scenarios")
    parser.add_argument(
        '--scenario', 
        choices=['tts', 'recognizer', 'integration', 'name_collection'],
        help='Run a specific scenario category'
    )
    
    args = parser.parse_args()
    
    if args.scenario:
        print(f"🎯 Running {args.scenario} scenarios...")
        success = run_specific_scenario(args.scenario)
        sys.exit(0 if success else 1)
    else:
        print("🎯 Running all scenarios...")
        success = run_all_scenarios()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 