#!/usr/bin/env python3
"""
AI Provider Test Script

Tests the AI provider system with specific scenarios:
1. Weather question: "What's the weather in Tampa tomorrow?"
2. Name question: "What is your name?"
"""

import sys
import os
from unittest.mock import patch

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from home_assistant.ai.orchestrator import AIOrchestrator
from home_assistant.ai.base_provider import IntentType
from home_assistant.utils.config import ConfigManager
from home_assistant.utils.logger import setup_logging


def test_weather_scenario():
    """Test scenario: Ask about weather in Tampa tomorrow."""
    print("🌤️  Testing Weather Scenario")
    print("-" * 40)
    
    # Initialize components
    config_manager = ConfigManager()
    
    # Set a test wake word if none exists
    if not config_manager.get_wake_word():
        config_manager.set_wake_word("TestAssistant")
    
    orchestrator = AIOrchestrator(config_manager)
    
    # Test message
    message = "What's the weather in Tampa tomorrow?"
    print(f"User: {message}")
    
    # Test intent classification
    intent = orchestrator.classify_intent(message)
    print(f"Classified Intent: {intent.value}")
    
    # Test device API translation
    api_call = orchestrator.translate_to_device_api(message, intent)
    print(f"API Translation: {api_call}")
    
    # Test full chat response (only if providers are available)
    available_providers = orchestrator.get_available_providers()
    print(f"Available Providers: {available_providers}")
    
    if any(available_providers.values()):
        try:
            response = orchestrator.chat(message)
            print(f"AI Response: {response.text}")
            print(f"Response Intent: {response.intent.value}")
            print(f"Confidence: {response.confidence:.2f}")
            if response.entities:
                print(f"Entities: {response.entities}")
        except Exception as e:
            print(f"AI Response Error: {e}")
    else:
        print("No AI providers available (missing API keys)")
    
    print()


def test_name_scenario():
    """Test scenario: Ask about the assistant's name."""
    print("🤖 Testing Name Scenario")
    print("-" * 40)
    
    # Initialize components
    config_manager = ConfigManager()
    
    # Set a test wake word
    test_wake_word = "TestAssistant"
    config_manager.set_wake_word(test_wake_word)
    
    orchestrator = AIOrchestrator(config_manager)
    
    # Test message
    message = "What is your name?"
    print(f"User: {message}")
    
    # Test intent classification
    intent = orchestrator.classify_intent(message)
    print(f"Classified Intent: {intent.value}")
    
    # Test device API translation
    api_call = orchestrator.translate_to_device_api(message, intent)
    print(f"API Translation: {api_call}")
    
    # Test full chat response (only if providers are available)
    available_providers = orchestrator.get_available_providers()
    print(f"Available Providers: {available_providers}")
    
    if any(available_providers.values()):
        try:
            response = orchestrator.chat(message)
            print(f"AI Response: {response.text}")
            print(f"Response Intent: {response.intent.value}")
            print(f"Confidence: {response.confidence:.2f}")
            
            # Check if response mentions the wake word
            if test_wake_word.lower() in response.text.lower():
                print("✅ Response correctly mentions wake word")
            else:
                print("⚠️  Response doesn't mention wake word")
        except Exception as e:
            print(f"AI Response Error: {e}")
    else:
        print("No AI providers available (missing API keys)")
    
    print()


def test_provider_switching():
    """Test switching between AI providers."""
    print("🔄 Testing Provider Switching")
    print("-" * 40)
    
    config_manager = ConfigManager()
    orchestrator = AIOrchestrator(config_manager)
    
    available_providers = orchestrator.get_available_providers()
    print(f"Available Providers: {available_providers}")
    
    # Test switching to each available provider
    for provider_name, is_available in available_providers.items():
        if is_available:
            print(f"Switching to {provider_name}...")
            success = orchestrator.switch_provider(provider_name)
            if success:
                print(f"✅ Successfully switched to {provider_name}")
                
                # Test a simple message with this provider
                try:
                    response = orchestrator.chat("Hello")
                    print(f"Test response: {response.text[:50]}...")
                except Exception as e:
                    print(f"Error testing {provider_name}: {e}")
            else:
                print(f"❌ Failed to switch to {provider_name}")
        else:
            print(f"⚠️  {provider_name} is not available")
    
    print()


def test_intent_classification():
    """Test intent classification with various messages."""
    print("🎯 Testing Intent Classification")
    print("-" * 40)
    
    config_manager = ConfigManager()
    orchestrator = AIOrchestrator(config_manager)
    
    test_messages = [
        ("What's the weather like?", IntentType.WEATHER),
        ("Turn on the lights", IntentType.DEVICE_CONTROL),
        ("What is your name?", IntentType.PERSONAL_INFO),
        ("What time is it?", IntentType.TIME_DATE),
        ("How are you doing?", IntentType.QUESTION),
        ("Hello there", IntentType.GENERAL_CHAT)
    ]
    
    for message, expected_intent in test_messages:
        classified_intent = orchestrator.classify_intent(message)
        status = "✅" if classified_intent == expected_intent else "❌"
        print(f"{status} '{message}' -> {classified_intent.value} (expected: {expected_intent.value})")
    
    print()


def main():
    """Run all AI provider tests."""
    logger = setup_logging("home_assistant.test_ai")
    
    print("🤖 AI Provider System Test")
    print("=" * 50)
    print("This test will verify the AI provider functionality")
    print("including intent recognition and response generation.\n")
    
    # Check configuration
    config_manager = ConfigManager()
    ai_config = config_manager.config.get('ai', {})
    
    print("Configuration Status:")
    print(f"  Provider: {ai_config.get('provider', 'not set')}")
    print(f"  Anthropic API Key: {'set' if ai_config.get('anthropic_api_key') else 'not set'}")
    print(f"  OpenAI API Key: {'set' if ai_config.get('openai_api_key') else 'not set'}")
    print()
    
    if not ai_config.get('anthropic_api_key') and not ai_config.get('openai_api_key'):
        print("⚠️  WARNING: No API keys configured!")
        print("   Add your API keys to config.yaml to test full functionality:")
        print("   ai:")
        print("     anthropic_api_key: 'your-key-here'")
        print("     openai_api_key: 'your-key-here'")
        print()
    
    # Run all tests
    try:
        test_intent_classification()
        test_weather_scenario()
        test_name_scenario()
        test_provider_switching()
        
        print("🎉 All tests completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        logger.error(f"Test error: {e}")


if __name__ == "__main__":
    main()