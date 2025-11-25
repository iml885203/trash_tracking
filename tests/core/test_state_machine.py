"""Tests for TruckStateMachine"""
import pytest
from trash_tracking_core.core.state_machine import StateTransition, TruckStateMachine
from trash_tracking_core.core.state_manager import TruckState
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.tracking_window import TrackingWindow
from trash_tracking_core.models.truck import TruckLine


@pytest.fixture
def sample_points():
    """Sample collection points for a truck route"""
    return [
        Point(
            source_point_id=1,
            vil="Village A",
            point_name="Point 1",
            lon=121.5,
            lat=25.0,
            point_id=101,
            point_rank=1,
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
            point_name="Point 2",
            lon=121.51,
            lat=25.01,
            point_id=102,
            point_rank=2,
            point_time="18:10",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
        Point(
            source_point_id=3,
            vil="Village C",
            point_name="Point 3",
            lon=121.52,
            lat=25.02,
            point_id=103,
            point_rank=3,
            point_time="18:20",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
        Point(
            source_point_id=4,
            vil="Village D",
            point_name="Point 4",
            lon=121.53,
            lat=25.03,
            point_id=104,
            point_rank=4,
            point_time="18:30",
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


@pytest.fixture
def tracking_window():
    """Sample tracking window"""
    return TrackingWindow(enter_point_name="Point 2", exit_point_name="Point 4")


class TestStateMachineInit:
    """Test StateMachine initialization"""

    def test_init_with_tracking_window(self, tracking_window):
        """Test initialization with tracking window"""
        machine = TruckStateMachine(tracking_window)

        assert machine.tracking_window == tracking_window


class TestStateTransition:
    """Test StateTransition data class"""

    def test_transition_init_minimal(self):
        """Test StateTransition with minimal parameters"""
        transition = StateTransition(new_state=TruckState.IDLE, reason="Test")

        assert transition.new_state == TruckState.IDLE
        assert transition.reason == "Test"
        assert transition.truck_line is None
        assert transition.enter_point is None
        assert transition.exit_point is None

    def test_transition_init_full(self, sample_truck, sample_points):
        """Test StateTransition with all parameters"""
        transition = StateTransition(
            new_state=TruckState.NEARBY,
            reason="Truck arrived",
            truck_line=sample_truck,
            enter_point=sample_points[1],
            exit_point=sample_points[3],
        )

        assert transition.new_state == TruckState.NEARBY
        assert transition.reason == "Truck arrived"
        assert transition.truck_line == sample_truck
        assert transition.enter_point == sample_points[1]
        assert transition.exit_point == sample_points[3]


class TestIdleToNearbyTransition:
    """Test IDLE → NEARBY state transition"""

    def test_idle_truck_approaching_no_transition(self, tracking_window, sample_truck):
        """Test IDLE state when truck is approaching but not arrived"""
        machine = TruckStateMachine(tracking_window)
        sample_truck.arrival_rank = 1  # Before enter point (rank 2)

        transition = machine.evaluate_transition(TruckState.IDLE, sample_truck)

        assert transition is None

    def test_idle_truck_arrived_at_enter_point(self, tracking_window, sample_truck, sample_points):
        """Test IDLE → NEARBY when truck arrives at enter point"""
        machine = TruckStateMachine(tracking_window)
        sample_truck.arrival_rank = 2
        sample_points[1].arrival = "18:10"  # Mark Point 2 as arrived
        sample_points[1].arrival_diff = 0

        transition = machine.evaluate_transition(TruckState.IDLE, sample_truck)

        assert transition is not None
        assert transition.new_state == TruckState.NEARBY
        assert "Point 2" in transition.reason
        assert transition.truck_line == sample_truck
        assert transition.enter_point == sample_points[1]
        assert transition.exit_point == sample_points[3]


class TestNearbyToIdleTransition:
    """Test NEARBY → IDLE state transition"""

    def test_nearby_truck_between_points_no_transition(self, tracking_window, sample_truck):
        """Test NEARBY state when truck is between enter and exit points"""
        machine = TruckStateMachine(tracking_window)
        sample_truck.arrival_rank = 3  # Between Point 2 and Point 4

        transition = machine.evaluate_transition(TruckState.NEARBY, sample_truck)

        assert transition is None

    def test_nearby_truck_passed_exit_point(self, tracking_window, sample_truck, sample_points):
        """Test NEARBY → IDLE when truck passes exit point (arrival marked)"""
        machine = TruckStateMachine(tracking_window)
        sample_truck.arrival_rank = 5
        sample_points[3].arrival = "18:30"  # Mark Point 4 as passed
        sample_points[3].arrival_diff = 0

        transition = machine.evaluate_transition(TruckState.NEARBY, sample_truck)

        assert transition is not None
        assert transition.new_state == TruckState.IDLE
        assert "Point 4" in transition.reason
        assert transition.truck_line == sample_truck
        assert transition.enter_point == sample_points[1]
        assert transition.exit_point == sample_points[3]

    def test_nearby_truck_rank_at_exit_point(self, tracking_window, sample_truck):
        """Test NEARBY → IDLE when truck rank >= exit point rank (fallback)"""
        machine = TruckStateMachine(tracking_window)
        sample_truck.arrival_rank = 4  # At or past Point 4 (rank 4)

        transition = machine.evaluate_transition(TruckState.NEARBY, sample_truck)

        assert transition is not None
        assert transition.new_state == TruckState.IDLE


class TestInvalidScenarios:
    """Test invalid scenarios and edge cases"""

    def test_tracking_window_not_found_in_route(self, sample_truck):
        """Test when tracking window points not found in route"""
        window = TrackingWindow(enter_point_name="Non-existent", exit_point_name="Point 4")
        machine = TruckStateMachine(window)

        transition = machine.evaluate_transition(TruckState.IDLE, sample_truck)

        assert transition is None

    def test_invalid_tracking_window_order(self, sample_truck):
        """Test when tracking window has invalid point order"""
        # Point 4 comes before Point 2 in the route
        window = TrackingWindow(enter_point_name="Point 4", exit_point_name="Point 2")
        machine = TruckStateMachine(window)

        transition = machine.evaluate_transition(TruckState.IDLE, sample_truck)

        assert transition is None


class TestReasonMessages:
    """Test reason message formatting"""

    def test_enter_reason_contains_point_name(self, tracking_window, sample_truck, sample_points):
        """Test enter transition reason contains point name"""
        machine = TruckStateMachine(tracking_window)
        sample_points[1].arrival = "18:10"
        sample_points[1].arrival_diff = 0

        transition = machine.evaluate_transition(TruckState.IDLE, sample_truck)

        assert transition is not None
        assert "Point 2" in transition.reason

    def test_exit_reason_contains_point_name(self, tracking_window, sample_truck, sample_points):
        """Test exit transition reason contains point name"""
        machine = TruckStateMachine(tracking_window)
        sample_truck.arrival_rank = 5
        sample_points[3].arrival = "18:30"
        sample_points[3].arrival_diff = 0

        transition = machine.evaluate_transition(TruckState.NEARBY, sample_truck)

        assert transition is not None
        assert "Point 4" in transition.reason
