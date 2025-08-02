"""
OpenAI ChatGPT AI Provider

Implements the BaseAIProvider interface for OpenAI's GPT models.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base_provider import BaseAIProvider, AIResponse, IntentType
from ..utils.logger import setup_logging


class OpenAIProvider(BaseAIProvider):
    """AI Provider for OpenAI GPT models."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = setup_logging("home_assistant.ai.openai")
        
        # Provider-specific configuration
        self.api_key = config.get('openai_api_key')
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.7)
        
        self.client = None
        
        if self.api_key and OPENAI_AVAILABLE:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                self.logger.info(f"OpenAI client initialized with model: {self.model}")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            if not OPENAI_AVAILABLE:
                self.logger.warning("OpenAI library not available. Install with: pip install openai")
            if not self.api_key:
                self.logger.warning("OpenAI API key not provided in configuration")
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        """Send message to ChatGPT and get response with intent classification."""
        if not self.is_available():
            raise Exception("OpenAI provider is not available")
        
        try:
            # Build system message with context
            system_message = self._build_system_message(context)
            
            # Build message history for OpenAI
            messages = self._build_message_history(message, system_message)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract response text
            response_text = response.choices[0].message.content if response.choices else ""
            
            # Classify intent
            # With the new API system, all responses are either API_CALL or CHAT
            # The intent will be determined by whether the response is JSON API call format
            intent = IntentType.CHAT  # Default to chat, will be updated if API call detected
            
            # Add to conversation history
            self.add_to_history(message, response_text)
            
            # Calculate confidence based on response quality indicators
            finish_reason = response.choices[0].finish_reason if response.choices else None
            confidence = self._calculate_response_confidence(response_text, finish_reason)
            
            self.logger.info(f"ChatGPT response generated. Intent: {intent.value}, Confidence: {confidence:.2f}")
            
            return AIResponse(
                text=response_text,
                intent=intent,
                confidence=confidence,
                entities=self._extract_entities(message, response_text),
                raw_response={
                    'model': response.model,
                    'usage': response.usage.dict() if hasattr(response.usage, 'dict') else response.usage.__dict__,
                    'finish_reason': response.choices[0].finish_reason if response.choices else None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in ChatGPT chat: {e}")
            # Return fallback response
            return AIResponse(
                text=f"I'm having trouble processing your request right now. Error: {str(e)}",
                intent=IntentType.CHAT,
                confidence=0.1
            )
    
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return (
            OPENAI_AVAILABLE and 
            self.client is not None and 
            self.api_key is not None
        )
    
    def _build_system_message(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Build system message with context information."""
        system_content = self._build_system_content(context)
        return {"role": "system", "content": system_content}
    
    def _build_message_history(self, current_message: str, system_message: Dict[str, str]) -> list:
        """Build message history for OpenAI API format."""
        messages = [system_message]
        messages.extend(self._build_conversation_messages(current_message))
        return messages
    
    
