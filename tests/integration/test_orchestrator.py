#!/usr/bin/env python3
"""
Orchestrator Integration Tests

Tests the orchestrator's ability to use native function calling across different AI providers:
1. Detect function calls from user input using provider-native function calling
2. Execute proper HomeAPIs methods with correct parameters  
3. Format results naturally using 2-step AI call flow
4. Handle errors gracefully
5. Pass through non-function calls normally

This test suite runs the same scenarios across multiple AI providers
(Anthropic Claude, OpenAI GPT) to ensure provider-agnostic functionality.
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


class TestOrchestrator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Import HomeAPIs to trigger decorator registration
        from home_assistant.apis.home_apis import HomeAPIs
        
        # Use real ConfigManager
        self.config_manager = ConfigManager()
        
        # Set a test wake word if none exists
        if not self.config_manager.get_wake_word():
            self.config_manager.set_wake_word("TestAssistant")
        
        # Only mock HomeAPIs to verify method calls while keeping everything else real
        self.mock_home_apis = Mock(spec=HomeAPIs)
        self.mock_home_apis.get_weather = Mock(return_value={
            "location": "Tampa",
            "temperature": 85,
            "description": "sunny",
            "forecast": "1 day forecast",
            "units": "metric"
        })
    
    def _setup_orchestrator_for_provider(self, provider_name):
        """Setup orchestrator with specific provider."""
        # Force specific provider for this test
        ai_config = self.config_manager.get_ai_config()
        ai_config['provider'] = provider_name
        self.config_manager.config['ai'] = ai_config
        
        # Create real orchestrator with specific provider
        orchestrator = AIOrchestrator(self.config_manager)
        
        # Replace the orchestrator's home_apis with our mock after initialization
        orchestrator._initialize_api_components()
        orchestrator.home_apis = self.mock_home_apis
        
        return orchestrator
    
    def test_function_calling_weather_detection_and_execution_anthropic(self):
        """Test that orchestrator detects weather request using Anthropic function calling."""
        self._test_function_calling_weather_detection_and_execution("anthropic")
    
    def test_function_calling_weather_detection_and_execution_openai(self):
        """Test that orchestrator detects weather request using OpenAI function calling."""
        self._test_function_calling_weather_detection_and_execution("openai")
    
    def _test_function_calling_weather_detection_and_execution(self, provider_name):
        """Test that orchestrator detects weather request using function calling and executes correct API.
        
        This test EXPECTS the AI to detect the weather API call using native function calling.
        If the function call is not detected, this test should FAIL.
        """
        orchestrator = self._setup_orchestrator_for_provider(provider_name)
        
        # Check if specific provider is available
        available_providers = orchestrator.get_available_providers()
        if not available_providers.get(provider_name, False):
            self.skipTest(f"{provider_name} provider not available (missing API key)")
        
        # Test user message that should trigger weather API via function calling
        user_message = "what is the weather today in Tampa?"
        
        # Execute chat with real AI provider using function calling
        response = orchestrator.chat(user_message)
        
        # Verify basic response properties
        self.assertIsNotNone(response)
        self.assertIsNotNone(response.text)
        self.assertIsInstance(response.intent, IntentType)
        self.assertGreaterEqual(response.confidence, 0.0)
        self.assertLessEqual(response.confidence, 1.0)
        
        # THIS IS THE KEY ASSERTION: The function call MUST have been detected and executed
        self.assertTrue(
            self.mock_home_apis.get_weather.called,
            f"Expected {provider_name} to detect weather function call for message: '{user_message}'. "
            f"Instead got regular chat response: '{response.text}'. "
            f"This indicates the function calling system needs debugging."
        )
        
        print(f"✅ {provider_name} successfully detected weather function call")
        
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
    
    def test_non_function_call_passthrough_anthropic(self):
        """Test that non-function calls pass through normally with Anthropic."""
        self._test_non_function_call_passthrough("anthropic")
    
    def test_non_function_call_passthrough_openai(self):
        """Test that non-function calls pass through normally with OpenAI."""
        self._test_non_function_call_passthrough("openai")
    
    def _test_non_function_call_passthrough(self, provider_name):
        """Test that non-function calls pass through normally with function calling system."""
        orchestrator = self._setup_orchestrator_for_provider(provider_name)
        
        # Check if specific provider is available
        available_providers = orchestrator.get_available_providers()
        if not available_providers.get(provider_name, False):
            self.skipTest(f"{provider_name} provider not available (missing API key)")
        
        # Test user message that should NOT trigger any function
        user_message = "Hello, how are you doing today?"
        
        # Execute chat
        try:
            response = orchestrator.chat(user_message)
            
            # Verify basic response properties
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.text)
            self.assertIsInstance(response.intent, IntentType)
            
            # Verify HomeAPIs was NOT called (no function detected)
            self.mock_home_apis.get_weather.assert_not_called()
            
            print(f"✅ {provider_name} handled non-function message correctly: {response.text}")
            
        except Exception as e:
            self.fail(f"Non-function test failed with {provider_name}: {e}")
    
    def test_function_call_error_handling_anthropic(self):
        """Test error handling when function execution fails with Anthropic."""
        self._test_function_call_error_handling("anthropic")
    
    def test_function_call_error_handling_openai(self):
        """Test error handling when function execution fails with OpenAI."""
        self._test_function_call_error_handling("openai")
    
    def _test_function_call_error_handling(self, provider_name):
        """Test error handling when function execution fails."""
        orchestrator = self._setup_orchestrator_for_provider(provider_name)
        
        # Check if specific provider is available
        available_providers = orchestrator.get_available_providers()
        if not available_providers.get(provider_name, False):
            self.skipTest(f"{provider_name} provider not available (missing API key)")
        
        # Configure mock to raise exception when called
        self.mock_home_apis.get_weather.side_effect = Exception("Weather service unavailable")
        
        # Test user message that might trigger function call
        user_message = "what is the weather in Tampa?"
        
        # Execute chat
        try:
            response = orchestrator.chat(user_message)
            
            # Verify basic response properties
            self.assertIsNotNone(response)
            self.assertIsNotNone(response.text)
            
            # If function was called and failed, verify error handling
            if self.mock_home_apis.get_weather.called:
                print(f"✅ {provider_name} detected function call, testing error handling")
                # Verify error is handled gracefully
                self.assertIn("error", response.text.lower())
                self.assertIn("Weather service unavailable", response.text)
                print(f"✅ {provider_name} handled error gracefully: {response.text}")
            else:
                print(f"ℹ️  {provider_name} did not detect function call - skipping error handling test")
                
        except Exception as e:
            self.fail(f"Error handling test failed with {provider_name}: {e}")
    
    def test_function_calling_system_setup_anthropic(self):
        """Test that the function calling system is properly set up for Anthropic."""
        self._test_function_calling_system_setup("anthropic")
    
    def test_function_calling_system_setup_openai(self):
        """Test that the function calling system is properly set up for OpenAI."""
        self._test_function_calling_system_setup("openai")
    
    def _test_function_calling_system_setup(self, provider_name):
        """Test that the function calling system is properly set up."""
        orchestrator = self._setup_orchestrator_for_provider(provider_name)
        
        # Verify API components are initialized correctly
        orchestrator._initialize_api_components()
        self.assertIsNotNone(orchestrator.api_registry)
        self.assertIsNotNone(orchestrator.api_executor)
        
        # Verify API definitions are available
        api_definitions = orchestrator.api_registry.get_all_apis()
        self.assertIn('get_weather', api_definitions)
        
        # Verify weather API definition structure
        weather_api = api_definitions['get_weather']
        self.assertEqual(weather_api.name, "Weather Information")
        self.assertIn('location', weather_api.parameters)
        self.assertTrue(weather_api.parameters['location']['required'])
        
        # Test function prompt generation for the specific provider
        if provider_name == "anthropic":
            from home_assistant.ai.function_prompts import AnthropicFunctionCallPrompt
            prompt = AnthropicFunctionCallPrompt(api_definitions)
            function_defs = prompt.get_function_definitions()
            self.assertEqual(len(function_defs), 1)
            print(f"✅ {provider_name} function definitions generated correctly")
        elif provider_name == "openai":
            from home_assistant.ai.function_prompts import OpenAIFunctionCallPrompt
            prompt = OpenAIFunctionCallPrompt(api_definitions)
            function_defs = prompt.get_function_definitions()
            self.assertEqual(len(function_defs), 1)
            print(f"✅ {provider_name} function definitions generated correctly")
        
        print(f"✅ Function calling system properly set up for {provider_name}")
        print(f"✅ Available APIs: {list(api_definitions.keys())}")


def run_orchestrator_tests():
    """Run the complete orchestrator function calling integration test suite."""
    print("🤖 Testing Function Calling Orchestrator Integration (All Providers)")
    print("-" * 70)
    print("PROVIDER-AGNOSTIC INTEGRATION TESTS:")
    print("  - Tests both Anthropic Claude and OpenAI GPT providers")
    print("  - Uses real ConfigManager and AI providers")
    print("  - Makes actual API calls with native function calling")
    print("  - Only mocks HomeAPIs to verify correct method calls")
    print()
    print("Test scenarios:")
    print("  1. Function call detection and execution (weather API)")
    print("  2. Non-function call passthrough")
    print("  3. Function call error handling")
    print("  4. Function calling system setup validation")
    print()
    
    # Run the test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestOrchestrator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All orchestrator integration tests passed!")
        print("The function calling orchestrator correctly works with:")
        print("  - Multiple AI providers (Anthropic, OpenAI)")
        print("  - Native function calling for each provider")
        print("  - Provider-agnostic orchestration logic")
        print("  - Consistent error handling across providers")
    else:
        print("\n❌ Some orchestrator integration tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print("\nNote: Tests may be skipped if AI provider API keys are not available")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_orchestrator_tests()