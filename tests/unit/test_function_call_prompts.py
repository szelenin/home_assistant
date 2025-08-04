#!/usr/bin/env python3
"""
Function Call Prompts Test

Tests the function call prompt generation system for both Anthropic and OpenAI formats.
Uses real HomeAPIs to verify prompt structure and parameter conversion.
"""

import unittest

from home_assistant.ai.function_prompts import (
    AnthropicFunctionCallPrompt, 
    OpenAIFunctionCallPrompt
)
from home_assistant.apis.decorators import APIRegistry


class TestFunctionCallPrompts(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures - use real HomeAPIs to get actual API definitions."""
        # Import HomeAPIs to trigger decorator registration (happens at import time)
        from home_assistant.apis.home_apis import HomeAPIs
        
        # Get the registered API definitions
        self.api_definitions = APIRegistry.get_all_apis()
        
        # Verify we have the weather API registered
        self.assertIn('get_weather', self.api_definitions)
    
    def test_anthropic_function_prompt_format(self):
        """Test Anthropic tools format generation."""
        prompt = AnthropicFunctionCallPrompt(self.api_definitions)
        tools = prompt.get_function_definitions()
        
        # Should have exactly one tool (weather API)
        self.assertEqual(len(tools), 1)
        
        # Verify tool structure
        weather_tool = tools[0]
        self.assertEqual(weather_tool['name'], 'get_weather')
        self.assertEqual(weather_tool['description'], "Get current weather conditions and forecast for any location. Use this when users ask about weather, temperature, rain, forecasts, or outdoor conditions.")
        
        # Verify input_schema structure
        self.assertIn('input_schema', weather_tool)
        input_schema = weather_tool['input_schema']
        self.assertEqual(input_schema['type'], 'object')
        self.assertIn('properties', input_schema)
        self.assertIn('required', input_schema)
        
        # Verify properties (all should be strings)
        properties = input_schema['properties']
        expected_params = ['location', 'units', 'days']
        
        for param_name in expected_params:
            self.assertIn(param_name, properties)
            self.assertEqual(properties[param_name]['type'], 'string')
            self.assertIn('description', properties[param_name])
        
        # Verify required parameters
        required = input_schema['required']
        self.assertIn('location', required)  # location is required
        self.assertNotIn('units', required)   # units has default
        self.assertNotIn('days', required)    # days has default
    
    def test_openai_function_prompt_format(self):
        """Test OpenAI functions format generation."""
        prompt = OpenAIFunctionCallPrompt(self.api_definitions)
        functions = prompt.get_function_definitions()
        
        # Should have exactly one function (weather API)
        self.assertEqual(len(functions), 1)
        
        # Verify function structure
        weather_func = functions[0]
        self.assertEqual(weather_func['name'], 'get_weather')
        self.assertEqual(weather_func['description'], "Get current weather conditions and forecast for any location. Use this when users ask about weather, temperature, rain, forecasts, or outdoor conditions.")
        
        # Verify parameters structure
        self.assertIn('parameters', weather_func)
        parameters = weather_func['parameters']
        self.assertEqual(parameters['type'], 'object')
        self.assertIn('properties', parameters)
        self.assertIn('required', parameters)
        
        # Verify properties (all should be strings)
        properties = parameters['properties']
        expected_params = ['location', 'units', 'days']
        
        for param_name in expected_params:
            self.assertIn(param_name, properties)
            self.assertEqual(properties[param_name]['type'], 'string')
            self.assertIn('description', properties[param_name])
        
        # Verify required parameters
        required = parameters['required']
        self.assertIn('location', required)  # location is required
        self.assertNotIn('units', required)   # units has default
        self.assertNotIn('days', required)    # days has default
    
    def test_parameter_descriptions_preserved(self):
        """Test that parameter descriptions from docstrings are preserved."""
        prompt = AnthropicFunctionCallPrompt(self.api_definitions)
        tools = prompt.get_function_definitions()
        
        weather_tool = tools[0]
        properties = weather_tool['input_schema']['properties']
        
        # Check that descriptions are meaningful (not just default)
        location_desc = properties['location']['description']
        self.assertIn('city', location_desc.lower())  # "City name or address"
        
        units_desc = properties['units']['description']
        self.assertIn('temperature', units_desc.lower())  # "Temperature units"
        
        days_desc = properties['days']['description']
        self.assertIn('forecast', days_desc.lower())  # "Number of forecast days"
    
    def test_both_formats_have_same_content(self):
        """Test that both Anthropic and OpenAI formats contain the same essential information."""
        anthropic_prompt = AnthropicFunctionCallPrompt(self.api_definitions)
        openai_prompt = OpenAIFunctionCallPrompt(self.api_definitions)
        
        anthropic_tools = anthropic_prompt.get_function_definitions()
        openai_functions = openai_prompt.get_function_definitions()
        
        # Both should have same number of functions
        self.assertEqual(len(anthropic_tools), len(openai_functions))
        
        # Compare the weather function/tool
        anthropic_weather = anthropic_tools[0]
        openai_weather = openai_functions[0]
        
        # Same name and description
        self.assertEqual(anthropic_weather['name'], openai_weather['name'])
        self.assertEqual(anthropic_weather['description'], openai_weather['description'])
        
        # Same parameters (different structure but same content)
        anthropic_props = anthropic_weather['input_schema']['properties']
        openai_props = openai_weather['parameters']['properties']
        
        self.assertEqual(set(anthropic_props.keys()), set(openai_props.keys()))
        
        # Same required parameters
        anthropic_required = set(anthropic_weather['input_schema']['required'])
        openai_required = set(openai_weather['parameters']['required'])
        
        self.assertEqual(anthropic_required, openai_required)
    
    def test_empty_api_definitions(self):
        """Test behavior with empty API definitions."""
        empty_definitions = {}
        
        anthropic_prompt = AnthropicFunctionCallPrompt(empty_definitions)
        openai_prompt = OpenAIFunctionCallPrompt(empty_definitions)
        
        anthropic_tools = anthropic_prompt.get_function_definitions()
        openai_functions = openai_prompt.get_function_definitions()
        
        self.assertEqual(len(anthropic_tools), 0)
        self.assertEqual(len(openai_functions), 0)


def run_function_call_prompts_test():
    """Run the function call prompts test suite."""
    print("🔧 Testing Function Call Prompts")
    print("-" * 50)
    print("Testing prompt generation for Anthropic Tools and OpenAI Functions formats")
    print()
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFunctionCallPrompts)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ Function call prompts test passed!")
        print("The prompt system correctly:")
        print("  - Generates Anthropic Tools format")
        print("  - Generates OpenAI Functions format")
        print("  - Converts all parameters to strings")
        print("  - Preserves parameter descriptions and requirements")
        print("  - Maintains consistency between formats")
    else:
        print("\n❌ Function call prompts test failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_function_call_prompts_test()