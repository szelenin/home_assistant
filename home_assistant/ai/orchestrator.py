"""
AI Orchestrator

Central orchestrator for AI providers that handles intent recognition,
provider selection, and natural language to device API translation.
"""

from typing import Dict, Any, Optional, Type
from datetime import datetime

from .base_provider import BaseAIProvider, AIResponse, IntentType
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from ..utils.config import ConfigManager
from ..utils.logger import setup_logging


class AIOrchestrator:
    """
    Central orchestrator for managing AI providers and handling requests.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the AI orchestrator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = setup_logging("home_assistant.ai.orchestrator")
        
        # Provider registry
        self.providers: Dict[str, Type[BaseAIProvider]] = {
            'anthropic': AnthropicProvider,
            'openai': OpenAIProvider
        }
        
        self.current_provider: Optional[BaseAIProvider] = None
        self.fallback_provider: Optional[BaseAIProvider] = None
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize AI providers based on configuration."""
        ai_config = self.config_manager.get_ai_config()
        provider_name = ai_config.get('provider', 'anthropic')
        
        try:
            # Initialize primary provider
            if provider_name in self.providers:
                provider_class = self.providers[provider_name]
                self.current_provider = provider_class(ai_config)
                
                if self.current_provider.is_available():
                    self.logger.info(f"Primary AI provider initialized: {provider_name}")
                else:
                    self.logger.warning(f"Primary provider {provider_name} not available")
                    self.current_provider = None
            
            # Initialize fallback provider (opposite of primary)
            fallback_name = 'openai' if provider_name == 'anthropic' else 'anthropic'
            if fallback_name in self.providers:
                fallback_class = self.providers[fallback_name]
                self.fallback_provider = fallback_class(ai_config)
                
                if self.fallback_provider.is_available():
                    self.logger.info(f"Fallback AI provider initialized: {fallback_name}")
                else:
                    self.fallback_provider = None
            
            # If no providers available, log error
            if not self.current_provider and not self.fallback_provider:
                self.logger.error("No AI providers available. Check API keys in config.yaml")
                
        except Exception as e:
            self.logger.error(f"Error initializing AI providers: {e}")
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        """
        Process a chat message through the AI provider with intent recognition.
        
        Args:
            message: User's message
            context: Optional context (wake word, user preferences, etc.)
            
        Returns:
            AIResponse with text, intent, and metadata
        """
        if not context:
            context = {}
        
        # Add wake word to context
        wake_word = self.config_manager.get_wake_word()
        if wake_word:
            context['wake_word'] = wake_word
        
        # Try primary provider first
        if self.current_provider:
            try:
                response = self.current_provider.chat(message, context)
                self.logger.debug(f"Response from {self.current_provider.get_provider_name()}: {response.intent.value}")
                return response
            except Exception as e:
                self.logger.warning(f"Primary provider failed: {e}")
        
        # Fallback to secondary provider
        if self.fallback_provider:
            try:
                response = self.fallback_provider.chat(message, context)
                self.logger.info(f"Using fallback provider: {self.fallback_provider.get_provider_name()}")
                return response
            except Exception as e:
                self.logger.error(f"Fallback provider also failed: {e}")
        
        # Return error response if all providers fail
        return AIResponse(
            text="I'm having trouble connecting to my AI services right now. Please check your internet connection and API keys.",
            intent=IntentType.UNKNOWN,
            confidence=0.1
        )
    
    def classify_intent(self, message: str) -> IntentType:
        """
        Classify the intent of a message using available providers.
        
        Args:
            message: User's message
            
        Returns:
            IntentType enum value
        """
        provider = self.current_provider or self.fallback_provider
        if provider:
            return provider.classify_intent(message)
        
        # Fallback to simple keyword-based classification
        return self._simple_intent_classification(message)
    
    def _simple_intent_classification(self, message: str) -> IntentType:
        """Simple fallback intent classification when no AI providers available."""
        message_lower = message.lower().strip()
        
        # Weather
        if any(word in message_lower for word in ['weather', 'temperature', 'rain', 'sunny']):
            return IntentType.WEATHER
        
        # Personal info
        if any(phrase in message_lower for phrase in ['your name', 'who are you']):
            return IntentType.PERSONAL_INFO
        
        # Device control
        if any(word in message_lower for word in ['turn', 'switch', 'light', 'device']):
            return IntentType.DEVICE_CONTROL
        
        # Question
        if message_lower.endswith('?') or any(message_lower.startswith(word) for word in ['what', 'how', 'why']):
            return IntentType.QUESTION
        
        return IntentType.GENERAL_CHAT
    
    def translate_to_device_api(self, message: str, intent: IntentType) -> Dict[str, Any]:
        """
        Translate natural language to device API calls based on intent.
        
        Args:
            message: User's message
            intent: Classified intent
            
        Returns:
            Dictionary representing device API call or action
        """
        message_lower = message.lower()
        
        if intent == IntentType.DEVICE_CONTROL:
            # Parse device control commands
            api_call = {
                'type': 'device_control',
                'action': None,
                'device': None,
                'parameters': {}
            }
            
            # Determine action
            if any(word in message_lower for word in ['turn on', 'switch on', 'enable']):
                api_call['action'] = 'turn_on'
            elif any(word in message_lower for word in ['turn off', 'switch off', 'disable']):
                api_call['action'] = 'turn_off'
            elif 'dim' in message_lower or 'brightness' in message_lower:
                api_call['action'] = 'set_brightness'
                # Extract brightness value if present
                import re
                brightness_match = re.search(r'(\d+)%?', message)
                if brightness_match:
                    api_call['parameters']['brightness'] = int(brightness_match.group(1))
            
            # Determine device
            if 'light' in message_lower:
                api_call['device'] = 'light'
            elif 'fan' in message_lower:
                api_call['device'] = 'fan'
            elif 'thermostat' in message_lower:
                api_call['device'] = 'thermostat'
            
            return api_call
        
        elif intent == IntentType.WEATHER:
            # Parse weather requests
            return {
                'type': 'weather_request',
                'location': self._extract_location(message),
                'time': self._extract_time_reference(message)
            }
        
        elif intent == IntentType.PERSONAL_INFO:
            # Handle personal information requests
            return {
                'type': 'personal_info',
                'question': 'name' if 'name' in message_lower else 'general'
            }
        
        else:
            # Generic response for other intents
            return {
                'type': 'general_response',
                'intent': intent.value,
                'message': message
            }
    
    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location from message."""
        # Simple location extraction - could be enhanced with NLP
        import re
        
        # Look for "in [Location]" pattern
        location_match = re.search(r'\bin\s+([A-Z][a-zA-Z\s]+)', message)
        if location_match:
            return location_match.group(1).strip()
        
        # Look for standalone capitalized words (likely places)
        words = message.split()
        for word in words:
            if word[0].isupper() and word.lower() not in ['I', 'What', 'How', 'The']:
                return word
        
        return None
    
    def _extract_time_reference(self, message: str) -> Optional[str]:
        """Extract time reference from message."""
        message_lower = message.lower()
        time_refs = ['today', 'tomorrow', 'yesterday', 'tonight', 'morning', 'afternoon', 'evening']
        
        for time_ref in time_refs:
            if time_ref in message_lower:
                return time_ref
        
        return None
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of all providers."""
        status = {}
        for name, provider_class in self.providers.items():
            ai_config = self.config_manager.get_ai_config()
            try:
                provider = provider_class(ai_config)
                status[name] = provider.is_available()
            except:
                status[name] = False
        return status
    
    def switch_provider(self, provider_name: str) -> bool:
        """
        Switch to a different AI provider.
        
        Args:
            provider_name: Name of the provider to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        if provider_name not in self.providers:
            self.logger.error(f"Unknown provider: {provider_name}")
            return False
        
        try:
            ai_config = self.config_manager.get_ai_config()
            ai_config['provider'] = provider_name  # Update provider in config
            provider_class = self.providers[provider_name]
            new_provider = provider_class(ai_config)
            
            if new_provider.is_available():
                self.current_provider = new_provider
                # Update main config
                self.config_manager.config['ai']['provider'] = provider_name
                self.config_manager.save_config()
                self.logger.info(f"Switched to provider: {provider_name}")
                return True
            else:
                self.logger.warning(f"Provider {provider_name} is not available")
                return False
        except Exception as e:
            self.logger.error(f"Error switching to provider {provider_name}: {e}")
            return False