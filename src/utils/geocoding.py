"""Address Geocoding Utilities"""

import re
from typing import Any, Dict, Optional, Tuple

import requests

from src.utils.logger import logger


class GeocodingError(Exception):
    """Geocoding error"""

    pass


class Geocoder:
    """Taiwan address to coordinates converter"""

    def __init__(self):
        # 使用政府資料開放平台的地址定位服務
        self.base_url = "https://api.nlsc.gov.tw/other/TownVillagePointQuery"

    def address_to_coordinates(self, address: str, timeout: int = 10) -> Tuple[float, float]:
        """
        Convert Taiwan address to GPS coordinates

        Args:
            address: Address string (Taiwan)
            timeout: Request timeout in seconds

        Returns:
            tuple: (latitude, longitude)

        Raises:
            GeocodingError: When conversion fails
        """
        # 清理地址
        cleaned_address = self._clean_address(address)

        try:
            # 方法 1: 使用國土測繪中心 API
            result = self._query_nlsc(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                return result

            # 方法 2: 使用 OpenStreetMap Nominatim (備用)
            result = self._query_nominatim(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                return result

            raise GeocodingError(f"無法找到地址的座標: {address}")

        except GeocodingError:
            raise
        except requests.RequestException as e:
            raise GeocodingError(f"地址查詢失敗: {e}")
        except Exception as e:
            raise GeocodingError(f"地址轉換錯誤: {e}")

    def _clean_address(self, address: str) -> str:
        """
        Clean and standardize address string

        Args:
            address: Original address

        Returns:
            str: Cleaned address
        """
        # 移除多餘空格
        address = re.sub(r"\s+", "", address)

        # 確保包含縣市資訊
        if not any(city in address for city in ["台北", "臺北", "新北", "基隆", "桃園", "新竹", "苗栗", "台中", "臺中"]):
            # 如果沒有縣市，預設新北市
            if "市" not in address[:3]:
                address = "新北市" + address

        return address

    def _query_nlsc(self, address: str, timeout: int) -> Optional[Tuple[float, float]]:
        """
        Query NLSC (National Land Surveying and Mapping Center) API

        Args:
            address: Cleaned address
            timeout: Request timeout

        Returns:
            Optional[tuple]: (latitude, longitude) or None
        """
        try:
            params: Dict[str, str] = {"addr": address, "format": "json"}
            response = requests.get(self.base_url, params=params, timeout=timeout)
            response.raise_for_status()

            data = response.json()

            # 檢查是否有結果
            if isinstance(data, list) and len(data) > 0:
                result = data[0]
                x = float(result.get("x", 0))
                y = float(result.get("y", 0))

                if x > 0 and y > 0:
                    # TWD97 轉 WGS84 (簡化版本，實際應使用更精確的轉換)
                    lat, lng = self._twd97_to_wgs84(x, y)
                    logger.info(f"NLSC API 查詢成功: {address} -> ({lat}, {lng})")
                    return (lat, lng)

        except Exception as e:
            logger.debug(f"NLSC API 查詢失敗: {e}")

        return None

    def _query_nominatim(self, address: str, timeout: int) -> Optional[Tuple[float, float]]:
        """
        Query OpenStreetMap Nominatim API (backup)

        Args:
            address: Cleaned address
            timeout: Request timeout

        Returns:
            Optional[tuple]: (latitude, longitude) or None
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params: Dict[str, Any] = {"q": address, "format": "json", "limit": 1, "countrycodes": "tw"}
            headers: Dict[str, str] = {"User-Agent": "TrashTrackingSystem/1.0"}

            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                logger.info(f"Nominatim API 查詢成功: {address} -> ({lat}, {lng})")
                return (lat, lng)

        except Exception as e:
            logger.debug(f"Nominatim API 查詢失敗: {e}")

        return None

    def _twd97_to_wgs84(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert TWD97 (Taiwan Datum 1997) to WGS84

        這是簡化版本，使用近似轉換
        實際應用建議使用 pyproj 等專業庫

        Args:
            x: TWD97 X coordinate
            y: TWD97 Y coordinate

        Returns:
            tuple: (latitude, longitude) in WGS84
        """
        # 簡化的近似轉換（誤差約數公尺）
        # 實際應用建議使用 pyproj 庫進行精確轉換

        # TWD97 的參數
        a = 6378137.0  # 長半軸
        lon0 = 121.0 * 3.14159265358979 / 180.0  # 中央經線
        k0 = 0.9999  # 比例因子
        dx = 250000  # 偏移量

        # 簡化計算（這只是近似值）
        lng = lon0 + (x - dx) / (a * k0)
        lat = y / (a * k0 * (1 - (1 / 298.257222101)))

        # 轉換為度
        lat = lat * 180.0 / 3.14159265358979
        lng = lng * 180.0 / 3.14159265358979

        return (lat, lng)


def get_current_location_from_address(address: str) -> Tuple[float, float]:
    """
    Convenience function to get coordinates from address

    Args:
        address: Taiwan address

    Returns:
        tuple: (latitude, longitude)

    Raises:
        GeocodingError: When conversion fails
    """
    geocoder = Geocoder()
    return geocoder.address_to_coordinates(address)
