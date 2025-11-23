#!/usr/bin/env python3
"""Garbage Truck Query CLI Tool"""

import argparse
import sys

import _setup_path  # noqa: F401 - Sets up sys.path for trash_tracking_core imports
from trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError
from trash_tracking_core.models.point import Point, PointStatus
from trash_tracking_core.models.truck import TruckLine
from trash_tracking_core.utils.geocoding import Geocoder, GeocodingError
from trash_tracking_core.utils.logger import setup_logger


def format_point_info(point: Point, index: int, truck_diff: int = 0) -> str:
    """
    Presentation Layer: Format collection point information

    Uses Domain logic from Point model for status and time calculations.

    Args:
        point: Collection point data
        index: Index number
        truck_diff: Truck's current delay in minutes

    Returns:
        str: Formatted string
    """
    # Use Domain logic
    point_status = point.get_status()
    estimated = point.get_estimated_arrival(truck_diff)

    # Presentation logic only
    if point_status == PointStatus.PASSED:
        status = f"✅ {point.arrival}"
    elif point_status == PointStatus.ARRIVING:
        status = f"⏰ {point.arrival}"
    else:
        if estimated and truck_diff != 0:
            estimated_str = estimated.strftime("%H:%M")
            delay_desc = point.get_delay_description(truck_diff)
            status = f"⏳ Scheduled {point.point_time} (Est. {estimated_str}, {delay_desc})"
        elif point.point_time:
            status = f"⏳ Scheduled {point.point_time}"
        else:
            status = "⏳ Not arrived"

    return f"  {index:2d}. [{status}] {point.point_name}"


def display_truck_info(truck: TruckLine, next_points: int = 10) -> None:
    """
    Display garbage truck information

    Args:
        truck: Truck route
        next_points: Number of upcoming points to display
    """
    print(f"\n{'='*80}")
    print(f"🚛 Route Name: {truck.line_name}")
    print(f"   Truck No.: {truck.car_no}")
    print(f"   Current Location: {truck.location or 'Unknown'}")
    print(f"   Current Stop: {truck.arrival_rank}/{len(truck.points)}")

    if truck.diff > 0:
        print(f"   ⚠️  Delay Status: {truck.diff} minutes late")
    elif truck.diff < 0:
        print(f"   ✅ Early Status: {abs(truck.diff)} minutes early")
    else:
        print("   ✅ On Time")

    print(f"{'='*80}")

    upcoming_points = truck.get_upcoming_points()

    if not upcoming_points:
        print("\n   ℹ️  All collection points completed")
        return

    points_to_show = upcoming_points[:next_points]

    print(f"\n📍 Next {len(points_to_show)} collection points:")
    for i, point in enumerate(points_to_show, 1):
        print(format_point_info(point, i, truck.diff))

    remaining = len(upcoming_points) - len(points_to_show)
    if remaining > 0:
        print(f"\n   ... {remaining} more collection points")

    print()


def _get_coordinates_from_address(address: str) -> tuple[float, float] | None:
    """Get coordinates from address"""
    geocoder = Geocoder()
    try:
        print(f"\n🔍 正在查詢地址座標: {address}")
        lat, lng = geocoder.address_to_coordinates(address)
        print(f"✅ 座標: ({lat:.6f}, {lng:.6f})")
        return (lat, lng)
    except GeocodingError as e:
        print(f"\n❌ 地址查詢失敗: {e}", file=sys.stderr)
        return None


def _query_and_display_trucks(lat: float, lng: float, args: argparse.Namespace) -> int:
    """Query and display truck information"""
    try:
        client = NTPCApiClient()

        print(f"\n🔍 Query Location: ({lat}, {lng})")
        print(f"📏 Query Radius: {args.radius} meters")

        # Use Monday (week=1) to show routes even during off-hours
        trucks = client.get_around_points(lat, lng, week=1)

        if not trucks:
            print("\n❌ No garbage trucks found in query range")
            return 0

        if args.line:
            trucks = [t for t in trucks if t.line_name == args.line]
            if not trucks:
                print(f"\n❌ Route not found: {args.line}")
                return 1

        print(f"\n✅ Found {len(trucks)} garbage truck(s)")

        for truck in trucks:
            display_truck_info(truck, args.next)

        return 0

    except NTPCApiError as e:
        print(f"\n❌ API Error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Query cancelled")
        return 130

    except Exception as e:
        print(f"\n❌ Error occurred: {e}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


def main() -> int:
    """Main program"""
    parser = argparse.ArgumentParser(
        description="Query New Taipei City garbage truck real-time information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query by address
  %(prog)s --address "新北市板橋區民生路二段80號"

  # Query with custom radius
  %(prog)s --address "新北市板橋區民生路二段80號" --radius 1000

  # Show next 5 collection points
  %(prog)s --address "新北市板橋區民生路二段80號" --next 5

  # Filter by specific route
  %(prog)s --address "新北市板橋區民生路二段80號" --line "A14路線下午"
        """,
    )

    parser.add_argument("--address", type=str, required=True, help='Address to query (e.g., "新北市板橋區民生路二段80號")')

    parser.add_argument("--radius", type=int, default=1000, help="Query radius in meters (default: 1000)")

    parser.add_argument(
        "--next", type=int, default=10, help="Number of upcoming collection points to display (default: 10)"
    )

    parser.add_argument("--line", type=str, help='Filter by specific route name (e.g., "A14路線下午")')

    parser.add_argument("--debug", action="store_true", help="Show debug messages")

    args = parser.parse_args()

    log_level = "DEBUG" if args.debug else "INFO"
    setup_logger(log_level=log_level)

    coordinates = _get_coordinates_from_address(args.address)
    if not coordinates:
        return 1
    lat, lng = coordinates

    return _query_and_display_trucks(lat, lng, args)


if __name__ == "__main__":
    sys.exit(main())
