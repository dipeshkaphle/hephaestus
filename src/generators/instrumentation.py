"""
Instrumentation helpers for tracing generator execution.

This module provides generic decorator and helper functions to add debug tracing
to generator methods without cluttering the core logic. Works with all language
generators (Java, Kotlin, Groovy, TypeScript, etc.)

The module is language-agnostic and relies on the debug_tracer in the context
object, which should be present in all generator implementations.
"""
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
import inspect


def trace_method(
    method_name: Optional[str] = None,
    param_names: Optional[List[str]] = None,
    capture_context: bool = True,
    max_str_length: int = 200
) -> Callable:
    """
    Generic decorator to add tracing to any generator method.

    This decorator is language-agnostic and works with any generator that has:
    - self.context.debug_tracer attribute
    - self.depth attribute (optional, only captured if capture_context=True)
    - self.namespace attribute (optional, only captured if capture_context=True)

    Args:
        method_name: Name to use in traces (if None, uses actual method name)
        param_names: List of parameter names to capture. If None, captures all
                     parameters with string truncation. If empty list, captures none.
        capture_context: If True, includes depth and namespace in traces
        max_str_length: Maximum length for stringified parameter values

    Usage:
        # Trace with specific parameters
        @trace_method(param_names=['expr_type', 'only_leaves'])
        def generate_expr(self, expr_type, only_leaves=False, ...):
            # method implementation

        # Trace all parameters
        @trace_method()
        def gen_new(self, expr_type, ...):
            # method implementation

        # Trace with custom name
        @trace_method(method_name='create_class')
        def gen_class_declaration(self):
            # method implementation

        # Trace without context info (minimal)
        @trace_method(capture_context=False, param_names=[])
        def simple_helper(self):
            # method implementation
    """
    def decorator(original_method: Callable) -> Callable:
        @wraps(original_method)
        def wrapper(self, *args, **kwargs):
            # Get tracer from context
            if not hasattr(self, 'context') or not hasattr(self.context, 'debug_tracer'):
                # If no tracer available, just call the method
                return original_method(self, *args, **kwargs)

            tracer = self.context.debug_tracer
            trace_name = method_name or original_method.__name__

            # Build parameter dict
            params = {}

            if param_names is not None:
                # Capture specific parameters
                sig = inspect.signature(original_method)
                try:
                    bound_args = sig.bind(self, *args, **kwargs)
                    bound_args.apply_defaults()

                    for param in param_names:
                        if param in bound_args.arguments:
                            value = bound_args.arguments[param]
                            params[param] = _stringify_value(value, max_str_length)
                except (TypeError, ValueError):
                    # Fallback if binding fails
                    params['args'] = str(args)[:max_str_length]
                    params['kwargs'] = str(kwargs)[:max_str_length]
            elif param_names is None:
                # Capture all parameters (default behavior)
                sig = inspect.signature(original_method)
                try:
                    bound_args = sig.bind(self, *args, **kwargs)
                    bound_args.apply_defaults()

                    # Skip 'self' parameter
                    for param_name, param_value in bound_args.arguments.items():
                        if param_name != 'self':
                            params[param_name] = _stringify_value(param_value, max_str_length)
                except (TypeError, ValueError):
                    # Fallback if binding fails
                    params['args'] = str(args)[:max_str_length]
                    params['kwargs'] = str(kwargs)[:max_str_length]
            # else: param_names is empty list, capture nothing

            # Add context info if requested
            if capture_context:
                if hasattr(self, 'depth'):
                    params['depth'] = self.depth
                if hasattr(self, 'namespace'):
                    params['namespace'] = str(self.namespace)

            # Trace call
            tracer.trace_call(trace_name, params)

            try:
                result = original_method(self, *args, **kwargs)

                # Trace return
                return_info = _build_return_info(result)
                tracer.trace_return(trace_name, return_info)

                return result

            except Exception as e:
                tracer.trace_exception(trace_name, e)
                raise

        return wrapper
    return decorator


