from typing import Dict, Any
from dataclasses import dataclass
from .decorators import APIRegistry


@dataclass 
class APICall:
    method_name: str
    parameters: Dict[str, Any]
    reasoning: str = ""


class APIExecutor:
    def execute_api_call(self, api_call: APICall, api_instance) -> Dict[str, Any]:
        """Execute a local Python API method call."""
        apis = APIRegistry.get_all_apis()

        if api_call.method_name not in apis:
            raise ValueError(f"Unknown API method: {api_call.method_name}")

        api_def = apis[api_call.method_name]
        method = getattr(api_instance, api_call.method_name)

        try:
            # Call the method with provided parameters
            result = method(**api_call.parameters)
            return {
                "success": True,
                "result": result,
                "method": api_call.method_name,
                "parameters": api_call.parameters
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": api_call.method_name,
                "parameters": api_call.parameters
            }