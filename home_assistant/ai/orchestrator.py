"""
AI Orchestrator

Central orchestrator for AI providers that handles intent recognition,
provider selection, and natural language to device API translation.
"""

from typing import Dict, Any, Optional, Type
from datetime import datetime
import json

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
        
        # API system components (lazy-loaded)
        self.api_registry = None
        self.api_executor = None
        self.home_apis = None
        
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
    
    def _initialize_api_components(self):
        """Initialize API system components lazily."""
        if self.api_registry is None:
            try:
                from ..apis.decorators import APIRegistry
                from ..apis.executor import APIExecutor
                from ..apis.home_apis import HomeAPIs
                
                self.api_registry = APIRegistry
                self.api_executor = APIExecutor()
                self.home_apis = HomeAPIs()
                
                self.logger.info("API system components initialized")
            except ImportError as e:
                self.logger.warning(f"API system not available: {e}")
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> AIResponse:
        """
        Process a chat message through the AI provider with API call detection.
        
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
        
        # Initialize API components if available
        self._initialize_api_components()
        
        # Add API context if available
        if self.api_registry:
            api_context = self._build_api_context()
            context['available_apis'] = api_context
        
        # Try to get AI response with API detection
        try:
            response = self._get_ai_response_with_api_detection(message, context)
            
            # If API call detected, execute it
            if self._is_api_call_response(response) and self.api_executor and self.home_apis:
                api_call_data = self._parse_api_call_response(response)
                if api_call_data:
                    api_result = self._execute_api_call(api_call_data)
                    response.text = self._format_api_result(message, api_result, context)
                    response.entities['api_call'] = api_call_data
                    response.entities['api_result'] = api_result
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in enhanced chat: {e}")
            return AIResponse(
                text="I'm having trouble processing your request right now.",
                intent=IntentType.UNKNOWN,
                confidence=0.1
            )
    
    
    
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
    
    def _build_api_context(self) -> str:
        """Build API context string for AI prompt."""
        if not self.api_registry:
            return ""
        
        apis = self.api_registry.get_all_apis()
        api_descriptions = []

        for api_name, api_def in apis.items():
            params_str = []
            for param_name, param_info in api_def.parameters.items():
                required = " (required)" if param_info['required'] else f" (default: {param_info['default']})"
                params_str.append(f"  - {param_name}: {param_info['description']}{required}")

            api_desc = f"""
API: {api_def.name}
Method: {api_name}
Description: {api_def.description}
Parameters:
{chr(10).join(params_str)}
"""
            api_descriptions.append(api_desc)

        return "\n".join(api_descriptions)
    
    def _get_ai_response_with_api_detection(self, message: str, context: Dict[str, Any]) -> AIResponse:
        """Get AI response with enhanced API detection prompt."""
        # Enhanced system prompt for API detection
        if 'available_apis' in context:
            enhanced_context = context.copy()
            enhanced_context['system_prompt'] = f"""
You are a helpful home assistant. You have access to the following APIs:

{context['available_apis']}

IMPORTANT: If the user's message can be fulfilled by calling one of these APIs, respond with a JSON object:
{{
  "intent": "api_call",
  "api_method": "method_name",
  "parameters": {{"param1": "value1", "param2": "value2"}},
  "reasoning": "why you chose this API"
}}

Otherwise, respond normally as a helpful assistant.
"""
        else:
            enhanced_context = context
        
        # Try primary provider first
        if self.current_provider:
            try:
                response = self.current_provider.chat(message, enhanced_context)
                self.logger.debug(f"Response from {self.current_provider.get_provider_name()}: {response.intent.value}")
                return response
            except Exception as e:
                self.logger.warning(f"Primary provider failed: {e}")
        
        # Fallback to secondary provider
        if self.fallback_provider:
            try:
                response = self.fallback_provider.chat(message, enhanced_context)
                self.logger.info(f"Using fallback provider: {self.fallback_provider.get_provider_name()}")
                return response
            except Exception as e:
                self.logger.error(f"Fallback provider also failed: {e}")
        
        # Return error response if all providers fail
        return AIResponse(
            text="I'm having trouble connecting to my AI services right now.",
            intent=IntentType.UNKNOWN,
            confidence=0.1
        )
    
    def _is_api_call_response(self, response: AIResponse) -> bool:
        """Check if response contains API call data."""
        try:
            # Try to parse as JSON to see if it's an API call
            if response.text.strip().startswith('{') and response.text.strip().endswith('}'):
                data = json.loads(response.text)
                return data.get('intent') == 'api_call' and 'api_method' in data
        except json.JSONDecodeError:
            pass
        return False
    
    def _parse_api_call_response(self, response: AIResponse) -> Optional[Dict[str, Any]]:
        """Parse API call data from response."""
        try:
            data = json.loads(response.text)
            if data.get('intent') == 'api_call':
                return {
                    'method_name': data.get('api_method'),
                    'parameters': data.get('parameters', {}),
                    'reasoning': data.get('reasoning', '')
                }
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API call response: {e}")
        return None
    
    def _execute_api_call(self, api_call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API call using the executor."""
        from ..apis.executor import APICall
        
        api_call = APICall(
            method_name=api_call_data['method_name'],
            parameters=api_call_data['parameters'],
            reasoning=api_call_data.get('reasoning', '')
        )
        
        return self.api_executor.execute_api_call(api_call, self.home_apis)
    
    def _format_api_result(self, original_message: str, api_result: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Format API result into natural language response."""
        if not api_result.get('success'):
            return f"I encountered an error: {api_result.get('error', 'Unknown error')}"
        
        result_data = api_result.get('result', {})
        method_name = api_result.get('method', '')
        
        # Format weather results
        if method_name == 'get_weather':
            location = result_data.get('location', 'your location')
            temperature = result_data.get('temperature', 'unknown')
            description = result_data.get('description', 'unknown conditions')
            units = result_data.get('units', 'metric')
            
            unit_symbol = '°C' if units == 'metric' else '°F' if units == 'imperial' else 'K'
            
            return f"The weather in {location} is currently {description} with a temperature of {temperature}{unit_symbol}."
        
        # Generic formatting for other APIs
        return f"Here's the result: {result_data}"