def trace_info(generator, method_name: str, info: Dict[str, Any]) -> None:
    """
    Helper function to add informational traces within methods.

    This function is language-agnostic and works with any generator that has
    a context.debug_tracer attribute. Safe to call even if tracer is not available.

    Args:
        generator: The generator instance (self)
        method_name: Name of the current method
        info: Dictionary of information to log

    Usage:
        def generate_expr(self, ...):
            if find_subtype:
                trace_info(self, 'generate_expr', {
                    'decision': 'finding_subtype',
                    'original_type': str(expr_type),
                    'subtypes_found': len(subtypes)
                })

        def gen_typescript_union(self, ...):
            trace_info(self, 'gen_typescript_union', {
                'union_members': [str(t) for t in types],
                'depth': self.depth
            })
    """
    if hasattr(generator, 'context') and hasattr(generator.context, 'debug_tracer'):
        generator.context.debug_tracer.trace_info(method_name, info)


def _stringify_value(value: Any, max_length: int = 200) -> str:
    """
    Convert a value to a string representation suitable for tracing.

    Handles various types safely and truncates long strings.

    Args:
        value: The value to stringify
        max_length: Maximum length of the resulting string

    Returns:
        String representation of the value
    """
    if value is None:
        return 'None'

    # Handle common types that have good string representations
    if isinstance(value, (bool, int, float)):
        return str(value)

    # Handle strings directly
    if isinstance(value, str):
        if len(value) > max_length:
            return value[:max_length] + '...'
        return value

    # Handle types (from src/ir/types.py)
    if hasattr(value, '__class__') and value.__class__.__name__ in [
        'Classifier', 'ParameterizedType', 'TypeVariable', 'WildCardType',
        'FunctionType', 'Type'
    ]:
        result = str(value)
        if len(result) > max_length:
            return result[:max_length] + '...'
        return result

    # Handle AST nodes (from src/ir/ast.py)
    if hasattr(value, '__class__') and hasattr(value, 'namespace'):
        result = f"{value.__class__.__name__}"
        if hasattr(value, 'get_type'):
            try:
                result += f"[{value.get_type()}]"
            except Exception:
                pass
        if len(result) > max_length:
            return result[:max_length] + '...'
        return result

    # Handle collections
    if isinstance(value, (list, tuple, set)):
        try:
            items = [_stringify_value(item, max_length // 4) for item in list(value)[:5]]
            if len(value) > 5:
                items.append(f'... +{len(value) - 5} more')
            result = f"[{', '.join(items)}]"
            if len(result) > max_length:
                return result[:max_length] + '...'
            return result
        except Exception:
            return f"{type(value).__name__}[{len(value)} items]"

    if isinstance(value, dict):
        try:
            items = [f"{k}: {_stringify_value(v, max_length // 4)}"
                    for k, v in list(value.items())[:3]]
            if len(value) > 3:
                items.append(f'... +{len(value) - 3} more')
            result = f"{{{', '.join(items)}}}"
            if len(result) > max_length:
                return result[:max_length] + '...'
            return result
        except Exception:
            return f"dict[{len(value)} items]"

    # Fallback: use string representation
    try:
        result = str(value)
        if len(result) > max_length:
            return result[:max_length] + '...'
        return result
    except Exception:
        return f"{type(value).__name__}[...]"


def _build_return_info(result: Any) -> Dict[str, str]:
    """
    Build information dictionary about a method's return value.

    Args:
        result: The return value from a method

    Returns:
        Dictionary with information about the return value
    """
    info = {}

    if result is None:
        info['result'] = 'None'
        return info

    # Type of the result object
    info['result_type'] = type(result).__name__

    # If it's an AST node with type information
    if hasattr(result, 'get_type'):
        try:
            info['result_value_type'] = str(result.get_type())
        except Exception:
            info['result_value_type'] = 'N/A'

    # If it's a list/collection, include size
    if isinstance(result, (list, tuple, set)):
        info['result_size'] = len(result)

    # If it's a type itself
    if hasattr(result, '__class__') and result.__class__.__name__ in [
        'Classifier', 'ParameterizedType', 'TypeVariable', 'WildCardType',
        'FunctionType', 'Type'
    ]:
        info['result_value'] = str(result)[:100]

    return info
