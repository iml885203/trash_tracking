"""Tests for StateManager"""
from datetime import datetime

import pytest
import pytz
from trash_tracking_core.core.state_manager import StateManager, TruckState
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine


@pytest.fixture
def sample_points():
    """Sample collection points"""
    return [
        Point(
            source_point_id=1,
            vil="Village A",
            point_name="Enter Point",
            lon=121.5,
            lat=25.0,
            point_id=101,
            point_rank=2,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
        Point(
            source_point_id=2,
            vil="Village B",
            point_name="Exit Point",
            lon=121.51,
            lat=25.01,
            point_id=102,
            point_rank=4,
            point_time="18:10",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
    ]


@pytest.fixture
def sample_truck(sample_points):
    """Sample truck line"""
    return TruckLine(
        line_id="L001",
        line_name="Test Route",
        area="Test Area",
        arrival_rank=1,
        diff=0,
        car_no="ABC-1234",
        location="Current Location",
        location_lat=25.0,
        location_lon=121.5,
        bar_code="12345",
        points=sample_points,
    )


class TestStateManagerInit:
    """Test StateManager initialization"""

    def test_init_default(self):
        """Test initialization with default timezone"""
        manager = StateManager()

        assert manager.current_state == TruckState.IDLE
        assert manager.current_truck is None
        assert manager.enter_point is None
        assert manager.exit_point is None
        assert manager.last_update is None
        assert manager.reason == "System initialized"
        assert manager.timezone == pytz.timezone("Asia/Taipei")

    def test_init_custom_timezone(self):
        """Test initialization with custom timezone"""
        manager = StateManager(timezone="UTC")

        assert manager.timezone == pytz.timezone("UTC")
        assert manager.current_state == TruckState.IDLE

    def test_str_representation_idle(self):
        """Test string representation when idle"""
        manager = StateManager()

        result = str(manager)
        assert "idle" in result
        assert "StateManager" in result


class TestUpdateState:
    """Test state update functionality"""

    def test_update_state_idle_to_nearby(self, sample_truck, sample_points):
        """Test updating state from idle to nearby"""
        manager = StateManager()

        manager.update_state(
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        assert manager.current_state == TruckState.NEARBY
        assert manager.reason == "Truck approaching"
        assert manager.current_truck == sample_truck
        assert manager.enter_point == sample_points[0]
        assert manager.exit_point == sample_points[1]
        assert manager.last_update is not None

    def test_update_state_nearby_to_idle(self, sample_truck, sample_points):
        """Test updating state from nearby to idle"""
        manager = StateManager()

        # First set to nearby
        manager.update_state(
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        # Then set to idle
        manager.update_state(
            new_state="idle",
            reason="Truck has passed",
        )

        assert manager.current_state == TruckState.IDLE
        assert manager.reason == "Truck has passed"
        assert manager.last_update is not None

    def test_update_state_invalid_state(self):
        """Test updating with invalid state value"""
        manager = StateManager()

        # Should log error and not change state
        manager.update_state(
            new_state="invalid_state",
            reason="Test",
        )

        # State should remain idle
        assert manager.current_state == TruckState.IDLE
        assert manager.reason == "System initialized"  # Unchanged

    def test_update_state_maintains_same_state(self, sample_truck, sample_points):
        """Test updating with same state"""
        manager = StateManager()

        manager.update_state(
            new_state="nearby",
            reason="First update",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        first_update = manager.last_update

        # Update with same state but different reason
        manager.update_state(
            new_state="nearby",
            reason="Second update",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        assert manager.current_state == TruckState.NEARBY
        assert manager.reason == "Second update"
        assert manager.last_update != first_update  # Timestamp should update

    def test_update_state_timezone_aware(self):
        """Test that last_update is timezone-aware"""
        manager = StateManager(timezone="Asia/Taipei")

        manager.update_state(
            new_state="idle",
            reason="Test",
        )

        assert manager.last_update is not None
        assert manager.last_update.tzinfo is not None
        # Check that the timezone name matches, not the exact tzinfo object
        assert manager.last_update.tzinfo.zone == "Asia/Taipei"


class TestGetStatusResponse:
    """Test status response generation"""

    def test_get_status_response_idle(self):
        """Test status response when idle"""
        manager = StateManager()

        manager.update_state(
            new_state="idle",
            reason="No trucks nearby",
        )

        response = manager.get_status_response()

        assert response["status"] == "idle"
        assert response["reason"] == "No trucks nearby"
        assert response["truck"] is None
        assert response["timestamp"] is not None

    def test_get_status_response_nearby(self, sample_truck, sample_points):
        """Test status response when truck is nearby"""
        manager = StateManager()

        manager.update_state(
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        response = manager.get_status_response()

        assert response["status"] == "nearby"
        assert response["reason"] == "Truck approaching"
        assert response["truck"] is not None
        assert response["truck"]["line_name"] == "Test Route"
        assert response["truck"]["car_no"] == "ABC-1234"
        assert "enter_point" in response["truck"]
        assert "exit_point" in response["truck"]
        assert response["timestamp"] is not None

    def test_get_status_response_initial_state(self):
        """Test status response in initial state"""
        manager = StateManager()

        response = manager.get_status_response()

        assert response["status"] == "idle"
        assert response["reason"] == "System initialized"
        assert response["truck"] is None
        assert response["timestamp"] is None  # No updates yet

    def test_get_status_response_timestamp_format(self):
        """Test that timestamp is in ISO format"""
        manager = StateManager()

        manager.update_state(
            new_state="idle",
            reason="Test",
        )

        response = manager.get_status_response()

        # Verify ISO format
        timestamp = response["timestamp"]
        assert timestamp is not None
        assert isinstance(timestamp, str)
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


class TestStateCheckers:
    """Test state checking methods"""

    def test_is_idle_true(self):
        """Test is_idle returns True when idle"""
        manager = StateManager()

        assert manager.is_idle() is True
        assert manager.is_nearby() is False

    def test_is_idle_false(self, sample_truck, sample_points):
        """Test is_idle returns False when not idle"""
        manager = StateManager()

        manager.update_state(
            new_state="nearby",
            reason="Test",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        assert manager.is_idle() is False
        assert manager.is_nearby() is True

    def test_is_nearby_true(self, sample_truck, sample_points):
        """Test is_nearby returns True when nearby"""
        manager = StateManager()

        manager.update_state(
            new_state="nearby",
            reason="Test",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        assert manager.is_nearby() is True
        assert manager.is_idle() is False

    def test_is_nearby_false(self):
        """Test is_nearby returns False when idle"""
        manager = StateManager()

        assert manager.is_nearby() is False
        assert manager.is_idle() is True


class TestReset:
    """Test state reset functionality"""

    def test_reset_from_nearby(self, sample_truck, sample_points):
        """Test reset from nearby state"""
        manager = StateManager()

        # Set to nearby
        manager.update_state(
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        # Reset
        manager.reset()

        assert manager.current_state == TruckState.IDLE
        assert manager.current_truck is None
        assert manager.enter_point is None
        assert manager.exit_point is None
        assert manager.reason == "Manual reset"
        assert manager.last_update is not None

    def test_reset_from_idle(self):
        """Test reset when already idle"""
        manager = StateManager()

        # Reset when already idle
        manager.reset()

        assert manager.current_state == TruckState.IDLE
        assert manager.reason == "Manual reset"
        assert manager.last_update is not None

    def test_reset_timezone_aware(self):
        """Test that reset timestamp is timezone-aware"""
        manager = StateManager(timezone="Asia/Taipei")

        manager.reset()

        assert manager.last_update is not None
        assert manager.last_update.tzinfo is not None


class TestStateTransitions:
    """Test various state transition scenarios"""

    def test_multiple_state_transitions(self, sample_truck, sample_points):
        """Test multiple state transitions"""
        manager = StateManager()

        # idle -> nearby
        manager.update_state(
            new_state="nearby",
            reason="Truck 1 approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )
        assert manager.is_nearby()

        # nearby -> idle
        manager.update_state(
            new_state="idle",
            reason="Truck 1 passed",
        )
        assert manager.is_idle()

        # idle -> nearby (different truck)
        manager.update_state(
            new_state="nearby",
            reason="Truck 2 approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )
        assert manager.is_nearby()

    def test_str_representation_with_truck(self, sample_truck, sample_points):
        """Test string representation when truck is present"""
        manager = StateManager()

        manager.update_state(
            new_state="nearby",
            reason="Test",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        result = str(manager)
        assert "nearby" in result
        assert "Test Route" in result
