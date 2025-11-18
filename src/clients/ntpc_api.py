"""New Taipei City Garbage Truck API Client"""

import time
import requests
from typing import Optional, Dict, Any, List
from src.utils.logger import logger
from src.models.truck import TruckLine


class NTPCApiError(Exception):
    """New Taipei City API Error"""
    pass


class NTPCApiClient:
    """New Taipei City Garbage Truck API Client"""

    def __init__(
        self,
        base_url: str = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI",
        timeout: int = 10,
        retry_count: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize API client

        Args:
            base_url: API base URL
            timeout: Request timeout in seconds
            retry_count: Number of retries
            retry_delay: Retry delay in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.session = requests.Session()

    def get_around_points(self, lat: float, lng: float) -> Optional[List[TruckLine]]:
        """
        Query nearby garbage trucks

        Args:
            lat: Latitude of query location
            lng: Longitude of query location

        Returns:
            List[TruckLine]: List of truck routes, None on failure

        Raises:
            NTPCApiError: When all retries fail
        """
        url = f"{self.base_url}/GetAroundPoints"
        payload = {"lat": lat, "lng": lng}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        last_error = None

        for attempt in range(self.retry_count):
            try:
                logger.debug(
                    f"Calling NTPC API (attempt {attempt + 1}/{self.retry_count}): "
                    f"lat={lat}, lng={lng}"
                )

                response = self.session.post(
                    url,
                    data=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                response.raise_for_status()

                data = response.json()

                if not isinstance(data, dict):
                    raise NTPCApiError(f"API response format error: not a dictionary")

                if 'Line' not in data:
                    logger.warning("No 'Line' field in API response, possibly no trucks nearby")
                    return []

                lines = []
                for line_data in data.get('Line', []):
                    try:
                        truck_line = TruckLine.from_dict(line_data)
                        lines.append(truck_line)
                    except Exception as e:
                        logger.warning(f"Failed to parse route data: {e}")
                        continue

                logger.info(
                    f"Successfully queried NTPC API: found {len(lines)} route(s) "
                    f"(TimeStamp: {data.get('TimeStamp')})"
                )

                return lines

            except requests.exceptions.Timeout:
                last_error = "Request timeout"
                logger.warning(f"API request timeout (attempt {attempt + 1}/{self.retry_count})")

            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP error: {e.response.status_code}"
                logger.warning(
                    f"API returned error status {e.response.status_code} "
                    f"(attempt {attempt + 1}/{self.retry_count})"
                )

            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {str(e)}"
                logger.warning(
                    f"API request failed: {e} "
                    f"(attempt {attempt + 1}/{self.retry_count})"
                )

            except ValueError as e:
                last_error = f"JSON parse error: {str(e)}"
                logger.error(f"API response cannot be parsed as JSON: {e}")
                break

            except Exception as e:
                last_error = f"Unknown error: {str(e)}"
                logger.error(f"Unexpected error in API request: {e}")
                break

            if attempt < self.retry_count - 1:
                logger.info(f"Waiting {self.retry_delay} seconds before retry...")
                time.sleep(self.retry_delay)

        error_msg = f"NTPC API request failed after {self.retry_count} retries: {last_error}"
        logger.error(error_msg)
        raise NTPCApiError(error_msg)

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()
