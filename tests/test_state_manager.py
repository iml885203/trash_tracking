"""狀態管理器測試"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import pytz

from src.core.state_manager import StateManager, TruckState
from src.models.truck import TruckLine
from src.models.point import Point


class TestStateManager:
    """狀態管理器測試"""

    @pytest.fixture
    def state_manager(self):
        """建立狀態管理器實例"""
        return StateManager(timezone='Asia/Taipei')

    @pytest.fixture
    def sample_truck(self):
        """建立範例垃圾車"""
        return TruckLine(
            line_id='C08',
            line_name='C08路線下午',
            area='板橋區',
            arrival_rank=10,
            diff=-5,
            car_no='KES-6950',
            location='新北市板橋區文化路一段100號',
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code='BC001',
            points=[]
        )

    @pytest.fixture
    def sample_point(self):
        """建立範例清運點"""
        return Point(
            source_point_id=1,
            vil='板橋區',
            point_name='民生路二段80號',
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

    def test_initial_state(self, state_manager):
        """測試初始狀態"""
        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.current_truck is None
        assert state_manager.enter_point is None
        assert state_manager.exit_point is None
        assert state_manager.reason == "系統初始化"

    def test_is_idle(self, state_manager):
        """測試 is_idle 方法"""
        assert state_manager.is_idle() is True
        assert state_manager.is_nearby() is False

    def test_update_state_idle_to_nearby(self, state_manager, sample_truck, sample_point):
        """測試從 idle 轉換到 nearby 狀態"""
        state_manager.update_state(
            new_state='nearby',
            reason='垃圾車即將到達',
            truck_line=sample_truck,
            enter_point=sample_point
        )

        assert state_manager.current_state == TruckState.NEARBY
        assert state_manager.is_nearby() is True
        assert state_manager.is_idle() is False
        assert state_manager.current_truck == sample_truck
        assert state_manager.enter_point == sample_point
        assert state_manager.reason == '垃圾車即將到達'
        assert state_manager.last_update is not None

    def test_update_state_nearby_to_idle(self, state_manager, sample_truck, sample_point):
        """測試從 nearby 轉換到 idle 狀態"""
        # 先設置為 nearby
        state_manager.update_state(
            new_state='nearby',
            reason='垃圾車到達',
            truck_line=sample_truck,
            enter_point=sample_point
        )

        # 再轉換為 idle
        state_manager.update_state(
            new_state='idle',
            reason='垃圾車已離開'
        )

        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.is_idle() is True
        assert state_manager.reason == '垃圾車已離開'
        # 資料不會被清除，只是狀態改變
        assert state_manager.current_truck is None

    def test_update_state_same_state(self, state_manager):
        """測試狀態沒有改變"""
        initial_update_time = state_manager.last_update

        state_manager.update_state(
            new_state='idle',
            reason='維持 idle'
        )

        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.reason == '維持 idle'
        # last_update 應該被更新
        assert state_manager.last_update != initial_update_time

    def test_update_state_invalid_state(self, state_manager):
        """測試無效的狀態值"""
        with patch('src.core.state_manager.logger') as mock_logger:
            state_manager.update_state(
                new_state='invalid_state',
                reason='測試無效狀態'
            )

            # 狀態不應該改變
            assert state_manager.current_state == TruckState.IDLE
            # 應該記錄錯誤
            mock_logger.error.assert_called_once()

    def test_get_status_response_idle(self, state_manager):
        """測試 idle 狀態的回應"""
        state_manager.update_state(
            new_state='idle',
            reason='無垃圾車在附近'
        )

        response = state_manager.get_status_response()

        assert response['status'] == 'idle'
        assert response['reason'] == '無垃圾車在附近'
        assert response['truck'] is None
        assert response['timestamp'] is not None

    def test_get_status_response_nearby(self, state_manager, sample_truck, sample_point):
        """測試 nearby 狀態的回應"""
        exit_point = Point(
            source_point_id=2,
            vil='板橋區',
            point_name='成功路23號',
            lon=121.4710,
            lat=25.0200,
            point_id=1002,
            point_rank=15,
            point_time='14:30',
            arrival='',
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd='Y',
            in_scope='Y',
            like_count=5
        )

        state_manager.update_state(
            new_state='nearby',
            reason='垃圾車即將到達進入清運點',
            truck_line=sample_truck,
            enter_point=sample_point,
            exit_point=exit_point
        )

        response = state_manager.get_status_response()

        assert response['status'] == 'nearby'
        assert response['reason'] == '垃圾車即將到達進入清運點'
        assert response['truck'] is not None
        assert response['truck']['line_name'] == 'C08路線下午'
        assert response['truck']['car_no'] == 'KES-6950'
        assert 'enter_point' in response['truck']
        assert 'exit_point' in response['truck']
        assert response['timestamp'] is not None

    def test_reset(self, state_manager, sample_truck, sample_point):
        """測試重置功能"""
        # 先設置為 nearby
        state_manager.update_state(
            new_state='nearby',
            reason='垃圾車到達',
            truck_line=sample_truck,
            enter_point=sample_point
        )

        # 重置
        state_manager.reset()

        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.current_truck is None
        assert state_manager.enter_point is None
        assert state_manager.exit_point is None
        assert state_manager.reason == '手動重置'
        assert state_manager.last_update is not None

    def test_str_representation(self, state_manager, sample_truck):
        """測試字串表示"""
        # idle 狀態
        str_idle = str(state_manager)
        assert 'idle' in str_idle
        assert 'StateManager' in str_idle

        # nearby 狀態
        state_manager.update_state(
            new_state='nearby',
            reason='測試',
            truck_line=sample_truck
        )
        str_nearby = str(state_manager)
        assert 'nearby' in str_nearby
        assert 'C08路線下午' in str_nearby

    def test_timezone_handling(self):
        """測試時區處理"""
        # 使用不同時區
        sm_taipei = StateManager(timezone='Asia/Taipei')
        sm_utc = StateManager(timezone='UTC')

        sm_taipei.update_state('idle', '測試')
        sm_utc.update_state('idle', '測試')

        # 驗證時區已正確設置
        assert sm_taipei.last_update is not None
        assert sm_utc.last_update is not None
        # 檢查時區名稱而不是直接比較 tzinfo 物件
        assert str(sm_taipei.last_update.tzinfo) == 'Asia/Taipei'
        assert str(sm_utc.last_update.tzinfo) == 'UTC'

    def test_state_transition_with_partial_data(self, state_manager, sample_truck):
        """測試只提供部分資料的狀態轉換"""
        # 只提供 truck，沒有 enter_point 和 exit_point
        state_manager.update_state(
            new_state='nearby',
            reason='測試部分資料',
            truck_line=sample_truck
        )

        assert state_manager.current_state == TruckState.NEARBY
        assert state_manager.current_truck == sample_truck
        assert state_manager.enter_point is None
        assert state_manager.exit_point is None

    def test_multiple_state_changes(self, state_manager, sample_truck, sample_point):
        """測試多次狀態變更"""
        # idle -> nearby
        state_manager.update_state(
            new_state='nearby',
            reason='進入清運點',
            truck_line=sample_truck,
            enter_point=sample_point
        )
        first_update = state_manager.last_update

        # nearby -> idle
        state_manager.update_state(
            new_state='idle',
            reason='離開清運點'
        )
        second_update = state_manager.last_update

        # idle -> nearby (再次)
        state_manager.update_state(
            new_state='nearby',
            reason='再次進入',
            truck_line=sample_truck
        )
        third_update = state_manager.last_update

        # 驗證時間戳記都有更新
        assert first_update < second_update < third_update
        assert state_manager.current_state == TruckState.NEARBY

    def test_concurrent_state_updates(self, state_manager, sample_truck):
        """測試狀態更新的覆蓋行為"""
        # 第一次更新
        state_manager.update_state(
            new_state='nearby',
            reason='第一次更新',
            truck_line=sample_truck
        )

        # 第二次更新（覆蓋）
        new_truck = TruckLine(
            line_id='C15',
            line_name='C15路線下午',
            area='板橋區',
            arrival_rank=5,
            diff=0,
            car_no='KEU-6132',
            location='新北市板橋區莊敬路56號',
            location_lat=25.0180,
            location_lon=121.4700,
            bar_code='BC002',
            points=[]
        )

        state_manager.update_state(
            new_state='nearby',
            reason='第二次更新',
            truck_line=new_truck
        )

        # 應該使用最新的資料
        assert state_manager.current_truck == new_truck
        assert state_manager.reason == '第二次更新'
        assert state_manager.current_truck.line_name == 'C15路線下午'
