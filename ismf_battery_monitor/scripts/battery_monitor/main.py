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


def _prepare_controllers(brightness: Optional[int]) -> List[object]:
    cache = get_cached_controllers()
    controllers = cache.get()
    if not controllers:
        raise RuntimeError('No LED matrix controllers detected.')

    for controller in controllers:
        if brightness is not None:
            controller.set_brightness(brightness)
        controller.clear()
    return controllers


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Entrypoint for the ``ismf-battery-monitor`` console script."""

    parser = BatteryMonitorArgumentParser()
    args = parser.parse_args(argv)
    logger = _configure_logging(args)

    if args.dry_run:
        logger.info('Dry run: would start monitoring with poll interval %.2fs', args.poll_interval)
        return

    try:
        monitor = BatteryMonitor(poll_interval=args.poll_interval)
    except NotImplementedError as exc:  # pragma: no cover - platform specific
        logger.error(str(exc))
        raise SystemExit(1) from exc

    controllers: List[object] = []
    if not args.dry_run:
        try:
            controllers = _prepare_controllers(args.brightness)
        except RuntimeError as err:
            parser.error(str(err))

    last_plugged_state: Optional[bool] = None

    def handle_status(status) -> None:
        nonlocal last_plugged_state
        if status.battery_percent is None:
            logger.debug('Battery percent unavailable in snapshot: %s', status)
            return

        scene = get_composite_scene_for_battery_level(
            status.battery_percent,
            digits_on_bottom=args.digits_on_bottom,
            invert_on_overlap=args.invert_on_overlap,
        )

        for controller in controllers:
            try:
                scene.draw(controller)
            except Exception as exc:  # pragma: no cover - hardware specific
                logger.error('Failed to draw scene on controller %s: %s', controller, exc)

        if (
            args.show_animations
            and controllers
            and last_plugged_state is not None
            and status.ac_online != last_plugged_state
        ):
            animation_fn = plugged_in if status.ac_online else unplugged
            try:
                animation_fn(controllers[0])
            except Exception as exc:  # pragma: no cover - hardware specific
                logger.warning('Failed to run animation: %s', exc)

        last_plugged_state = status.ac_online

        if status.battery_percent <= args.critical_battery_threshold:
            logger.warning('Battery critical: %s%%', status.battery_percent)
        elif status.battery_percent <= args.low_battery_threshold:
            logger.info('Battery low: %s%%', status.battery_percent)
        else:
            logger.debug('Battery status updated: %s%%', status.battery_percent)

    stop_event = Event()

    def _shutdown(*_):
        if not stop_event.is_set():
            logger.info('Stopping battery monitor...')
            stop_event.set()
            monitor.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):  # pragma: no branch - small set
        try:
            signal.signal(sig, _shutdown)
        except ValueError:
            # Some platforms (like Windows) may not support SIGTERM
            if sig is signal.SIGINT:
                raise

    logger.info('Starting battery monitor loop...')
    monitor.start(handle_status)

    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:  # pragma: no cover - handled by signals typically
        _shutdown()

    logger.info('Battery monitor stopped.')


if __name__ == '__main__':  # pragma: no cover
    main()
