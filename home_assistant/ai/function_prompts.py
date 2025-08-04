"""
Function Call Prompt System

Base classes and provider-specific implementations for generating 
function calling prompts compatible with different AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
try:
    from ..apis.decorators import APIDefinition
except ImportError:
    from decorators import APIDefinition


class BaseFunctionCallPrompt(ABC):
    """Abstract base class for generating function calling prompts."""
    
    def __init__(self, api_definitions: Dict[str, APIDefinition]):
        """
        Initialize with API definitions from the registry.
        
        Args:
            api_definitions: Dictionary mapping method names to APIDefinition objects
        """
        self.api_definitions = api_definitions
    
    @abstractmethod
    def get_function_definitions(self) -> List[Dict]:
        """
        Return provider-specific function definitions for AI API.
        
        Returns:
            List of function/tool definitions in provider-specific format
        """
        pass
    
    def _get_required_params(self, api_parameters: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract required parameter names from API definition."""
        return [
            param_name 
            for param_name, param_info in api_parameters.items() 
            if param_info.get('required', False)
        ]
    
    def _convert_properties(self, api_parameters: Dict[str, Dict[str, Any]]) -> Dict[str, Dict]:
        """
        Convert API parameters to JSON Schema properties.
        All parameters are converted to string type for simplicity.
        
        Args:
            api_parameters: Parameter definitions from APIDefinition
            
        Returns:
            JSON Schema properties dictionary
        """
        properties = {}
        for param_name, param_info in api_parameters.items():
            properties[param_name] = {
                "type": "string",  # All parameters as strings
                "description": param_info.get('description', f"Parameter {param_name}")
            }
        return properties


class AnthropicFunctionCallPrompt(BaseFunctionCallPrompt):
    """Generate function calling prompts in Anthropic Tools format."""
    
    def get_function_definitions(self) -> List[Dict]:
        """
        Return function definitions in Anthropic Tools format.
        
        Returns:
            List of tool definitions compatible with Anthropic's messages API
        """
        tools = []
        
        for method_name, api_def in self.api_definitions.items():
            tool = {
                "name": method_name,
                "description": api_def.description,
                "input_schema": {
                    "type": "object",
                    "properties": self._convert_properties(api_def.parameters),
                    "required": self._get_required_params(api_def.parameters)
                }
            }
            tools.append(tool)
        
        return tools


class OpenAIFunctionCallPrompt(BaseFunctionCallPrompt):
    """Generate function calling prompts in OpenAI Functions format."""
    
    def get_function_definitions(self) -> List[Dict]:
        """
        Return function definitions in OpenAI Functions format.
        
        Returns:
            List of function definitions compatible with OpenAI's chat completions API
        """
        functions = []
        
        for method_name, api_def in self.api_definitions.items():
            function = {
                "name": method_name,
                "description": api_def.description,
                "parameters": {
                    "type": "object",
                    "properties": self._convert_properties(api_def.parameters),
                    "required": self._get_required_params(api_def.parameters)
                }
            }
            functions.append(function)
        
        return functions