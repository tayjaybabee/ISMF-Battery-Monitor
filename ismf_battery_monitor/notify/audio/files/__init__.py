from pathlib import Path
from is_matrix_forge.log_engine import ROOT_LOGGER as PARENT_LOGGER


MOD_LOGGER = PARENT_LOGGER.get_child('assets.audio.files')


CUR_DIR = Path(__file__).parent.expanduser().resolve().absolute()
MOD_LOGGER.debug(f'Audio files directory: {CUR_DIR}')

AUDIO_MAP = {
    'plugged': CUR_DIR / 'plugged.wav',
    'unplugged': CUR_DIR / 'unplugged.wav'
}


def integrity_check():
    """
    Checks the integrity of the audio files.

    Raises:
        FileNotFoundError:
            If any of the audio files are not found.

    Returns:
        None
    """
    log = MOD_LOGGER.get_child('integrity_check')
    log.debug('Checking audio files...')
    for file in AUDIO_MAP.values():
        log.debug(f'Checking file: {file}')
        if not file.exists():
            log.error(f'File not found: {file}')
            raise FileNotFoundError(f'Audio file not found: {file}')

        if not file.is_file():
            log.error(f'File is not a file: {file}')
            raise FileNotFoundError(f'Audio file not found: {file}')

    log.debug('Audio files are valid.')
    return True


MOD_LOGGER.debug('Performing integrity check...')

if not integrity_check():
    MOD_LOGGER.error('Audio files are invalid.')
    raise FileNotFoundError('Audio files are invalid.')


__all__ = [
    'AUDIO_MAP',
]
