#!/usr/bin/env python3
"""Test config flow locally"""

import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "custom_components" / "trash_tracking"))

from trash_tracking_core.clients.ntpc_api import NTPCApiClient  # noqa: E402
from trash_tracking_core.utils.geocoding import Geocoder  # noqa: E402
from trash_tracking_core.utils.route_analyzer import RouteAnalyzer  # noqa: E402


def test_config_flow():
    """Test the config flow steps"""
    address = "新北市板橋區民生路二段80號"

    print(f"Testing config flow with address: {address}\n")

    # Step 1: Geocode
    print("Step 1: Geocoding address...")
    try:
        geocoder = Geocoder()
        lat, lng = geocoder.address_to_coordinates(address)
        print(f"✓ Geocoded to: {lat}, {lng}\n")
    except Exception as e:
        print(f"✗ Geocoding failed: {e}")
        return False

    # Step 2: Get routes
    print("Step 2: Fetching routes...")
    try:
        api_client = NTPCApiClient()
        routes = api_client.get_around_points(lat, lng, 0, 1)
        print(f"✓ Found {len(routes)} routes\n")

        if routes:
            print("Sample route:")
            route = routes[0]
            print(f"  - Line: {route.line_name}")
            print(f"  - Car: {route.car_no}")
            print(f"  - Points: {len(route.points)}")
            print()
    except Exception as e:
        print(f"✗ API failed: {e}")
        return False

    # Step 3: Analyze routes
    print("Step 3: Analyzing routes...")
    try:
        analyzer = RouteAnalyzer(lat, lng)
        recommendations = analyzer.analyze_all_routes(routes)
        print(f"✓ Generated {len(recommendations)} recommendations\n")

        if recommendations:
            rec = recommendations[0]
            print("Sample recommendation:")
            print(f"  - Route: {rec.truck.line_name}")
            print(f"  - Enter point: {rec.enter_point.point_name}")
            print(f"  - Exit point: {rec.exit_point.point_name}")
            print(f"  - Nearest point: {rec.nearest_point.point_name}")
            print()
    except Exception as e:
        print(f"✗ Route analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("✓ All steps completed successfully!")
    return True


if __name__ == "__main__":
    success = test_config_flow()
    sys.exit(0 if success else 1)
