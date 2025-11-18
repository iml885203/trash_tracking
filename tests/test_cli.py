"""CLI 功能測試"""

import pytest
import sys
from io import StringIO
from unittest.mock import Mock, patch
from cli import format_point_info, display_truck_info, main
from src.models.point import Point
from src.models.truck import TruckLine


class TestFormatPointInfo:
    """測試清運點資訊格式化"""

    def test_format_passed_point(self):
        """測試已經過的清運點"""
        point = Point(
            source_point_id=1,
            vil='板橋區',
            point_name='文化路一段100號',
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time='14:00',
            arrival='13:55',
            arrival_diff=5,
            fixed_point=1,
            point_weekknd='Y',
            in_scope='Y',
            like_count=10
        )

        result = format_point_info(point, 1, 0)

        assert '✅' in result
        assert '13:55' in result
        assert '文化路一段100號' in result

    def test_format_upcoming_point_with_delay(self):
        """測試未到達的清運點（有延遲）"""
        point = Point(
            source_point_id=1,
            vil='板橋區',
            point_name='文化路一段100號',
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time='14:00',
            arrival='',
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd='Y',
            in_scope='Y',
            like_count=10
        )

        # 測試延遲 5 分鐘
        result = format_point_info(point, 1, 5)

        assert '⏳' in result
        assert '14:00' in result  # 預定時間
        assert '14:05' in result  # 預計時間
        assert '晚5分' in result
        assert '文化路一段100號' in result

    def test_format_upcoming_point_early(self):
        """測試未到達的清運點（提早）"""
        point = Point(
            source_point_id=1,
            vil='板橋區',
            point_name='文化路一段100號',
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time='14:00',
            arrival='',
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd='Y',
            in_scope='Y',
            like_count=10
        )

        # 測試提早 3 分鐘
        result = format_point_info(point, 1, -3)

        assert '⏳' in result
        assert '14:00' in result  # 預定時間
        assert '13:57' in result  # 預計時間
        assert '早3分' in result

    def test_format_upcoming_point_no_delay(self):
        """測試未到達的清運點（準時）"""
        point = Point(
            source_point_id=1,
            vil='板橋區',
            point_name='文化路一段100號',
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time='14:00',
            arrival='',
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd='Y',
            in_scope='Y',
            like_count=10
        )

        result = format_point_info(point, 1, 0)

        assert '⏳' in result
        assert '14:00' in result
        assert '文化路一段100號' in result

    def test_format_point_no_time(self):
        """測試沒有時間資訊的清運點"""
        point = Point(
            source_point_id=1,
            vil='板橋區',
            point_name='文化路一段100號',
            lon=121.4705,
            lat=25.0199,
            point_id=1001,
            point_rank=5,
            point_time='',
            arrival='',
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd='Y',
            in_scope='Y',
            like_count=10
        )

        result = format_point_info(point, 1, 0)

        assert '⏳' in result
        assert '未到' in result
        assert '文化路一段100號' in result


class TestDisplayTruckInfo:
    """測試垃圾車資訊顯示"""

    @pytest.fixture
    def sample_truck(self):
        """建立範例垃圾車"""
        points = [
            Point(
                source_point_id=i,
                vil='板橋區',
                point_name=f'清運點{i}',
                lon=121.47 + i * 0.001,
                lat=25.019 + i * 0.001,
                point_id=1000 + i,
                point_rank=i,
                point_time=f'14:{i:02d}',
                arrival='14:00' if i < 5 else '',
                arrival_diff=i if i < 5 else 65535,
                fixed_point=1,
                point_weekknd='Y',
                in_scope='Y',
                like_count=10
            )
            for i in range(1, 16)
        ]

        return TruckLine(
            line_id='C08',
            line_name='C08路線下午',
            area='板橋區',
            arrival_rank=5,
            diff=-2,
            car_no='KES-6950',
            location='新北市板橋區文化路一段100號',
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code='BC001',
            points=points
        )

    def test_display_truck_info_with_upcoming_points(self, sample_truck, capsys):
        """測試顯示垃圾車資訊（有未到達的點）"""
        display_truck_info(sample_truck, next_points=5)

        captured = capsys.readouterr()
        output = captured.out

        # 驗證基本資訊
        assert 'C08路線下午' in output
        assert 'KES-6950' in output
        assert '新北市板橋區文化路一段100號' in output
        assert '5/15' in output

        # 驗證延遲狀態
        assert '提早狀態' in output
        assert '早 2 分鐘' in output

        # 驗證顯示接下來的點
        assert '接下來' in output
        assert '5 個清運點' in output

    def test_display_truck_info_all_completed(self, capsys):
        """測試顯示垃圾車資訊（所有點都完成）"""
        points = [
            Point(
                source_point_id=i,
                vil='板橋區',
                point_name=f'清運點{i}',
                lon=121.47,
                lat=25.019,
                point_id=1000 + i,
                point_rank=i,
                point_time=f'14:{i:02d}',
                arrival='14:00',
                arrival_diff=i,
                fixed_point=1,
                point_weekknd='Y',
                in_scope='Y',
                like_count=10
            )
            for i in range(1, 6)
        ]

        truck = TruckLine(
            line_id='C08',
            line_name='C08路線下午',
            area='板橋區',
            arrival_rank=10,  # 超過最大 rank
            diff=0,
            car_no='KES-6950',
            location='新北市板橋區文化路一段100號',
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code='BC001',
            points=points
        )

        display_truck_info(truck, next_points=10)

        captured = capsys.readouterr()
        output = captured.out

        assert '所有清運點都已完成' in output


