#!/usr/bin/env python3
"""
Weather API Scenario Test

Tests the decorator-based API system with weather scenario:
User: "what is the weather today in Tampa?"
Expected: get_weather(location="Tampa", units="metric", days=1)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from home_assistant.apis.decorators import APIRegistry
from home_assistant.apis.executor import APIExecutor, APICall


class TestWeatherAPIScenario(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Import HomeAPIs to trigger decorator registration (import happens first time only)
        from home_assistant.apis.home_apis import HomeAPIs
        self.HomeAPIs = HomeAPIs
        
        # Create mock HomeAPIs instance
        self.mock_home_apis = Mock(spec=HomeAPIs)
        self.mock_home_apis.get_weather = Mock(return_value={
            "location": "Tampa",
            "temperature": 85,
            "description": "sunny",
            "forecast": "1 day forecast",
            "units": "metric"
        })
        
        # Initialize executor
        self.executor = APIExecutor()
    
    def test_api_registration(self):
        """Test that weather API is properly registered."""
        # API should already be registered from setUp
        
        # Check API is registered
        apis = APIRegistry.get_all_apis()
        self.assertIn('get_weather', apis)
        
        # Check API definition
        weather_api = apis['get_weather']
        self.assertEqual(weather_api.name, "Weather Information")
        self.assertIn("weather", weather_api.description.lower())
        self.assertIn("conditions", weather_api.description.lower())
        
        # Check parameters
        params = weather_api.parameters
        self.assertIn('location', params)
        self.assertIn('units', params)
        self.assertIn('days', params)
        
        # Check parameter requirements
        self.assertTrue(params['location']['required'])
        self.assertFalse(params['units']['required'])
        self.assertFalse(params['days']['required'])
        
        # Check defaults
        self.assertEqual(params['units']['default'], "metric")
        self.assertEqual(params['days']['default'], 1)
    
    def test_weather_api_call_execution(self):
        """Test executing weather API call with specific parameters."""
        # API should already be registered from setUp
        
        # Create API call
        api_call = APICall(
            method_name="get_weather",
            parameters={
                "location": "Tampa",
                "units": "metric", 
                "days": 1
            },
            reasoning="User asked for weather today in Tampa"
        )
        
        # Execute the API call
        result = self.executor.execute_api_call(api_call, self.mock_home_apis)
        
        # Verify execution
        self.assertTrue(result["success"])
        self.assertEqual(result["method"], "get_weather")
        self.assertEqual(result["parameters"]["location"], "Tampa")
        self.assertEqual(result["parameters"]["units"], "metric")
        self.assertEqual(result["parameters"]["days"], 1)
        
        # Verify mock was called correctly
        self.mock_home_apis.get_weather.assert_called_once_with(
            location="Tampa",
            units="metric",
            days=1
        )
        
        # Verify result contains expected data
        expected_result = {
            "location": "Tampa",
            "temperature": 85,
            "description": "sunny",
            "forecast": "1 day forecast",
            "units": "metric"
        }
        self.assertEqual(result["result"], expected_result)
    
    def test_weather_api_call_with_defaults(self):
        """Test weather API call using default parameters."""
        # API should already be registered from setUp
        
        # Create API call with minimal parameters
        api_call = APICall(
            method_name="get_weather",
            parameters={"location": "Tampa"},
            reasoning="User asked for weather in Tampa"
        )
        
        # Execute the API call
        result = self.executor.execute_api_call(api_call, self.mock_home_apis)
        
        # Verify execution
        self.assertTrue(result["success"])
        
        # Verify mock was called with defaults
        self.mock_home_apis.get_weather.assert_called_once_with(
            location="Tampa"
        )
    
    def test_weather_api_call_error_handling(self):
        """Test error handling in API execution."""
        # API should already be registered from setUp
        
        # Configure mock to raise exception
        self.mock_home_apis.get_weather.side_effect = Exception("Weather service unavailable")
        
        # Create API call
        api_call = APICall(
            method_name="get_weather",
            parameters={"location": "Tampa"},
            reasoning="Test error handling"
        )
        
        # Execute the API call
        result = self.executor.execute_api_call(api_call, self.mock_home_apis)
        
        # Verify error handling
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Weather service unavailable")
        self.assertEqual(result["method"], "get_weather")
    
    def test_invalid_api_method(self):
        """Test calling non-existent API method."""
        # Create API call for non-existent method
        api_call = APICall(
            method_name="non_existent_method",
            parameters={"param": "value"}
        )
        
        # Execute should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.executor.execute_api_call(api_call, self.mock_home_apis)
        
        self.assertIn("Unknown API method", str(context.exception))
    
    def test_real_weather_api_implementation(self):
        """Test the actual HomeAPIs implementation."""
        # Create real instance
        home_apis = self.HomeAPIs()
        
        # Create API call
        api_call = APICall(
            method_name="get_weather",
            parameters={
                "location": "Tampa",
                "units": "metric",
                "days": 1
            }
        )
        
        # Execute with real instance
        result = self.executor.execute_api_call(api_call, home_apis)
        
        # Verify result structure
        self.assertTrue(result["success"])
        weather_data = result["result"]
        
        self.assertEqual(weather_data["location"], "Tampa")
        self.assertEqual(weather_data["units"], "metric")
        self.assertIn("temperature", weather_data)
        self.assertIn("description", weather_data)
        self.assertIn("forecast", weather_data)


def run_weather_scenario():
    """Run the complete weather scenario test."""
    print("🌤️  Testing Weather API Scenario")
    print("-" * 50)
    print("Scenario: User asks 'what is the weather today in Tampa?'")
    print("Expected: get_weather(location='Tampa', units='metric', days=1)")
    print()
    
    # Run the test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWeatherAPIScenario)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ Weather API scenario test passed!")
        print("The API system correctly:")
        print("  - Registers the weather API with decorators")
        print("  - Executes API calls with proper parameters")
        print("  - Handles defaults and error cases")
        print("  - Returns structured results")
    else:
        print("\n❌ Weather API scenario test failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_weather_scenario()