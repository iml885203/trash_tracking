"""Tests for TruckLine model"""
import pytest
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine


@pytest.fixture
def sample_points():
    """Sample collection points"""
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
            arrival="18:25",
            arrival_diff=5,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
    ]


@pytest.fixture
def sample_truck_data():
    """Sample truck data from API"""
    return {
        "LineID": "L001",
        "LineName": "Test Route 123",
        "Area": "Test Area",
        "ArrivalRank": 2,
        "Diff": 5,
        "CarNO": "ABC-1234",
        "Location": "Test Location",
        "LocationLat": 25.01,
        "LocationLon": 121.51,
        "BarCode": "12345",
        "Point": [
            {
                "SourcePointID": 1,
                "Vil": "Village A",
                "PointName": "Point 1",
                "Lon": 121.5,
                "Lat": 25.0,
                "PointID": 101,
                "PointRank": 1,
                "PointTime": "18:00",
                "Arrival": "",
                "ArrivalDiff": 65535,
                "FixedPoint": 1,
                "PointWeekKnd": "1,3,5",
                "InScope": "Y",
                "LikeCount": 0,
            },
            {
                "SourcePointID": 2,
                "Vil": "Village B",
                "PointName": "Point 2",
                "Lon": 121.51,
                "Lat": 25.01,
                "PointID": 102,
                "PointRank": 2,
                "PointTime": "18:10",
                "Arrival": "",
                "ArrivalDiff": 65535,
                "FixedPoint": 1,
                "PointWeekKnd": "1,3,5",
                "InScope": "Y",
                "LikeCount": 0,
            },
        ],
    }


@pytest.fixture
def sample_truck(sample_points):
    """Sample TruckLine object"""
    return TruckLine(
        line_id="L001",
        line_name="Test Route 123",
        area="Test Area",
        arrival_rank=2,
        diff=5,
        car_no="ABC-1234",
        location="Test Location",
        location_lat=25.01,
        location_lon=121.51,
        bar_code="12345",
        points=sample_points,
    )


class TestTruckCreation:
    """Test TruckLine object creation"""

    def test_truck_from_dict(self, sample_truck_data):
        """Test creating TruckLine from dict"""
        truck = TruckLine.from_dict(sample_truck_data)

        assert truck.line_id == "L001"
        assert truck.line_name == "Test Route 123"
        assert truck.area == "Test Area"
        assert truck.arrival_rank == 2
        assert truck.diff == 5
        assert truck.car_no == "ABC-1234"
        assert truck.location == "Test Location"
        assert truck.location_lat == 25.01
        assert truck.location_lon == 121.51
        assert truck.bar_code == "12345"
        assert len(truck.points) == 2
        assert truck.points[0].point_name == "Point 1"
        assert truck.points[1].point_name == "Point 2"

    def test_truck_from_dict_with_defaults(self):
        """Test creating TruckLine from dict with missing fields"""
        minimal_data = {"Point": []}
        truck = TruckLine.from_dict(minimal_data)

        assert truck.line_id == ""
        assert truck.line_name == ""
        assert truck.area == ""
        assert truck.arrival_rank == 0
        assert truck.diff == 0
        assert truck.car_no == ""
        assert truck.location == ""
        assert truck.location_lat == 0.0
        assert truck.location_lon == 0.0
        assert truck.bar_code == ""
        assert len(truck.points) == 0

    def test_truck_from_dict_no_points(self):
        """Test creating TruckLine from dict without points"""
        data = {
            "LineID": "L001",
            "LineName": "Test Route",
        }
        truck = TruckLine.from_dict(data)

        assert truck.line_id == "L001"
        assert truck.line_name == "Test Route"
        assert len(truck.points) == 0


class TestFindPoint:
    """Test finding collection points"""

    def test_find_point_exists(self, sample_truck):
        """Test finding an existing point by name"""
        point = sample_truck.find_point("Point 2")

        assert point is not None
        assert point.point_name == "Point 2"
        assert point.point_rank == 2

    def test_find_point_not_exists(self, sample_truck):
        """Test finding a non-existent point"""
        point = sample_truck.find_point("Non-existent Point")

        assert point is None

    def test_find_point_empty_name(self, sample_truck):
        """Test finding point with empty name"""
        point = sample_truck.find_point("")

        assert point is None

    def test_find_point_case_sensitive(self, sample_truck):
        """Test that point name search is case-sensitive"""
        point = sample_truck.find_point("point 2")  # lowercase

        assert point is None  # Should not find "Point 2"


