"""清運點匹配器測試"""

import pytest
from unittest.mock import patch, Mock

from src.core.point_matcher import PointMatcher, MatchResult
from src.models.truck import TruckLine
from src.models.point import Point


class TestMatchResult:
    """匹配結果測試"""

    def test_match_result_creation(self):
        """測試建立匹配結果"""
        result = MatchResult(
            should_trigger=True,
            new_state='nearby',
            reason='測試原因'
        )

        assert result.should_trigger is True
        assert result.new_state == 'nearby'
        assert result.reason == '測試原因'
        assert result.truck_line is None
        assert result.enter_point is None
        assert result.exit_point is None

    def test_match_result_with_full_data(self):
        """測試包含完整資料的匹配結果"""
        truck = Mock(spec=TruckLine)
        enter_point = Mock(spec=Point)
        exit_point = Mock(spec=Point)

        result = MatchResult(
            should_trigger=True,
            new_state='idle',
            reason='完整測試',
            truck_line=truck,
            enter_point=enter_point,
            exit_point=exit_point
        )

        assert result.should_trigger is True
        assert result.new_state == 'idle'
        assert result.truck_line == truck
        assert result.enter_point == enter_point
        assert result.exit_point == exit_point


class TestPointMatcher:
    """清運點匹配器測試"""

    @pytest.fixture
    def matcher_arriving(self):
        """建立 arriving 模式的匹配器"""
        return PointMatcher(
            enter_point_name='民生路二段80號',
            exit_point_name='成功路23號',
            trigger_mode='arriving',
            approaching_threshold=2
        )

    @pytest.fixture
    def matcher_arrived(self):
        """建立 arrived 模式的匹配器"""
        return PointMatcher(
            enter_point_name='民生路二段80號',
            exit_point_name='成功路23號',
            trigger_mode='arrived',
            approaching_threshold=2
        )

    @pytest.fixture
    def create_point(self):
        """建立清運點的輔助函數"""
        def _create_point(name, rank, arrival='', arrival_diff=65535):
            return Point(
                source_point_id=rank,
                vil='板橋區',
                point_name=name,
                lon=121.4705,
                lat=25.0199,
                point_id=1000 + rank,
                point_rank=rank,
                point_time=f'14:{rank:02d}',
                arrival=arrival,
                arrival_diff=arrival_diff,
                fixed_point=1,
                point_weekknd='Y',
                in_scope='Y',
                like_count=10
            )
        return _create_point

    @pytest.fixture
    def create_truck(self, create_point):
        """建立垃圾車的輔助函數"""
        def _create_truck(arrival_rank, points_config):
            """
            points_config: list of tuples (name, rank, arrival, arrival_diff)
            """
            points = [create_point(*config) for config in points_config]

            return TruckLine(
                line_id='C08',
                line_name='C08路線下午',
                area='板橋區',
                arrival_rank=arrival_rank,
                diff=-5,
                car_no='KES-6950',
                location='新北市板橋區',
                location_lat=25.0199,
                location_lon=121.4705,
                bar_code='BC001',
                points=points
            )
        return _create_truck

    def test_initialization(self, matcher_arriving):
        """測試匹配器初始化"""
        assert matcher_arriving.enter_point_name == '民生路二段80號'
        assert matcher_arriving.exit_point_name == '成功路23號'
        assert matcher_arriving.trigger_mode == 'arriving'
        assert matcher_arriving.approaching_threshold == 2

    def test_str_representation(self, matcher_arriving):
        """測試字串表示"""
        result = str(matcher_arriving)

        assert '民生路二段80號' in result
        assert '成功路23號' in result
        assert 'arriving' in result

    def test_check_line_enter_point_not_found(self, matcher_arriving, create_truck):
        """測試找不到進入清運點"""
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('其他點1', 5, '', 65535),
                ('成功路23號', 10, '', 65535),  # 只有離開點
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_check_line_exit_point_not_found(self, matcher_arriving, create_truck):
        """測試找不到離開清運點"""
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('民生路二段80號', 8, '', 65535),  # 只有進入點
                ('其他點2', 10, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_check_line_invalid_order(self, matcher_arriving, create_truck):
        """測試清運點順序錯誤（離開點在進入點之前）"""
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('成功路23號', 8, '', 65535),  # 離開點
                ('民生路二段80號', 10, '', 65535),  # 進入點（順序錯誤）
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_check_line_invalid_order_same_rank(self, matcher_arriving, create_truck):
        """測試清運點順序錯誤（相同 rank）"""
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('民生路二段80號', 10, '', 65535),
                ('成功路23號', 10, '', 65535),  # 相同 rank
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    # Arriving 模式測試
    def test_arriving_mode_trigger_at_threshold(self, matcher_arriving, create_truck):
        """測試 arriving 模式：剛好在閾值距離時觸發"""
        truck = create_truck(
            arrival_rank=6,  # 距離進入點 2 個停靠點
            points_config=[
                ('民生路二段80號', 8, '', 65535),  # rank 8
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'nearby'
        assert '即將到達' in result.reason
        assert result.truck_line == truck
        assert result.enter_point.point_name == '民生路二段80號'
        assert result.exit_point.point_name == '成功路23號'

    def test_arriving_mode_trigger_within_threshold(self, matcher_arriving, create_truck):
        """測試 arriving 模式：在閾值範圍內觸發"""
        truck = create_truck(
            arrival_rank=7,  # 距離進入點 1 個停靠點
            points_config=[
                ('民生路二段80號', 8, '', 65535),
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'nearby'

    def test_arriving_mode_not_trigger_too_far(self, matcher_arriving, create_truck):
        """測試 arriving 模式：距離太遠不觸發"""
        truck = create_truck(
            arrival_rank=5,  # 距離進入點 3 個停靠點（超過閾值 2）
            points_config=[
                ('民生路二段80號', 8, '', 65535),
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_arriving_mode_not_trigger_already_passed(self, matcher_arriving, create_truck):
        """測試 arriving 模式：已經過進入點不觸發"""
        truck = create_truck(
            arrival_rank=9,  # 已經過進入點
            points_config=[
                ('民生路二段80號', 8, '14:05', 5),  # 已經過
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        # 不應該觸發進入，應該繼續往下檢查離開
        assert result.should_trigger is False

    # Arrived 模式測試
    def test_arrived_mode_trigger_when_arrived(self, matcher_arrived, create_truck):
        """測試 arrived 模式：到達時觸發"""
        truck = create_truck(
            arrival_rank=8,  # 剛到達進入點
            points_config=[
                ('民生路二段80號', 8, '14:05', 0),  # 已到達
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher_arrived.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'nearby'
        assert result.enter_point.has_passed() is True

    def test_arrived_mode_not_trigger_before_arrival(self, matcher_arrived, create_truck):
        """測試 arrived 模式：未到達前不觸發"""
        truck = create_truck(
            arrival_rank=7,  # 還沒到達進入點
            points_config=[
                ('民生路二段80號', 8, '', 65535),  # 未到達
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher_arrived.check_line(truck)

        assert result.should_trigger is False

    # 離開點觸發測試
    def test_trigger_exit_when_passed(self, matcher_arriving, create_truck):
        """測試垃圾車經過離開點時觸發"""
        truck = create_truck(
            arrival_rank=16,  # 已經過離開點
            points_config=[
                ('民生路二段80號', 8, '14:05', 5),  # 已經過
                ('成功路23號', 15, '14:25', 5),  # 已經過
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'idle'
        assert '已經過離開清運點' in result.reason
        assert result.exit_point.has_passed() is True

    def test_not_trigger_exit_before_passed(self, matcher_arriving, create_truck):
        """測試垃圾車未經過離開點時不觸發離開"""
        truck = create_truck(
            arrival_rank=10,  # 在進入點和離開點之間
            points_config=[
                ('民生路二段80號', 8, '14:05', 5),  # 已經過
                ('成功路23號', 15, '', 65535),  # 未經過
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    # 邊界情況測試
    def test_arriving_mode_at_exact_enter_point(self, matcher_arriving, create_truck):
        """測試 arriving 模式：剛好在進入點位置"""
        truck = create_truck(
            arrival_rank=8,  # 剛好在進入點
            points_config=[
                ('民生路二段80號', 8, '', 65535),  # 未標記為經過
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        # distance = 8 - 8 = 0，在閾值範圍內
        assert result.should_trigger is True
        assert result.new_state == 'nearby'

    def test_threshold_zero(self, create_truck):
        """測試閾值為 0 的情況"""
        matcher = PointMatcher(
            enter_point_name='民生路二段80號',
            exit_point_name='成功路23號',
            trigger_mode='arriving',
            approaching_threshold=0
        )

        truck = create_truck(
            arrival_rank=8,  # 剛好在進入點
            points_config=[
                ('民生路二段80號', 8, '', 65535),
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher.check_line(truck)

        # distance = 0，在閾值範圍內
        assert result.should_trigger is True

    def test_large_threshold(self, create_truck):
        """測試很大的閾值"""
        matcher = PointMatcher(
            enter_point_name='民生路二段80號',
            exit_point_name='成功路23號',
            trigger_mode='arriving',
            approaching_threshold=10
        )

        truck = create_truck(
            arrival_rank=1,  # 距離進入點 7 個停靠點
            points_config=[
                ('民生路二段80號', 8, '', 65535),
                ('成功路23號', 15, '', 65535),
            ]
        )

        result = matcher.check_line(truck)

        # distance = 7，在閾值範圍內
        assert result.should_trigger is True

    def test_complete_workflow(self, matcher_arriving, create_truck):
        """測試完整工作流程：從接近到經過"""
        # 1. 垃圾車接近進入點
        truck_approaching = create_truck(
            arrival_rank=6,
            points_config=[
                ('民生路二段80號', 8, '', 65535),
                ('成功路23號', 15, '', 65535),
            ]
        )

        result1 = matcher_arriving.check_line(truck_approaching)
        assert result1.should_trigger is True
        assert result1.new_state == 'nearby'

        # 2. 垃圾車經過進入點和離開點之間
        truck_between = create_truck(
            arrival_rank=10,
            points_config=[
                ('民生路二段80號', 8, '14:05', 5),  # 已經過
                ('成功路23號', 15, '', 65535),  # 未經過
            ]
        )

        result2 = matcher_arriving.check_line(truck_between)
        assert result2.should_trigger is False  # 維持 nearby 狀態

        # 3. 垃圾車經過離開點
        truck_passed = create_truck(
            arrival_rank=16,
            points_config=[
                ('民生路二段80號', 8, '14:05', 5),  # 已經過
                ('成功路23號', 15, '14:25', 5),  # 已經過
            ]
        )

        result3 = matcher_arriving.check_line(truck_passed)
        assert result3.should_trigger is True
        assert result3.new_state == 'idle'
