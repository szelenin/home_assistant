"""
Anthropic Claude AI Provider

Implements the BaseAIProvider interface for Anthropic's Claude models.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base_provider import BaseAIProvider, AIResponse, IntentType
from ..utils.logger import setup_logging


class AnthropicProvider(BaseAIProvider):
    """AI Provider for Anthropic Claude models."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = setup_logging("home_assistant.ai.anthropic")
        
        # Provider-specific configuration
        self.api_key = config.get('anthropic_api_key')
        self.model = config.get('model', 'claude-3-5-sonnet-20241022')
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.7)
        
        self.client = None
        
        if self.api_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.logger.info(f"Anthropic client initialized with model: {self.model}")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic client: {e}")
        else:
            if not ANTHROPIC_AVAILABLE:
                self.logger.warning("Anthropic library not available. Install with: pip install anthropic")
            if not self.api_key:
                self.logger.warning("Anthropic API key not provided in configuration")
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        """Send message to Claude and get response with intent classification."""
        if not self.is_available():
            raise Exception("Anthropic provider is not available")
        
        try:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context)
            
            # Build message history for Claude
            messages = self._build_message_history(message)
            
            # Make API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages
            )
            
            # Extract response text
            response_text = response.content[0].text if response.content else ""
            
            # Classify intent
            # With the new API system, all responses are either API_CALL or CHAT
            # The intent will be determined by whether the response is JSON API call format
            intent = IntentType.CHAT  # Default to chat, will be updated if API call detected
            
            # Add to conversation history
            self.add_to_history(message, response_text)
            
            # Calculate confidence
            confidence = self._calculate_response_confidence(response_text, response.stop_reason)
            
            self.logger.info(f"Claude response generated. Intent: {intent.value}, Confidence: {confidence:.2f}")
            
            return AIResponse(
                text=response_text,
                intent=intent,
                confidence=confidence,
                entities=self._extract_entities(message, response_text),
                raw_response={
                    'model': response.model,
                    'usage': response.usage.dict() if hasattr(response, 'usage') else {},
                    'stop_reason': response.stop_reason
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in Claude chat: {e}")
            # Return fallback response
            return AIResponse(
                text=f"I'm having trouble processing your request right now. Error: {str(e)}",
                intent=IntentType.CHAT,
                confidence=0.1
            )
    
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        return (
            ANTHROPIC_AVAILABLE and 
            self.client is not None and 
            self.api_key is not None
        )
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt with context information."""
        return self._build_system_content(context)
    
    def _build_message_history(self, current_message: str) -> list:
        """Build message history for Claude API format."""
        return self._build_conversation_messages(current_message)
    
