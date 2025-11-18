"""State manager tests"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import pytz

from src.core.state_manager import StateManager, TruckState
from src.models.truck import TruckLine
from src.models.point import Point


class TestStateManager:
    """State manager tests"""

    @pytest.fixture
    def state_manager(self):
        return StateManager(timezone='Asia/Taipei')

    @pytest.fixture
    def sample_truck(self):
        return TruckLine(
            line_id='C08',
            line_name='C08 Afternoon Route',
            area='Banqiao District',
            arrival_rank=10,
            diff=-5,
            car_no='KES-6950',
            location='New Taipei City Banqiao District Wenhua Rd. Sec. 1, No. 100',
            location_lat=25.0199,
            location_lon=121.4705,
            bar_code='BC001',
            points=[]
        )

    @pytest.fixture
    def sample_point(self):
        return Point(
            source_point_id=1,
            vil='Banqiao District',
            point_name='Minsheng Rd. Sec. 2, No. 80',
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
        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.current_truck is None
        assert state_manager.enter_point is None
        assert state_manager.exit_point is None
        assert state_manager.reason == "系統初始化"

    def test_is_idle(self, state_manager):
        assert state_manager.is_idle() is True
        assert state_manager.is_nearby() is False

    def test_update_state_idle_to_nearby(self, state_manager, sample_truck, sample_point):
        state_manager.update_state(
            new_state='nearby',
            reason='Trash truck approaching',
            truck_line=sample_truck,
            enter_point=sample_point
        )

        assert state_manager.current_state == TruckState.NEARBY
        assert state_manager.is_nearby() is True
        assert state_manager.is_idle() is False
        assert state_manager.current_truck == sample_truck
        assert state_manager.enter_point == sample_point
        assert state_manager.reason == 'Trash truck approaching'
        assert state_manager.last_update is not None

    def test_update_state_nearby_to_idle(self, state_manager, sample_truck, sample_point):
        state_manager.update_state(
            new_state='nearby',
            reason='Trash truck arrived',
            truck_line=sample_truck,
            enter_point=sample_point
        )

        state_manager.update_state(
            new_state='idle',
            reason='Trash truck left'
        )

        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.is_idle() is True
        assert state_manager.reason == 'Trash truck left'
        assert state_manager.current_truck is None

    def test_update_state_same_state(self, state_manager):
        initial_update_time = state_manager.last_update

        state_manager.update_state(
            new_state='idle',
            reason='Maintain idle'
        )

        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.reason == 'Maintain idle'
        assert state_manager.last_update != initial_update_time

    def test_update_state_invalid_state(self, state_manager):
        with patch('src.core.state_manager.logger') as mock_logger:
            state_manager.update_state(
                new_state='invalid_state',
                reason='Test invalid state'
            )

            assert state_manager.current_state == TruckState.IDLE
            mock_logger.error.assert_called_once()

    def test_get_status_response_idle(self, state_manager):
        state_manager.update_state(
            new_state='idle',
            reason='No trash trucks nearby'
        )

        response = state_manager.get_status_response()

        assert response['status'] == 'idle'
        assert response['reason'] == 'No trash trucks nearby'
        assert response['truck'] is None
        assert response['timestamp'] is not None

    def test_get_status_response_nearby(self, state_manager, sample_truck, sample_point):
        exit_point = Point(
            source_point_id=2,
            vil='Banqiao District',
            point_name='Chenggong Rd. No. 23',
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
            reason='Trash truck approaching entry point',
            truck_line=sample_truck,
            enter_point=sample_point,
            exit_point=exit_point
        )

        response = state_manager.get_status_response()

        assert response['status'] == 'nearby'
        assert response['reason'] == 'Trash truck approaching entry point'
        assert response['truck'] is not None
        assert response['truck']['line_name'] == 'C08 Afternoon Route'
        assert response['truck']['car_no'] == 'KES-6950'
        assert 'enter_point' in response['truck']
        assert 'exit_point' in response['truck']
        assert response['timestamp'] is not None

    def test_reset(self, state_manager, sample_truck, sample_point):
        state_manager.update_state(
            new_state='nearby',
            reason='Trash truck arrived',
            truck_line=sample_truck,
            enter_point=sample_point
        )

        state_manager.reset()

        assert state_manager.current_state == TruckState.IDLE
        assert state_manager.current_truck is None
        assert state_manager.enter_point is None
        assert state_manager.exit_point is None
        assert state_manager.reason == '手動重置'
        assert state_manager.last_update is not None

    def test_str_representation(self, state_manager, sample_truck):
        str_idle = str(state_manager)
        assert 'idle' in str_idle
        assert 'StateManager' in str_idle

        state_manager.update_state(
            new_state='nearby',
            reason='Test',
            truck_line=sample_truck
        )
        str_nearby = str(state_manager)
        assert 'nearby' in str_nearby
        assert 'C08 Afternoon Route' in str_nearby

    def test_timezone_handling(self):
        sm_taipei = StateManager(timezone='Asia/Taipei')
        sm_utc = StateManager(timezone='UTC')

        sm_taipei.update_state('idle', 'Test')
        sm_utc.update_state('idle', 'Test')

        assert sm_taipei.last_update is not None
        assert sm_utc.last_update is not None
        assert str(sm_taipei.last_update.tzinfo) == 'Asia/Taipei'
        assert str(sm_utc.last_update.tzinfo) == 'UTC'

    def test_state_transition_with_partial_data(self, state_manager, sample_truck):
        state_manager.update_state(
            new_state='nearby',
            reason='Test partial data',
            truck_line=sample_truck
        )

        assert state_manager.current_state == TruckState.NEARBY
        assert state_manager.current_truck == sample_truck
        assert state_manager.enter_point is None
        assert state_manager.exit_point is None

    def test_multiple_state_changes(self, state_manager, sample_truck, sample_point):
        state_manager.update_state(
            new_state='nearby',
            reason='Enter collection point',
            truck_line=sample_truck,
            enter_point=sample_point
        )
        first_update = state_manager.last_update

        state_manager.update_state(
            new_state='idle',
            reason='Leave collection point'
        )
        second_update = state_manager.last_update

        state_manager.update_state(
            new_state='nearby',
            reason='Enter again',
            truck_line=sample_truck
        )
        third_update = state_manager.last_update

        assert first_update < second_update < third_update
        assert state_manager.current_state == TruckState.NEARBY

    def test_concurrent_state_updates(self, state_manager, sample_truck):
        state_manager.update_state(
            new_state='nearby',
            reason='First update',
            truck_line=sample_truck
        )

        new_truck = TruckLine(
            line_id='C15',
            line_name='C15 Afternoon Route',
            area='Banqiao District',
            arrival_rank=5,
            diff=0,
            car_no='KEU-6132',
            location='New Taipei City Banqiao District Zhuangjing Rd. No. 56',
            location_lat=25.0180,
            location_lon=121.4700,
            bar_code='BC002',
            points=[]
        )

        state_manager.update_state(
            new_state='nearby',
            reason='Second update',
            truck_line=new_truck
        )

        assert state_manager.current_truck == new_truck
        assert state_manager.reason == 'Second update'
        assert state_manager.current_truck.line_name == 'C15 Afternoon Route'
