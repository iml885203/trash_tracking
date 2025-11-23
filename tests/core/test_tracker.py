"""Tests for TruckTracker"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError
from trash_tracking_core.core.point_matcher import MatchResult, PointMatcher
from trash_tracking_core.core.state_manager import StateManager
from trash_tracking_core.core.tracker import TruckTracker
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine
from trash_tracking_core.utils.config import ConfigManager


@pytest.fixture
def sample_points():
    """Sample collection points for a truck route"""
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
        line_name="Test Route 1",
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


@pytest.fixture
def mock_config():
    """Mock ConfigManager"""
    config = Mock(spec=ConfigManager)
    config.location = {"lat": 25.0, "lng": 121.5}
    config.api_base_url = "https://example.com/api"
    config.api_timeout = 10
    config.enter_point = "Enter Point"
    config.exit_point = "Exit Point"
    config.trigger_mode = "arriving"
    config.approaching_threshold = 2
    config.target_lines = []
    config.get = Mock(side_effect=lambda key, default: default)
    config.__str__ = Mock(return_value="MockConfig")
    return config


class TestTruckTrackerInit:
    """Test TruckTracker initialization"""

    def test_init_with_config(self, mock_config):
        """Test initialization with ConfigManager"""
        with patch.object(NTPCApiClient, "__init__", return_value=None):
            with patch.object(StateManager, "__init__", return_value=None):
                with patch.object(PointMatcher, "__init__", return_value=None):
                    tracker = TruckTracker(mock_config)

                    assert tracker.config == mock_config
                    assert isinstance(tracker.api_client, NTPCApiClient)
                    assert isinstance(tracker.state_manager, StateManager)
                    assert isinstance(tracker.point_matcher, PointMatcher)

    def test_init_creates_api_client_with_config(self, mock_config):
        """Test that API client is created with correct config"""
        tracker = TruckTracker(mock_config)

        assert tracker.api_client.base_url == "https://example.com/api"
        assert tracker.api_client.timeout == 10
        assert tracker.api_client.retry_count == 3
        assert tracker.api_client.retry_delay == 2

    def test_init_creates_point_matcher_with_config(self, mock_config):
        """Test that PointMatcher is created with correct config"""
        tracker = TruckTracker(mock_config)

        assert tracker.point_matcher.enter_point_name == "Enter Point"
        assert tracker.point_matcher.exit_point_name == "Exit Point"
        assert tracker.point_matcher.trigger_mode == "arriving"
        assert tracker.point_matcher.approaching_threshold == 2

    def test_str_representation(self, mock_config):
        """Test string representation"""
        tracker = TruckTracker(mock_config)

        result = str(tracker)
        assert "TruckTracker" in result


class TestGetCurrentStatusNormalFlow:
    """Test get_current_status() normal flow"""

    def test_get_current_status_truck_triggers_nearby(self, mock_config, sample_truck, sample_points):
        """Test normal flow when truck triggers nearby state"""
        tracker = TruckTracker(mock_config)

        # Mock API client to return truck data
        tracker.api_client.get_around_points = Mock(return_value=[sample_truck])

        # Mock point matcher to trigger nearby state
        match_result = MatchResult(
            should_trigger=True,
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )
        tracker.point_matcher.check_line = Mock(return_value=match_result)

        # Mock state manager methods
        tracker.state_manager.update_state = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "nearby",
                "reason": "Truck approaching",
                "truck": {"line_name": "Test Route 1"},
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify API was called with correct location
        tracker.api_client.get_around_points.assert_called_once_with(lat=25.0, lng=121.5)

        # Verify point matcher was called
        tracker.point_matcher.check_line.assert_called_once_with(sample_truck)

        # Verify state manager was updated
        tracker.state_manager.update_state.assert_called_once_with(
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        # Verify response
        assert response["status"] == "nearby"
        assert response["reason"] == "Truck approaching"

    def test_get_current_status_no_trigger(self, mock_config, sample_truck):
        """Test when truck exists but doesn't trigger state change"""
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(return_value=[sample_truck])

        # Mock point matcher to not trigger
        match_result = MatchResult(should_trigger=False)
        tracker.point_matcher.check_line = Mock(return_value=match_result)

        # Mock state manager methods
        tracker.state_manager.update_state = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "No matching trucks",
                "truck": None,
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify state manager was not updated
        tracker.state_manager.update_state.assert_not_called()

        # Verify response
        assert response["status"] == "idle"


