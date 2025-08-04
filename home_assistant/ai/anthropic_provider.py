"""
Anthropic Claude AI Provider

Implements the BaseAIProvider interface for Anthropic's Claude models with native function calling.
"""

import json
from typing import Dict, Any, Optional, List

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from .base_provider import BaseAIProvider, AIResponse, IntentType, ToolCall
    from .function_prompts import AnthropicFunctionCallPrompt
    from ..utils.logger import setup_logging
except ImportError:
    from base_provider import BaseAIProvider, AIResponse, IntentType, ToolCall
    from function_prompts import AnthropicFunctionCallPrompt


class AnthropicProvider(BaseAIProvider):
    """AI Provider for Anthropic Claude models with native function calling."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            self.logger = setup_logging("home_assistant.ai.anthropic")
        except:
            import logging
            self.logger = logging.getLogger("anthropic_provider")
        
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
    
    def chat_with_functions(
        self, 
        message: str, 
        api_definitions: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Send message to Claude with function calling capability."""
        if not self.is_available():
            raise Exception("Anthropic provider is not available")
        
        try:
            # Create function call prompt
            function_prompt = AnthropicFunctionCallPrompt(api_definitions)
            tools = function_prompt.get_function_definitions()
            
            # Build system prompt
            system_prompt = self._build_system_content(context)
            
            # Build messages
            messages = [{"role": "user", "content": message}]
            
            # Make API call with tools (don't specify tool_choice for Anthropic)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
                tools=tools
            )
            
            # Process response
            return self._process_response(response, message)
            
        except Exception as e:
            self.logger.error(f"Error in Claude function calling: {e}")
            return AIResponse(
                text=f"I'm having trouble processing your request right now. Error: {str(e)}",
                intent=IntentType.UNKNOWN,
                confidence=0.1
            )
    
    def simple_chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Send a simple message to Claude without function calling (for formatting responses)."""
        if not self.is_available():
            raise Exception("Anthropic provider is not available")
        
        try:
            # Build system prompt
            system_prompt = self._build_system_content(context)
            
            # Build messages
            messages = [{"role": "user", "content": message}]
            
            # Make simple API call without tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages
            )
            
            # Extract and return text
            response_text = response.content[0].text if response.content else ""
            return response_text
            
        except Exception as e:
            self.logger.error(f"Error in Claude simple chat: {e}")
            return f"I'm having trouble processing your request right now. Error: {str(e)}"
    
    def _process_response(self, response, original_message: str) -> AIResponse:
        """Process Claude response and extract function calls or text."""
        tool_calls = []
        response_text = ""
        intent = IntentType.CHAT
        
        # Process response content
        for content_block in response.content:
            if content_block.type == "text":
                response_text += content_block.text
            elif content_block.type == "tool_use":
                # Claude made a function call
                tool_call = ToolCall(
                    id=content_block.id,
                    name=content_block.name,
                    arguments=content_block.input
                )
                tool_calls.append(tool_call)
                intent = IntentType.FUNCTION_CALL
        
        # Calculate confidence
        confidence = self._calculate_response_confidence(
            response_text, 
            response.stop_reason
        )
        
        self.logger.info(
            f"Claude response: {len(tool_calls)} tool calls, "
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
                'usage': response.usage.dict() if hasattr(response, 'usage') else {},
                'stop_reason': response.stop_reason
            }
        )
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        return (
            ANTHROPIC_AVAILABLE and 
            self.client is not None and 
            self.api_key is not None
        )