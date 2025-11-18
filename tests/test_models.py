"""資料模型單元測試"""

import pytest
from src.models.point import Point
from src.models.truck import TruckLine


class TestPoint:
    """清運點模型測試"""

    @pytest.fixture
    def sample_point_data(self):
        """範例清運點資料"""
        return {
            'SourcePointID': 12345,
            'Vil': '板橋區',
            'PointName': '文化路一段100號',
            'Lon': 121.4705,
            'Lat': 25.0199,
            'PointID': 1001,
            'PointRank': 5,
            'PointTime': '14:30',
            'Arrival': '',
            'ArrivalDiff': 65535,
            'FixedPoint': 1,
            'PointWeekKnd': 'Y',
            'InScope': 'Y',
            'LikeCount': 10
        }

    @pytest.fixture
    def passed_point_data(self):
        """已經過的清運點資料"""
        return {
            'SourcePointID': 12346,
            'Vil': '板橋區',
            'PointName': '文化路一段50號',
            'Lon': 121.4700,
            'Lat': 25.0190,
            'PointID': 1002,
            'PointRank': 3,
            'PointTime': '14:00',
            'Arrival': '14:05',
            'ArrivalDiff': 5,
            'FixedPoint': 1,
            'PointWeekKnd': 'Y',
            'InScope': 'Y',
            'LikeCount': 15
        }

    def test_point_from_dict(self, sample_point_data):
        """測試從字典建立 Point 物件"""
        point = Point.from_dict(sample_point_data)

        assert point.source_point_id == 12345
        assert point.vil == '板橋區'
        assert point.point_name == '文化路一段100號'
        assert point.lon == 121.4705
        assert point.lat == 25.0199
        assert point.point_id == 1001
        assert point.point_rank == 5
        assert point.point_time == '14:30'
        assert point.arrival == ''
        assert point.arrival_diff == 65535

    def test_point_has_passed_false(self, sample_point_data):
        """測試未經過的清運點"""
        point = Point.from_dict(sample_point_data)

        assert not point.has_passed()

    def test_point_has_passed_true(self, passed_point_data):
        """測試已經過的清運點"""
        point = Point.from_dict(passed_point_data)

        assert point.has_passed()
        assert point.arrival == '14:05'
        assert point.arrival_diff == 5

    def test_point_is_in_scope(self, sample_point_data):
        """測試清運點是否在範圍內"""
        point = Point.from_dict(sample_point_data)

        assert point.is_in_scope()

    def test_point_is_not_in_scope(self, sample_point_data):
        """測試清運點不在範圍內"""
        sample_point_data['InScope'] = 'N'
        point = Point.from_dict(sample_point_data)

        assert not point.is_in_scope()

    def test_point_to_dict(self, sample_point_data):
        """測試轉換為字典"""
        point = Point.from_dict(sample_point_data)
        point_dict = point.to_dict()

        assert point_dict['name'] == '文化路一段100號'
        assert point_dict['rank'] == 5
        assert point_dict['point_time'] == '14:30'
        assert point_dict['arrival'] == ''
        assert point_dict['arrival_diff'] == 65535
        assert point_dict['passed'] is False
        assert point_dict['in_scope'] is True

    def test_point_str(self, sample_point_data):
        """測試字串表示"""
        point = Point.from_dict(sample_point_data)
        point_str = str(point)

        assert '文化路一段100號' in point_str
        assert '5' in point_str
        assert '未到達' in point_str


