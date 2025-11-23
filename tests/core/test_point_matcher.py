"""Tests for PointMatcher"""
import pytest
from trash_tracking_core.core.point_matcher import MatchResult, PointMatcher
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
        assert matcher.trigger_mode == "arriving"
        assert matcher.approaching_threshold == 2

    def test_init_custom_mode(self):
        """Test initialization with custom trigger mode"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
            trigger_mode="arrived",
        )

        assert matcher.trigger_mode == "arrived"

    def test_init_custom_threshold(self):
        """Test initialization with custom approaching threshold"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
            approaching_threshold=5,
        )

        assert matcher.approaching_threshold == 5

    def test_str_representation(self):
        """Test string representation"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
            trigger_mode="arriving",
        )

        result = str(matcher)
        assert "Point 2" in result
        assert "Point 4" in result
        assert "arriving" in result


class TestCheckLineBasics:
    """Test basic check_line functionality"""

    def test_check_line_enter_point_not_found(self, sample_truck):
        """Test check_line when enter point not found"""
        matcher = PointMatcher(
            enter_point_name="Non-existent Point",
            exit_point_name="Point 4",
        )

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is False
        assert result.new_state is None

    def test_check_line_exit_point_not_found(self, sample_truck):
        """Test check_line when exit point not found"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Non-existent Point",
        )

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is False
        assert result.new_state is None

    def test_check_line_invalid_point_order(self, sample_truck):
        """Test check_line when exit point comes before enter point"""
        matcher = PointMatcher(
            enter_point_name="Point 4",  # Later point
            exit_point_name="Point 2",  # Earlier point
        )

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is False
        assert result.new_state is None

    def test_check_line_same_point_order(self, sample_truck):
        """Test check_line when exit and enter are the same point"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 2",
        )

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is False


class TestArrivingMode:
    """Test 'arriving' trigger mode"""

    def test_arriving_mode_truck_far_away(self, sample_truck):
        """Test arriving mode when truck is far from enter point"""
        matcher = PointMatcher(
            enter_point_name="Point 4",  # Rank 4
            exit_point_name="Point 5",
            trigger_mode="arriving",
            approaching_threshold=2,
        )

        sample_truck.arrival_rank = 1  # Current at rank 1, distance = 3

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is False

    def test_arriving_mode_truck_within_threshold(self, sample_truck):
        """Test arriving mode when truck is within approaching threshold"""
        matcher = PointMatcher(
            enter_point_name="Point 3",  # Rank 3
            exit_point_name="Point 5",
            trigger_mode="arriving",
            approaching_threshold=2,
        )

        sample_truck.arrival_rank = 1  # Distance = 2 (within threshold)

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is True
        assert result.new_state == "nearby"
        assert result.truck_line == sample_truck
        assert result.enter_point.point_name == "Point 3"
        assert result.exit_point.point_name == "Point 5"

    def test_arriving_mode_truck_at_enter_point(self, sample_truck):
        """Test arriving mode when truck is exactly at enter point"""
        matcher = PointMatcher(
            enter_point_name="Point 2",  # Rank 2
            exit_point_name="Point 4",
            trigger_mode="arriving",
            approaching_threshold=2,
        )

        sample_truck.arrival_rank = 2  # Distance = 0

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is True
        assert result.new_state == "nearby"

    def test_arriving_mode_truck_passed_enter_point(self, sample_truck, sample_points):
        """Test arriving mode when truck has passed enter point"""
        matcher = PointMatcher(
            enter_point_name="Point 2",  # Rank 2
            exit_point_name="Point 4",
            trigger_mode="arriving",
        )

        sample_truck.arrival_rank = 3  # Past Point 2
        # Mark Point 2 as passed
        sample_points[1].arrival = "18:10"
        sample_points[1].arrival_diff = 0

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is False  # Already passed, shouldn't trigger again


class TestArrivedMode:
    """Test 'arrived' trigger mode"""

    def test_arrived_mode_truck_approaching(self, sample_truck):
        """Test arrived mode when truck is approaching but not yet arrived"""
        matcher = PointMatcher(
            enter_point_name="Point 3",  # Rank 3
            exit_point_name="Point 5",
            trigger_mode="arrived",
        )

        sample_truck.arrival_rank = 2  # One stop before Point 3

        result = matcher.check_line(sample_truck)

        assert result.should_trigger is False

    def test_arrived_mode_truck_arrived(self, sample_truck, sample_points):
        """Test arrived mode when truck has actually arrived"""
        matcher = PointMatcher(
            enter_point_name="Point 2",  # Rank 2
            exit_point_name="Point 4",
            trigger_mode="arrived",
        )

        sample_truck.arrival_rank = 2
        # Mark Point 2 as arrived
        sample_points[1].arrival = "18:10"
        sample_points[1].arrival_diff = 0

        result = matcher.check_line(sample_truck)

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

        result = matcher.check_line(sample_truck)

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

        result = matcher.check_line(sample_truck)

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


class TestEdgeCases:
    """Test edge cases and special scenarios"""

    def test_threshold_zero(self, sample_truck):
        """Test with threshold set to 0 (only trigger at exact point)"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 4",
            trigger_mode="arriving",
            approaching_threshold=0,
        )

        # At point 1 (distance = 1), should not trigger
        sample_truck.arrival_rank = 1
        result = matcher.check_line(sample_truck)
        assert result.should_trigger is False

        # At point 2 (distance = 0), should trigger
        sample_truck.arrival_rank = 2
        result = matcher.check_line(sample_truck)
        assert result.should_trigger is True

    def test_large_threshold(self, sample_truck):
        """Test with very large threshold"""
        matcher = PointMatcher(
            enter_point_name="Point 5",
            exit_point_name="Point 5",  # Same point (will fail point order check)
            trigger_mode="arriving",
            approaching_threshold=100,
        )

        sample_truck.arrival_rank = 1
        result = matcher.check_line(sample_truck)

        # Should fail due to invalid point order (same enter/exit)
        assert result.should_trigger is False

    def test_enter_exit_priority(self, sample_truck, sample_points):
        """Test that enter is checked before exit"""
        matcher = PointMatcher(
            enter_point_name="Point 2",
            exit_point_name="Point 3",
            trigger_mode="arriving",
            approaching_threshold=2,
        )

        sample_truck.arrival_rank = 2
        # Both points marked as passed
        sample_points[1].arrival = "18:10"
        sample_points[1].arrival_diff = 0
        sample_points[2].arrival = "18:20"
        sample_points[2].arrival_diff = 0

        result = matcher.check_line(sample_truck)

        # Should trigger exit since enter already passed
        assert result.should_trigger is True
        assert result.new_state == "idle"