class TestMainCLI:
    """測試 CLI 主程式"""

    @patch('cli.NTPCApiClient')
    def test_main_success(self, mock_client_class):
        """測試成功查詢"""
        # 模擬 API 回應
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        points = [
            Point(
                source_point_id=1,
                vil='板橋區',
                point_name='清運點1',
                lon=121.47,
                lat=25.019,
                point_id=1001,
                point_rank=5,
                point_time='14:00',
                arrival='',
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd='Y',
                in_scope='Y',
                like_count=10
            )
        ]

        truck = TruckLine(
            line_id='C08',
            line_name='C08路線下午',
            area='板橋區',
            arrival_rank=3,
            diff=0,
            car_no='KES-6950',
            location='新北市板橋區文化路一段100號',
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code='BC001',
            points=points
        )

        mock_client.get_around_points.return_value = [truck]

        # 測試執行
        test_args = ['cli.py', '--lat', '25.0199', '--lng', '121.4705']
        with patch.object(sys, 'argv', test_args):
            result = main()

        assert result == 0
        mock_client.get_around_points.assert_called_once_with(25.0199, 121.4705)

    @patch('cli.NTPCApiClient')
    def test_main_no_trucks_found(self, mock_client_class):
        """測試找不到垃圾車"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_around_points.return_value = []

        test_args = ['cli.py', '--lat', '25.0199', '--lng', '121.4705']
        with patch.object(sys, 'argv', test_args):
            result = main()

        assert result == 0

    @patch('cli.NTPCApiClient')
    def test_main_with_radius(self, mock_client_class):
        """測試指定半徑"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_around_points.return_value = []

        test_args = ['cli.py', '--lat', '25.0199', '--lng', '121.4705', '--radius', '2000']
        with patch.object(sys, 'argv', test_args):
            result = main()

        assert result == 0

    @patch('cli.NTPCApiClient')
    def test_main_with_line_filter(self, mock_client_class):
        """測試過濾特定路線"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        truck1 = Mock(spec=TruckLine)
        truck1.line_name = 'C08路線下午'
        truck2 = Mock(spec=TruckLine)
        truck2.line_name = 'C15路線下午'

        mock_client.get_around_points.return_value = [truck1, truck2]

        test_args = ['cli.py', '--lat', '25.0199', '--lng', '121.4705', '--line', 'C08路線下午']
        with patch.object(sys, 'argv', test_args):
            with patch('cli.display_truck_info'):
                result = main()

        assert result == 0

    def test_main_missing_required_args(self):
        """測試缺少必要參數"""
        test_args = ['cli.py']
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit):
                main()

    @patch('cli.NTPCApiClient')
    def test_main_api_error(self, mock_client_class):
        """測試 API 錯誤"""
        from src.clients.ntpc_api import NTPCApiError

        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_around_points.side_effect = NTPCApiError("API 錯誤")

        test_args = ['cli.py', '--lat', '25.0199', '--lng', '121.4705']
        with patch.object(sys, 'argv', test_args):
            result = main()

        assert result == 1
