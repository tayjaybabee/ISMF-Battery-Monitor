"""OS-aware BatteryMonitor dispatcher."""

from __future__ import annotations

import sys
from typing import Type

if sys.platform.startswith('win'):
    from .windows import BatteryMonitor as _BatteryMonitor  # noqa: F401
else:
    class _BatteryMonitor:  # type: ignore[too-many-ancestors]
        """Stub BatteryMonitor for unsupported platforms."""

        def __init__(self, *_, **__):
            raise NotImplementedError(
                'Battery monitoring is currently implemented only on Windows.'
            )

BatteryMonitor: Type[_BatteryMonitor] = _BatteryMonitor

__all__ = ['BatteryMonitor']
