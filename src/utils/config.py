"""Configuration Management Module"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.utils.logger import logger


class ConfigError(Exception):
    """Configuration file error"""
    pass


class ConfigManager:
    """Configuration file manager"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager

        Args:
            config_path: Configuration file path

        Raises:
            ConfigError: When config file doesn't exist or has invalid format
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration file

        Returns:
            dict: Configuration content

        Raises:
            ConfigError: When config file doesn't exist or cannot be parsed
        """
        if not self.config_path.exists():
            raise ConfigError(f"Config file does not exist: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                raise ConfigError("Config file is empty")

            logger.info(f"Config file loaded successfully: {self.config_path}")
            return config

        except yaml.YAMLError as e:
            raise ConfigError(f"Config file format error: {e}")
        except Exception as e:
            raise ConfigError(f"Cannot read config file: {e}")

    def _validate_config(self) -> None:
        """
        Validate required config fields

        Raises:
            ConfigError: When required fields are missing or have invalid format
        """
        required_keys = ['location', 'tracking', 'api']
        for key in required_keys:
            if key not in self.config:
                raise ConfigError(f"Config missing required field: {key}")

        location = self.config['location']
        if 'lat' not in location or 'lng' not in location:
            raise ConfigError("location must contain lat and lng")

        try:
            lat = float(location['lat'])
            lng = float(location['lng'])

            if not (-90 <= lat <= 90):
                raise ConfigError(f"Latitude out of range (-90 to 90): {lat}")
            if not (-180 <= lng <= 180):
                raise ConfigError(f"Longitude out of range (-180 to 180): {lng}")

        except (ValueError, TypeError) as e:
            raise ConfigError(f"Coordinate format error: {e}")

        tracking = self.config['tracking']
        required_tracking = ['enter_point', 'exit_point']
        for key in required_tracking:
            if key not in tracking:
                raise ConfigError(f"tracking missing required field: {key}")
            if not tracking[key] or not isinstance(tracking[key], str):
                raise ConfigError(f"{key} must be a non-empty string")

        if tracking['enter_point'] == tracking['exit_point']:
            raise ConfigError("Enter point and exit point cannot be the same")

        trigger_mode = tracking.get('trigger_mode', 'arriving')
        if trigger_mode not in ['arriving', 'arrived']:
            raise ConfigError(f"trigger_mode must be 'arriving' or 'arrived': {trigger_mode}")

        logger.info("Config validation passed")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value (supports nested keys like 'api.server.port')

        Args:
            key: Config key (supports dot-separated nested keys)
            default: Default value

        Returns:
            Config value, or default if not exists
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    @property
    def location(self) -> Dict[str, float]:
        """Get query location coordinates"""
        return {
            'lat': float(self.config['location']['lat']),
            'lng': float(self.config['location']['lng'])
        }

    @property
    def target_lines(self) -> List[str]:
        """Get list of routes to track"""
        lines = self.config['tracking'].get('target_lines', [])
        return lines if lines else []

    @property
    def enter_point(self) -> str:
        """Get enter point name"""
        return self.config['tracking']['enter_point']

    @property
    def exit_point(self) -> str:
        """Get exit point name"""
        return self.config['tracking']['exit_point']

    @property
    def trigger_mode(self) -> str:
        """Get trigger mode"""
        return self.config['tracking'].get('trigger_mode', 'arriving')

    @property
    def approaching_threshold(self) -> int:
        """Get number of stops ahead for early notification"""
        return self.config['tracking'].get('approaching_threshold', 2)

    @property
    def log_level(self) -> str:
        """Get log level"""
        return self.config.get('system', {}).get('log_level', 'INFO')

    @property
    def api_timeout(self) -> int:
        """Get API timeout"""
        return self.config.get('api', {}).get('ntpc', {}).get('timeout', 10)

    @property
    def api_base_url(self) -> str:
        """Get NTPC API base URL"""
        return self.config.get('api', {}).get('ntpc', {}).get(
            'base_url',
            'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI'
        )

    @property
    def server_host(self) -> str:
        """Get Flask server host"""
        return self.config.get('api', {}).get('server', {}).get('host', '0.0.0.0')

    @property
    def server_port(self) -> int:
        """Get Flask server port"""
        return self.config.get('api', {}).get('server', {}).get('port', 5000)

    @property
    def server_debug(self) -> bool:
        """Get Flask debug mode"""
        return self.config.get('api', {}).get('server', {}).get('debug', False)

    def __str__(self) -> str:
        """Return string representation of config"""
        return (
            f"ConfigManager(\n"
            f"  location: ({self.location['lat']:.4f}, {self.location['lng']:.4f})\n"
            f"  enter_point: {self.enter_point}\n"
            f"  exit_point: {self.exit_point}\n"
            f"  trigger_mode: {self.trigger_mode}\n"
            f"  target_lines: {self.target_lines or 'all routes'}\n"
            f")"
        )
