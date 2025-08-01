from typing import Optional
from .decorators import api_method


class HomeAPIs:
    @api_method(
        name="Weather Information",
        description="Get current weather conditions and forecast for any location",
        trigger_words=["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "today"]
    )
    def get_weather(
        self, 
        location: str,
        units: str = "metric",
        days: int = 1
    ) -> dict:
        """
        Get weather information for a specific location.
        
        Args:
            location: City name or address (e.g., "Tampa, FL")
            units: Temperature units - "metric", "imperial", or "kelvin"
            days: Number of forecast days (1-7)
            
        Returns:
            Weather information dictionary
        """
        # Mock implementation for now
        return {
            "location": location,
            "temperature": 85,
            "description": "sunny",
            "forecast": f"{days} day forecast",
            "units": units
        }