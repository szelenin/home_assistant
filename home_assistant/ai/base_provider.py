"""
Base AI Provider Interface

Abstract base class that defines the interface for all AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import re


class IntentType(Enum):
    """Simplified intent types for the decorator-based API system."""
    API_CALL = "api_call"    # AI detected and wants to execute an API call
    CHAT = "chat"            # Regular conversational response
    UNKNOWN = "unknown"      # Fallback for errors


@dataclass
class AIResponse:
    """Response from AI provider with intent classification."""
    text: str
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = None
    raw_response: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.raw_response is None:
            self.raw_response = {}


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AI provider with configuration.
        
        Args:
            config: Configuration dictionary containing API keys and settings
        """
        self.config = config
    
    @abstractmethod
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        """
        Send a message to the AI and get a response.
        
        Args:
            message: User's message
            context: Optional context information (wake word, user preferences, etc.)
            
        Returns:
            AIResponse object with text, intent, and metadata
        """
        pass
    
    
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the AI provider is available and properly configured.
        
        Returns:
            True if provider is available, False otherwise
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        return self.__class__.__name__.replace('Provider', '').lower()
    
    def _build_system_content(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build common system content with context information."""
        wake_word = context.get('wake_word', 'Assistant') if context else 'Assistant'
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_content = f"""You are {wake_word}, a helpful home assistant. Current time: {current_time}

Key behaviors:
- Be concise and helpful in your responses
- For weather questions, acknowledge you don't have real-time weather data but provide general guidance
- For personal questions about your name, respond with your wake word: "{wake_word}"
- For device control requests, acknowledge the command but explain you're not yet connected to physical devices
- Maintain a friendly, conversational tone
- Keep responses brief unless more detail is specifically requested
- Be honest about your limitations"""
        
        if context and 'user_preferences' in context:
            system_content += f"\n\nUser preferences: {context['user_preferences']}"
        
        if context and 'system_prompt' in context:
            system_content += f"\n\n{context['system_prompt']}"
        
        return system_content
    
    
    def _extract_entities(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Extract entities from the conversation."""
        entities = {}
        
        # Extract locations (cities, places)
        location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        locations = re.findall(location_pattern, user_message)
        # Filter common words that aren't locations
        common_words = {'What', 'How', 'Where', 'When', 'Why', 'Who', 'The', 'This', 'That'}
        locations = [loc for loc in locations if loc not in common_words]
        if locations:
            entities['locations'] = locations
        
        # Extract time references
        time_words = ['today', 'tomorrow', 'yesterday', 'tonight', 'morning', 'afternoon', 'evening', 'now']
        time_refs = [word for word in time_words if word in user_message.lower()]
        if time_refs:
            entities['time_references'] = time_refs
        
        # Extract numbers (for device control, temperatures, etc.)
        numbers = re.findall(r'\b\d+\b', user_message)
        if numbers:
            entities['numbers'] = [int(num) for num in numbers]
        
        return entities
    
    def _calculate_response_confidence(self, response_text: str, finish_reason: str = None) -> float:
        """Calculate confidence score based on response quality indicators."""
        base_confidence = 0.8
        
        # Adjust based on response length (too short or too long might indicate issues)
        length_factor = min(1.0, len(response_text) / 100)  # Optimal around 100 chars
        if length_factor < 0.1:  # Very short responses
            base_confidence -= 0.3
        elif length_factor > 5.0:  # Very long responses
            base_confidence -= 0.1
        
        # Check finish reason if provided
        if finish_reason:
            if finish_reason == 'length':  # Truncated response
                base_confidence -= 0.2
            elif finish_reason in ['content_filter', 'stop_sequence']:  # Content filtered or stopped
                base_confidence -= 0.4
        
        # Check for error indicators in response
        error_indicators = ['error', 'sorry', 'cannot', 'unable', 'unavailable']
        if any(indicator in response_text.lower() for indicator in error_indicators):
            base_confidence -= 0.2
        
        return max(0.1, min(0.95, base_confidence))