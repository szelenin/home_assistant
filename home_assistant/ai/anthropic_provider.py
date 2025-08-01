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
            intent = self.classify_intent(message)
            
            # Add to conversation history
            self.add_to_history(message, response_text)
            
            # Calculate confidence (simple heuristic based on response length and coherence)
            confidence = min(0.95, 0.7 + (len(response_text) / 1000) * 0.2)
            
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
                intent=IntentType.UNKNOWN,
                confidence=0.1
            )
    
    def classify_intent(self, message: str) -> IntentType:
        """Classify message intent using keyword matching and patterns."""
        message_lower = message.lower().strip()
        
        # Weather patterns
        weather_keywords = ['weather', 'temperature', 'rain', 'sunny', 'cloudy', 'forecast']
        if any(keyword in message_lower for keyword in weather_keywords):
            return IntentType.WEATHER
        
        # Personal info patterns
        if any(phrase in message_lower for phrase in ['what is your name', 'who are you', 'your name']):
            return IntentType.PERSONAL_INFO
        
        # Device control patterns
        device_keywords = ['turn on', 'turn off', 'switch', 'light', 'device', 'control']
        if any(keyword in message_lower for keyword in device_keywords):
            return IntentType.DEVICE_CONTROL
        
        # Time/date patterns
        time_keywords = ['time', 'date', 'today', 'tomorrow', 'yesterday', 'when', 'schedule']
        if any(keyword in message_lower for keyword in time_keywords):
            return IntentType.TIME_DATE
        
        # Question patterns
        question_words = ['what', 'how', 'why', 'where', 'when', 'who']
        if any(message_lower.startswith(word) for word in question_words) or message_lower.endswith('?'):
            return IntentType.QUESTION
        
        # Default to general chat
        return IntentType.GENERAL_CHAT
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        return (
            ANTHROPIC_AVAILABLE and 
            self.client is not None and 
            self.api_key is not None
        )
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt with context information."""
        wake_word = context.get('wake_word', 'Assistant') if context else 'Assistant'
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_prompt = f"""You are {wake_word}, a helpful home assistant. Current time: {current_time}

Key behaviors:
- Be concise and helpful
- For weather questions, acknowledge you don't have real-time data but provide general guidance
- For personal questions about your name, respond with your wake word: "{wake_word}"
- For device control requests, acknowledge the command but explain you're not yet connected to devices
- Maintain a friendly, conversational tone
- Keep responses brief unless more detail is specifically requested"""
        
        if context and 'user_preferences' in context:
            system_prompt += f"\n\nUser preferences: {context['user_preferences']}"
        
        return system_prompt
    
    def _build_message_history(self, current_message: str) -> list:
        """Build message history for Claude API format."""
        messages = []
        
        # Add conversation history
        for entry in self.conversation_history[-5:]:  # Last 5 exchanges
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["assistant"]})
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _extract_entities(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Extract entities from the conversation."""
        entities = {}
        
        # Extract locations (simple pattern matching)
        location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        locations = re.findall(location_pattern, user_message)
        if locations:
            entities['locations'] = locations
        
        # Extract time references
        time_words = ['today', 'tomorrow', 'yesterday', 'tonight', 'morning', 'afternoon', 'evening']
        time_refs = [word for word in time_words if word in user_message.lower()]
        if time_refs:
            entities['time_references'] = time_refs
        
        return entities