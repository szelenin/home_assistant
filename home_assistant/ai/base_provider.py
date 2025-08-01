"""
Base AI Provider Interface

Abstract base class that defines the interface for all AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


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
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_length = config.get('max_history_length', 10)
    
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
    
    
    def add_to_history(self, user_message: str, ai_response: str):
        """Add message pair to conversation history."""
        self.conversation_history.append({
            "user": user_message,
            "assistant": ai_response
        })
        
        # Trim history if it gets too long
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
    
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