class TestGetCurrentStatusNoTrucks:
    """Test get_current_status() when no trucks found"""

    def test_no_trucks_when_idle(self, mock_config):
        """Test when no trucks and already idle"""
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(return_value=[])
        tracker.state_manager.is_idle = Mock(return_value=True)
        tracker.state_manager.update_state = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "System initialized",
                "truck": None,
                "timestamp": None,
            }
        )

        response = tracker.get_current_status()

        # Verify state manager was not updated (already idle)
        tracker.state_manager.update_state.assert_not_called()

        assert response["status"] == "idle"

    def test_no_trucks_when_nearby(self, mock_config):
        """Test when no trucks but currently nearby (transition to idle)"""
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(return_value=[])
        tracker.state_manager.is_idle = Mock(return_value=False)
        tracker.state_manager.update_state = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "No trucks nearby",
                "truck": None,
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify state manager was updated to idle
        tracker.state_manager.update_state.assert_called_once_with(
            new_state="idle", reason="No trucks nearby"
        )

        assert response["status"] == "idle"
        assert response["reason"] == "No trucks nearby"


class TestGetCurrentStatusTargetLines:
    """Test get_current_status() with target lines filtering"""

    def test_with_target_lines_match(self, mock_config, sample_truck, sample_points):
        """Test with target lines when truck matches"""
        mock_config.target_lines = ["Test Route 1"]
        tracker = TruckTracker(mock_config)

        truck2 = TruckLine(
            line_id="L002",
            line_name="Test Route 2",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="XYZ-5678",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="67890",
            points=sample_points,
        )

        tracker.api_client.get_around_points = Mock(return_value=[sample_truck, truck2])

        # Mock point matcher to trigger for the matching truck
        match_result = MatchResult(
            should_trigger=True,
            new_state="nearby",
            reason="Truck approaching",
            truck_line=sample_truck,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )
        tracker.point_matcher.check_line = Mock(return_value=match_result)

        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "nearby",
                "reason": "Truck approaching",
                "truck": {"line_name": "Test Route 1"},
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify only the matching truck was checked
        tracker.point_matcher.check_line.assert_called_once_with(sample_truck)

        assert response["status"] == "nearby"

    def test_with_target_lines_no_match(self, mock_config, sample_truck):
        """Test with target lines when no trucks match"""
        mock_config.target_lines = ["Different Route"]
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(return_value=[sample_truck])
        tracker.point_matcher.check_line = Mock()
        tracker.state_manager.is_idle = Mock(return_value=True)
        tracker.state_manager.update_state = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "System initialized",
                "truck": None,
                "timestamp": None,
            }
        )

        response = tracker.get_current_status()

        # Verify point matcher was never called (no matching trucks)
        tracker.point_matcher.check_line.assert_not_called()

        # Verify state manager was not updated (already idle)
        tracker.state_manager.update_state.assert_not_called()

        assert response["status"] == "idle"

    def test_with_target_lines_transitions_to_idle(self, mock_config, sample_truck):
        """Test with target lines when no match and currently nearby"""
        mock_config.target_lines = ["Different Route"]
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(return_value=[sample_truck])
        tracker.state_manager.is_idle = Mock(return_value=False)
        tracker.state_manager.update_state = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "Tracked routes not nearby",
                "truck": None,
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify state manager was updated to idle
        tracker.state_manager.update_state.assert_called_once_with(
            new_state="idle", reason="Tracked routes not nearby"
        )

        assert response["status"] == "idle"


class TestGetCurrentStatusApiErrors:
    """Test get_current_status() with API errors"""

    def test_ntpc_api_error(self, mock_config):
        """Test handling of NTPCApiError"""
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(side_effect=NTPCApiError("API connection failed"))
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "System initialized",
                "truck": None,
                "timestamp": None,
            }
        )

        response = tracker.get_current_status()

        # Verify error is included in response
        assert "error" in response
        assert "API connection failed" in response["error"]
        assert response["status"] == "idle"

    def test_ntpc_api_error_maintains_state(self, mock_config):
        """Test that API error doesn't reset state"""
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(side_effect=NTPCApiError("Timeout"))
        tracker.state_manager.reset = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "nearby",
                "reason": "Truck approaching",
                "truck": {"line_name": "Test Route"},
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify state manager was not reset
        tracker.state_manager.reset.assert_not_called()

        # Verify current state is maintained
        assert response["status"] == "nearby"
        assert "error" in response


