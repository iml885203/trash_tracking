"""New Taipei City Garbage Truck API Client for Home Assistant."""

import asyncio
import logging
from typing import Optional

from aiohttp import ClientSession, ClientError, ClientTimeout

from .models.truck import TruckLine

_LOGGER = logging.getLogger(__name__)


class NTPCApiError(Exception):
    """New Taipei City API Error."""

    pass


class NTPCApiClient:
    """New Taipei City Garbage Truck API Client (async version for HA)."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI",
        timeout: int = 10,
        retry_count: int = 3,
        retry_delay: int = 2,
    ):
        """Initialize API client."""
        self.session = session
        self.base_url = base_url
        self.timeout = ClientTimeout(total=timeout)
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    async def get_around_points(
        self, lat: float, lng: float, time_filter: int = 0
    ) -> Optional[list[TruckLine]]:
        """Query nearby garbage trucks (async version)."""
        url = f"{self.base_url}/GetAroundPoints"
        payload = {"lat": lat, "lng": lng, "time": time_filter}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        last_error = None

        for attempt in range(self.retry_count):
            try:
                _LOGGER.debug(
                    f"Calling NTPC API (attempt {attempt + 1}/{self.retry_count}): "
                    f"lat={lat}, lng={lng}, time={time_filter}"
                )

                async with self.session.post(
                    url, data=payload, headers=headers, timeout=self.timeout
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if not isinstance(data, dict):
                        raise NTPCApiError("API response format error: not a dictionary")

                    if "Line" not in data:
                        _LOGGER.warning("No 'Line' field in API response, possibly no trucks nearby")
                        return []

                    lines = []
                    for line_data in data.get("Line", []):
                        try:
                            truck_line = TruckLine.from_dict(line_data)
                            lines.append(truck_line)
                        except Exception as e:
                            _LOGGER.warning(f"Failed to parse route data: {e}")
                            continue

                    _LOGGER.info(
                        f"Successfully queried NTPC API: found {len(lines)} route(s) "
                        f"(TimeStamp: {data.get('TimeStamp')})"
                    )

                    return lines

            except asyncio.TimeoutError:
                last_error = "Request timeout"
                _LOGGER.warning(f"API request timeout (attempt {attempt + 1}/{self.retry_count})")

            except ClientError as e:
                last_error = f"HTTP error: {str(e)}"
                _LOGGER.warning(
                    f"API request failed: {e} (attempt {attempt + 1}/{self.retry_count})"
                )

            except ValueError as e:
                last_error = f"JSON parse error: {str(e)}"
                _LOGGER.error(f"API response cannot be parsed as JSON: {e}")
                break

            except Exception as e:
                last_error = f"Unknown error: {str(e)}"
                _LOGGER.error(f"Unexpected error in API request: {e}")
                break

            if attempt < self.retry_count - 1:
                _LOGGER.info(f"Waiting {self.retry_delay} seconds before retry...")
                await asyncio.sleep(self.retry_delay)

        error_msg = f"NTPC API request failed after {self.retry_count} retries: {last_error}"
        _LOGGER.error(error_msg)
        raise NTPCApiError(error_msg)
