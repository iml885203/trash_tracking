"""設定管理模組"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.utils.logger import logger


class ConfigError(Exception):
    """設定檔錯誤"""
    pass


class ConfigManager:
    """設定檔管理器"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化設定管理器

        Args:
            config_path: 設定檔路徑

        Raises:
            ConfigError: 當設定檔不存在或格式錯誤時
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        載入設定檔

        Returns:
            dict: 設定內容

        Raises:
            ConfigError: 當設定檔不存在或無法解析時
        """
        if not self.config_path.exists():
            raise ConfigError(f"設定檔不存在: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                raise ConfigError("設定檔為空")

            logger.info(f"成功載入設定檔: {self.config_path}")
            return config

        except yaml.YAMLError as e:
            raise ConfigError(f"設定檔格式錯誤: {e}")
        except Exception as e:
            raise ConfigError(f"無法讀取設定檔: {e}")

    def _validate_config(self) -> None:
        """
        驗證設定檔必要欄位

        Raises:
            ConfigError: 當必要欄位缺失或格式錯誤時
        """
        # 驗證必要的頂層鍵
        required_keys = ['location', 'tracking', 'api']
        for key in required_keys:
            if key not in self.config:
                raise ConfigError(f"設定檔缺少必要欄位: {key}")

        # 驗證 location
        location = self.config['location']
        if 'lat' not in location or 'lng' not in location:
            raise ConfigError("location 必須包含 lat 和 lng")

        try:
            lat = float(location['lat'])
            lng = float(location['lng'])

            if not (-90 <= lat <= 90):
                raise ConfigError(f"緯度超出範圍 (-90 到 90): {lat}")
            if not (-180 <= lng <= 180):
                raise ConfigError(f"經度超出範圍 (-180 到 180): {lng}")

        except (ValueError, TypeError) as e:
            raise ConfigError(f"座標格式錯誤: {e}")

        # 驗證 tracking
        tracking = self.config['tracking']
        required_tracking = ['enter_point', 'exit_point']
        for key in required_tracking:
            if key not in tracking:
                raise ConfigError(f"tracking 缺少必要欄位: {key}")
            if not tracking[key] or not isinstance(tracking[key], str):
                raise ConfigError(f"{key} 必須為非空字串")

        # 驗證進入點和離開點不可相同
        if tracking['enter_point'] == tracking['exit_point']:
            raise ConfigError("進入清運點和離開清運點不可相同")

        # 驗證 trigger_mode
        trigger_mode = tracking.get('trigger_mode', 'arriving')
        if trigger_mode not in ['arriving', 'arrived']:
            raise ConfigError(f"trigger_mode 必須為 'arriving' 或 'arrived': {trigger_mode}")

        logger.info("設定檔驗證通過")

    def get(self, key: str, default: Any = None) -> Any:
        """
        取得設定值（支援巢狀鍵，例如 'api.server.port'）

        Args:
            key: 設定鍵（支援點號分隔的巢狀鍵）
            default: 預設值

        Returns:
            設定值，若不存在則返回 default
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
        """取得查詢位置座標"""
        return {
            'lat': float(self.config['location']['lat']),
            'lng': float(self.config['location']['lng'])
        }

    @property
    def target_lines(self) -> List[str]:
        """取得追蹤的路線清單"""
        lines = self.config['tracking'].get('target_lines', [])
        return lines if lines else []

    @property
    def enter_point(self) -> str:
        """取得進入清運點名稱"""
        return self.config['tracking']['enter_point']

    @property
    def exit_point(self) -> str:
        """取得離開清運點名稱"""
        return self.config['tracking']['exit_point']

    @property
    def trigger_mode(self) -> str:
        """取得觸發模式"""
        return self.config['tracking'].get('trigger_mode', 'arriving')

    @property
    def approaching_threshold(self) -> int:
        """取得提前通知停靠點數"""
        return self.config['tracking'].get('approaching_threshold', 2)

    @property
    def log_level(self) -> str:
        """取得日誌等級"""
        return self.config.get('system', {}).get('log_level', 'INFO')

    @property
    def api_timeout(self) -> int:
        """取得 API 逾時時間"""
        return self.config.get('api', {}).get('ntpc', {}).get('timeout', 10)

    @property
    def api_base_url(self) -> str:
        """取得新北市 API 基礎 URL"""
        return self.config.get('api', {}).get('ntpc', {}).get(
            'base_url',
            'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI'
        )

    @property
    def server_host(self) -> str:
        """取得 Flask 伺服器 host"""
        return self.config.get('api', {}).get('server', {}).get('host', '0.0.0.0')

    @property
    def server_port(self) -> int:
        """取得 Flask 伺服器 port"""
        return self.config.get('api', {}).get('server', {}).get('port', 5000)

    @property
    def server_debug(self) -> bool:
        """取得 Flask debug 模式"""
        return self.config.get('api', {}).get('server', {}).get('debug', False)

    def __str__(self) -> str:
        """返回設定的字串表示（隱藏座標）"""
        return (
            f"ConfigManager(\n"
            f"  location: ({self.location['lat']:.4f}, {self.location['lng']:.4f})\n"
            f"  enter_point: {self.enter_point}\n"
            f"  exit_point: {self.exit_point}\n"
            f"  trigger_mode: {self.trigger_mode}\n"
            f"  target_lines: {self.target_lines or '所有路線'}\n"
            f")"
        )
