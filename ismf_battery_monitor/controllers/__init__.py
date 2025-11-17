"""
Author: Taylor-Jayde Blackstone (Inspyre Softworks)
Project: ISMF Battery Monitor
File: controllers/__init__.py

Description:
    Provides a shared, lazily initialized controller cache instance.
    The cache ensures controller discovery runs only once, on-demand.

Exports:
    cached_controllers (ControllerCache[LEDMatrixController])
"""

from typing import Optional

from ismf_battery_monitor.controllers.cache import ControllerCache
from is_matrix_forge.led_matrix.controller import LEDMatrixController, get_controllers

# Singleton cache instance
_cached_cache: Optional[ControllerCache[LEDMatrixController]] = None


def get_cached_controllers() -> ControllerCache[LEDMatrixController]:
    """
    Return a shared, lazily populated ControllerCache instance.

    Returns:
        ControllerCache[LEDMatrixController]:
            The global controller cache.
    """
    global _cached_cache
    if _cached_cache is None:
        cache = ControllerCache[LEDMatrixController]()
        try:
            controllers = get_controllers(
                threaded=True,
                clear_on_init=True,
                skip_all_init_animations=True
            )
            cache.extend(controllers)
        except Exception as e:
            # Fail gracefully — create an empty cache instead
            print(f"[WARN] Controller discovery failed: {e}")
        _cached_cache = cache
    return _cached_cache


# Preload lazily
cached_controllers = get_cached_controllers()

__all__ = ['cached_controllers', 'get_cached_controllers']
