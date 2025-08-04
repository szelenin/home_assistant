#!/usr/bin/env python3
"""
Orchestrator Weather API Integration Test

Tests the orchestrator's ability to use native function calling:
1. Detect weather API calls from user input using native AI function calling
2. Execute proper HomeAPIs methods with correct parameters  
3. Format results naturally

Scenario: User asks "what is the weather today in Tampa?"
Expected: Orchestrator uses AI provider with function calling to detect API call, 
then executes get_weather(location="Tampa", units="metric", days=1)

This test maintains the same structure as the original but tests the new function calling system.
"""

import sys
import os
import unittest
from unittest.mock import Mock

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from home_assistant.ai.orchestrator import AIOrchestrator
from home_assistant.ai.base_provider import AIResponse, IntentType
from home_assistant.utils.config import ConfigManager
from home_assistant.apis.decorators import APIRegistry
from home_assistant.apis.home_apis import HomeAPIs


class TestOrchestratorWeatherAPIScenario(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Import HomeAPIs to trigger decorator registration
        from home_assistant.apis.home_apis import HomeAPIs
        
        # Use real ConfigManager
        self.config_manager = ConfigManager()
        
        # Set a test wake word if none exists
        if not self.config_manager.get_wake_word():
            self.config_manager.set_wake_word("TestAssistant")
        
        # Create real orchestrator
        self.orchestrator = AIOrchestrator(self.config_manager)
        
        # Only mock HomeAPIs to verify method calls while keeping everything else real
        self.mock_home_apis = Mock(spec=HomeAPIs)
        self.mock_home_apis.get_weather = Mock(return_value={
            "location": "Tampa",
            "temperature": 85,
            "description": "sunny",
            "forecast": "1 day forecast",
            "units": "metric"
        })
        
        # Replace the orchestrator's home_apis with our mock after initialization
        self.orchestrator._initialize_api_components()
        self.orchestrator.home_apis = self.mock_home_apis
    
    def test_orchestrator_function_calling_weather_detection_and_execution(self):
        """Test that orchestrator detects weather request using function calling and executes correct API.
        
        This test EXPECTS the AI to detect the weather API call using native function calling.
        If the function call is not detected, this test should FAIL.
        """
        # Check if AI providers are available
        available_providers = self.orchestrator.get_available_providers()
        if not any(available_providers.values()):
            self.skipTest("No AI providers available (missing API keys)")
        
        # Test user message that should trigger weather API via function calling
        user_message = "what is the weather today in Tampa?"
        
        # Execute chat with real AI provider using function calling
        response = self.orchestrator.chat(user_message)
        
        # Verify basic response properties
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.text)
        self.assertIsInstance(response.intent, IntentType)
        self.assertGreaterEqual(response.confidence, 0.0)
        self.assertLessEqual(response.confidence, 1.0)
        
        # THIS IS THE KEY ASSERTION: The function call MUST have been detected and executed
        self.assertTrue(
            self.mock_home_apis.get_weather.called,
            f"Expected AI to detect weather function call for message: '{user_message}'. "
            f"Instead got regular chat response: '{response.text}'. "
            f"This indicates the function calling system needs debugging."
        )
        
        print("✅ AI successfully detected weather function call")
        
        # Verify HomeAPIs method was called with correct parameters
        call_args = self.mock_home_apis.get_weather.call_args
        self.assertIsNotNone(call_args)
        
        # Check that location parameter was provided
        kwargs = call_args.kwargs if call_args.kwargs else {}
        args = call_args.args if call_args.args else []
        
        # Location should be in kwargs or first positional arg
        location_found = 'location' in kwargs or len(args) > 0
        self.assertTrue(location_found, "Location parameter should be provided to get_weather")
        
        # Verify response contains formatted weather information from our mock
        self.assertIn("Tampa", response.text)
        self.assertIn("sunny", response.text)
        
        # Verify function call results are in entities if available
        if hasattr(response, 'entities') and response.entities:
            if 'function_results' in response.entities:
                function_results = response.entities['function_results']
                self.assertGreater(len(function_results), 0, "Should have function call results")
        
        print(f"✅ Function executed with parameters: {call_args}")
        print(f"✅ Formatted response: {response.text}")
    
    def test_orchestrator_non_function_call_passthrough(self):
        """Test that non-function calls pass through normally with function calling system."""
        # Check if AI providers are available
        available_providers = self.orchestrator.get_available_providers()
        if not any(available_providers.values()):
            self.skipTest("No AI providers available (missing API keys)")
        
        # Test user message that should NOT trigger any function
        user_message = "Hello, how are you doing today?"
        
        # Execute chat
        try:
            response = self.orchestrator.chat(user_message)
            
            # Verify basic response properties
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.text)
            self.assertIsInstance(response.intent, IntentType)
            
            # Verify HomeAPIs was NOT called (no function detected)
            self.mock_home_apis.get_weather.assert_not_called()
            
            print(f"✅ Non-function message handled correctly: {response.text}")
            
        except Exception as e:
            self.fail(f"Non-function test failed with error: {e}")
    
    def test_orchestrator_function_call_error_handling(self):
        """Test error handling when function execution fails."""
        # Check if AI providers are available
        available_providers = self.orchestrator.get_available_providers()
        if not any(available_providers.values()):
            self.skipTest("No AI providers available (missing API keys)")
        
        # Configure mock to raise exception when called
        self.mock_home_apis.get_weather.side_effect = Exception("Weather service unavailable")
        
        # Test user message that might trigger function call
        user_message = "what is the weather in Tampa?"
        
        # Execute chat
        try:
            response = self.orchestrator.chat(user_message)
            
            # Verify basic response properties
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.text)
            
            # If function was called and failed, verify error handling
            if self.mock_home_apis.get_weather.called:
                print("✅ AI detected function call, testing error handling")
                # Verify error is handled gracefully
                self.assertIn("error", response.text.lower())
                self.assertIn("Weather service unavailable", response.text)
                print(f"✅ Error handled gracefully: {response.text}")
            else:
                print("ℹ️  AI did not detect function call - skipping error handling test")
                
        except Exception as e:
            self.fail(f"Error handling test failed with error: {e}")
    
    def test_orchestrator_function_calling_system_setup(self):
        """Test that the function calling system is properly set up."""
        # Verify API components are initialized correctly
        self.orchestrator._initialize_api_components()
        self.assertIsNotNone(self.orchestrator.api_registry)
        self.assertIsNotNone(self.orchestrator.api_executor)
        
        # Verify API definitions are available
        api_definitions = self.orchestrator.api_registry.get_all_apis()
        self.assertIn('get_weather', api_definitions)
        
        # Verify weather API definition structure
        weather_api = api_definitions['get_weather']
        self.assertEqual(weather_api.name, "Weather Information")
        self.assertIn('location', weather_api.parameters)
        self.assertTrue(weather_api.parameters['location']['required'])
        
        # Test function prompt generation
        from home_assistant.ai.function_prompts import AnthropicFunctionCallPrompt, OpenAIFunctionCallPrompt
        
        # Test Anthropic format
        anthropic_prompt = AnthropicFunctionCallPrompt(api_definitions)
        anthropic_tools = anthropic_prompt.get_function_definitions()
        self.assertEqual(len(anthropic_tools), 1)
        
        # Test OpenAI format
        openai_prompt = OpenAIFunctionCallPrompt(api_definitions)
        openai_functions = openai_prompt.get_function_definitions()
        self.assertEqual(len(openai_functions), 1)
        
        print("✅ Function calling system is properly set up")
        print(f"✅ Available APIs: {list(api_definitions.keys())}")
        print(f"✅ Function formats generated: Anthropic Tools, OpenAI Functions")


def run_orchestrator_weather_scenario():
    """Run the complete orchestrator function calling integration test."""
    print("🤖 Testing Function Calling Orchestrator Integration")
    print("-" * 60)
    print("FUNCTION CALLING INTEGRATION TEST:")
    print("  - Uses real ConfigManager and AI providers")
    print("  - Makes actual API calls to Anthropic/OpenAI with function calling")
    print("  - Only mocks HomeAPIs to verify correct method calls")
    print()
    print("Scenario: User asks 'what is the weather today in Tampa?'")
    print("Expected: AI function calling → Executes get_weather → Returns formatted response")
    print()
    
    # Run the test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestOrchestratorWeatherAPIScenario)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ Function calling orchestrator integration test passed!")
        print("The function calling orchestrator correctly:")
        print("  - Uses real AI providers with native function calling")
        print("  - Generates proper function definitions from API decorators")
        print("  - Executes HomeAPIs methods with correct parameters")
        print("  - Formats function results into natural language")
        print("  - Handles errors and missing providers gracefully")
    else:
        print("\n❌ Function calling orchestrator integration test failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print("\nNote: Tests may be skipped if AI provider API keys are not available")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_orchestrator_weather_scenario()