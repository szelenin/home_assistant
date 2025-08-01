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
            intent = self.classify_intent(message)
            
            # Add to conversation history
            self.add_to_history(message, response_text)
            
            # Calculate confidence based on response quality indicators
            confidence = self._calculate_confidence(response, response_text)
            
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
                intent=IntentType.UNKNOWN,
                confidence=0.1
            )
    
    def classify_intent(self, message: str) -> IntentType:
        """Classify message intent using keyword matching and patterns."""
        message_lower = message.lower().strip()
        
        # Weather patterns
        weather_keywords = ['weather', 'temperature', 'rain', 'sunny', 'cloudy', 'forecast', 'climate']
        if any(keyword in message_lower for keyword in weather_keywords):
            return IntentType.WEATHER
        
        # Personal info patterns
        personal_patterns = ['what is your name', 'who are you', 'your name', 'tell me about yourself']
        if any(phrase in message_lower for phrase in personal_patterns):
            return IntentType.PERSONAL_INFO
        
        # Device control patterns
        device_keywords = ['turn on', 'turn off', 'switch', 'light', 'device', 'control', 'dim', 'brightness']
        if any(keyword in message_lower for keyword in device_keywords):
            return IntentType.DEVICE_CONTROL
        
        # Time/date patterns
        time_keywords = ['time', 'date', 'today', 'tomorrow', 'yesterday', 'when', 'schedule', 'calendar']
        if any(keyword in message_lower for keyword in time_keywords):
            return IntentType.TIME_DATE
        
        # Question patterns (must come after specific patterns)
        question_words = ['what', 'how', 'why', 'where', 'when', 'who', 'which', 'can you']
        if any(message_lower.startswith(word) for word in question_words) or message_lower.endswith('?'):
            return IntentType.QUESTION
        
        # Default to general chat
        return IntentType.GENERAL_CHAT
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return (
            OPENAI_AVAILABLE and 
            self.client is not None and 
            self.api_key is not None
        )
    
    def _build_system_message(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Build system message with context information."""
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
        
        return {"role": "system", "content": system_content}
    
    def _build_message_history(self, current_message: str, system_message: Dict[str, str]) -> list:
        """Build message history for OpenAI API format."""
        messages = [system_message]
        
        # Add conversation history (last 5 exchanges to manage token usage)
        for entry in self.conversation_history[-5:]:
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["assistant"]})
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _calculate_confidence(self, response, response_text: str) -> float:
        """Calculate confidence score based on response quality indicators."""
        base_confidence = 0.8
        
        # Adjust based on response length (too short or too long might indicate issues)
        length_factor = min(1.0, len(response_text) / 100)  # Optimal around 100 chars
        if length_factor < 0.1:  # Very short responses
            base_confidence -= 0.3
        elif length_factor > 5.0:  # Very long responses
            base_confidence -= 0.1
        
        # Check finish reason
        if hasattr(response, 'choices') and response.choices:
            finish_reason = response.choices[0].finish_reason
            if finish_reason == 'length':  # Truncated response
                base_confidence -= 0.2
            elif finish_reason == 'content_filter':  # Content filtered
                base_confidence -= 0.4
        
        # Check for error indicators in response
        error_indicators = ['error', 'sorry', 'cannot', 'unable', 'unavailable']
        if any(indicator in response_text.lower() for indicator in error_indicators):
            base_confidence -= 0.2
        
        return max(0.1, min(0.95, base_confidence))
    
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