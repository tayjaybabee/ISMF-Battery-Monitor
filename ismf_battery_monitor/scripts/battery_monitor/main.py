"""
CLI entry point for the ISMF Battery Monitor application.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from threading import Event, Thread
from typing import Dict, List, Optional, Sequence

from easy_exit_calls import ExitCallHandler

from is_matrix_forge.led_matrix.controller.helpers import find_leftmost, find_rightmost
from ismf_battery_monitor.log_engine import ROOT_LOGGER, Loggable
from ...animations import play_batt_down_animation, play_batt_up_animation
from ...controllers import get_cached_controllers
from ...monitor import BatteryMonitor
from ...scenes import get_composite_scene_for_battery_level
from .arguments import BatteryMonitorArgumentParser


MOD_LOGGER = ROOT_LOGGER.get_child("ismf_battery_monitor.scripts.battery_monitor.main")
MOD_LOGGER.set_level(console_level="debug")


def _determine_log_level(args) -> int:
    if getattr(args, "quiet", False):
        return logging.ERROR

    verbosity = getattr(args, "verbose", 0) or 0
    if verbosity >= 2:
        return logging.DEBUG
    if verbosity == 1:
        return logging.INFO
    return logging.WARNING


def _configure_logging(args) -> logging.Logger:
    """Configure logging level and destination based on CLI args."""
    level = _determine_log_level(args)

    logger = logging.getLogger("ismf_battery_monitor.cli")
    logger.setLevel(level)
    logger.handlers.clear()

    handler: logging.Handler
    if getattr(args, "log_file", None):
        handler = logging.FileHandler(args.log_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


@dataclass(frozen=True)
class ErrorDecision:
    exit_code: int
    user_message: str
    log_message: str
    can_retry: bool = False


def _looks_like_no_matrix(exc: BaseException) -> bool:
    msg = str(exc)
    return (
        "No LED matrix controllers detected" in msg
        or BatteryMonitorCLI.NO_MATRIX_ERR in msg  # type: ignore[name-defined]
    )


class BatteryMonitorCLI(Loggable):
    """Encapsulates the CLI workflow for easier testing and maintenance."""

    NO_MATRIX_ERR = "No LED matrix controllers detected."

    def __init__(self, args, *, logger: Optional[logging.Logger] = None):
        super().__init__(MOD_LOGGER)

        self._threads: List[Thread] = []
        self._cycles = 0

        self.args = args
        # Use injected logger if provided; otherwise fall back to the Loggable logger.
        self.logger = logger or self.class_logger

        self.monitor = BatteryMonitor(poll_interval=args.poll_interval)
        self.stop_event = Event()

        self.controllers: List[object] = []
        self.last_charging_state: Optional[bool] = None

        self.exit_handler = ExitCallHandler()
        self.exit_handler.register_handler(self._shutdown)

        self._monitor_started = False
        self._controller_states: Dict[object, Dict[str, object]] = {}

    @property
    def cycles(self) -> int:
        return self._cycles

    @property
    def threads(self) -> List[Thread]:
        return self._threads

    @threads.deleter
    def threads(self) -> None:
        for thread in self._threads:
            thread.join()
        self._threads.clear()

    # ------------------------------------------------------------------
    # Error decisioning (centralized)
    # ------------------------------------------------------------------
    def _triage_error(self, exc: BaseException) -> ErrorDecision:
        msg = str(exc)

        if _looks_like_no_matrix(exc):
            return ErrorDecision(
                exit_code=1,
                user_message="No LED matrix controllers detected. Is there at least one matrix module connected?",
                log_message=msg,
                can_retry=False,
            )

        # Keep your existing behavior: everything else exits 1 with a generic message.
        return ErrorDecision(
            exit_code=1,
            user_message=f"An error occurred: {msg}",
            log_message=msg,
            can_retry=False,
        )

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def _prepare_controllers(self) -> List[object]:
        log = self.method_logger
        log.debug("Preparing controllers...")

        cache = get_cached_controllers()
        controllers = cache.get()
        log.debug("Controllers: %s", controllers)

        if not controllers:
            log.error(self.NO_MATRIX_ERR)
            raise RuntimeError(self.NO_MATRIX_ERR)

        log.debug("Filtering controllers...")
        controllers = self._filter_controllers(controllers)
        if not controllers:
            log.error("No LED matrix controllers matched the requested side selection.")
            raise RuntimeError("No LED matrix controllers matched the requested side selection.")

        log.debug("Controllers after filtering: %s", controllers)

        for controller in controllers:
            log.debug("Preparing controller: %s", controller)

            if self.args.brightness is not None:
                log.debug("Setting brightness to %s", self.args.brightness)
                controller.set_brightness(self.args.brightness)

            log.debug("Clearing controller: %s", controller)
            controller.clear()

            log.debug("Enabling keep_alive for controller: %s", controller)
            self._toggle_flag(controller, "keep_alive", True)

            if getattr(self.args, "breathing", False):
                log.debug("Enabling breathing for controller: %s", controller)
                self._toggle_flag(controller, "breathing", True)

        log.debug("Controllers prepared: %s", controllers)
        return controllers

    def _filter_controllers(self, controllers: List[object]) -> List[object]:
        left = find_leftmost(controllers)
        right = find_rightmost(controllers)

        if getattr(self.args, "left_only", False):
            selected = [left]
        elif getattr(self.args, "right_only", False):
            selected = [right]
        else:
            primary = right or left
            secondary = None
            if left is not None and right is not None and left is not right:
                secondary = left if primary is right else right
            selected = [primary, secondary]

        return [ctrl for ctrl in selected if ctrl is not None]

    def _toggle_flag(self, controller: object, name: str, enabled: bool) -> None:
        if not hasattr(controller, name):
            return

        state = self._controller_states.setdefault(controller, {})
        state.setdefault(name, getattr(controller, name))

        try:
            setattr(controller, name, enabled)
        except Exception as exc:  # pragma: no cover - hardware specific
            self.logger.debug("Failed to toggle %s for %s: %s", name, controller, exc)

    def _restore_controllers(self) -> None:
        log = self.method_logger
        for controller, state in self._controller_states.items():
            for name, original in state.items():
                if not hasattr(controller, name):
                    continue
                try:
                    setattr(controller, name, original)
                except Exception as exc:  # pragma: no cover - hardware specific
                    self.logger.debug("Failed to restore %s for %s: %s", name, controller, exc)

            log.debug(f'Clearing matrix {id(controller)}/{controller.location}...')
            controller.clear()

        self._controller_states.clear()

    def _shutdown(self, *_: object) -> None:
        if self.stop_event.is_set():
            return

        if self._monitor_started:
            self.logger.info("Stopping battery monitor...")

        self.stop_event.set()

        if self._monitor_started:
            self.monitor.stop()

        self._restore_controllers()

    def _wait_for_stop(self) -> None:
        log = self.method_logger
        waits = 0
        try:
            while not self.stop_event.is_set():
                if waits >= 150:
                    log.debug("Waiting for stop...")
                    waits = 0
                waits += 1
                self._cycles += 1
                time.sleep(0.2)
        except KeyboardInterrupt:  # pragma: no cover
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
        self._maybe_run_animation(status.charging)
        self._log_battery_level(pct)
        self.last_charging_state = status.charging

    def _log_unavailable(self, status) -> None:
        self.logger.debug("Battery percent unavailable in snapshot: %s", status)

    def _draw_scene(self, battery_percent: int, charging_state: Optional[bool]) -> None:
        scene = get_composite_scene_for_battery_level(
            battery_percent,
            digits_on_bottom=self.args.digits_on_bottom,
            invert_on_overlap=self.args.invert_on_overlap,
            charging_state=charging_state,
        )

        for controller in self.controllers:
            t = Thread(target=scene.draw, args=(controller,))
            try:
                t.start()
                # If you want to join these later, track them:
                self.threads.append(t)
            except Exception as exc:  # pragma: no cover - hardware specific
                self.logger.error("Failed to draw scene on controller %s: %s", controller, exc)

    def _maybe_run_animation(self, charging: Optional[bool]) -> None:
        log = self.method_logger

        if not (
            getattr(self.args, "show_animations", False)
            and self.controllers
            and charging is not None
        ):
            log.debug("Not running animation: %s", charging)
            return

        has_secondary = len(self.controllers) > 1
        last = self.last_charging_state
        if has_secondary:
            should_animate = charging != last
        else:
            should_animate = last is not None and charging != last

        if not should_animate:
            log.debug(
                "Not running animation (%s controller rule), state: %s → %s",
                "secondary" if has_secondary else "primary",
                last,
                charging,
            )
            return

        log.debug("Running animation: %s", charging)
        animation_fn = play_batt_up_animation if charging else play_batt_down_animation

        args = self.args
        opts = {
            "brightness": args.animation_brightness,
            "frame_duration": args.frame_duration,
            "direction": args.scroll_direction,
            "loop": has_secondary,
        }

        controller = self.controllers[1] if has_secondary else self.controllers[0]
        log.debug(
            "Running animation on %s controller: %s, charging=%s, loop=%s",
            "secondary" if has_secondary else "primary",
            controller,
            charging,
            opts["loop"],
        )

        t = Thread(target=animation_fn, args=(controller,), kwargs=opts)
        try:
            t.start()
            self.threads.append(t)
        except Exception as exc:  # pragma: no cover - hardware specific
            log.warning("Failed to run animation on %s: %s", controller, exc)

    def _log_battery_level(self, battery_percent: int) -> None:
        if battery_percent <= self.args.critical_battery_threshold:
            self.logger.warning("Battery critical: %s%%", battery_percent)
        elif battery_percent <= self.args.low_battery_threshold:
            self.logger.info("Battery low: %s%%", battery_percent)
        else:
            self.logger.debug("Battery status updated: %s%%", battery_percent)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        log = self.method_logger

        # Optional: if you later add an arg, this won’t crash without it.
        max_attempts = 2 if getattr(self.args, "recover_once", False) else 1

        try:
            for attempt in range(1, max_attempts + 1):
                try:
                    self.controllers = self._prepare_controllers()
                    log.info("Starting battery monitor loop...")
                    self.monitor.start(self._handle_status)
                    self._monitor_started = True
                    self._wait_for_stop()
                    break
                except Exception as exc:
                    decision = self._triage_error(exc)
                    log.error(f'Battery monitor loop failed: {decision.log_message}')

                    if decision.can_retry and attempt < max_attempts:
                        log.warning(f"Attempting recovery ({attempt}/{max_attempts})...")

                        self._shutdown()
                        # reset for next attempt
                        self.stop_event.clear()
                        self._monitor_started = False
                        continue

                    raise SystemExit(decision.exit_code) from exc

        finally:
            log.debug("Cleaning up exit handlers...")
            if self.exit_handler.function_registered(self._shutdown):
                log.debug("Unregistering found exit handler...")
                self.exit_handler.unregister_handler(self._shutdown)
            else:
                log.debug("No exit handler found.")
            self._shutdown()

        if self._monitor_started:
            log.info("Battery monitor stopped.")


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Entrypoint for the ``ismf-battery-monitor`` console script."""
    parser = BatteryMonitorArgumentParser()
    args = parser.parse_args(argv)
    logger = _configure_logging(args)

    if getattr(args, "dry_run", False):
        logger.info("Dry run: would start monitoring with poll interval %.2fs", args.poll_interval)
        return

    try:
        cli = BatteryMonitorCLI(args, logger=logger)
        cli.run()
    except NotImplementedError as exc:  # pragma: no cover - platform specific
        logger.error(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":  # pragma: no cover
    main()
