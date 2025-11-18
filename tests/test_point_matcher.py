"""Collection point matcher tests"""

import pytest
from unittest.mock import patch, Mock

from src.core.point_matcher import PointMatcher, MatchResult
from src.models.truck import TruckLine
from src.models.point import Point


class TestMatchResult:
    """Match result tests"""

    def test_match_result_creation(self):
        result = MatchResult(
            should_trigger=True,
            new_state='nearby',
            reason='Test reason'
        )

        assert result.should_trigger is True
        assert result.new_state == 'nearby'
        assert result.reason == 'Test reason'
        assert result.truck_line is None
        assert result.enter_point is None
        assert result.exit_point is None

    def test_match_result_with_full_data(self):
        truck = Mock(spec=TruckLine)
        enter_point = Mock(spec=Point)
        exit_point = Mock(spec=Point)

        result = MatchResult(
            should_trigger=True,
            new_state='idle',
            reason='Complete test',
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
    """Point matcher tests"""

    @pytest.fixture
    def matcher_arriving(self):
        return PointMatcher(
            enter_point_name='Minsheng Rd. Sec. 2, No. 80',
            exit_point_name='Chenggong Rd. No. 23',
            trigger_mode='arriving',
            approaching_threshold=2
        )

    @pytest.fixture
    def matcher_arrived(self):
        return PointMatcher(
            enter_point_name='Minsheng Rd. Sec. 2, No. 80',
            exit_point_name='Chenggong Rd. No. 23',
            trigger_mode='arrived',
            approaching_threshold=2
        )

    @pytest.fixture
    def create_point(self):
        def _create_point(name, rank, arrival='', arrival_diff=65535):
            return Point(
                source_point_id=rank,
                vil='Banqiao District',
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
        def _create_truck(arrival_rank, points_config):
            points = [create_point(*config) for config in points_config]

            return TruckLine(
                line_id='C08',
                line_name='C08 Afternoon Route',
                area='Banqiao District',
                arrival_rank=arrival_rank,
                diff=-5,
                car_no='KES-6950',
                location='New Taipei City Banqiao District',
                location_lat=25.0199,
                location_lon=121.4705,
                bar_code='BC001',
                points=points
            )
        return _create_truck

    def test_initialization(self, matcher_arriving):
        assert matcher_arriving.enter_point_name == 'Minsheng Rd. Sec. 2, No. 80'
        assert matcher_arriving.exit_point_name == 'Chenggong Rd. No. 23'
        assert matcher_arriving.trigger_mode == 'arriving'
        assert matcher_arriving.approaching_threshold == 2

    def test_str_representation(self, matcher_arriving):
        result = str(matcher_arriving)

        assert 'Minsheng Rd. Sec. 2, No. 80' in result
        assert 'Chenggong Rd. No. 23' in result
        assert 'arriving' in result

    def test_check_line_enter_point_not_found(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('Other Point 1', 5, '', 65535),
                ('Chenggong Rd. No. 23', 10, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_check_line_exit_point_not_found(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Other Point 2', 10, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_check_line_invalid_order(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('Chenggong Rd. No. 23', 8, '', 65535),
                ('Minsheng Rd. Sec. 2, No. 80', 10, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_check_line_invalid_order_same_rank(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 10, '', 65535),
                ('Chenggong Rd. No. 23', 10, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_arriving_mode_trigger_at_threshold(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=6,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'nearby'
        assert '即將到達' in result.reason
        assert result.truck_line == truck
        assert result.enter_point.point_name == 'Minsheng Rd. Sec. 2, No. 80'
        assert result.exit_point.point_name == 'Chenggong Rd. No. 23'

    def test_arriving_mode_trigger_within_threshold(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=7,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'nearby'

    def test_arriving_mode_not_trigger_too_far(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=5,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_arriving_mode_not_trigger_already_passed(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=9,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '14:05', 5),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_arrived_mode_trigger_when_arrived(self, matcher_arrived, create_truck):
        truck = create_truck(
            arrival_rank=8,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '14:05', 0),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arrived.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'nearby'
        assert result.enter_point.has_passed() is True

    def test_arrived_mode_not_trigger_before_arrival(self, matcher_arrived, create_truck):
        truck = create_truck(
            arrival_rank=7,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arrived.check_line(truck)

        assert result.should_trigger is False

    def test_trigger_exit_when_passed(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=16,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '14:05', 5),
                ('Chenggong Rd. No. 23', 15, '14:25', 5),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'idle'
        assert '已經過離開清運點' in result.reason
        assert result.exit_point.has_passed() is True

    def test_not_trigger_exit_before_passed(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=10,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '14:05', 5),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is False

    def test_arriving_mode_at_exact_enter_point(self, matcher_arriving, create_truck):
        truck = create_truck(
            arrival_rank=8,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher_arriving.check_line(truck)

        assert result.should_trigger is True
        assert result.new_state == 'nearby'

    def test_threshold_zero(self, create_truck):
        matcher = PointMatcher(
            enter_point_name='Minsheng Rd. Sec. 2, No. 80',
            exit_point_name='Chenggong Rd. No. 23',
            trigger_mode='arriving',
            approaching_threshold=0
        )

        truck = create_truck(
            arrival_rank=8,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher.check_line(truck)

        assert result.should_trigger is True

    def test_large_threshold(self, create_truck):
        matcher = PointMatcher(
            enter_point_name='Minsheng Rd. Sec. 2, No. 80',
            exit_point_name='Chenggong Rd. No. 23',
            trigger_mode='arriving',
            approaching_threshold=10
        )

        truck = create_truck(
            arrival_rank=1,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result = matcher.check_line(truck)

        assert result.should_trigger is True

    def test_complete_workflow(self, matcher_arriving, create_truck):
        truck_approaching = create_truck(
            arrival_rank=6,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '', 65535),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result1 = matcher_arriving.check_line(truck_approaching)
        assert result1.should_trigger is True
        assert result1.new_state == 'nearby'

        truck_between = create_truck(
            arrival_rank=10,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '14:05', 5),
                ('Chenggong Rd. No. 23', 15, '', 65535),
            ]
        )

        result2 = matcher_arriving.check_line(truck_between)
        assert result2.should_trigger is False

        truck_passed = create_truck(
            arrival_rank=16,
            points_config=[
                ('Minsheng Rd. Sec. 2, No. 80', 8, '14:05', 5),
                ('Chenggong Rd. No. 23', 15, '14:25', 5),
            ]
        )

        result3 = matcher_arriving.check_line(truck_passed)
        assert result3.should_trigger is True
        assert result3.new_state == 'idle'