class TestGetCurrentPoint:
    """Test getting current collection point"""

    def test_get_current_point_exists(self, sample_truck):
        """Test getting current point when it exists"""
        current = sample_truck.get_current_point()

        assert current is not None
        assert current.point_rank == 2
        assert current.point_name == "Point 2"

    def test_get_current_point_not_found(self, sample_truck):
        """Test getting current point when rank doesn't match"""
        sample_truck.arrival_rank = 99  # Non-existent rank

        current = sample_truck.get_current_point()

        assert current is None

    def test_get_current_point_first(self, sample_truck):
        """Test getting current point at first stop"""
        sample_truck.arrival_rank = 1

        current = sample_truck.get_current_point()

        assert current is not None
        assert current.point_rank == 1
        assert current.point_name == "Point 1"

    def test_get_current_point_last(self, sample_truck):
        """Test getting current point at last stop"""
        sample_truck.arrival_rank = 3

        current = sample_truck.get_current_point()

        assert current is not None
        assert current.point_rank == 3
        assert current.point_name == "Point 3"


class TestGetUpcomingPoints:
    """Test getting upcoming collection points"""

    def test_get_upcoming_points_normal(self, sample_truck):
        """Test getting upcoming points from middle of route"""
        sample_truck.arrival_rank = 1

        upcoming = sample_truck.get_upcoming_points()

        assert len(upcoming) == 2
        assert upcoming[0].point_name == "Point 2"
        assert upcoming[1].point_name == "Point 3"

    def test_get_upcoming_points_at_end(self, sample_truck):
        """Test getting upcoming points when at last stop"""
        sample_truck.arrival_rank = 3

        upcoming = sample_truck.get_upcoming_points()

        assert len(upcoming) == 0

    def test_get_upcoming_points_at_start(self, sample_truck):
        """Test getting upcoming points when at first stop"""
        sample_truck.arrival_rank = 0

        upcoming = sample_truck.get_upcoming_points()

        assert len(upcoming) == 3
        assert upcoming[0].point_rank == 1
        assert upcoming[1].point_rank == 2
        assert upcoming[2].point_rank == 3

    def test_get_upcoming_points_sorted(self, sample_truck):
        """Test that upcoming points are sorted by rank"""
        sample_truck.arrival_rank = 0

        upcoming = sample_truck.get_upcoming_points()

        # Verify sorted order
        for i in range(len(upcoming) - 1):
            assert upcoming[i].point_rank < upcoming[i + 1].point_rank


class TestToDict:
    """Test converting TruckLine to dict"""

    def test_to_dict_basic(self, sample_truck):
        """Test basic to_dict conversion"""
        result = sample_truck.to_dict()

        assert result["line_name"] == "Test Route 123"
        assert result["line_id"] == "L001"
        assert result["car_no"] == "ABC-1234"
        assert result["area"] == "Test Area"
        assert result["current_location"] == "Test Location"
        assert result["current_lat"] == 25.01
        assert result["current_lon"] == 121.51
        assert result["current_rank"] == 2
        assert result["total_points"] == 3
        assert result["arrival_diff"] == 5
        assert "enter_point" not in result
        assert "exit_point" not in result

    def test_to_dict_with_enter_point(self, sample_truck, sample_points):
        """Test to_dict with enter point"""
        enter_point = sample_points[0]  # Point 1, rank 1
        result = sample_truck.to_dict(enter_point=enter_point)

        assert "enter_point" in result
        assert result["enter_point"]["name"] == "Point 1"
        assert result["enter_point"]["rank"] == 1
        assert result["enter_point"]["distance_to_current"] == 1 - 2  # -1

    def test_to_dict_with_exit_point(self, sample_truck, sample_points):
        """Test to_dict with exit point"""
        exit_point = sample_points[2]  # Point 3, rank 3
        result = sample_truck.to_dict(exit_point=exit_point)

        assert "exit_point" in result
        assert result["exit_point"]["name"] == "Point 3"
        assert result["exit_point"]["rank"] == 3
        assert result["exit_point"]["distance_to_current"] == 3 - 2  # 1

    def test_to_dict_with_both_points(self, sample_truck, sample_points):
        """Test to_dict with both enter and exit points"""
        enter_point = sample_points[0]
        exit_point = sample_points[2]
        result = sample_truck.to_dict(enter_point=enter_point, exit_point=exit_point)

        assert "enter_point" in result
        assert "exit_point" in result
        assert result["enter_point"]["name"] == "Point 1"
        assert result["exit_point"]["name"] == "Point 3"


class TestStringRepresentation:
    """Test string representation"""

    def test_str_with_current_point(self, sample_truck):
        """Test __str__ when current point exists"""
        result = str(sample_truck)

        assert "Test Route 123" in result
        assert "ABC-1234" in result
        assert "Point 2" in result  # Current location
        assert "2/3" in result  # Current rank / total points

    def test_str_without_current_point(self, sample_truck):
        """Test __str__ when current point doesn't exist"""
        sample_truck.arrival_rank = 99  # Non-existent rank

        result = str(sample_truck)

        assert "Test Route 123" in result
        assert "ABC-1234" in result
        assert "Unknown" in result  # Should show Unknown for current location
        assert "99/3" in result
