"""Truck map-location resolution.

Pure decision logic (no Home Assistant dependency) for whether a truck's
live GPS position should be shown on the map, and which coordinates to use.

This is intentionally framework-agnostic so it can be unit-tested without a
running Home Assistant instance. The Home Assistant ``device_tracker`` entity
delegates to :func:`resolve_truck_location`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TruckLocation:
    """Resolved map position for a tracked truck.

    Attributes:
        available: Whether the truck has a live position to show on the map.
        latitude: WGS84 latitude, or None when unavailable.
        longitude: WGS84 longitude, or None when unavailable.
    """

    available: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def resolve_truck_location(data: Optional[dict[str, Any]]) -> TruckLocation:
    """Decide whether a truck's live GPS position should be shown on the map.

    A position is shown only when the most recent update carries live truck
    data with valid coordinates. Idle / out-of-schedule cycles carry no truck
    data, so the tracker becomes unavailable and its dot disappears from the
    map instead of lingering at a stale position. This keeps the map clean
    when multiple routes are configured.

    Args:
        data: The status-response dict produced by ``StatusResponseBuilder``
            (i.e. the coordinator's ``data``). May be None before the first
            successful update.

    Returns:
        TruckLocation: availability flag plus coordinates when available.
    """
    if not data:
        return TruckLocation(available=False)

    truck = data.get("truck")
    if not truck:
        return TruckLocation(available=False)

    lat = truck.get("current_lat")
    lon = truck.get("current_lon")

    if not _is_valid_coordinate(lat, lon):
        return TruckLocation(available=False)

    return TruckLocation(available=True, latitude=float(lat), longitude=float(lon))


def _is_valid_coordinate(lat: Any, lon: Any) -> bool:
    """Return True if (lat, lon) is a usable WGS84 fix.

    Guards against the API default of 0.0 for missing coordinates, which would
    otherwise plot the truck off the coast of Africa at (0, 0).
    """
    if lat is None or lon is None:
        return False

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return False

    # API defaults missing coordinates to 0.0; treat (0, 0) as "no fix".
    if lat_f == 0.0 and lon_f == 0.0:
        return False

    # Sanity-bound to the valid WGS84 range.
    if not (-90.0 <= lat_f <= 90.0):
        return False
    if not (-180.0 <= lon_f <= 180.0):
        return False

    return True
