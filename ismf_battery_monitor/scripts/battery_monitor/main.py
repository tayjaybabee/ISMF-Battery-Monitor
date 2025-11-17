"""CLI entry point for the ISMF Battery Monitor."""

from __future__ import annotations

import logging
import signal
import time
from threading import Event
from typing import List, Optional, Sequence

from ...animations import plugged_in, unplugged
from ...controllers import get_cached_controllers
from ...monitor import BatteryMonitor
from ...scenes import get_composite_scene_for_battery_level
from .arguments import BatteryMonitorArgumentParser


def _configure_logging(args) -> logging.Logger:
    """Configure logging level and destination based on CLI args."""

    if args.quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING
        if args.verbose == 1:
            level = logging.INFO
        elif args.verbose >= 2:
            level = logging.DEBUG

    logging_kwargs = {
        'level': level,
        'format': '[%(asctime)s] %(levelname)s: %(message)s',
    }
    if args.log_file:
        logging_kwargs['filename'] = args.log_file
    logging.basicConfig(**logging_kwargs)
    return logging.getLogger('ismf_battery_monitor.cli')


class BatteryMonitorCLI:
    """Encapsulates the CLI workflow for easier testing and maintenance."""

    def __init__(self, args, *, logger: Optional[logging.Logger] = None):
        self.args = args
        self.logger = logger or logging.getLogger('ismf_battery_monitor.cli')
        self.monitor = BatteryMonitor(poll_interval=args.poll_interval)
        self.stop_event = Event()
        self.controllers: List[object] = []
        self.last_plugged_state: Optional[bool] = None

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def _prepare_controllers(self) -> List[object]:
        cache = get_cached_controllers()
        controllers = cache.get()
        if not controllers:
            raise RuntimeError('No LED matrix controllers detected.')

        for controller in controllers:
            if self.args.brightness is not None:
                controller.set_brightness(self.args.brightness)
            controller.clear()
        return controllers

    def _register_signals(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):  # pragma: no branch - small set
            try:
                signal.signal(sig, self._shutdown)
            except ValueError:
                if sig is signal.SIGINT:
                    raise

    def _shutdown(self, *_):
        if not self.stop_event.is_set():
            self.logger.info('Stopping battery monitor...')
            self.stop_event.set()
            self.monitor.stop()

    def _wait_for_stop(self) -> None:
        try:
            while not self.stop_event.is_set():
                time.sleep(0.2)
        except KeyboardInterrupt:  # pragma: no cover - handled by signals typically
            self._shutdown()

    # ------------------------------------------------------------------
    # Status handling
    # ------------------------------------------------------------------
    def _handle_status(self, status) -> None:
        if status.battery_percent is None:
            self.logger.debug('Battery percent unavailable in snapshot: %s', status)
            return

        scene = get_composite_scene_for_battery_level(
            status.battery_percent,
            digits_on_bottom=self.args.digits_on_bottom,
            invert_on_overlap=self.args.invert_on_overlap,
        )

        for controller in self.controllers:
            try:
                scene.draw(controller)
            except Exception as exc:  # pragma: no cover - hardware specific
                self.logger.error('Failed to draw scene on controller %s: %s', controller, exc)

        if (
            self.args.show_animations
            and self.controllers
            and self.last_plugged_state is not None
            and status.ac_online != self.last_plugged_state
        ):
            animation_fn = plugged_in if status.ac_online else unplugged
            try:
                animation_fn(self.controllers[0])
            except Exception as exc:  # pragma: no cover - hardware specific
                self.logger.warning('Failed to run animation: %s', exc)

        self.last_plugged_state = status.ac_online

        if status.battery_percent <= self.args.critical_battery_threshold:
            self.logger.warning('Battery critical: %s%%', status.battery_percent)
        elif status.battery_percent <= self.args.low_battery_threshold:
            self.logger.info('Battery low: %s%%', status.battery_percent)
        else:
            self.logger.debug('Battery status updated: %s%%', status.battery_percent)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.controllers = self._prepare_controllers()
        self._register_signals()
        self.logger.info('Starting battery monitor loop...')
        self.monitor.start(self._handle_status)
        self._wait_for_stop()
        self.logger.info('Battery monitor stopped.')


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Entrypoint for the ``ismf-battery-monitor`` console script."""

    parser = BatteryMonitorArgumentParser()
    args = parser.parse_args(argv)
    logger = _configure_logging(args)

    if args.dry_run:
        logger.info('Dry run: would start monitoring with poll interval %.2fs', args.poll_interval)
        return

    try:
        cli = BatteryMonitorCLI(args, logger=logger)
    except NotImplementedError as exc:  # pragma: no cover - platform specific
        logger.error(str(exc))
        raise SystemExit(1) from exc

    try:
        cli.run()
    except RuntimeError as err:
        parser.error(str(err))


if __name__ == '__main__':  # pragma: no cover
    main()
