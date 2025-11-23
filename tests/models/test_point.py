"""Tests for Point model"""
import pytest
from trash_tracking_core.models.point import Point, PointStatus


@pytest.fixture
def sample_point_data():
    """Sample point data from API"""
    return {
        "SourcePointID": 123,
        "Vil": "Test Village",
        "PointName": "Test Point",
        "Lon": 121.5,
        "Lat": 25.0,
        "PointID": 456,
        "PointRank": 10,
        "PointTime": "18:00",
        "Arrival": "",
        "ArrivalDiff": 65535,
        "FixedPoint": 1,
        "PointWeekKnd": "1,3,5",
        "InScope": "Y",
        "LikeCount": 5,
    }


@pytest.fixture
def sample_point():
    """Sample Point object"""
    return Point(
        source_point_id=123,
        vil="Test Village",
        point_name="Test Point",
        lon=121.5,
        lat=25.0,
        point_id=456,
        point_rank=10,
        point_time="18:00",
        arrival="",
        arrival_diff=65535,
        fixed_point=1,
        point_weekknd="1,3,5",
        in_scope="Y",
        like_count=5,
    )


class TestPointCreation:
    """Test Point object creation"""

    def test_point_from_dict(self, sample_point_data):
        """Test creating Point from dict"""
        point = Point.from_dict(sample_point_data)

        assert point.source_point_id == 123
        assert point.vil == "Test Village"
        assert point.point_name == "Test Point"
        assert point.lon == 121.5
        assert point.lat == 25.0
        assert point.point_id == 456
        assert point.point_rank == 10
        assert point.point_time == "18:00"
        assert point.arrival == ""
        assert point.arrival_diff == 65535
        assert point.fixed_point == 1
        assert point.point_weekknd == "1,3,5"
        assert point.in_scope == "Y"
        assert point.like_count == 5

    def test_point_from_dict_with_defaults(self):
        """Test creating Point from dict with missing fields"""
        minimal_data = {"SourcePointID": 123, "PointID": 456}
        point = Point.from_dict(minimal_data)

        assert point.source_point_id == 123
        assert point.point_id == 456
        assert point.vil == ""
        assert point.point_name == ""
        assert point.lon == 0.0
        assert point.lat == 0.0
        assert point.point_rank == 0
        assert point.point_time == ""
        assert point.arrival == ""
        assert point.arrival_diff == 65535
        assert point.fixed_point == 0
        assert point.point_weekknd == ""
        assert point.in_scope == ""
        assert point.like_count == 0

    def test_point_to_dict(self, sample_point):
        """Test converting Point to dict"""
        result = sample_point.to_dict()

        assert result["name"] == "Test Point"
        assert result["rank"] == 10
        assert result["point_time"] == "18:00"
        assert result["arrival"] == ""
        assert result["arrival_diff"] == 65535
        assert result["passed"] is False
        assert result["in_scope"] is True


class TestPointStatus:
    """Test Point status methods"""

    def test_has_passed_false(self, sample_point):
        """Test has_passed returns False for not-yet-arrived point"""
        assert sample_point.has_passed() is False

    def test_has_passed_true(self, sample_point):
        """Test has_passed returns True for passed point"""
        sample_point.arrival = "18:05"
        sample_point.arrival_diff = 5
        assert sample_point.has_passed() is True

    def test_has_passed_with_arrival_but_no_diff(self, sample_point):
        """Test has_passed with arrival time but default diff"""
        sample_point.arrival = "18:05"
        sample_point.arrival_diff = 65535
        assert sample_point.has_passed() is False

    def test_is_in_scope_true(self, sample_point):
        """Test is_in_scope returns True when in scope"""
        assert sample_point.is_in_scope() is True

    def test_is_in_scope_false(self, sample_point):
        """Test is_in_scope returns False when out of scope"""
        sample_point.in_scope = "N"
        assert sample_point.is_in_scope() is False

    def test_get_status_scheduled(self, sample_point):
        """Test get_status returns SCHEDULED for future point"""
        assert sample_point.get_status() == PointStatus.SCHEDULED

    def test_get_status_arriving(self, sample_point):
        """Test get_status returns ARRIVING when truck is approaching"""
        sample_point.arrival = "18:00~18:10"
        assert sample_point.get_status() == PointStatus.ARRIVING

    def test_get_status_passed(self, sample_point):
        """Test get_status returns PASSED after truck passed"""
        sample_point.arrival = "18:05"
        sample_point.arrival_diff = 5
        assert sample_point.get_status() == PointStatus.PASSED


