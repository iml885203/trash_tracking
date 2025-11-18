"""CLI functionality tests"""

import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from cli import display_truck_info, format_point_info, main
from src.models.point import Point
from src.models.truck import TruckLine


class TestFormatPointInfo:
    """Point info formatting tests"""

    def test_format_passed_point(self):
        point = Point(
            source_point_id=1,
            vil="Banqiao District",
            point_name="Wenhua Rd. Sec. 1, No. 100",
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time="14:00",
            arrival="13:55",
            arrival_diff=5,
            fixed_point=1,
            point_weekknd="Y",
            in_scope="Y",
            like_count=10,
        )

        result = format_point_info(point, 1, 0)

        assert "✅" in result
        assert "13:55" in result
        assert "Wenhua Rd. Sec. 1, No. 100" in result

    def test_format_upcoming_point_with_delay(self):
        point = Point(
            source_point_id=1,
            vil="Banqiao District",
            point_name="Wenhua Rd. Sec. 1, No. 100",
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time="14:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="Y",
            in_scope="Y",
            like_count=10,
        )

        result = format_point_info(point, 1, 5)

        assert "⏳" in result
        assert "14:00" in result
        assert "14:05" in result
        assert "5min late" in result
        assert "Wenhua Rd. Sec. 1, No. 100" in result

    def test_format_upcoming_point_early(self):
        point = Point(
            source_point_id=1,
            vil="Banqiao District",
            point_name="Wenhua Rd. Sec. 1, No. 100",
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time="14:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="Y",
            in_scope="Y",
            like_count=10,
        )

        result = format_point_info(point, 1, -3)

        assert "⏳" in result
        assert "14:00" in result
        assert "13:57" in result
        assert "3min early" in result

    def test_format_upcoming_point_no_delay(self):
        point = Point(
            source_point_id=1,
            vil="Banqiao District",
            point_name="Wenhua Rd. Sec. 1, No. 100",
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time="14:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="Y",
            in_scope="Y",
            like_count=10,
        )

        result = format_point_info(point, 1, 0)

        assert "⏳" in result
        assert "14:00" in result
        assert "Wenhua Rd. Sec. 1, No. 100" in result

    def test_format_point_no_time(self):
        point = Point(
            source_point_id=1,
            vil="Banqiao District",
            point_name="Wenhua Rd. Sec. 1, No. 100",
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time="",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="Y",
            in_scope="Y",
            like_count=10,
        )

        result = format_point_info(point, 1, 0)

        assert "⏳" in result
        assert "Not arrived" in result
        assert "Wenhua Rd. Sec. 1, No. 100" in result


class TestDisplayTruckInfo:
    """Truck info display tests"""

    @pytest.fixture
    def sample_truck(self):
        points = [
            Point(
                source_point_id=i,
                vil="Banqiao District",
                point_name=f"Collection Point {i}",
                lon=121.47 + i * 0.001,
                lat=25.019 + i * 0.001,
                point_id=1000 + i,
                point_rank=i,
                point_time=f"14:{i:02d}",
                arrival="14:00" if i < 5 else "",
                arrival_diff=i if i < 5 else 65535,
                fixed_point=1,
                point_weekknd="Y",
                in_scope="Y",
                like_count=10,
            )
            for i in range(1, 16)
        ]

        return TruckLine(
            line_id="C08",
            line_name="C08 Afternoon Route",
            area="Banqiao District",
            arrival_rank=5,
            diff=-2,
            car_no="KES-6950",
            location="New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100",
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code="BC001",
            points=points,
        )

    def test_display_truck_info_with_upcoming_points(self, sample_truck, capsys):
        display_truck_info(sample_truck, next_points=5)

        captured = capsys.readouterr()
        output = captured.out

        assert "C08 Afternoon Route" in output
        assert "KES-6950" in output
        assert "New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100" in output
        assert "5/15" in output
        assert "Early Status" in output
        assert "2 minutes early" in output
        assert "Next" in output
        assert "5 collection points" in output

    def test_display_truck_info_all_completed(self, capsys):
        points = [
            Point(
                source_point_id=i,
                vil="Banqiao District",
                point_name=f"Collection Point {i}",
                lon=121.47,
                lat=25.019,
                point_id=1000 + i,
                point_rank=i,
                point_time=f"14:{i:02d}",
                arrival="14:00",
                arrival_diff=i,
                fixed_point=1,
                point_weekknd="Y",
                in_scope="Y",
                like_count=10,
            )
            for i in range(1, 6)
        ]

        truck = TruckLine(
            line_id="C08",
            line_name="C08 Afternoon Route",
            area="Banqiao District",
            arrival_rank=10,
            diff=0,
            car_no="KES-6950",
            location="New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100",
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code="BC001",
            points=points,
        )

        display_truck_info(truck, next_points=10)

        captured = capsys.readouterr()
        output = captured.out

        assert "All collection points completed" in output


class TestMainCLI:
    """CLI main program tests"""

    @patch("cli.NTPCApiClient")
    def test_main_success(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        points = [
            Point(
                source_point_id=1,
                vil="Banqiao District",
                point_name="Collection Point 1",
                lon=121.47,
                lat=25.019,
                point_id=1001,
                point_rank=5,
                point_time="14:00",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="Y",
                in_scope="Y",
                like_count=10,
            )
        ]

        truck = TruckLine(
            line_id="C08",
            line_name="C08 Afternoon Route",
            area="Banqiao District",
            arrival_rank=3,
            diff=0,
            car_no="KES-6950",
            location="New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100",
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code="BC001",
            points=points,
        )

        mock_client.get_around_points.return_value = [truck]

        test_args = ["cli.py", "--lat", "25.0199", "--lng", "121.4705"]
        with patch.object(sys, "argv", test_args):
            result = main()

        assert result == 0
        mock_client.get_around_points.assert_called_once_with(25.0199, 121.4705)

    @patch("cli.NTPCApiClient")
    def test_main_no_trucks_found(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_around_points.return_value = []

        test_args = ["cli.py", "--lat", "25.0199", "--lng", "121.4705"]
        with patch.object(sys, "argv", test_args):
            result = main()

        assert result == 0

    @patch("cli.NTPCApiClient")
    def test_main_with_radius(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_around_points.return_value = []

        test_args = ["cli.py", "--lat", "25.0199", "--lng", "121.4705", "--radius", "2000"]
        with patch.object(sys, "argv", test_args):
            result = main()

        assert result == 0

    @patch("cli.NTPCApiClient")
    def test_main_with_line_filter(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        truck1 = Mock(spec=TruckLine)
        truck1.line_name = "C08 Afternoon Route"
        truck2 = Mock(spec=TruckLine)
        truck2.line_name = "C15 Afternoon Route"

        mock_client.get_around_points.return_value = [truck1, truck2]

        test_args = ["cli.py", "--lat", "25.0199", "--lng", "121.4705", "--line", "C08 Afternoon Route"]
        with patch.object(sys, "argv", test_args):
            with patch("cli.display_truck_info"):
                result = main()

        assert result == 0

    def test_main_missing_required_args(self):
        test_args = ["cli.py"]
        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit):
                main()

    @patch("cli.NTPCApiClient")
    def test_main_api_error(self, mock_client_class):
        from src.clients.ntpc_api import NTPCApiError

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_around_points.side_effect = NTPCApiError("API error")

        test_args = ["cli.py", "--lat", "25.0199", "--lng", "121.4705"]
        with patch.object(sys, "argv", test_args):
            result = main()

        assert result == 1
