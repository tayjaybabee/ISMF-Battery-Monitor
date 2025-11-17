"""Allow ``python -m ismf_battery_monitor`` execution."""

from .scripts.battery_monitor.main import main

if __name__ == '__main__':  # pragma: no cover
    main()
