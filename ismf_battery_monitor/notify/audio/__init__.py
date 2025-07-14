from chime import play_wav
from .files import AUDIO_MAP as PLUG_ALERT_MAP
from is_matrix_forge.log_engine import ROOT_LOGGER as PARENT_LOGGER


MOD_LOGGER = PARENT_LOGGER.get_child('assets.audio')


def alert(alert_type: str):
    """
    Plays an alert sound.

    Parameters:
        alert_type (str):
            The type of alert sound to play.
    """
    log = MOD_LOGGER.get_child('alert')

    if not isinstance(alert_type, str):
        log.error(f'"alert_type" must be a string, not {type(alert_type)}')
        raise TypeError(f'alert_type must be a string, not {type(alert_type)}')

    alert_type = alert_type.lower().strip()
    log.debug(f'Checking if alert_type is valid: {alert_type} ({type(alert_type)})')
    if alert_type not in PLUG_ALERT_MAP:
        log.error(f'Invalid alert_type: {alert_type}')
        raise ValueError(f'alert_type must be one of {", ".join(PLUG_ALERT_MAP.keys())}')

    log.debug(f'Playing alert sound: {alert_type}')
    play_wav(PLUG_ALERT_MAP[alert_type])


__all__ = [
    'alert'
]

