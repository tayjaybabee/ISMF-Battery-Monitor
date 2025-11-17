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
            if expected_types:
                if not isinstance(coerced, expected_types):
                    expected = ', '.join(t.__name__ for t in expected_types if isinstance(t, type)) or 'specified types'
                    raise TypeError(f'Expected value of type {expected}, got {type(coerced).__name__}')
            return func(self, coerced, *args, **kwargs)

        return wrapper

    return decorator


def method_alias(*aliases: str) -> Callable:
    """Decorator that records alias names for a method."""

    def decorator(func: Callable) -> Callable:
        setattr(func, '_method_aliases', aliases)
        return func

    return decorator


def add_aliases(cls: type | None = None, **extra_aliases: str) -> Callable | type:
    """Class decorator that wires method aliases declared via ``method_alias``."""

    def _apply(target_cls: type) -> type:
        for name, attr in list(vars(target_cls).items()):
            aliases = getattr(attr, '_method_aliases', ())
            for alias in aliases:
                setattr(target_cls, alias, attr)
        for alias_name, target_name in extra_aliases.items():
            if hasattr(target_cls, target_name):
                setattr(target_cls, alias_name, getattr(target_cls, target_name))
        return target_cls

    if cls is not None:
        return _apply(cls)

    return _apply
