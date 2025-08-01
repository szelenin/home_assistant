import inspect
from typing import Dict, Any, List, Callable, get_type_hints
from functools import wraps
from dataclasses import dataclass


@dataclass
class APIDefinition:
    name: str
    description: str
    method: Callable
    parameters: Dict[str, Dict[str, Any]]
    trigger_words: List[str]


class APIRegistry:
    _apis: Dict[str, APIDefinition] = {}

    @classmethod
    def register(cls, api_def: APIDefinition):
        cls._apis[api_def.method.__name__] = api_def

    @classmethod
    def get_all_apis(cls) -> Dict[str, APIDefinition]:
        return cls._apis.copy()

    @classmethod
    def clear(cls):
        """Clear registry for testing purposes."""
        cls._apis.clear()


def api_method(name: str, description: str, trigger_words: List[str]):
    """
    Decorator to register a method as an API endpoint.
    
    Args:
        name: Human-readable API name
        description: What this API does
        trigger_words: Keywords that might indicate this API should be used
    """
    def decorator(func: Callable):
        # Introspect the function signature
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        parameters = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            param_info = {
                'type': type_hints.get(param_name, str).__name__,
                'required': param.default == inspect.Parameter.empty,
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'description': extract_param_description(func, param_name)
            }
            parameters[param_name] = param_info

        # Register the API
        api_def = APIDefinition(
            name=name,
            description=description,
            method=func,
            parameters=parameters,
            trigger_words=trigger_words
        )

        APIRegistry.register(api_def)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator


def extract_param_description(func: Callable, param_name: str) -> str:
    """Extract parameter description from docstring."""
    if not func.__doc__:
        return ""

    # Simple docstring parsing
    lines = func.__doc__.split('\n')
    in_args_section = False

    for line in lines:
        line = line.strip()
        if line.startswith('Args:'):
            in_args_section = True
            continue
        if in_args_section and line.startswith('Returns:'):
            break
        if in_args_section and line.startswith(f'{param_name}:'):
            return line.split(':', 1)[1].strip()

    return ""