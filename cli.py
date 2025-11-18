#!/usr/bin/env python3
"""Garbage Truck Query CLI Tool"""

import argparse
import sys
from typing import Optional, List
from src.clients.ntpc_api import NTPCApiClient, NTPCApiError
from src.models.truck import TruckLine
from src.models.point import Point
from src.utils.logger import setup_logger, logger


def format_point_info(point: Point, index: int, truck_diff: int = 0) -> str:
    """
    Format collection point information

    Args:
        point: Collection point data
        index: Index number
        truck_diff: Truck's current delay in minutes

    Returns:
        str: Formatted string
    """
    if point.has_passed():
        status = f"✅ {point.arrival}"
    elif point.arrival:
        status = f"⏰ {point.arrival}"
    else:
        if point.point_time and truck_diff != 0:
            from datetime import datetime, timedelta
            try:
                scheduled_time = datetime.strptime(point.point_time, "%H:%M")
                estimated_time = scheduled_time + timedelta(minutes=truck_diff)
                estimated_str = estimated_time.strftime("%H:%M")

                if truck_diff > 0:
                    status = f"⏳ Scheduled {point.point_time} (Est. {estimated_str}, {truck_diff}min late)"
                elif truck_diff < 0:
                    status = f"⏳ Scheduled {point.point_time} (Est. {estimated_str}, {abs(truck_diff)}min early)"
                else:
                    status = f"⏳ Scheduled {point.point_time}"
            except ValueError:
                status = f"⏳ Scheduled {point.point_time}"
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
        print(f"   ✅ On Time")

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


def main():
    """Main program"""
    parser = argparse.ArgumentParser(
        description='Query New Taipei City garbage truck real-time information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --lat 25.0199 --lng 121.4705
  %(prog)s --lat 25.0199 --lng 121.4705 --radius 1000
  %(prog)s --lat 25.0199 --lng 121.4705 --next 5
  %(prog)s --lat 25.0199 --lng 121.4705 --line "Area 1 Evening 1"
        """
    )

    parser.add_argument(
        '--lat',
        type=float,
        required=True,
        help='Latitude of query location (e.g., 25.0199)'
    )

    parser.add_argument(
        '--lng',
        type=float,
        required=True,
        help='Longitude of query location (e.g., 121.4705)'
    )

    parser.add_argument(
        '--radius',
        type=int,
        default=1000,
        help='Query radius in meters (default: 1000)'
    )

    parser.add_argument(
        '--next',
        type=int,
        default=10,
        help='Number of upcoming collection points to display (default: 10)'
    )

    parser.add_argument(
        '--line',
        type=str,
        help='Filter by specific route name (e.g., "Area 1 Evening 1")'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show debug messages'
    )

    args = parser.parse_args()

    log_level = "DEBUG" if args.debug else "INFO"
    setup_logger(log_level=log_level)

    try:
        client = NTPCApiClient()

        print(f"\n🔍 Query Location: ({args.lat}, {args.lng})")
        print(f"📏 Query Radius: {args.radius} meters")

        trucks = client.get_around_points(args.lat, args.lng)

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


if __name__ == "__main__":
    sys.exit(main())
