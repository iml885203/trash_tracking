"""Tests for PointMatcher"""
import pytest
from trash_tracking_core.core.point_matcher import MatchResult, PointMatcher
from trash_tracking_core.core.state_manager import TruckState
from trash_tracking_core.models.point import Point
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
        Point(
            source_point_id=5,
            vil="Village E",
            point_name="Point 5",
            lon=121.54,
            lat=25.04,
            point_id=105,
            point_rank=5,
            point_time="18:40",
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


class TestPointMatcherInit:
    """Test PointMatcher initialization"""

    def test_init_default(self):
        """Test initialization with default parameters"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
        )

        assert matcher.enter_point_name == "Point 2"
        assert matcher.exit_point_name == "Point 4"



    def test_str_representation(self):
        """Test string representation"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
        )

        result = str(matcher)
        assert "Point 2" in result
        assert "Point 4" in result


class TestCheckLineBasics:
    """Test basic check_line functionality"""

    def test_check_line_enter_point_not_found(self, sample_truck):
        """Test check_line when enter point not found"""
        matcher = PointMatcher(
            enter_point_name="Non-existent Point",
            exit_point_name="Point 4",
        )

        result = matcher.check_line(sample_truck, current_state=TruckState.IDLE)

        assert result.should_trigger is False
        assert result.new_state is None

    def test_check_line_exit_point_not_found(self, sample_truck):
        """Test check_line when exit point not found"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Non-existent Point",
        )

        result = matcher.check_line(sample_truck, current_state=TruckState.IDLE)

        assert result.should_trigger is False
        assert result.new_state is None

    def test_check_line_invalid_point_order(self, sample_truck):
        """Test check_line when exit point comes before enter point"""
        matcher = PointMatcher(
            enter_point_name="Point 4",  # Later point
            exit_point_name="Point 2",  # Earlier point
        )

        result = matcher.check_line(sample_truck, current_state=TruckState.IDLE)

        assert result.should_trigger is False
        assert result.new_state is None

    def test_check_line_same_point_order(self, sample_truck):
        """Test check_line when exit and enter are the same point"""
        with pytest.raises(ValueError, match="Enter and exit points must be different"):
            PointMatcher(
                enter_point_name="Point 2",
                exit_point_name="Point 2",
            )



class TestArrivedMode:
    """Test 'arrived' trigger mode"""

    def test_arrived_mode_truck_approaching(self, sample_truck):
        """Test arrived mode when truck is approaching but not yet arrived"""
        matcher = PointMatcher(
            enter_point_name="Point 3",  # Rank 3
            exit_point_name="Point 5",
        )

        sample_truck.arrival_rank = 2  # One stop before Point 3

        result = matcher.check_line(sample_truck, current_state=TruckState.IDLE)

        assert result.should_trigger is False

    def test_arrived_mode_truck_arrived(self, sample_truck, sample_points):
        """Test arrived mode when truck has actually arrived"""
        matcher = PointMatcher(
            enter_point_name="Point 2",  # Rank 2
            exit_point_name="Point 4",
        )

        sample_truck.arrival_rank = 2
        sample_points[1].arrival = "18:10"
        sample_points[1].arrival_diff = 0

        result = matcher.check_line(sample_truck, current_state=TruckState.IDLE)

        assert result.should_trigger is True
        assert result.new_state == "nearby"
        assert result.enter_point.point_name == "Point 2"


class TestExitTrigger:
    """Test exit point trigger logic"""

    def test_exit_trigger_not_passed(self, sample_truck):
        """Test exit trigger when truck hasn't reached exit point"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",  # Rank 4
        )

        sample_truck.arrival_rank = 3  # Before exit point

        result = matcher.check_line(sample_truck, current_state=TruckState.NEARBY)

        assert result.should_trigger is False

    def test_exit_trigger_passed(self, sample_truck, sample_points):
        """Test exit trigger when truck has passed exit point"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",  # Rank 4
        )

        sample_truck.arrival_rank = 5
        # Mark Point 4 as passed
        sample_points[3].arrival = "18:30"
        sample_points[3].arrival_diff = 0

        result = matcher.check_line(sample_truck, current_state=TruckState.NEARBY)

        assert result.should_trigger is True
        assert result.new_state == "idle"
        assert result.reason.lower().find("passed") >= 0
        assert result.exit_point.point_name == "Point 4"


class TestMatchResult:
    """Test MatchResult class"""

    def test_match_result_init_minimal(self):
        """Test MatchResult initialization with minimal parameters"""
        result = MatchResult(should_trigger=False)

        assert result.should_trigger is False
        assert result.new_state is None
        assert result.reason == ""
        assert result.truck_line is None
        assert result.enter_point is None
        assert result.exit_point is None

    def test_match_result_init_full(self, sample_truck, sample_points):
        """Test MatchResult initialization with all parameters"""
        result = MatchResult(
            should_trigger=True,
            new_state="nearby",
            reason="Test reason",
            truck_line=sample_truck,
            enter_point=sample_points[1],
            exit_point=sample_points[3],
        )

        assert result.should_trigger is True
        assert result.new_state == "nearby"
        assert result.reason == "Test reason"
        assert result.truck_line == sample_truck
        assert result.enter_point == sample_points[1]
        assert result.exit_point == sample_points[3]


class TestStateTypeValidation:
    """Test that current_state parameter uses TruckState enum"""

    def test_check_line_idle_state_checks_enter(self, sample_truck, sample_points):
        """Test IDLE state checks enter condition"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
        )

        sample_points[1].arrival = "18:10"
        sample_points[1].arrival_diff = 0

        result = matcher.check_line(sample_truck, current_state=TruckState.IDLE)

        assert result.should_trigger is True
        assert result.new_state == "nearby"

    def test_check_line_nearby_state_checks_exit(self, sample_truck, sample_points):
        """Test NEARBY state checks exit condition"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
        )

        sample_truck.arrival_rank = 5
        sample_points[3].arrival = "18:30"
        sample_points[3].arrival_diff = 0

        result = matcher.check_line(sample_truck, current_state=TruckState.NEARBY)

        assert result.should_trigger is True
        assert result.new_state == "idle"

    def test_check_line_requires_current_state_keyword(self, sample_truck):
        """Test current_state must be passed as keyword argument"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
        )

        with pytest.raises(TypeError, match="takes 2 positional arguments but 3 were given"):
            matcher.check_line(sample_truck, TruckState.IDLE)


class TestEdgeCases:
    """Test edge cases and special scenarios"""
