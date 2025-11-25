"""Tests for StatusResponseBuilder"""
import pytest
from datetime import datetime, timezone
from trash_tracking_core.core.response_builder import StatusResponseBuilder
from trash_tracking_core.core.state_manager import StateManager, TruckState
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine


@pytest.fixture
def sample_point():
    """Sample collection point"""
    return Point(
        source_point_id=1,
        vil="Village A",
        point_name="Test Point",
        lon=121.5,
        lat=25.0,
        point_id=101,
        point_rank=10,
        point_time="18:00",
        arrival="18:05",
        arrival_diff=5,
        fixed_point=1,
        point_weekknd="1,3,5",
        in_scope="Y",
        like_count=0,
    )


@pytest.fixture
def sample_truck(sample_point):
    """Sample truck line"""
    return TruckLine(
        line_id="L001",
        line_name="Test Route",
        area="Test Area",
        arrival_rank=10,
        diff=5,
        car_no="ABC-1234",
        location="Current Location",
        location_lat=25.0,
        location_lon=121.5,
        bar_code="12345",
        points=[sample_point],
    )


class TestResponseBuilderIdle:
    """Test response building for idle state"""

    def test_build_response_idle_no_truck(self):
        """Test building response when idle with no truck data"""
        state_manager = StateManager()
        builder = StatusResponseBuilder()

        response = builder.build(state_manager)

        assert response["status"] == "idle"
        assert response["reason"] == "System initialized"
        assert response["truck"] is None
        assert response["timestamp"] is None

    def test_build_response_idle_with_reason(self):
        """Test building response when idle with reason"""
        state_manager = StateManager()
        state_manager.update_state(new_state="idle", reason="No trucks nearby")

        builder = StatusResponseBuilder()
        response = builder.build(state_manager)

        assert response["status"] == "idle"
        assert response["reason"] == "No trucks nearby"
        assert response["truck"] is None
        assert response["timestamp"] is not None


class TestResponseBuilderNearby:
    """Test response building for nearby state"""

    def test_build_response_nearby_with_truck(self, sample_truck, sample_point):
        """Test building response when nearby with truck data"""
        state_manager = StateManager()
        state_manager.update_state(
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_point,
            exit_point=sample_point,
        )

        builder = StatusResponseBuilder()
        response = builder.build(state_manager)

        assert response["status"] == "nearby"
        assert response["reason"] == "Truck approaching"
        assert response["truck"] is not None
        assert response["truck"]["line_name"] == "Test Route"
        assert response["truck"]["car_no"] == "ABC-1234"
        assert response["timestamp"] is not None

    def test_build_response_nearby_without_truck(self):
        """Test building response when nearby but truck data missing"""
        state_manager = StateManager()
        state_manager.update_state(new_state="nearby", reason="Test")

        builder = StatusResponseBuilder()
        response = builder.build(state_manager)

        assert response["status"] == "nearby"
        assert response["truck"] is None


class TestResponseTimestamp:
    """Test timestamp formatting"""

    def test_response_timestamp_format(self):
        """Test timestamp is in ISO format"""
        state_manager = StateManager()
        state_manager.update_state(new_state="idle", reason="Test")

        builder = StatusResponseBuilder()
        response = builder.build(state_manager)

        timestamp = response["timestamp"]
        assert timestamp is not None
        assert "T" in timestamp

        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

    def test_response_no_timestamp_on_initial_state(self):
        """Test no timestamp when state manager hasn't updated"""
        state_manager = StateManager()

        builder = StatusResponseBuilder()
        response = builder.build(state_manager)

        assert response["timestamp"] is None
