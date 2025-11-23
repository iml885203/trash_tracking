"""New Taipei City Garbage Truck API Client"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
import urllib3
from trash_tracking_core.models.truck import TruckLine
from trash_tracking_core.utils.logger import logger

# Disable SSL warnings for NTPC API (their certificate has issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NTPCApiError(Exception):
    """New Taipei City API Error"""


class NTPCApiClient:
    """New Taipei City Garbage Truck API Client"""

    # Class-level cache shared across all instances
    _cache: Dict[str, Tuple[List[TruckLine], datetime]] = {}
    _cache_ttl: int = 60  # seconds

    def __init__(
        self,
        base_url: str = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI",
        timeout: int = 10,
        retry_count: int = 3,
        retry_delay: int = 2,
        cache_enabled: bool = True,
    ):
        """
        Initialize API client

        Args:
            base_url: API base URL
            timeout: Request timeout in seconds
            retry_count: Number of retries
            retry_delay: Retry delay in seconds
            cache_enabled: Enable response caching (default: True)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.cache_enabled = cache_enabled
        self.session = requests.Session()

    @classmethod
    def _get_cache_key(cls, lat: float, lng: float, time_filter: int, week: Optional[int]) -> str:
        """
        Generate cache key from query parameters

        Args:
            lat: Latitude (rounded to 4 decimal places ~11m precision)
            lng: Longitude (rounded to 4 decimal places ~11m precision)
            time_filter: Time filter value
            week: Week day value

        Returns:
            str: Cache key
        """
        # Round coordinates to 4 decimal places to allow nearby requests to share cache
        lat_rounded = round(lat, 4)
        lng_rounded = round(lng, 4)
        return f"{lat_rounded},{lng_rounded},{time_filter},{week}"

    @classmethod
    def _get_from_cache(cls, cache_key: str) -> Optional[List[TruckLine]]:
        """
        Get data from cache if not expired

        Args:
            cache_key: Cache key

        Returns:
            Optional[List[TruckLine]]: Cached data if valid, None if expired or not found
        """
        if cache_key not in cls._cache:
            return None

        data, cached_at = cls._cache[cache_key]
        age = (datetime.now() - cached_at).total_seconds()

        if age > cls._cache_ttl:
            # Cache expired, remove it
            logger.debug("Cache expired for key %s (age: %.1fs)", cache_key, age)
            del cls._cache[cache_key]
            return None

        logger.debug("Cache hit for key %s (age: %.1fs)", cache_key, age)
        return data

    @classmethod
    def _put_in_cache(cls, cache_key: str, data: List[TruckLine]) -> None:
        """
        Store data in cache

        Args:
            cache_key: Cache key
            data: Data to cache
        """
        cls._cache[cache_key] = (data, datetime.now())
        logger.debug("Cached data for key %s", cache_key)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached data"""
        cls._cache.clear()
        logger.info("API cache cleared")

    def get_around_points(  # noqa: C901
        self, lat: float, lng: float, time_filter: int = 0, week: Optional[int] = None
    ) -> Optional[List[TruckLine]]:
        """
        Query nearby garbage trucks

        Args:
            lat: Latitude of query location
            lng: Longitude of query location
            time_filter: Time period filter
                0: No limit (all routes)
                1: Morning (06:00-11:59)
                2: Afternoon (12:00-17:59)
                3: Evening (18:00-23:59)
            week: Day of week filter (0=Sunday, 1=Monday, ..., 6=Saturday)
                None: Use current day (default)
                Note: Sunday (0) and Wednesday (3) may have limited service

        Returns:
            List[TruckLine]: List of truck routes, None on failure

        Raises:
            NTPCApiError: When all retries fail
        """
        # Check cache first if enabled
        if self.cache_enabled:
            cache_key = self._get_cache_key(lat, lng, time_filter, week)
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data

        url = f"{self.base_url}/GetAroundPoints"
        payload = {"lat": lat, "lng": lng, "time": time_filter}

        # Add week parameter if specified
        if week is not None:
            payload["week"] = week

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        last_error = None

        for attempt in range(self.retry_count):
            try:
                logger.debug(
                    "Calling NTPC API (attempt %d/%d): lat=%s, lng=%s, time=%s",
                    attempt + 1,
                    self.retry_count,
                    lat,
                    lng,
                    time_filter,
                )

                response = self.session.post(url, data=payload, headers=headers, timeout=self.timeout, verify=False)

                response.raise_for_status()

                data = response.json()

                if not isinstance(data, dict):
                    raise NTPCApiError("API response format error: not a dictionary")

                if "Line" not in data:
                    logger.warning("No 'Line' field in API response, possibly no trucks nearby")
                    return []

                lines = []
                for line_data in data.get("Line", []):
                    try:
                        truck_line = TruckLine.from_dict(line_data)
                        lines.append(truck_line)
                    except Exception as e:
                        logger.warning("Failed to parse route data: %s", e)
                        continue

                logger.info(
                    "Successfully queried NTPC API: found %d route(s) (TimeStamp: %s)",
                    len(lines),
                    data.get("TimeStamp"),
                )

                # Cache the result if cache is enabled
                if self.cache_enabled:
                    cache_key = self._get_cache_key(lat, lng, time_filter, week)
                    self._put_in_cache(cache_key, lines)

                return lines

            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                logger.warning("API request timeout (attempt %d/%d)", attempt + 1, self.retry_count)

            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP error: {e.response.status_code}"
                logger.warning(
                    "API returned error status %s (attempt %d/%d)",
                    e.response.status_code,
                    attempt + 1,
                    self.retry_count,
                )

            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {str(e)}"
                logger.warning("API request failed: %s (attempt %d/%d)", e, attempt + 1, self.retry_count)

            except ValueError as e:
                last_error = f"JSON parse error: {str(e)}"
                logger.error("API response cannot be parsed as JSON: %s", e)
                break

            except Exception as e:
                last_error = f"Unknown error: {str(e)}"
                logger.error("Unexpected error in API request: %s", e)
                break

            if attempt < self.retry_count - 1:
                logger.info("Waiting %d seconds before retry...", self.retry_delay)
                time.sleep(self.retry_delay)

        error_msg = f"NTPC API request failed after {self.retry_count} retries: {last_error}"
        logger.error(error_msg)
        raise NTPCApiError(error_msg)

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, "session"):
            self.session.close()