class TestWeekdayParsing:
    """Test weekday parsing functionality"""

    def test_get_weekdays_normal(self):
        """Test parsing normal weekday string"""
        point = Point(
            source_point_id=1,
            vil="Test",
            point_name="Test Point",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        )

        weekdays = point.get_weekdays()
        assert weekdays == [1, 3, 5]

    def test_get_weekdays_with_sunday_as_7(self):
        """Test parsing weekday string with Sunday as 7"""
        point = Point(
            source_point_id=1,
            vil="Test",
            point_name="Test Point",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="7",
            in_scope="Y",
            like_count=0,
        )

        weekdays = point.get_weekdays()
        assert weekdays == [0]  # Should convert 7 to 0

    def test_get_weekdays_with_sunday_as_0(self):
        """Test parsing weekday string with Sunday as 0"""
        point = Point(
            source_point_id=1,
            vil="Test",
            point_name="Test Point",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="0",
            in_scope="Y",
            like_count=0,
        )

        weekdays = point.get_weekdays()
        assert weekdays == [0]

    def test_get_weekdays_with_both_sunday_formats(self):
        """Test parsing weekday string with both 0 and 7 for Sunday"""
        point = Point(
            source_point_id=1,
            vil="Test",
            point_name="Test Point",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="0,7",
            in_scope="Y",
            like_count=0,
        )

        weekdays = point.get_weekdays()
        assert weekdays == [0]  # Should normalize to [0]

    def test_get_weekdays_empty(self):
        """Test parsing empty weekday string"""
        point = Point(
            source_point_id=1,
            vil="Test",
            point_name="Test Point",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="",
            in_scope="Y",
            like_count=0,
        )

        weekdays = point.get_weekdays()
        assert weekdays == []

    def test_get_weekdays_invalid(self):
        """Test parsing invalid weekday string"""
        point = Point(
            source_point_id=1,
            vil="Test",
            point_name="Test Point",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="invalid",
            in_scope="Y",
            like_count=0,
        )

        weekdays = point.get_weekdays()
        assert weekdays == []

    def test_get_weekdays_all_days(self):
        """Test parsing all weekdays"""
        point = Point(
            source_point_id=1,
            vil="Test",
            point_name="Test Point",
            lon=121.5,
            lat=25.0,
            point_id=1,
            point_rank=1,
            point_time="18:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="0,1,2,3,4,5,6",
            in_scope="Y",
            like_count=0,
        )

        weekdays = point.get_weekdays()
        assert weekdays == [0, 1, 2, 3, 4, 5, 6]


class TestEstimatedArrival:
    """Test estimated arrival calculations"""

    def test_get_estimated_arrival_on_time(self, sample_point):
        """Test estimated arrival when truck is on time"""
        estimated = sample_point.get_estimated_arrival(0)

        assert estimated is not None
        assert estimated.hour == 18
        assert estimated.minute == 0

    def test_get_estimated_arrival_delayed(self, sample_point):
        """Test estimated arrival when truck is delayed"""
        estimated = sample_point.get_estimated_arrival(15)

        assert estimated is not None
        assert estimated.hour == 18
        assert estimated.minute == 15

    def test_get_estimated_arrival_early(self, sample_point):
        """Test estimated arrival when truck is early"""
        estimated = sample_point.get_estimated_arrival(-10)

        assert estimated is not None
        assert estimated.hour == 17
        assert estimated.minute == 50

    def test_get_estimated_arrival_no_schedule(self, sample_point):
        """Test estimated arrival when no schedule time"""
        sample_point.point_time = ""
        estimated = sample_point.get_estimated_arrival(0)

        assert estimated is None

    def test_get_estimated_arrival_invalid_time(self, sample_point):
        """Test estimated arrival with invalid time format"""
        sample_point.point_time = "invalid"
        estimated = sample_point.get_estimated_arrival(0)

        assert estimated is None


class TestDelayDescription:
    """Test delay description generation"""

    def test_get_delay_description_on_time(self, sample_point):
        """Test delay description when on time"""
        description = sample_point.get_delay_description(0)
        assert description == "on time"

    def test_get_delay_description_late(self, sample_point):
        """Test delay description when late"""
        description = sample_point.get_delay_description(5)
        assert description == "5min late"

    def test_get_delay_description_very_late(self, sample_point):
        """Test delay description when very late"""
        description = sample_point.get_delay_description(30)
        assert description == "30min late"

    def test_get_delay_description_early(self, sample_point):
        """Test delay description when early"""
        description = sample_point.get_delay_description(-3)
        assert description == "3min early"

    def test_get_delay_description_very_early(self, sample_point):
        """Test delay description when very early"""
        description = sample_point.get_delay_description(-20)
        assert description == "20min early"


class TestStringRepresentation:
    """Test string representation"""

    def test_str_not_arrived(self, sample_point):
        """Test __str__ for point not yet arrived"""
        result = str(sample_point)
        assert "Test Point" in result
        assert "rank: 10" in result
        assert "Not arrived" in result

    def test_str_arrived(self, sample_point):
        """Test __str__ for point already passed"""
        sample_point.arrival = "18:05"
        sample_point.arrival_diff = 5
        result = str(sample_point)
        assert "Test Point" in result
        assert "rank: 10" in result
        assert "Arrived" in result
