"""Tests for truck map-location resolution (device_tracker decision logic)"""
from trash_tracking_core.core.location import TruckLocation, resolve_truck_location


def _response_with_truck(lat, lon, **extra):
    """Build a minimal status-response dict carrying truck coordinates."""
    truck = {
        "line_name": "Test Route",
        "car_no": "ABC-1234",
        "current_lat": lat,
        "current_lon": lon,
    }
    truck.update(extra)
    return {"status": "nearby", "reason": "Truck approaching", "truck": truck}


class TestLiveTruckShown:
    """A live truck with valid coordinates should appear on the map"""

    def test_valid_coordinates_are_available(self):
        result = resolve_truck_location(_response_with_truck(25.0, 121.5))

        assert result == TruckLocation(available=True, latitude=25.0, longitude=121.5)

    def test_available_even_when_idle_but_truck_present(self):
        """Truck still within API radius (idle state) is shown until it leaves."""
        data = _response_with_truck(25.018269, 121.471703)
        data["status"] = "idle"

        result = resolve_truck_location(data)

        assert result.available is True
        assert result.latitude == 25.018269
        assert result.longitude == 121.471703

    def test_string_coordinates_are_coerced(self):
        result = resolve_truck_location(_response_with_truck("25.0", "121.5"))

        assert result.available is True
        assert result.latitude == 25.0
        assert result.longitude == 121.5


class TestNoLivePosition:
    """No live truck data this cycle -> dot disappears from the map"""

    def test_none_data_is_unavailable(self):
        result = resolve_truck_location(None)

        assert result == TruckLocation(available=False, latitude=None, longitude=None)

    def test_empty_data_is_unavailable(self):
        result = resolve_truck_location({})

        assert result.available is False

    def test_idle_without_truck_is_unavailable(self):
        data = {"status": "idle", "reason": "No trucks nearby", "truck": None}

        result = resolve_truck_location(data)

        assert result.available is False
        assert result.latitude is None
        assert result.longitude is None


class TestInvalidCoordinates:
    """Guard against the API's 0.0 default and out-of-range values"""

    def test_zero_zero_is_unavailable(self):
        """API defaults missing coordinates to 0.0; (0, 0) must not be plotted."""
        result = resolve_truck_location(_response_with_truck(0.0, 0.0))

        assert result.available is False

    def test_missing_coordinates_are_unavailable(self):
        data = {"status": "nearby", "truck": {"line_name": "Test Route"}}

        result = resolve_truck_location(data)

        assert result.available is False

    def test_none_coordinates_are_unavailable(self):
        result = resolve_truck_location(_response_with_truck(None, None))

        assert result.available is False

    def test_non_numeric_coordinates_are_unavailable(self):
        result = resolve_truck_location(_response_with_truck("not-a-number", "x"))

        assert result.available is False

    def test_out_of_range_latitude_is_unavailable(self):
        result = resolve_truck_location(_response_with_truck(95.0, 121.5))

        assert result.available is False

    def test_out_of_range_longitude_is_unavailable(self):
        result = resolve_truck_location(_response_with_truck(25.0, 200.0))

        assert result.available is False

    def test_nonzero_latitude_with_zero_longitude_is_available(self):
        """Only (0, 0) is rejected; a real fix with one zero component is valid."""
        result = resolve_truck_location(_response_with_truck(25.0, 0.0))

        assert result.available is True
        assert result.latitude == 25.0
        assert result.longitude == 0.0


class TestMultipleRoutes:
    """With several routes, only the route with a live truck shows a dot"""

    def test_only_live_route_is_available(self):
        live = _response_with_truck(25.0, 121.5)
        idle = {"status": "idle", "reason": "Tracked route not nearby", "truck": None}

        assert resolve_truck_location(live).available is True
        assert resolve_truck_location(idle).available is False