class TestGetCurrentStatusUnexpectedErrors:
    """Test get_current_status() with unexpected errors"""

    def test_unexpected_error_resets_state(self, mock_config):
        """Test that unexpected errors reset state"""
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(side_effect=ValueError("Unexpected error"))
        tracker.state_manager.reset = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "Manual reset",
                "truck": None,
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify state manager was reset
        tracker.state_manager.reset.assert_called_once()

        # Verify error is included in response
        assert "error" in response
        assert "System error" in response["error"]
        assert "Unexpected error" in response["error"]

    def test_unexpected_error_in_point_matcher(self, mock_config, sample_truck):
        """Test unexpected error during point matching"""
        tracker = TruckTracker(mock_config)

        tracker.api_client.get_around_points = Mock(return_value=[sample_truck])
        tracker.point_matcher.check_line = Mock(side_effect=RuntimeError("Matching failed"))
        tracker.state_manager.reset = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "Manual reset",
                "truck": None,
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify state manager was reset
        tracker.state_manager.reset.assert_called_once()

        # Verify error is included
        assert "error" in response
        assert "System error" in response["error"]


class TestFilterTargetLines:
    """Test _filter_target_lines() method"""

    def test_filter_target_lines_no_filter(self, mock_config, sample_truck, sample_points):
        """Test filtering with no target lines specified"""
        mock_config.target_lines = []
        tracker = TruckTracker(mock_config)

        truck2 = TruckLine(
            line_id="L002",
            line_name="Test Route 2",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="XYZ-5678",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="67890",
            points=sample_points,
        )

        all_trucks = [sample_truck, truck2]
        filtered = tracker._filter_target_lines(all_trucks)

        # Should return all trucks
        assert len(filtered) == 2
        assert filtered == all_trucks

    def test_filter_target_lines_with_filter(self, mock_config, sample_truck, sample_points):
        """Test filtering with specific target lines"""
        mock_config.target_lines = ["Test Route 1"]
        tracker = TruckTracker(mock_config)

        truck2 = TruckLine(
            line_id="L002",
            line_name="Test Route 2",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="XYZ-5678",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="67890",
            points=sample_points,
        )

        all_trucks = [sample_truck, truck2]
        filtered = tracker._filter_target_lines(all_trucks)

        # Should return only matching truck
        assert len(filtered) == 1
        assert filtered[0] == sample_truck

    def test_filter_target_lines_multiple_matches(self, mock_config, sample_points):
        """Test filtering with multiple target lines"""
        mock_config.target_lines = ["Test Route 1", "Test Route 2"]
        tracker = TruckTracker(mock_config)

        truck1 = TruckLine(
            line_id="L001",
            line_name="Test Route 1",
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

        truck2 = TruckLine(
            line_id="L002",
            line_name="Test Route 2",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="XYZ-5678",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="67890",
            points=sample_points,
        )

        truck3 = TruckLine(
            line_id="L003",
            line_name="Test Route 3",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="DEF-9999",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="11111",
            points=sample_points,
        )

        all_trucks = [truck1, truck2, truck3]
        filtered = tracker._filter_target_lines(all_trucks)

        # Should return both matching trucks
        assert len(filtered) == 2
        assert truck1 in filtered
        assert truck2 in filtered
        assert truck3 not in filtered

    def test_filter_target_lines_no_matches(self, mock_config, sample_truck):
        """Test filtering when no trucks match"""
        mock_config.target_lines = ["Non-existent Route"]
        tracker = TruckTracker(mock_config)

        all_trucks = [sample_truck]
        filtered = tracker._filter_target_lines(all_trucks)

        # Should return empty list
        assert len(filtered) == 0

    def test_filter_target_lines_empty_input(self, mock_config):
        """Test filtering with empty truck list"""
        mock_config.target_lines = ["Test Route 1"]
        tracker = TruckTracker(mock_config)

        all_trucks = []
        filtered = tracker._filter_target_lines(all_trucks)

        # Should return empty list
        assert len(filtered) == 0


class TestReset:
    """Test reset() method"""

    def test_reset(self, mock_config):
        """Test reset method"""
        tracker = TruckTracker(mock_config)
        tracker.state_manager.reset = Mock()

        tracker.reset()

        # Verify state manager was reset
        tracker.state_manager.reset.assert_called_once()

    def test_reset_multiple_times(self, mock_config):
        """Test calling reset multiple times"""
        tracker = TruckTracker(mock_config)
        tracker.state_manager.reset = Mock()

        tracker.reset()
        tracker.reset()
        tracker.reset()

        # Verify state manager was reset three times
        assert tracker.state_manager.reset.call_count == 3


class TestMultipleTrucksScenarios:
    """Test scenarios with multiple trucks"""

    def test_multiple_trucks_first_triggers(self, mock_config, sample_points):
        """Test when first truck in list triggers state change"""
        tracker = TruckTracker(mock_config)

        truck1 = TruckLine(
            line_id="L001",
            line_name="Test Route 1",
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

        truck2 = TruckLine(
            line_id="L002",
            line_name="Test Route 2",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="XYZ-5678",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="67890",
            points=sample_points,
        )

        tracker.api_client.get_around_points = Mock(return_value=[truck1, truck2])

        # First truck triggers, second truck shouldn't be checked
        match_result1 = MatchResult(
            should_trigger=True,
            new_state="nearby",
            reason="Truck 1 approaching",
            truck_line=truck1,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        tracker.point_matcher.check_line = Mock(return_value=match_result1)
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "nearby",
                "reason": "Truck 1 approaching",
                "truck": {"line_name": "Test Route 1"},
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify only first truck was checked (loop breaks after first trigger)
        tracker.point_matcher.check_line.assert_called_once_with(truck1)

        assert response["status"] == "nearby"

    def test_multiple_trucks_second_triggers(self, mock_config, sample_points):
        """Test when second truck in list triggers state change"""
        tracker = TruckTracker(mock_config)

        truck1 = TruckLine(
            line_id="L001",
            line_name="Test Route 1",
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

        truck2 = TruckLine(
            line_id="L002",
            line_name="Test Route 2",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="XYZ-5678",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="67890",
            points=sample_points,
        )

        tracker.api_client.get_around_points = Mock(return_value=[truck1, truck2])

        # First truck doesn't trigger, second truck triggers
        match_result1 = MatchResult(should_trigger=False)
        match_result2 = MatchResult(
            should_trigger=True,
            new_state="nearby",
            reason="Truck 2 approaching",
            truck_line=truck2,
            enter_point=sample_points[0],
            exit_point=sample_points[1],
        )

        tracker.point_matcher.check_line = Mock(side_effect=[match_result1, match_result2])
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "nearby",
                "reason": "Truck 2 approaching",
                "truck": {"line_name": "Test Route 2"},
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify both trucks were checked
        assert tracker.point_matcher.check_line.call_count == 2
        tracker.point_matcher.check_line.assert_any_call(truck1)
        tracker.point_matcher.check_line.assert_any_call(truck2)

        assert response["status"] == "nearby"

    def test_multiple_trucks_none_trigger(self, mock_config, sample_points):
        """Test when multiple trucks exist but none trigger"""
        tracker = TruckTracker(mock_config)

        truck1 = TruckLine(
            line_id="L001",
            line_name="Test Route 1",
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

        truck2 = TruckLine(
            line_id="L002",
            line_name="Test Route 2",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="XYZ-5678",
            location="Current Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="67890",
            points=sample_points,
        )

        tracker.api_client.get_around_points = Mock(return_value=[truck1, truck2])

        # Neither truck triggers
        match_result = MatchResult(should_trigger=False)
        tracker.point_matcher.check_line = Mock(return_value=match_result)
        tracker.state_manager.update_state = Mock()
        tracker.state_manager.get_status_response = Mock(
            return_value={
                "status": "idle",
                "reason": "No matching trucks",
                "truck": None,
                "timestamp": "2025-01-01T18:00:00",
            }
        )

        response = tracker.get_current_status()

        # Verify both trucks were checked
        assert tracker.point_matcher.check_line.call_count == 2

        # Verify state manager was not updated
        tracker.state_manager.update_state.assert_not_called()

        assert response["status"] == "idle"
