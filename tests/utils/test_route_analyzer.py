"""Tests for RouteAnalyzer"""

import math
from unittest.mock import Mock

import pytest
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine
from trash_tracking_core.utils.route_analyzer import (
    CollectionPointRecommendation,
    RouteAnalyzer,
    RouteRecommendation,
)


@pytest.fixture
def sample_points_with_coords():
    """Sample collection points with coordinates"""
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
            lon=121.501,
            lat=25.001,
            point_id=102,
            point_rank=2,
            point_time="18:05",
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
            lon=121.502,
            lat=25.002,
            point_id=103,
            point_rank=3,
            point_time="18:10",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
        Point(
            source_point_id=4,
            vil="Village D",
            point_name="Point 4",
            lon=121.503,
            lat=25.003,
            point_id=104,
            point_rank=4,
            point_time="18:15",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
        Point(
            source_point_id=5,
            vil="Village E",
            point_name="Point 5",
            lon=121.504,
            lat=25.004,
            point_id=105,
            point_rank=5,
            point_time="18:20",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="1,3,5",
            in_scope="Y",
            like_count=0,
        ),
    ]


@pytest.fixture
def sample_points_no_coords():
    """Sample collection points without coordinates"""
    return [
        Point(
            source_point_id=1,
            vil="Village A",
            point_name="Point 1",
            lon=0.0,
            lat=0.0,
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
    ]


@pytest.fixture
def sample_truck(sample_points_with_coords):
    """Sample truck line"""
    return TruckLine(
        line_id="L001",
        line_name="Test Route 1",
        area="Test Area",
        arrival_rank=1,
        diff=0,
        car_no="ABC-1234",
        location="Current Location",
        location_lat=25.0,
        location_lon=121.5,
        bar_code="12345",
        points=sample_points_with_coords,
    )


@pytest.fixture
def sample_trucks(sample_points_with_coords):
    """Multiple sample truck lines"""
    # Create second set of points (farther away)
    far_points = [
        Point(
            source_point_id=6,
            vil="Village F",
            point_name="Far Point 1",
            lon=121.6,
            lat=25.1,
            point_id=201,
            point_rank=1,
            point_time="19:00",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="2,4,6",
            in_scope="Y",
            like_count=0,
        ),
        Point(
            source_point_id=7,
            vil="Village G",
            point_name="Far Point 2",
            lon=121.601,
            lat=25.101,
            point_id=202,
            point_rank=2,
            point_time="19:05",
            arrival="",
            arrival_diff=65535,
            fixed_point=1,
            point_weekknd="2,4,6",
            in_scope="Y",
            like_count=0,
        ),
    ]

    truck1 = TruckLine(
        line_id="L001",
        line_name="Test Route 1",
        area="Test Area 1",
        arrival_rank=1,
        diff=0,
        car_no="ABC-1234",
        location="Location 1",
        location_lat=25.0,
        location_lon=121.5,
        bar_code="12345",
        points=sample_points_with_coords,
    )

    truck2 = TruckLine(
        line_id="L002",
        line_name="Test Route 2",
        area="Test Area 2",
        arrival_rank=1,
        diff=0,
        car_no="XYZ-5678",
        location="Location 2",
        location_lat=25.1,
        location_lon=121.6,
        bar_code="67890",
        points=far_points,
    )

    return [truck1, truck2]


class TestRouteAnalyzerInit:
    """Test RouteAnalyzer initialization"""

    def test_init_with_valid_coordinates(self):
        """Test initialization with valid coordinates"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        assert analyzer.user_lat == 25.0
        assert analyzer.user_lng == 121.5

    def test_init_with_zero_coordinates(self):
        """Test initialization with zero coordinates"""
        analyzer = RouteAnalyzer(lat=0.0, lng=0.0)

        assert analyzer.user_lat == 0.0
        assert analyzer.user_lng == 0.0

    def test_init_with_negative_coordinates(self):
        """Test initialization with negative coordinates"""
        analyzer = RouteAnalyzer(lat=-25.0, lng=-121.5)

        assert analyzer.user_lat == -25.0
        assert analyzer.user_lng == -121.5


class TestCalculateDistance:
    """Test distance calculation"""

    def test_calculate_distance_same_point(self):
        """Test distance calculation for same point"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        distance = analyzer.calculate_distance(25.0, 121.5)

        assert distance == 0.0

    def test_calculate_distance_different_points(self):
        """Test distance calculation for different points"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        # Calculate distance to a point ~111km north (1 degree latitude)
        distance = analyzer.calculate_distance(26.0, 121.5)

        # 1 degree latitude is approximately 111 km
        assert 110000 < distance < 112000

    def test_calculate_distance_haversine_formula(self):
        """Test that Haversine formula is correctly implemented"""
        # Test known distance: Taipei to New Taipei City (approximate)
        analyzer = RouteAnalyzer(lat=25.0479, lng=121.5319)

        # Point about 10km away
        distance = analyzer.calculate_distance(25.0, 121.5)

        # Should be several kilometers
        assert distance > 1000
        assert distance < 10000

    def test_calculate_distance_across_meridian(self):
        """Test distance calculation across meridian"""
        analyzer = RouteAnalyzer(lat=0.0, lng=-179.0)

        distance = analyzer.calculate_distance(0.0, 179.0)

        # Distance should be ~222km (2 degrees at equator)
        assert distance > 200000


class TestFindNearestPoint:
    """Test finding nearest collection point"""

    def test_find_nearest_point_single_point(self):
        """Test finding nearest point with single point"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        truck = Mock(spec=TruckLine)
        truck.points = [
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
            )
        ]

        nearest = analyzer.find_nearest_point(truck)

        assert nearest is not None
        assert nearest.point_name == "Point 1"
        assert nearest.rank == 1
        assert nearest.scheduled_time == "18:00"
        assert nearest.distance_meters == 0.0

    def test_find_nearest_point_multiple_points(self, sample_truck):
        """Test finding nearest point with multiple points"""
        # User location at Point 2 coordinates
        analyzer = RouteAnalyzer(lat=25.001, lng=121.501)

        nearest = analyzer.find_nearest_point(sample_truck)

        assert nearest is not None
        assert nearest.point_name == "Point 2"
        assert nearest.rank == 2
        assert nearest.scheduled_time == "18:05"

    def test_find_nearest_point_empty_points(self):
        """Test finding nearest point with empty points list"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        truck = Mock(spec=TruckLine)
        truck.points = []

        nearest = analyzer.find_nearest_point(truck)

        assert nearest is None

    def test_find_nearest_point_no_coordinates(self, sample_points_no_coords):
        """Test finding nearest point when points have no coordinates"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        truck = Mock(spec=TruckLine)
        truck.points = sample_points_no_coords

        nearest = analyzer.find_nearest_point(truck)

        # When points have 0.0, 0.0 coordinates, they are still processed
        # The method filters points that have lat and lon, but 0.0 is falsy
        # So it returns None when all points have 0.0, 0.0
        assert nearest is None

    def test_find_nearest_point_returns_recommendation(self, sample_truck):
        """Test that find_nearest_point returns CollectionPointRecommendation"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        nearest = analyzer.find_nearest_point(sample_truck)

        assert isinstance(nearest, CollectionPointRecommendation)
        assert hasattr(nearest, "point_name")
        assert hasattr(nearest, "distance_meters")
        assert hasattr(nearest, "rank")
        assert hasattr(nearest, "scheduled_time")


class TestRecommendEnterExitPoints:
    """Test enter/exit point recommendation"""

    def test_recommend_enter_exit_points_default_span(self, sample_truck):
        """Test recommendation with default span"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        nearest = analyzer.find_nearest_point(sample_truck)
        enter, exit_point = analyzer.recommend_enter_exit_points(sample_truck, nearest)

        assert enter is not None
        assert exit_point is not None
        assert enter.point_name == "Point 1"
        assert exit_point.point_name == "Point 3"  # 2 stops after (default span)
        assert exit_point.rank == 3

    def test_recommend_enter_exit_points_custom_span(self, sample_truck):
        """Test recommendation with custom span"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        nearest = analyzer.find_nearest_point(sample_truck)
        enter, exit_point = analyzer.recommend_enter_exit_points(sample_truck, nearest, span=3)

        assert enter is not None
        assert exit_point is not None
        assert enter.point_name == "Point 1"
        assert exit_point.point_name == "Point 4"  # 3 stops after
        assert exit_point.rank == 4

    def test_recommend_enter_exit_points_span_exceeds_route(self, sample_truck):
        """Test recommendation when span exceeds route length"""
        analyzer = RouteAnalyzer(lat=25.004, lng=121.504)

        # Find nearest point (should be Point 5, the last one)
        nearest = analyzer.find_nearest_point(sample_truck)
        enter, exit_point = analyzer.recommend_enter_exit_points(sample_truck, nearest, span=10)

        assert enter is not None
        assert exit_point is not None
        # New logic: enter = nearest - 1 (Point 4, since nearest is Point 5)
        assert enter.point_name == "Point 4"
        assert exit_point.point_name == "Point 5"  # Should clamp to last point
        assert exit_point.rank == 5

    def test_recommend_enter_exit_points_none_nearest(self, sample_truck):
        """Test recommendation with None nearest point"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        enter, exit_point = analyzer.recommend_enter_exit_points(sample_truck, None)

        assert enter is None
        assert exit_point is None

    def test_recommend_enter_exit_points_empty_truck_points(self):
        """Test recommendation with empty truck points"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        truck = Mock(spec=TruckLine)
        truck.points = []

        nearest = CollectionPointRecommendation(
            point_name="Point 1", distance_meters=100.0, rank=1, scheduled_time="18:00"
        )

        enter, exit_point = analyzer.recommend_enter_exit_points(truck, nearest)

        assert enter is None
        assert exit_point is None

    def test_recommend_enter_exit_points_point_not_found(self, sample_truck):
        """Test recommendation when nearest point not found in truck points"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        # Create a recommendation that doesn't match any point
        nearest = CollectionPointRecommendation(
            point_name="Nonexistent Point", distance_meters=100.0, rank=99, scheduled_time="18:00"
        )

        enter, exit_point = analyzer.recommend_enter_exit_points(sample_truck, nearest)

        assert enter is None
        assert exit_point is None

    def test_recommend_enter_exit_points_exit_no_coordinates(self):
        """Test recommendation when exit point has no coordinates"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        # Create points where exit point has no coordinates
        points = [
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
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=2,
                vil="Village B",
                point_name="Point 2 No Coords",
                lon=0.0,  # No coordinates
                lat=0.0,
                point_id=102,
                point_rank=2,
                point_time="18:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
        ]

        truck = Mock(spec=TruckLine)
        truck.points = points

        nearest = analyzer.find_nearest_point(truck)
        enter, exit_point = analyzer.recommend_enter_exit_points(truck, nearest, span=1)

        assert enter is not None
        assert enter.point_name == "Point 1"
        # Exit point should be None because Point 2 has no coordinates
        assert exit_point is None


class TestAnalyzeRoute:
    """Test single route analysis"""

    def test_analyze_route_success(self, sample_truck):
        """Test successful route analysis"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendation = analyzer.analyze_route(sample_truck)

        assert recommendation is not None
        assert isinstance(recommendation, RouteRecommendation)
        assert recommendation.truck == sample_truck
        assert recommendation.nearest_point.point_name == "Point 1"
        assert recommendation.enter_point.point_name == "Point 1"
        assert recommendation.exit_point.point_name == "Point 3"
        assert "18:00" in recommendation.schedule_info
        assert "18:20" in recommendation.schedule_info

    def test_analyze_route_custom_span(self, sample_truck):
        """Test route analysis with custom span"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendation = analyzer.analyze_route(sample_truck, span=1)

        assert recommendation is not None
        assert recommendation.enter_point.point_name == "Point 1"
        assert recommendation.exit_point.point_name == "Point 2"  # Only 1 stop after

    def test_analyze_route_no_points(self):
        """Test route analysis with no points"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        truck = Mock(spec=TruckLine)
        truck.points = []

        recommendation = analyzer.analyze_route(truck)

        assert recommendation is None

    def test_analyze_route_schedule_info_format(self, sample_truck):
        """Test schedule info format in recommendation"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendation = analyzer.analyze_route(sample_truck)

        assert recommendation is not None
        # Schedule should be "18:00 - 18:20"
        assert recommendation.schedule_info == "18:00 - 18:20"

    def test_analyze_route_no_schedule_times(self):
        """Test route analysis when points have no schedule times"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        points = [
            Point(
                source_point_id=1,
                vil="Village A",
                point_name="Point 1",
                lon=121.5,
                lat=25.0,
                point_id=101,
                point_rank=1,
                point_time="",  # No time
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
                lon=121.501,
                lat=25.001,
                point_id=102,
                point_rank=2,
                point_time="",  # No time
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1,3,5",
                in_scope="Y",
                like_count=0,
            ),
        ]

        truck = Mock(spec=TruckLine)
        truck.points = points

        recommendation = analyzer.analyze_route(truck)

        assert recommendation is not None
        assert recommendation.schedule_info == "時間未知"

    def test_analyze_route_exit_point_none(self):
        """Test route analysis when exit point cannot be determined"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        # Create a route where exit point will have no coordinates
        points = [
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
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=2,
                vil="Village B",
                point_name="Point 2 No Coords",
                lon=0.0,  # No coordinates
                lat=0.0,
                point_id=102,
                point_rank=2,
                point_time="18:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
        ]

        truck = TruckLine(
            line_id="L001",
            line_name="Test Route",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="ABC-1234",
            location="Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="123",
            points=points,
        )

        recommendation = analyzer.analyze_route(truck, span=1)

        # Should return None because exit point cannot be determined
        assert recommendation is None


class TestAnalyzeAllRoutes:
    """Test multiple routes analysis"""

    def test_analyze_all_routes_multiple_trucks(self, sample_trucks):
        """Test analyzing multiple truck routes"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendations = analyzer.analyze_all_routes(sample_trucks)

        assert len(recommendations) == 2
        # Should be sorted by distance, closer truck first
        assert recommendations[0].truck.line_name == "Test Route 1"
        assert recommendations[1].truck.line_name == "Test Route 2"

    def test_analyze_all_routes_empty_list(self):
        """Test analyzing empty truck list"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendations = analyzer.analyze_all_routes([])

        assert len(recommendations) == 0

    def test_analyze_all_routes_filters_invalid(self, sample_truck):
        """Test that analyze_all_routes filters out invalid routes"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        # Create a truck with no points
        empty_truck = Mock(spec=TruckLine)
        empty_truck.points = []

        trucks = [sample_truck, empty_truck]

        recommendations = analyzer.analyze_all_routes(trucks)

        # Should only include the valid truck
        assert len(recommendations) == 1
        assert recommendations[0].truck == sample_truck

    def test_analyze_all_routes_sorted_by_distance(self):
        """Test that routes are sorted by distance"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        # Create trucks at different distances
        near_points = [
            Point(
                source_point_id=1,
                vil="Village A",
                point_name="Near Point",
                lon=121.5001,
                lat=25.0001,
                point_id=101,
                point_rank=1,
                point_time="18:00",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=2,
                vil="Village B",
                point_name="Near Point 2",
                lon=121.5002,
                lat=25.0002,
                point_id=102,
                point_rank=2,
                point_time="18:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=3,
                vil="Village C",
                point_name="Near Point 3",
                lon=121.5003,
                lat=25.0003,
                point_id=103,
                point_rank=3,
                point_time="18:10",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
        ]

        far_points = [
            Point(
                source_point_id=4,
                vil="Village D",
                point_name="Far Point",
                lon=121.51,
                lat=25.01,
                point_id=201,
                point_rank=1,
                point_time="19:00",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=5,
                vil="Village E",
                point_name="Far Point 2",
                lon=121.511,
                lat=25.011,
                point_id=202,
                point_rank=2,
                point_time="19:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=6,
                vil="Village F",
                point_name="Far Point 3",
                lon=121.512,
                lat=25.012,
                point_id=203,
                point_rank=3,
                point_time="19:10",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
        ]

        near_truck = TruckLine(
            line_id="L001",
            line_name="Near Route",
            area="Area 1",
            arrival_rank=1,
            diff=0,
            car_no="NEAR-001",
            location="Location 1",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="111",
            points=near_points,
        )

        far_truck = TruckLine(
            line_id="L002",
            line_name="Far Route",
            area="Area 2",
            arrival_rank=1,
            diff=0,
            car_no="FAR-001",
            location="Location 2",
            location_lat=25.01,
            location_lon=121.51,
            bar_code="222",
            points=far_points,
        )

        # Add them in reverse order (far first)
        trucks = [far_truck, near_truck]

        recommendations = analyzer.analyze_all_routes(trucks)

        assert len(recommendations) == 2
        # Should be sorted by distance (near truck first)
        assert recommendations[0].truck.line_name == "Near Route"
        assert recommendations[1].truck.line_name == "Far Route"
        assert recommendations[0].nearest_point.distance_meters < recommendations[1].nearest_point.distance_meters

    def test_analyze_all_routes_custom_span(self, sample_trucks):
        """Test analyzing multiple routes with custom span"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendations = analyzer.analyze_all_routes(sample_trucks, span=1)

        assert len(recommendations) == 2
        # Check that span was applied
        for rec in recommendations:
            # exit_point should be 1 stop after enter_point
            assert rec.exit_point.rank == rec.enter_point.rank + 1


