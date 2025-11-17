"""CLI entry point for the ISMF Battery Monitor."""

from __future__ import annotations

import logging
import time
from threading import Event
from typing import Dict, List, Optional, Sequence

from easy_exit_calls import ExitCallHandler

from is_matrix_forge.led_matrix.controller.helpers import find_leftmost, find_rightmost

from ...animations import plugged_in, unplugged
from ...controllers import get_cached_controllers
from ...monitor import BatteryMonitor
from ...scenes import get_composite_scene_for_battery_level
from .arguments import BatteryMonitorArgumentParser


def _determine_log_level(args) -> int:
    if getattr(args, 'quiet', False):
        return logging.ERROR

    verbosity = getattr(args, 'verbose', 0) or 0
    if verbosity >= 2:
        return logging.DEBUG
    if verbosity == 1:
        return logging.INFO
    return logging.WARNING


def _configure_logging(args) -> logging.Logger:
    """Configure logging level and destination based on CLI args."""

    level = _determine_log_level(args)

    logger = logging.getLogger('ismf_battery_monitor.cli')
    logger.setLevel(level)
    logger.handlers.clear()
    handler: logging.Handler
    if args.log_file:
        handler = logging.FileHandler(args.log_file, encoding='utf-8')
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


class BatteryMonitorCLI:
    """Encapsulates the CLI workflow for easier testing and maintenance."""

    def __init__(self, args, *, logger: Optional[logging.Logger] = None):
        self.args = args
        self.logger = logger or logging.getLogger('ismf_battery_monitor.cli')
        self.monitor = BatteryMonitor(poll_interval=args.poll_interval)
        self.stop_event = Event()
        self.controllers: List[object] = []
        self.last_plugged_state: Optional[bool] = None
        self.exit_handler = ExitCallHandler()
        self.exit_handler.register_handler(self._shutdown)
        self._monitor_started = False
        self._controller_states: Dict[object, Dict[str, object]] = {}

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def _prepare_controllers(self) -> List[object]:
        cache = get_cached_controllers()
        controllers = cache.get()
        if not controllers:
            raise RuntimeError('No LED matrix controllers detected.')

        controllers = self._filter_controllers(controllers)
        if not controllers:
            raise RuntimeError('No LED matrix controllers matched the requested side selection.')

        for controller in controllers:
            if self.args.brightness is not None:
                controller.set_brightness(self.args.brightness)
            controller.clear()
            self._toggle_flag(controller, 'keep_alive', True)
            if self.args.breathing:
                self._toggle_flag(controller, 'breathing', True)
        return controllers

    def _filter_controllers(self, controllers: List[object]) -> List[object]:
        if getattr(self.args, 'left_only', False):
            selected = [find_leftmost(controllers)]
        elif getattr(self.args, 'right_only', False):
            selected = [find_rightmost(controllers)]
        else:
            selected = controllers
        return [ctrl for ctrl in selected if ctrl is not None]

    def _toggle_flag(self, controller, name: str, enabled: bool) -> None:
        if not hasattr(controller, name):
            return
        state = self._controller_states.setdefault(controller, {})
        state.setdefault(name, getattr(controller, name))
        try:
            setattr(controller, name, enabled)
        except Exception as exc:  # pragma: no cover - hardware specific
            self.logger.debug('Failed to toggle %s for %s: %s', name, controller, exc)

    def _restore_controllers(self) -> None:
        for controller, state in self._controller_states.items():
            for name, original in state.items():
                if not hasattr(controller, name):
                    continue
                try:
                    setattr(controller, name, original)
                except Exception as exc:  # pragma: no cover - hardware specific
                    self.logger.debug('Failed to restore %s for %s: %s', name, controller, exc)
        self._controller_states.clear()

    def _shutdown(self, *_):
        if self.stop_event.is_set():
            return

        if self._monitor_started:
            self.logger.info('Stopping battery monitor...')
        self.stop_event.set()
        if self._monitor_started:
            self.monitor.stop()
        self._restore_controllers()

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
            self._log_unavailable(status)
            return

        pct = status.battery_percent
        self._draw_scene(pct, status.charging)
        self._maybe_run_animation(status.ac_online)
        self._log_battery_level(pct)
        self.last_plugged_state = status.ac_online

    def _log_unavailable(self, status) -> None:
        self.logger.debug('Battery percent unavailable in snapshot: %s', status)

    def _draw_scene(self, battery_percent: int, charging_state: Optional[bool]) -> None:
        scene = get_composite_scene_for_battery_level(
            battery_percent,
            digits_on_bottom=self.args.digits_on_bottom,
            invert_on_overlap=self.args.invert_on_overlap,
            charging_state=charging_state,
        )

        for controller in self.controllers:
            try:
                scene.draw(controller)
            except Exception as exc:  # pragma: no cover - hardware specific
                self.logger.error('Failed to draw scene on controller %s: %s', controller, exc)

    def _maybe_run_animation(self, ac_online: Optional[bool]) -> None:
        if not (
            self.args.show_animations
            and self.controllers
            and self.last_plugged_state is not None
            and ac_online is not None
            and ac_online != self.last_plugged_state
        ):
            return

        animation_fn = plugged_in if ac_online else unplugged
        for controller in self.controllers:
            try:
                animation_fn(
                    controller,
                    brightness=self.args.animation_brightness,
                    frame_duration=self.args.frame_duration,
                    direction=self.args.scroll_direction,
                )
            except Exception as exc:  # pragma: no cover - hardware specific
                self.logger.warning('Failed to run animation on %s: %s', controller, exc)

    def _log_battery_level(self, battery_percent: int) -> None:
        if battery_percent <= self.args.critical_battery_threshold:
            self.logger.warning('Battery critical: %s%%', battery_percent)
        elif battery_percent <= self.args.low_battery_threshold:
            self.logger.info('Battery low: %s%%', battery_percent)
        else:
            self.logger.debug('Battery status updated: %s%%', battery_percent)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        try:
            self.controllers = self._prepare_controllers()
            self.logger.info('Starting battery monitor loop...')
            self.monitor.start(self._handle_status)
            self._monitor_started = True
            self._wait_for_stop()
        finally:
            self.exit_handler.unregister_handler(self._shutdown)
            self._shutdown()
        if self._monitor_started:
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
