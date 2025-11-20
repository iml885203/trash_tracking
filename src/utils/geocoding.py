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
                logger.info("NLSC API 成功解析地址")
                return result

            # 方法 2: 使用 OpenStreetMap Nominatim (備用)
            result = self._query_nominatim(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                logger.info("Nominatim API 成功解析地址")
                return result

            # 方法 3: 簡化地址重試 (移除巷弄號等詳細資訊)
            simplified = self._simplify_address(cleaned_address)
            if simplified != cleaned_address:
                logger.info(f"嘗試簡化地址: {simplified}")

                result = self._query_nominatim(simplified, timeout)
                if result is not None and len(result) == 2:
                    logger.warning("使用簡化地址找到座標，可能不夠精確")
                    return result

            # 方法 4: 使用 TW97 地址轉換服務
            result = self._query_tgos(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                logger.info("TGOS API 成功解析地址")
                return result

            # 提供詳細的錯誤訊息和建議
            error_msg = f"無法找到地址的座標: {address}\n\n"
            error_msg += "建議解決方法：\n"
            error_msg += "1. 使用 Google Maps 查詢你的地址，右鍵點擊位置，複製座標\n"
            error_msg += "2. 然後使用座標執行: python3 cli.py --lat 緯度 --lng 經度\n"
            error_msg += f"3. 或嘗試簡化地址，例如: {simplified}\n"
            error_msg += "4. 或使用互動式設定手動輸入座標: python3 cli.py --setup"

            raise GeocodingError(error_msg)

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

    def _simplify_address(self, address: str) -> str:
        """
        Simplify address by removing detailed info (alley, lane, number)

        Args:
            address: Full address

        Returns:
            str: Simplified address
        """
        # 移除巷弄號等詳細資訊，保留到路或街
        import re

        # 移除 "XX巷XX弄XX號"
        simplified = re.sub(r"\d+巷.*", "", address)
        # 移除 "XX弄XX號"
        simplified = re.sub(r"\d+弄.*", "", simplified)
        # 移除 "XX號.*"
        simplified = re.sub(r"\d+號.*", "", simplified)

        return simplified.strip()

    def _query_tgos(self, address: str, timeout: int) -> Optional[Tuple[float, float]]:
        """
        Query TGOS (Taiwan Geographic Online Service) API

        Args:
            address: Address to query
            timeout: Request timeout

        Returns:
            Optional[tuple]: (latitude, longitude) or None
        """
        try:
            url = "https://addr.tgos.tw/addrapi/addr"
            params: Dict[str, Any] = {"addr": address, "type": "json"}

            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            data = response.json()

            # TGOS API 返回格式檢查
            if isinstance(data, dict) and "AddressList" in data:
                addr_list = data.get("AddressList", [])
                if addr_list and len(addr_list) > 0:
                    first = addr_list[0]
                    x = first.get("X")
                    y = first.get("Y")

                    if x and y:
                        # TGOS 使用 TWD97，需要轉換
                        lat, lng = self._twd97_to_wgs84(float(x), float(y))
                        logger.info(f"TGOS API 查詢成功: {address} -> ({lat}, {lng})")
                        return (lat, lng)

        except Exception as e:
            logger.debug(f"TGOS API 查詢失敗: {e}")

        return None

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
