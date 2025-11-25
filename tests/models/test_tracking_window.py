"""Tests for TrackingWindow value object"""
import pytest
from trash_tracking_core.models.tracking_window import TrackingWindow
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine


@pytest.fixture
def sample_points():
    """Sample collection points"""
    return [
        Point(
            source_point_id=1,
            vil="Village A",
            point_name="Point A",
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
            point_name="Point B",
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
            point_name="Point C",
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


class TestTrackingWindowInit:
    """Test TrackingWindow initialization"""

    def test_init_valid_points(self):
        """Test initialization with valid points"""
        window = TrackingWindow(enter_point_name="Point A", exit_point_name="Point C")

        assert window.enter_point_name == "Point A"
        assert window.exit_point_name == "Point C"

    def test_init_same_point_raises_error(self):
        """Test initialization with same enter and exit point raises error"""
        with pytest.raises(ValueError, match="Enter and exit points must be different"):
            TrackingWindow(enter_point_name="Point A", exit_point_name="Point A")

    def test_window_is_immutable(self):
        """Test TrackingWindow is immutable (frozen dataclass)"""
        window = TrackingWindow(enter_point_name="Point A", exit_point_name="Point C")

        with pytest.raises(Exception):
            window.enter_point_name = "Point B"


class TestFindPoints:
    """Test find_points method"""

    def test_find_points_success(self, sample_truck):
        """Test finding both points successfully"""
        window = TrackingWindow(enter_point_name="Point A", exit_point_name="Point C")

        result = window.find_points(sample_truck)

        assert result is not None
        enter_point, exit_point = result
        assert enter_point.point_name == "Point A"
        assert enter_point.point_rank == 1
        assert exit_point.point_name == "Point C"
        assert exit_point.point_rank == 3

    def test_find_points_enter_not_found(self, sample_truck):
        """Test when enter point not found"""
        window = TrackingWindow(enter_point_name="Non-existent", exit_point_name="Point C")

        result = window.find_points(sample_truck)

        assert result is None

    def test_find_points_exit_not_found(self, sample_truck):
        """Test when exit point not found"""
        window = TrackingWindow(enter_point_name="Point A", exit_point_name="Non-existent")

        result = window.find_points(sample_truck)

        assert result is None

    def test_find_points_both_not_found(self, sample_truck):
        """Test when both points not found"""
        window = TrackingWindow(enter_point_name="Non-existent 1", exit_point_name="Non-existent 2")

        result = window.find_points(sample_truck)

        assert result is None

    def test_find_points_invalid_order_raises_error(self, sample_truck):
        """Test when exit point comes before enter point"""
        window = TrackingWindow(enter_point_name="Point C", exit_point_name="Point A")

        with pytest.raises(ValueError, match="Exit point rank .* must be > enter point rank"):
            window.find_points(sample_truck)

    def test_find_points_empty_truck_points(self):
        """Test when truck has no points"""
        window = TrackingWindow(enter_point_name="Point A", exit_point_name="Point C")
        empty_truck = TruckLine(
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
            points=[],
        )

        result = window.find_points(empty_truck)

        assert result is None


class TestStringRepresentation:
    """Test string representation"""

    def test_str_representation(self):
        """Test string representation"""
        window = TrackingWindow(enter_point_name="Point A", exit_point_name="Point C")

        result = str(window)

        assert "Point A" in result
        assert "Point C" in result