class TestTruckLine:
    """垃圾車路線模型測試"""

    @pytest.fixture
    def sample_truck_data(self):
        """範例垃圾車資料"""
        return {
            'LineID': 'C08',
            'LineName': 'C08路線下午',
            'Area': '板橋區',
            'ArrivalRank': 10,
            'Diff': -5,
            'CarNO': 'KES-6950',
            'Location': '新北市板橋區文化路一段100號',
            'LocationLat': 25.0199,
            'LocationLon': 121.4705,
            'BarCode': 'BC001',
            'Point': [
                {
                    'SourcePointID': 1,
                    'Vil': '板橋區',
                    'PointName': '文化路一段50號',
                    'Lon': 121.47,
                    'Lat': 25.019,
                    'PointID': 1001,
                    'PointRank': 5,
                    'PointTime': '14:00',
                    'Arrival': '13:55',
                    'ArrivalDiff': -5,
                    'FixedPoint': 1,
                    'PointWeekKnd': 'Y',
                    'InScope': 'Y',
                    'LikeCount': 10
                },
                {
                    'SourcePointID': 2,
                    'Vil': '板橋區',
                    'PointName': '文化路一段100號',
                    'Lon': 121.4705,
                    'Lat': 25.0199,
                    'PointID': 1002,
                    'PointRank': 10,
                    'PointTime': '14:30',
                    'Arrival': '',
                    'ArrivalDiff': 65535,
                    'FixedPoint': 1,
                    'PointWeekKnd': 'Y',
                    'InScope': 'Y',
                    'LikeCount': 15
                },
                {
                    'SourcePointID': 3,
                    'Vil': '板橋區',
                    'PointName': '文化路一段150號',
                    'Lon': 121.471,
                    'Lat': 25.0205,
                    'PointID': 1003,
                    'PointRank': 15,
                    'PointTime': '15:00',
                    'Arrival': '',
                    'ArrivalDiff': 65535,
                    'FixedPoint': 1,
                    'PointWeekKnd': 'Y',
                    'InScope': 'N',
                    'LikeCount': 20
                }
            ]
        }

    def test_truck_from_dict(self, sample_truck_data):
        """測試從字典建立 TruckLine 物件"""
        truck = TruckLine.from_dict(sample_truck_data)

        assert truck.line_id == 'C08'
        assert truck.line_name == 'C08路線下午'
        assert truck.area == '板橋區'
        assert truck.arrival_rank == 10
        assert truck.diff == -5
        assert truck.car_no == 'KES-6950'
        assert truck.location == '新北市板橋區文化路一段100號'
        assert truck.location_lat == 25.0199
        assert truck.location_lon == 121.4705
        assert truck.bar_code == 'BC001'
        assert len(truck.points) == 3

    def test_truck_find_point(self, sample_truck_data):
        """測試尋找清運點"""
        truck = TruckLine.from_dict(sample_truck_data)

        point = truck.find_point('文化路一段100號')
        assert point is not None
        assert point.point_rank == 10

        # 測試找不到的情況
        point = truck.find_point('不存在的點')
        assert point is None

    def test_truck_get_current_point(self, sample_truck_data):
        """測試取得目前清運點"""
        truck = TruckLine.from_dict(sample_truck_data)

        current = truck.get_current_point()
        assert current is not None
        assert current.point_rank == 10
        assert current.point_name == '文化路一段100號'

    def test_truck_get_upcoming_points(self, sample_truck_data):
        """測試取得即將到達的清運點"""
        truck = TruckLine.from_dict(sample_truck_data)

        upcoming = truck.get_upcoming_points()

        # 應該只有 rank > 10 的點
        assert len(upcoming) == 1
        assert upcoming[0].point_rank == 15
        assert upcoming[0].point_name == '文化路一段150號'

    def test_truck_get_upcoming_points_sorted(self, sample_truck_data):
        """測試即將到達的清運點按順序排列"""
        # 修改資料，增加更多未到達的點
        sample_truck_data['ArrivalRank'] = 5
        truck = TruckLine.from_dict(sample_truck_data)

        upcoming = truck.get_upcoming_points()

        # 應該有 2 個點（rank 10 和 15）
        assert len(upcoming) == 2

        # 驗證排序
        assert upcoming[0].point_rank == 10
        assert upcoming[1].point_rank == 15

    def test_truck_to_dict_basic(self, sample_truck_data):
        """測試轉換為字典（基本資訊）"""
        truck = TruckLine.from_dict(sample_truck_data)
        truck_dict = truck.to_dict()

        assert truck_dict['line_name'] == 'C08路線下午'
        assert truck_dict['line_id'] == 'C08'
        assert truck_dict['car_no'] == 'KES-6950'
        assert truck_dict['area'] == '板橋區'
        assert truck_dict['current_location'] == '新北市板橋區文化路一段100號'
        assert truck_dict['current_lat'] == 25.0199
        assert truck_dict['current_lon'] == 121.4705
        assert truck_dict['current_rank'] == 10
        assert truck_dict['total_points'] == 3
        assert truck_dict['arrival_diff'] == -5

    def test_truck_to_dict_with_enter_point(self, sample_truck_data):
        """測試轉換為字典（包含進入點）"""
        truck = TruckLine.from_dict(sample_truck_data)
        enter_point = truck.find_point('文化路一段150號')

        truck_dict = truck.to_dict(enter_point=enter_point)

        assert 'enter_point' in truck_dict
        assert truck_dict['enter_point']['name'] == '文化路一段150號'
        assert truck_dict['enter_point']['distance_to_current'] == 5  # 15 - 10

    def test_truck_to_dict_with_exit_point(self, sample_truck_data):
        """測試轉換為字典（包含離開點）"""
        truck = TruckLine.from_dict(sample_truck_data)
        exit_point = truck.find_point('文化路一段50號')

        truck_dict = truck.to_dict(exit_point=exit_point)

        assert 'exit_point' in truck_dict
        assert truck_dict['exit_point']['name'] == '文化路一段50號'
        assert truck_dict['exit_point']['distance_to_current'] == -5  # 5 - 10

    def test_truck_str(self, sample_truck_data):
        """測試字串表示"""
        truck = TruckLine.from_dict(sample_truck_data)
        truck_str = str(truck)

        assert 'C08路線下午' in truck_str
        assert 'KES-6950' in truck_str
        assert '文化路一段100號' in truck_str
        assert '10/3' in truck_str

    def test_truck_empty_points(self):
        """測試沒有清運點的情況"""
        data = {
            'LineID': 'TEST',
            'LineName': 'Test Line',
            'Area': 'Test Area',
            'ArrivalRank': 0,
            'Diff': 0,
            'CarNO': 'TEST-001',
            'Location': 'Test Location',
            'LocationLat': 25.0,
            'LocationLon': 121.0,
            'BarCode': 'BC001',
            'Point': []
        }

        truck = TruckLine.from_dict(data)

        assert len(truck.points) == 0
        assert truck.get_current_point() is None
        assert truck.get_upcoming_points() == []

    def test_truck_diff_values(self):
        """測試不同的延遲值"""
        # 測試提早（負值）
        data = {
            'LineID': 'TEST',
            'LineName': 'Test Line',
            'Area': 'Test Area',
            'ArrivalRank': 1,
            'Diff': -10,
            'CarNO': 'TEST-001',
            'Location': 'Test',
            'LocationLat': 25.0,
            'LocationLon': 121.0,
            'BarCode': 'BC001',
            'Point': []
        }

        truck = TruckLine.from_dict(data)
        assert truck.diff == -10

        # 測試延遲（正值）
        data['Diff'] = 5
        truck = TruckLine.from_dict(data)
        assert truck.diff == 5

        # 測試準時（零）
        data['Diff'] = 0
        truck = TruckLine.from_dict(data)
        assert truck.diff == 0
