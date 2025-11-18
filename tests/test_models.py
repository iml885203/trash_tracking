"""Data model unit tests"""

import pytest

from src.models.point import Point
from src.models.truck import TruckLine


class TestPoint:
    """Point model tests"""

    @pytest.fixture
    def sample_point_data(self):
        return {
            "SourcePointID": 12345,
            "Vil": "Banqiao District",
            "PointName": "Wenhua Rd. Sec. 1, No. 100",
            "Lon": 121.4705,
            "Lat": 25.0199,
            "PointID": 1001,
            "PointRank": 5,
            "PointTime": "14:30",
            "Arrival": "",
            "ArrivalDiff": 65535,
            "FixedPoint": 1,
            "PointWeekKnd": "Y",
            "InScope": "Y",
            "LikeCount": 10,
        }

    @pytest.fixture
    def passed_point_data(self):
        return {
            "SourcePointID": 12346,
            "Vil": "Banqiao District",
            "PointName": "Wenhua Rd. Sec. 1, No. 50",
            "Lon": 121.4700,
            "Lat": 25.0190,
            "PointID": 1002,
            "PointRank": 3,
            "PointTime": "14:00",
            "Arrival": "14:05",
            "ArrivalDiff": 5,
            "FixedPoint": 1,
            "PointWeekKnd": "Y",
            "InScope": "Y",
            "LikeCount": 15,
        }

    def test_point_from_dict(self, sample_point_data):
        point = Point.from_dict(sample_point_data)

        assert point.source_point_id == 12345
        assert point.vil == "Banqiao District"
        assert point.point_name == "Wenhua Rd. Sec. 1, No. 100"
        assert point.lon == 121.4705
        assert point.lat == 25.0199
        assert point.point_id == 1001
        assert point.point_rank == 5
        assert point.point_time == "14:30"
        assert point.arrival == ""
        assert point.arrival_diff == 65535

    def test_point_has_passed_false(self, sample_point_data):
        point = Point.from_dict(sample_point_data)

        assert not point.has_passed()

    def test_point_has_passed_true(self, passed_point_data):
        point = Point.from_dict(passed_point_data)

        assert point.has_passed()
        assert point.arrival == "14:05"
        assert point.arrival_diff == 5

    def test_point_is_in_scope(self, sample_point_data):
        point = Point.from_dict(sample_point_data)

        assert point.is_in_scope()

    def test_point_is_not_in_scope(self, sample_point_data):
        sample_point_data["InScope"] = "N"
        point = Point.from_dict(sample_point_data)

        assert not point.is_in_scope()

    def test_point_to_dict(self, sample_point_data):
        point = Point.from_dict(sample_point_data)
        point_dict = point.to_dict()

        assert point_dict["name"] == "Wenhua Rd. Sec. 1, No. 100"
        assert point_dict["rank"] == 5
        assert point_dict["point_time"] == "14:30"
        assert point_dict["arrival"] == ""
        assert point_dict["arrival_diff"] == 65535
        assert point_dict["passed"] is False
        assert point_dict["in_scope"] is True

    def test_point_str(self, sample_point_data):
        point = Point.from_dict(sample_point_data)
        point_str = str(point)

        assert "Wenhua Rd. Sec. 1, No. 100" in point_str
        assert "5" in point_str
        assert "Not arrived" in point_str


