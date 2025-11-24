"""Lightweight stand-ins for optional Inspyre Toolbox helpers."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterable


class CustomRootException(Exception):
    """Simplified base exception used throughout the project."""


def validate_type(*expected_types: type | tuple[type, ...], preferred_type: type | None = None,
                  conversion_funcs: Iterable[Callable[[Any], Any]] | None = None) -> Callable:
    """Return a decorator that coerces values and validates their type."""

    conversions = list(conversion_funcs or [])

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value, *args, **kwargs):
            coerced = value
            if preferred_type is not None and not isinstance(coerced, preferred_type):
                for converter in conversions:
                    try:
                        coerced = preferred_type(converter(value))
                        break
                    except Exception:
                        continue
            if expected_types and not isinstance(coerced, expected_types):
                expected = ', '.join(t.__name__ for t in expected_types if isinstance(t, type)) or 'specified types'
                raise TypeError(f'Expected value of type {expected}, got {type(coerced).__name__}')
            return func(self, coerced, *args, **kwargs)

        return wrapper

    return decorator


def alias(*method_aliases: str, **class_aliases: str) -> Callable:
    """Decorator for registering method aliases or wiring them onto a class."""

    def decorator(obj: Any) -> Any:
        if isinstance(obj, type):
            for _, attr in vars(obj).items():
                for alias_name in getattr(attr, '_method_aliases', ()):
                    setattr(obj, alias_name, attr)
            for new_name, target_name in class_aliases.items():
                if hasattr(obj, target_name):
                    setattr(obj, new_name, getattr(obj, target_name))
            return obj

        setattr(obj, '_method_aliases', method_aliases)
        return obj

    return decorator
