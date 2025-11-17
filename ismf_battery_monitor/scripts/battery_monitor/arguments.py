import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional, Sequence

from platformdirs import PlatformDirs


class BatteryMonitorArgumentParser(ArgumentParser):
    """ArgumentParser subclass with all battery monitor options."""
    
    def __init__(self, *args, **kwargs):
        # Set defaults for the parser if not provided
        if 'description' not in kwargs:
            kwargs['description'] = (
                'Monitor battery status and display it on the Framework 16 LED matrix module.'
            )
        if 'prog' not in kwargs:
            kwargs['prog'] = 'battery-monitor'
        
        super().__init__(*args, **kwargs)
        self._config_file_path: Optional[Path] = None
        self._add_arguments()
    
    @staticmethod
    def get_default_config_path() -> Path:
        """Get the default configuration file path."""
        platform_dirs = PlatformDirs(appauthor='Inspyre Softworks', appname='ISMF-Battery-Monitor')
        config_dir = Path(platform_dirs.user_config_path)
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.json'
    
    def _add_arguments(self):
        """Add all available arguments for the battery monitor."""
        
        # Monitoring options
        monitoring_group = self.add_argument_group('Monitoring Options')
        monitoring_group.add_argument(
            '-i', '--poll-interval',
            type=float,
            default=1.0,
            metavar='SECONDS',
            help='Interval in seconds between battery status checks (default: 1.0)'
        )
        monitoring_group.add_argument(
            '--low-battery-threshold',
            type=int,
            default=20,
            metavar='PERCENT',
            help='Battery percentage threshold for low battery warning (default: 20)'
        )
        monitoring_group.add_argument(
            '--critical-battery-threshold',
            type=int,
            default=10,
            metavar='PERCENT',
            help='Battery percentage threshold for critical battery warning (default: 10)'
        )
        
        # Display options
        display_group = self.add_argument_group('Display Options')
        display_group.add_argument(
            '-b', '--brightness',
            type=int,
            default=50,
            metavar='PERCENT',
            help='LED matrix brightness percentage (0-100, default: 50)'
        )
        display_group.add_argument(
            '--invert-on-overlap',
            action='store_true',
            default=True,
            help='Invert pixels when foreground and background overlap (default: True)'
        )
        display_group.add_argument(
            '--no-invert-on-overlap',
            action='store_false',
            dest='invert_on_overlap',
            help='Disable pixel inversion on overlap'
        )
        display_group.add_argument(
            '--digits-on-bottom',
            action='store_true',
            help='Force battery percentage digits to bottom of display'
        )
        display_group.add_argument(
            '--digits-on-top',
            action='store_false',
            dest='digits_on_bottom',
            help='Force battery percentage digits to top of display'
        )
        
        # Animation options
        animation_group = self.add_argument_group('Animation Options')
        animation_group.add_argument(
            '--show-animations',
            action='store_true',
            default=True,
            help='Show animations when plugging/unplugging (default: True)'
        )
        animation_group.add_argument(
            '--no-animations',
            action='store_false',
            dest='show_animations',
            help='Disable plug/unplug animations'
        )
        animation_group.add_argument(
            '--animation-brightness',
            type=int,
            default=50,
            metavar='PERCENT',
            help='Brightness for plug/unplug animations (0-100, default: 50)'
        )
        animation_group.add_argument(
            '--frame-duration',
            type=float,
            default=0.03,
            metavar='SECONDS',
            help='Duration of each animation frame in seconds (default: 0.03)'
        )
        animation_group.add_argument(
            '--scroll-direction',
            choices=['vertical_up', 'vertical_down', 'horizontal_left', 'horizontal_right'],
            default='vertical_up',
            help='Direction for scrolling text animations (default: vertical_up)'
        )
        
        # Device options
        device_group = self.add_argument_group('Device Options')
        device_group.add_argument(
            '-d', '--device',
            type=str,
            metavar='PATH',
            help='Path to the LED matrix device (auto-detect if not specified)'
        )
        device_group.add_argument(
            '--thread-safe',
            action='store_true',
            default=True,
            help='Enable thread-safe mode for the controller (default: True)'
        )
        device_group.add_argument(
            '--no-thread-safe',
            action='store_false',
            dest='thread_safe',
            help='Disable thread-safe mode'
        )
        
        # Runtime options
        runtime_group = self.add_argument_group('Runtime Options')
        runtime_group.add_argument(
            '--daemon',
            action='store_true',
            help='Run as a background daemon'
        )
        runtime_group.add_argument(
            '--foreground',
            action='store_false',
            dest='daemon',
            help='Run in foreground (default)'
        )
        runtime_group.add_argument(
            '-v', '--verbose',
            action='count',
            default=0,
            help='Increase verbosity level (can be repeated: -v, -vv, -vvv)'
        )
        runtime_group.add_argument(
            '-q', '--quiet',
            action='store_true',
            help='Suppress all output except errors'
        )
        runtime_group.add_argument(
            '--log-file',
            type=str,
            metavar='PATH',
            help='Path to log file (default: log to console)'
        )
        
        # Configuration options
        config_group = self.add_argument_group('Configuration Options')
        config_group.add_argument(
            '-c', '--config-file',
            type=str,
            metavar='PATH',
            help='Path to configuration file (default: platform-specific user config directory)'
        )
        config_group.add_argument(
            '--do-not-save-config',
            action='store_true',
            help='Do not save current options to the config file'
        )
        config_group.add_argument(
            '--no-config',
            action='store_true',
            help='Do not load or save configuration file'
        )
        
        # Miscellaneous options
        misc_group = self.add_argument_group('Miscellaneous Options')
        misc_group.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0-dev.1'
        )
        misc_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )


    def _load_config(self, config_path: Path) -> dict:
        """Load configuration from a JSON file."""
        if not config_path.exists():
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            return {}
    
    def _save_config_pointer(self, custom_config_path: Path) -> None:
        """Save a pointer to a custom config location in the default location."""
        default_path = self.get_default_config_path()
        if default_path != custom_config_path:
            try:
                default_path.parent.mkdir(parents=True, exist_ok=True)
                pointer_data = {
                    "_config_pointer": str(custom_config_path.resolve())
                }
                with open(default_path, 'w', encoding='utf-8') as f:
                    json.dump(pointer_data, f, indent=2)
            except IOError as e:
                print(f"Warning: Failed to save config pointer to {default_path}: {e}")
    
    def _save_config(self, config_path: Path, args: Namespace) -> None:
        """Save configuration to a JSON file."""
        # Convert namespace to dict, excluding certain runtime-only options
        config = vars(args).copy()
        
        # Remove options that shouldn't be saved
        exclude_keys = {'do_not_save_config', 'no_config', 'config_file', 'dry_run', 'version'}
        for key in exclude_keys:
            config.pop(key, None)
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            # If using a custom config path, save a pointer at the default location
            default_path = self.get_default_config_path()
            if config_path.resolve() != default_path.resolve():
                self._save_config_pointer(config_path)
        except IOError as e:
            print(f"Warning: Failed to save config to {config_path}: {e}")
    
    def _resolve_config_path(self, specified_path: Optional[str]) -> Path:
        """Resolve the config file path, following pointers if necessary."""
        if specified_path:
            # User explicitly specified a path
            return Path(specified_path)
        
        # Check default location
        default_path = self.get_default_config_path()
        
        # If default config exists, check if it's a pointer
        if default_path.exists():
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Check if this is a pointer file
                    if '_config_pointer' in data and len(data) == 1:
                        pointer_path = Path(data['_config_pointer'])
                        if pointer_path.exists():
                            return pointer_path
                        else:
                            print(f"Warning: Config pointer references non-existent file: {pointer_path}")
                            print(f"Using default location: {default_path}")
            except (json.JSONDecodeError, IOError):
                pass  # Not a pointer, or corrupt file - use default
        
        return default_path
    
    def parse_args(self, args: Optional[Sequence[str]] = None, namespace: Optional[Namespace] = None) -> Namespace:
        """Parse arguments with config file support."""
        # First, parse args to get config-related options
        parsed_args = super().parse_args(args, namespace)
        
        # Determine if we should use config
        if parsed_args.no_config:
            return parsed_args
        
        # Determine config file path (follow pointers if needed)
        self._config_file_path = self._resolve_config_path(parsed_args.config_file)
        
        # Load config file
        config_data = self._load_config(self._config_file_path)
        
        # Set defaults from config file (command-line args override config file)
        if config_data:
            # Re-parse with config as defaults
            for key, value in config_data.items():
                if hasattr(parsed_args, key):
                    # Only use config value if command-line didn't specify it
                    if key not in self._get_args_from_command_line(args or []):
                        setattr(parsed_args, key, value)
        
        # Save config if not disabled
        if not parsed_args.do_not_save_config and not parsed_args.dry_run:
            self._save_config(self._config_file_path, parsed_args)
        
        return parsed_args
    
    def _get_args_from_command_line(self, args: Sequence[str]) -> set:
        """Extract which arguments were actually provided on the command line."""
        provided = set()
        for action in self._actions:
            for option_string in action.option_strings:
                if option_string in args:
                    provided.add(action.dest)
        return provided


__all__ = ['BatteryMonitorArgumentParser']



