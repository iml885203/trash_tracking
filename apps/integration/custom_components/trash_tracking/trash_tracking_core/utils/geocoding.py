"""Address Geocoding Utilities"""

import re
from typing import Any, Dict, Optional, Tuple

import requests
from trash_tracking_core.utils.logger import logger


class GeocodingError(Exception):
    """Geocoding error"""

    pass


class Geocoder:
    """Taiwan address to coordinates converter"""

    def __init__(self):
        self.base_url = "https://api.nlsc.gov.tw/other/TownVillagePointQuery"

    def _try_simplified_addresses(self, address: str, timeout: int) -> Optional[Tuple[float, float]]:
        """
        Try progressively simplified addresses with Nominatim

        Args:
            address: Cleaned address
            timeout: Request timeout

        Returns:
            Optional[tuple]: (latitude, longitude) or None
        """
        current_address = address
        for attempt in range(4):
            simplified = self._simplify_address(current_address)
            if simplified == current_address:
                break

            logger.info(f"Trying simplified address (level {attempt + 1}): {simplified}")

            result = self._query_nominatim(simplified, timeout)
            if result is not None and len(result) == 2:
                logger.warning(f"Found coordinates using simplified address: {simplified}")
                return result

            current_address = simplified

        return None

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
        cleaned_address = self._clean_address(address)

        try:
            result = self._query_nlsc(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                logger.info("NLSC API succeeded")
                return result

            result = self._query_nominatim(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                logger.info("Nominatim API succeeded")
                return result

            result = self._try_simplified_addresses(cleaned_address, timeout)
            if result is not None:
                return result

            result = self._query_tgos(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                logger.info("TGOS API succeeded")
                return result

            simplified = self._simplify_address(cleaned_address)
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
        address = re.sub(r"\s+", "", address)

        if not any(city in address for city in ["台北", "臺北", "新北", "基隆", "桃園", "新竹", "苗栗", "台中", "臺中"]):
            if "市" not in address[:3]:
                address = "新北市" + address

        return address

    def _simplify_address(self, address: str) -> str:
        """
        Simplify address by removing the most detailed component

        Args:
            address: Full address

        Returns:
            str: Simplified address (one level up)
        """
        import re

        if re.search(r"\d+號", address):
            return re.sub(r"\d+號.*", "", address).strip()

        if re.search(r"\d+弄", address):
            return re.sub(r"\d+弄.*", "", address).strip()

        if re.search(r"\d+巷", address):
            return re.sub(r"\d+巷.*", "", address).strip()

        if re.search(r"\d+段", address):
            return re.sub(r"\d+段.*", "", address).strip()

        return address

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

            if isinstance(data, dict) and "AddressList" in data:
                addr_list = data.get("AddressList", [])
                if addr_list and len(addr_list) > 0:
                    first = addr_list[0]
                    x = first.get("X")
                    y = first.get("Y")

                    if x and y:
                        lat, lng = self._twd97_to_wgs84(float(x), float(y))
                        logger.info(f"TGOS API succeeded: {address} -> ({lat}, {lng})")
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

            if isinstance(data, list) and len(data) > 0:
                result = data[0]
                x = float(result.get("x", 0))
                y = float(result.get("y", 0))

                if x > 0 and y > 0:
                    lat, lng = self._twd97_to_wgs84(x, y)
                    logger.info(f"NLSC API succeeded: {address} -> ({lat}, {lng})")
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
                logger.info(f"Nominatim API succeeded: {address} -> ({lat}, {lng})")
                return (lat, lng)

        except Exception as e:
            logger.debug(f"Nominatim API 查詢失敗: {e}")

        return None

    def _twd97_to_wgs84(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert TWD97 to WGS84 (simplified approximation)

        Note: For production use, consider using pyproj library for accurate conversion
        """
        a = 6378137.0
        lon0 = 121.0 * 3.14159265358979 / 180.0
        k0 = 0.9999
        dx = 250000

        lng = lon0 + (x - dx) / (a * k0)
        lat = y / (a * k0 * (1 - (1 / 298.257222101)))

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
