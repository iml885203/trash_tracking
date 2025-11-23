"""Step implementations for config flow testing"""

import sys
from pathlib import Path

from behave import given, then, when

# Add trash_tracking_core to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "custom_components" / "trash_tracking"))

from trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError  # noqa: E402
from trash_tracking_core.utils.geocoding import Geocoder, GeocodingError  # noqa: E402
from trash_tracking_core.utils.route_analyzer import RouteAnalyzer  # noqa: E402


@given("the trash_tracking_core modules are available")
def step_modules_available(context):
    """Verify modules can be imported"""
    context.geocoder = Geocoder()
    context.api_client = NTPCApiClient()


@given('I have the address "{address}"')
def step_have_address(context, address):
    """Store address in context"""
    context.address = address


@given("I have coordinates latitude {lat:f} and longitude {lng:f}")
def step_have_coordinates(context, lat, lng):
    """Store coordinates in context"""
    context.latitude = lat
    context.longitude = lng


@when("I geocode the address")
def step_geocode_address(context):
    """Geocode the address"""
    try:
        context.latitude, context.longitude = context.geocoder.address_to_coordinates(context.address)
        context.geocoding_error = None
    except Exception as e:
        context.geocoding_error = e


@when("I attempt to geocode the address")
def step_attempt_geocode(context):
    """Attempt to geocode, expecting failure"""
    try:
        context.latitude, context.longitude = context.geocoder.address_to_coordinates(context.address)
        context.geocoding_error = None
    except GeocodingError as e:
        context.geocoding_error = e


@when("I fetch nearby routes for those coordinates")
def step_fetch_routes(context):
    """Fetch routes from API"""
    try:
        context.routes = context.api_client.get_around_points(
            context.latitude, context.longitude, time_filter=0, week=1
        )
        context.api_error = None
    except NTPCApiError as e:
        context.api_error = e
        context.routes = []


@when("I analyze the routes")
def step_analyze_routes(context):
    """Analyze routes to generate recommendations"""
    analyzer = RouteAnalyzer(context.latitude, context.longitude)
    context.recommendations = analyzer.analyze_all_routes(context.routes)


@when("I complete the full config flow")
def step_complete_flow(context):
    """Complete the entire config flow"""
    # Geocode
    context.latitude, context.longitude = context.geocoder.address_to_coordinates(context.address)

    # Fetch routes
    context.routes = context.api_client.get_around_points(context.latitude, context.longitude, 0, 1)

    # Analyze
    analyzer = RouteAnalyzer(context.latitude, context.longitude)
    context.recommendations = analyzer.analyze_all_routes(context.routes)

    # Select first recommendation
    if context.recommendations:
        context.selected_recommendation = context.recommendations[0]


@then("the coordinates should be near latitude {expected_lat:f} and longitude {expected_lng:f}")
def step_verify_coordinates(context, expected_lat, expected_lng):
    """Verify coordinates are close to expected values"""
    assert abs(context.latitude - expected_lat) < 0.01, f"Latitude {context.latitude} not near {expected_lat}"
    assert abs(context.longitude - expected_lng) < 0.01, f"Longitude {context.longitude} not near {expected_lng}"


@then("I should get at least {min_count:d} route")
def step_verify_min_routes(context, min_count):
    """Verify minimum number of routes"""
    actual = len(context.routes) if context.routes else 0
    assert actual >= min_count, f"Expected at least {min_count} routes, got {actual}"


@then("I should get {expected_count:d} routes")
def step_verify_exact_routes(context, expected_count):
    """Verify exact number of routes"""
    actual = len(context.routes) if context.routes else 0
    assert actual == expected_count, f"Expected {expected_count} routes, got {actual}"


@then("I should get route recommendations")
def step_verify_recommendations(context):
    """Verify we got recommendations"""
    assert context.recommendations, "Expected route recommendations but got none"
    assert len(context.recommendations) > 0, "Expected at least one recommendation"


@then("each recommendation should have a truck")
def step_verify_truck(context):
    """Verify each recommendation has truck"""
    for rec in context.recommendations:
        assert hasattr(rec, "truck"), "Recommendation missing 'truck' attribute"
        assert rec.truck is not None, "Recommendation truck is None"
        assert hasattr(rec.truck, "line_name"), "Truck missing 'line_name' attribute"


@then("each recommendation should have an enter_point")
def step_verify_enter_point(context):
    """Verify each recommendation has enter_point"""
    for rec in context.recommendations:
        assert hasattr(rec, "enter_point"), "Recommendation missing 'enter_point' attribute"
        assert rec.enter_point is not None, "Recommendation enter_point is None"
        assert hasattr(rec.enter_point, "point_name"), "Enter point missing 'point_name' attribute"


@then("each recommendation should have an exit_point")
def step_verify_exit_point(context):
    """Verify each recommendation has exit_point"""
    for rec in context.recommendations:
        assert hasattr(rec, "exit_point"), "Recommendation missing 'exit_point' attribute"
        assert rec.exit_point is not None, "Recommendation exit_point is None"
        assert hasattr(rec.exit_point, "point_name"), "Exit point missing 'point_name' attribute"


@then("each recommendation should have a nearest_point")
def step_verify_nearest_point(context):
    """Verify each recommendation has nearest_point"""
    for rec in context.recommendations:
        assert hasattr(rec, "nearest_point"), "Recommendation missing 'nearest_point' attribute"
        assert rec.nearest_point is not None, "Recommendation nearest_point is None"
        assert hasattr(rec.nearest_point, "point_name"), "Nearest point missing 'point_name' attribute"


@then("geocoding should fail with an error")
def step_verify_geocoding_error(context):
    """Verify geocoding failed"""
    assert context.geocoding_error is not None, "Expected geocoding to fail but it succeeded"
    assert isinstance(context.geocoding_error, GeocodingError), "Expected GeocodingError"


@then("the selected route should have collection points")
def step_verify_collection_points(context):
    """Verify selected route has collection points"""
    assert hasattr(context.selected_recommendation.truck, "points"), "Truck missing 'points' attribute"
    assert len(context.selected_recommendation.truck.points) > 0, "Truck has no collection points"


@then("the enter_point should be in the collection points list")
def step_verify_enter_in_points(context):
    """Verify enter_point exists in collection points"""
    enter_name = context.selected_recommendation.enter_point.point_name
    point_names = [p.point_name for p in context.selected_recommendation.truck.points]
    assert enter_name in point_names, f"Enter point '{enter_name}' not found in collection points"


@then("the exit_point should be in the collection points list")
def step_verify_exit_in_points(context):
    """Verify exit_point exists in collection points"""
    exit_name = context.selected_recommendation.exit_point.point_name
    point_names = [p.point_name for p in context.selected_recommendation.truck.points]
    assert exit_name in point_names, f"Exit point '{exit_name}' not found in collection points"
