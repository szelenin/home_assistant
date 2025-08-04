"""
AI Orchestrator

Central orchestrator for AI providers with native function calling support.
Simplified architecture that uses provider-native function calling instead of custom JSON parsing.
"""

from typing import Dict, Any, Optional, Type
import json

from .base_provider import BaseAIProvider, AIResponse, IntentType, ToolCall
from .anthropic_provider import AnthropicProvider  
from .openai_provider import OpenAIProvider
from ..utils.config import ConfigManager
from ..utils.logger import setup_logging


class AIOrchestrator:
    """
    Central orchestrator for managing AI providers with function calling.
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
        Process a chat message through the AI provider with function calling.
        
        Args:
            message: User's message
            context: Optional context (wake word, user preferences, etc.)
            
        Returns:
            AIResponse with text, function calls, and metadata
        """
        if not context:
            context = {}
        
        # Add wake word to context
        wake_word = self.config_manager.get_wake_word()
        if wake_word:
            context['wake_word'] = wake_word
        
        # Initialize API components
        self._initialize_api_components()
        
        try:
            # Get API definitions for function calling
            api_definitions = {}
            if self.api_registry:
                api_definitions = self.api_registry.get_all_apis()
            
            # Get AI response with function calling
            response = self._get_ai_response_with_functions(message, api_definitions, context)
            
            # Execute any function calls
            if response.tool_calls and self.api_executor and self.home_apis:
                response = self._execute_function_calls(response, message, context)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in chat processing: {e}")
            return AIResponse(
                text="I'm having trouble processing your request right now.",
                intent=IntentType.UNKNOWN,
                confidence=0.1
            )
    
    def _get_ai_response_with_functions(
        self, 
        message: str, 
        api_definitions: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> AIResponse:
        """Get AI response with function calling capability."""
        
        # Try primary provider first
        if self.current_provider:
            try:
                response = self.current_provider.chat_with_functions(
                    message, api_definitions, context
                )
                self.logger.debug(
                    f"Response from {self.current_provider.get_provider_name()}: "
                    f"{response.intent.value}, {len(response.tool_calls)} function calls"
                )
                return response
            except Exception as e:
                self.logger.warning(f"Primary provider failed: {e}")
        
        # Fallback to secondary provider
        if self.fallback_provider:
            try:
                response = self.fallback_provider.chat_with_functions(
                    message, api_definitions, context
                )
                self.logger.info(
                    f"Using fallback provider: {self.fallback_provider.get_provider_name()}"
                )
                return response
            except Exception as e:
                self.logger.error(f"Fallback provider also failed: {e}")
        
        # Return error response if all providers fail
        return AIResponse(
            text="I'm having trouble connecting to my AI services right now.",
            intent=IntentType.UNKNOWN,
            confidence=0.1
        )
    
    def _execute_function_calls(
        self, 
        response: AIResponse, 
        original_message: str,
        context: Dict[str, Any]
    ) -> AIResponse:
        """Execute function calls and format the final response."""
        
        # Execute all function calls
        function_results = []
        for tool_call in response.tool_calls:
            try:
                # Execute the function call
                from ..apis.executor import APICall
                
                api_call = APICall(
                    method_name=tool_call.name,
                    parameters=tool_call.arguments,
                    reasoning="Function call from AI"
                )
                
                result = self.api_executor.execute_api_call(api_call, self.home_apis)
                function_results.append({
                    'tool_call_id': tool_call.id,
                    'result': result
                })
                
                self.logger.info(f"Executed function {tool_call.name}: {result.get('success', False)}")
                
            except Exception as e:
                self.logger.error(f"Error executing function {tool_call.name}: {e}")
                function_results.append({
                    'tool_call_id': tool_call.id,
                    'result': {'success': False, 'error': str(e)}
                })
        
        # Format the final response
        formatted_text = self._format_function_results(function_results, original_message)
        
        # Update response with formatted text and results
        response.text = formatted_text
        response.entities['function_results'] = function_results
        
        return response
    
    def _format_function_results(
        self, 
        function_results, 
        original_message: str
    ) -> str:
        """Format function results into natural language response."""
        
        if not function_results:
            return "I couldn't execute any functions to help with your request."
        
        # Handle single result case
        if len(function_results) == 1:
            result_data = function_results[0]['result']
            
            if not result_data.get('success'):
                return f"I encountered an error: {result_data.get('error', 'Unknown error')}"
            
            method_name = result_data.get('method', '')
            result = result_data.get('result', {})
            
            # Format weather results
            if method_name == 'get_weather':
                location = result.get('location', 'your location')
                temperature = result.get('temperature', 'unknown')
                description = result.get('description', 'unknown conditions')
                units = result.get('units', 'metric')
                
                unit_symbol = '°C' if units == 'metric' else '°F' if units == 'imperial' else 'K'
                
                return f"The weather in {location} is currently {description} with a temperature of {temperature}{unit_symbol}."
            
            # Generic formatting for other functions
            return f"Here's the result: {result}"
        
        # Handle multiple results
        formatted_parts = []
        for func_result in function_results:
            result_data = func_result['result']
            if result_data.get('success'):
                method_name = result_data.get('method', 'function')
                formatted_parts.append(f"{method_name}: {result_data.get('result', {})}")
            else:
                formatted_parts.append(f"Error: {result_data.get('error', 'Unknown error')}")
        
        return "Here are the results:\n" + "\n".join(formatted_parts)
    
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