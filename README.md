# ISMF Battery Monitor

A lightweight battery monitor for the Framework 16 LED matrix expansion cards, powered by [IS-Matrix-Forge](https://github.com/Inspyre-Softworks/IS-Matrix-Forge). It polls the Windows battery APIs, selects an LED scene that matches the current charge level, and renders it across your connected matrices. Plug and unplug animations provide an at-a-glance view of the current power state.

> **Note**
> Battery monitoring is currently implemented only for Windows. Other platforms will raise a clear error when the monitor or CLI is invoked.

## Requirements

- Windows 10/11 with at least one Framework 16 LED matrix controller connected
- Python 3.12+
- [IS-Matrix-Forge](https://pypi.org/project/is-matrix-forge/) and the other dependencies listed in `pyproject.toml`

## Installation

```bash
pip install ismf-battery-monitor
```

To install from a local checkout:

```bash
pip install .
```

## Usage

After installation the `ismf-battery-monitor` command becomes available:

```bash
ismf-battery-monitor --poll-interval 2 --brightness 60
```

The CLI accepts many options (see `--help`), including:

- `--poll-interval`: how frequently to poll the OS for battery updates
- `--brightness`: set LED matrix brightness when rendering scenes
- `--digits-on-bottom/--digits-on-top`: control where the numeric percentage is drawn
- `--no-animations`: disable plug/unplug animations
- `--dry-run`: print what would happen without touching any controllers

The monitor runs until interrupted (Ctrl+C). When the battery percentage crosses the low/critical thresholds the CLI logs informative messages so you can hook the output into your own automation or logging pipeline.

## Library example

You can also use the monitor directly in your own scripts:

```python
from ismf_battery_monitor import BatteryMonitor, get_composite_scene_for_battery_level
from ismf_battery_monitor.controllers import get_cached_controllers

controllers = get_cached_controllers().get()
monitor = BatteryMonitor(poll_interval=2)

def on_status(status):
    if status.battery_percent is None:
        return
    scene = get_composite_scene_for_battery_level(status.battery_percent)
    for controller in controllers:
        scene.draw(controller)

monitor.start(on_status)
```

Remember to call `monitor.stop()` (or use a context manager) when your application exits.

## Development

1. Install development dependencies: `pip install -e .[dev]` or `poetry install` if you prefer Poetry workflows.
2. Run the unit tests with `pytest`.

Contributions and bug reports are welcome!