class TestTruckLine:
    """Truck line model tests"""

    @pytest.fixture
    def sample_truck_data(self):
        return {
            "LineID": "C08",
            "LineName": "C08 Afternoon Route",
            "Area": "Banqiao District",
            "ArrivalRank": 10,
            "Diff": -5,
            "CarNO": "KES-6950",
            "Location": "New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100",
            "LocationLat": 25.0199,
            "LocationLon": 121.4705,
            "BarCode": "BC001",
            "Point": [
                {
                    "SourcePointID": 1,
                    "Vil": "Banqiao District",
                    "PointName": "Wenhua Rd. Sec. 1, No. 50",
                    "Lon": 121.47,
                    "Lat": 25.019,
                    "PointID": 1001,
                    "PointRank": 5,
                    "PointTime": "14:00",
                    "Arrival": "13:55",
                    "ArrivalDiff": -5,
                    "FixedPoint": 1,
                    "PointWeekKnd": "Y",
                    "InScope": "Y",
                    "LikeCount": 10,
                },
                {
                    "SourcePointID": 2,
                    "Vil": "Banqiao District",
                    "PointName": "Wenhua Rd. Sec. 1, No. 100",
                    "Lon": 121.4705,
                    "Lat": 25.0199,
                    "PointID": 1002,
                    "PointRank": 10,
                    "PointTime": "14:30",
                    "Arrival": "",
                    "ArrivalDiff": 65535,
                    "FixedPoint": 1,
                    "PointWeekKnd": "Y",
                    "InScope": "Y",
                    "LikeCount": 15,
                },
                {
                    "SourcePointID": 3,
                    "Vil": "Banqiao District",
                    "PointName": "Wenhua Rd. Sec. 1, No. 150",
                    "Lon": 121.471,
                    "Lat": 25.0205,
                    "PointID": 1003,
                    "PointRank": 15,
                    "PointTime": "15:00",
                    "Arrival": "",
                    "ArrivalDiff": 65535,
                    "FixedPoint": 1,
                    "PointWeekKnd": "Y",
                    "InScope": "N",
                    "LikeCount": 20,
                },
            ],
        }

    def test_truck_from_dict(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)

        assert truck.line_id == "C08"
        assert truck.line_name == "C08 Afternoon Route"
        assert truck.area == "Banqiao District"
        assert truck.arrival_rank == 10
        assert truck.diff == -5
        assert truck.car_no == "KES-6950"
        assert truck.location == "New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100"
        assert truck.location_lat == 25.0199
        assert truck.location_lon == 121.4705
        assert truck.bar_code == "BC001"
        assert len(truck.points) == 3

    def test_truck_find_point(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)

        point = truck.find_point("Wenhua Rd. Sec. 1, No. 100")
        assert point is not None
        assert point.point_rank == 10

        point = truck.find_point("Nonexistent Point")
        assert point is None

    def test_truck_get_current_point(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)

        current = truck.get_current_point()
        assert current is not None
        assert current.point_rank == 10
        assert current.point_name == "Wenhua Rd. Sec. 1, No. 100"

    def test_truck_get_upcoming_points(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)

        upcoming = truck.get_upcoming_points()

        assert len(upcoming) == 1
        assert upcoming[0].point_rank == 15
        assert upcoming[0].point_name == "Wenhua Rd. Sec. 1, No. 150"

    def test_truck_get_upcoming_points_sorted(self, sample_truck_data):
        sample_truck_data["ArrivalRank"] = 5
        truck = TruckLine.from_dict(sample_truck_data)

        upcoming = truck.get_upcoming_points()

        assert len(upcoming) == 2
        assert upcoming[0].point_rank == 10
        assert upcoming[1].point_rank == 15

    def test_truck_to_dict_basic(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)
        truck_dict = truck.to_dict()

        assert truck_dict["line_name"] == "C08 Afternoon Route"
        assert truck_dict["line_id"] == "C08"
        assert truck_dict["car_no"] == "KES-6950"
        assert truck_dict["area"] == "Banqiao District"
        assert truck_dict["current_location"] == "New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100"
        assert truck_dict["current_lat"] == 25.0199
        assert truck_dict["current_lon"] == 121.4705
        assert truck_dict["current_rank"] == 10
        assert truck_dict["total_points"] == 3
        assert truck_dict["arrival_diff"] == -5

    def test_truck_to_dict_with_enter_point(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)
        enter_point = truck.find_point("Wenhua Rd. Sec. 1, No. 150")

        truck_dict = truck.to_dict(enter_point=enter_point)

        assert "enter_point" in truck_dict
        assert truck_dict["enter_point"]["name"] == "Wenhua Rd. Sec. 1, No. 150"
        assert truck_dict["enter_point"]["distance_to_current"] == 5

    def test_truck_to_dict_with_exit_point(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)
        exit_point = truck.find_point("Wenhua Rd. Sec. 1, No. 50")

        truck_dict = truck.to_dict(exit_point=exit_point)

        assert "exit_point" in truck_dict
        assert truck_dict["exit_point"]["name"] == "Wenhua Rd. Sec. 1, No. 50"
        assert truck_dict["exit_point"]["distance_to_current"] == -5

    def test_truck_str(self, sample_truck_data):
        truck = TruckLine.from_dict(sample_truck_data)
        truck_str = str(truck)

        assert "C08 Afternoon Route" in truck_str
        assert "KES-6950" in truck_str
        assert "Wenhua Rd. Sec. 1, No. 100" in truck_str
        assert "10/3" in truck_str

    def test_truck_empty_points(self):
        data = {
            "LineID": "TEST",
            "LineName": "Test Line",
            "Area": "Test Area",
            "ArrivalRank": 0,
            "Diff": 0,
            "CarNO": "TEST-001",
            "Location": "Test Location",
            "LocationLat": 25.0,
            "LocationLon": 121.0,
            "BarCode": "BC001",
            "Point": [],
        }

        truck = TruckLine.from_dict(data)

        assert len(truck.points) == 0
        assert truck.get_current_point() is None
        assert truck.get_upcoming_points() == []

    def test_truck_diff_values(self):
        data = {
            "LineID": "TEST",
            "LineName": "Test Line",
            "Area": "Test Area",
            "ArrivalRank": 1,
            "Diff": -10,
            "CarNO": "TEST-001",
            "Location": "Test",
            "LocationLat": 25.0,
            "LocationLon": 121.0,
            "BarCode": "BC001",
            "Point": [],
        }

        truck = TruckLine.from_dict(data)
        assert truck.diff == -10

        data["Diff"] = 5
        truck = TruckLine.from_dict(data)
        assert truck.diff == 5

        data["Diff"] = 0
        truck = TruckLine.from_dict(data)
        assert truck.diff == 0