class TestScheduleExtraction:
    """Test schedule extraction logic"""

    def test_schedule_weekdays_extraction(self):
        """Test extracting weekdays from collection points"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        points = [
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
                point_weekknd="1,3,5",  # Mon, Wed, Fri
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=2,
                vil="Village B",
                point_name="Point 2",
                lon=121.501,
                lat=25.001,
                point_id=102,
                point_rank=2,
                point_time="18:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1,3,5",
                in_scope="Y",
                like_count=0,
            ),
        ]

        # Verify points have correct weekdays
        weekdays = points[0].get_weekdays()
        assert weekdays == [1, 3, 5]  # Monday, Wednesday, Friday

    def test_schedule_time_range_extraction(self, sample_truck):
        """Test extracting start and end times from route"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendation = analyzer.analyze_route(sample_truck)

        assert recommendation is not None
        # Schedule info should contain time range
        schedule_parts = recommendation.schedule_info.split(" - ")
        assert len(schedule_parts) == 2
        start_time = schedule_parts[0]
        end_time = schedule_parts[1]

        # Verify times are from the points
        assert start_time == "18:00"  # First point time
        assert end_time == "18:20"  # Last point time

    def test_schedule_with_mixed_weekdays(self):
        """Test schedule extraction with different weekdays per point"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        points = [
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
                point_weekknd="1,3,5",  # Mon, Wed, Fri
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=2,
                vil="Village B",
                point_name="Point 2",
                lon=121.501,
                lat=25.001,
                point_id=102,
                point_rank=2,
                point_time="18:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="2,4,6",  # Tue, Thu, Sat
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=3,
                vil="Village C",
                point_name="Point 3",
                lon=121.502,
                lat=25.002,
                point_id=103,
                point_rank=3,
                point_time="18:10",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="2,4,6",
                in_scope="Y",
                like_count=0,
            ),
        ]

        truck = TruckLine(
            line_id="L001",
            line_name="Mixed Schedule Route",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="MIX-001",
            location="Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="123",
            points=points,
        )

        recommendation = analyzer.analyze_route(truck)

        assert recommendation is not None
        # Each point can have different weekdays
        assert points[0].get_weekdays() == [1, 3, 5]
        assert points[1].get_weekdays() == [2, 4, 6]

    def test_schedule_with_sunday(self):
        """Test schedule extraction with Sunday (0 or 7)"""
        points = [
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
                point_weekknd="0",  # Sunday
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=2,
                vil="Village B",
                point_name="Point 2",
                lon=121.501,
                lat=25.001,
                point_id=102,
                point_rank=2,
                point_time="18:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="7",  # Sunday (alternative format)
                in_scope="Y",
                like_count=0,
            ),
        ]

        # Both should normalize to 0
        assert points[0].get_weekdays() == [0]
        assert points[1].get_weekdays() == [0]


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_routes_list(self):
        """Test with empty routes list"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        recommendations = analyzer.analyze_all_routes([])

        assert recommendations == []

    def test_routes_with_no_valid_points(self):
        """Test routes where no points have coordinates"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        truck = Mock(spec=TruckLine)
        truck.points = []

        recommendations = analyzer.analyze_all_routes([truck])

        assert len(recommendations) == 0

    def test_single_point_route(self):
        """Test route with only one collection point"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        points = [
            Point(
                source_point_id=1,
                vil="Village A",
                point_name="Single Point",
                lon=121.5,
                lat=25.0,
                point_id=101,
                point_rank=1,
                point_time="18:00",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            )
        ]

        truck = TruckLine(
            line_id="L001",
            line_name="Single Point Route",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="SGL-001",
            location="Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="123",
            points=points,
        )

        recommendation = analyzer.analyze_route(truck)

        # Should still work, enter and exit will be same point
        assert recommendation is not None
        assert recommendation.enter_point.point_name == "Single Point"
        assert recommendation.exit_point.point_name == "Single Point"

    def test_two_point_route_span_larger_than_route(self):
        """Test route with two points and span larger than route"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        points = [
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
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
            Point(
                source_point_id=2,
                vil="Village B",
                point_name="Point 2",
                lon=121.501,
                lat=25.001,
                point_id=102,
                point_rank=2,
                point_time="18:05",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1",
                in_scope="Y",
                like_count=0,
            ),
        ]

        truck = TruckLine(
            line_id="L001",
            line_name="Two Point Route",
            area="Test Area",
            arrival_rank=1,
            diff=0,
            car_no="TWO-001",
            location="Location",
            location_lat=25.0,
            location_lon=121.5,
            bar_code="123",
            points=points,
        )

        recommendation = analyzer.analyze_route(truck, span=10)

        assert recommendation is not None
        assert recommendation.enter_point.point_name == "Point 1"
        assert recommendation.exit_point.point_name == "Point 2"  # Clamped to last point

    def test_extreme_coordinates(self):
        """Test with extreme coordinate values"""
        # Test at poles
        analyzer = RouteAnalyzer(lat=90.0, lng=0.0)

        distance = analyzer.calculate_distance(89.0, 0.0)

        # 1 degree latitude is ~111km
        assert distance > 100000

    def test_calculate_distance_precision(self):
        """Test distance calculation precision"""
        analyzer = RouteAnalyzer(lat=25.0, lng=121.5)

        # Very small distance
        distance = analyzer.calculate_distance(25.0001, 121.5001)

        # Should be around 15 meters
        assert distance > 10
        assert distance < 20


class TestCollectionPointRecommendation:
    """Test CollectionPointRecommendation dataclass"""

    def test_create_recommendation(self):
        """Test creating a recommendation"""
        rec = CollectionPointRecommendation(
            point_name="Test Point", distance_meters=100.5, rank=5, scheduled_time="18:30"
        )

        assert rec.point_name == "Test Point"
        assert rec.distance_meters == 100.5
        assert rec.rank == 5
        assert rec.scheduled_time == "18:30"

    def test_recommendation_with_none_time(self):
        """Test recommendation with no scheduled time"""
        rec = CollectionPointRecommendation(point_name="Test Point", distance_meters=100.5, rank=5, scheduled_time=None)

        assert rec.scheduled_time is None


class TestRouteRecommendation:
    """Test RouteRecommendation dataclass"""

    def test_create_route_recommendation(self, sample_truck):
        """Test creating a route recommendation"""
        nearest = CollectionPointRecommendation(
            point_name="Point 1", distance_meters=100.0, rank=1, scheduled_time="18:00"
        )
        enter = CollectionPointRecommendation(
            point_name="Point 1", distance_meters=100.0, rank=1, scheduled_time="18:00"
        )
        exit_point = CollectionPointRecommendation(
            point_name="Point 3", distance_meters=300.0, rank=3, scheduled_time="18:10"
        )

        rec = RouteRecommendation(
            truck=sample_truck,
            nearest_point=nearest,
            enter_point=enter,
            exit_point=exit_point,
            schedule_info="18:00 - 18:20",
        )

        assert rec.truck == sample_truck
        assert rec.nearest_point == nearest
        assert rec.enter_point == enter
        assert rec.exit_point == exit_point
        assert rec.schedule_info == "18:00 - 18:20"
