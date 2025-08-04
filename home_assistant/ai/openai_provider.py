"""
OpenAI ChatGPT AI Provider

Implements the BaseAIProvider interface for OpenAI's GPT models with native function calling.
"""

import json
from typing import Dict, Any, Optional, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from .base_provider import BaseAIProvider, AIResponse, IntentType, ToolCall
    from .function_prompts import OpenAIFunctionCallPrompt
    from ..utils.logger import setup_logging
except ImportError:
    from base_provider import BaseAIProvider, AIResponse, IntentType, ToolCall
    from function_prompts import OpenAIFunctionCallPrompt


class OpenAIProvider(BaseAIProvider):
    """AI Provider for OpenAI GPT models with native function calling."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            self.logger = setup_logging("home_assistant.ai.openai")
        except:
            import logging
            self.logger = logging.getLogger("openai_provider")
        
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
    
    def chat_with_functions(
        self, 
        message: str, 
        api_definitions: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Send message to ChatGPT with function calling capability."""
        if not self.is_available():
            raise Exception("OpenAI provider is not available")
        
        try:
            # Create function call prompt
            function_prompt = OpenAIFunctionCallPrompt(api_definitions)
            functions = function_prompt.get_function_definitions()
            
            # Build system message
            system_content = self._build_system_content(context)
            
            # Build messages
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": message}
            ]
            
            # Make API call with functions
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                functions=functions,
                function_call="auto"
            )
            
            # Process response
            return self._process_response(response, message)
            
        except Exception as e:
            self.logger.error(f"Error in OpenAI function calling: {e}")
            return AIResponse(
                text=f"I'm having trouble processing your request right now. Error: {str(e)}",
                intent=IntentType.UNKNOWN,
                confidence=0.1
            )
    
    def simple_chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Send a simple message to ChatGPT without function calling (for formatting responses)."""
        if not self.is_available():
            raise Exception("OpenAI provider is not available")
        
        try:
            # Build system message
            system_content = self._build_system_content(context)
            
            # Build messages
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": message}
            ]
            
            # Make simple API call without functions
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract and return text
            response_text = response.choices[0].message.content if response.choices else ""
            return response_text
            
        except Exception as e:
            self.logger.error(f"Error in OpenAI simple chat: {e}")
            return f"I'm having trouble processing your request right now. Error: {str(e)}"
    
    def _process_response(self, response, original_message: str) -> AIResponse:
        """Process OpenAI response and extract function calls or text."""
        tool_calls = []
        response_text = ""
        intent = IntentType.CHAT
        
        # Process response
        if response.choices:
            choice = response.choices[0]
            message = choice.message
            
            # Extract text content
            if message.content:
                response_text = message.content
            
            # Extract function calls
            if message.function_call:
                # Single function call (legacy format)
                tool_call = ToolCall(
                    id=f"call_{hash(message.function_call.name)}",  # Generate ID
                    name=message.function_call.name,
                    arguments=json.loads(message.function_call.arguments)
                )
                tool_calls.append(tool_call)
                intent = IntentType.FUNCTION_CALL
            
            elif hasattr(message, 'tool_calls') and message.tool_calls:
                # Multiple function calls (newer format)
                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        tc = ToolCall(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=json.loads(tool_call.function.arguments)
                        )
                        tool_calls.append(tc)
                        intent = IntentType.FUNCTION_CALL
        
        # Calculate confidence
        finish_reason = response.choices[0].finish_reason if response.choices else None
        confidence = self._calculate_response_confidence(response_text, finish_reason)
        
        self.logger.info(
            f"OpenAI response: {len(tool_calls)} function calls, "
            f"intent: {intent.value}, confidence: {confidence:.2f}"
        )
        
        return AIResponse(
            text=response_text,
            intent=intent,
            confidence=confidence,
            tool_calls=tool_calls,
            entities=self._extract_entities(original_message, response_text),
            raw_response={
                'model': response.model,
                'usage': response.usage.dict() if hasattr(response.usage, 'dict') else response.usage.__dict__,
                'finish_reason': finish_reason
            }
        )
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return (
            OPENAI_AVAILABLE and 
            self.client is not None and 
            self.api_key is not None
        )