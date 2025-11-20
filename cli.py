#!/usr/bin/env python3
"""Garbage Truck Query CLI Tool"""

import argparse
import sys
from pathlib import Path

import yaml

from src.clients.ntpc_api import NTPCApiClient, NTPCApiError
from src.models.point import Point
from src.models.truck import TruckLine
from src.utils.geocoding import Geocoder, GeocodingError
from src.utils.logger import setup_logger
from src.utils.route_analyzer import RouteAnalyzer, RouteRecommendation


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


def _get_location_from_user() -> tuple[float, float] | None:
    """Get location coordinates from user (Step 1)"""
    print("📍 步驟 1/4: 設定你的位置")
    print("-" * 80)

    address = input("請輸入你的地址 (例如: 新北市板橋區民生路二段80號): ").strip()
    if not address:
        print("❌ 地址不能空白")
        return None

    geocoder = Geocoder()
    print("\n🔍 正在查詢地址座標...")
    try:
        lat, lng = geocoder.address_to_coordinates(address)
        print(f"✅ 座標: ({lat:.6f}, {lng:.6f})")
        return (lat, lng)
    except GeocodingError as e:
        print(f"❌ 地址查詢失敗: {e}")
        print("提示: 你可以手動輸入座標")
        lat_input = input("緯度 (例如: 25.018269): ").strip()
        lng_input = input("經度 (例如: 121.471703): ").strip()
        try:
            lat = float(lat_input)
            lng = float(lng_input)
            return (lat, lng)
        except ValueError:
            print("❌ 座標格式錯誤")
            return None


def _query_and_display_routes(lat: float, lng: float) -> list[RouteRecommendation] | None:
    """Query and display nearby routes (Step 2)"""
    print("\n🚛 步驟 2/4: 查詢附近的垃圾車路線")
    print("-" * 80)
    print("正在查詢所有時段的路線（早上、下午、晚上）...")

    try:
        client = NTPCApiClient()
        trucks = client.get_around_points(lat, lng, time_filter=0)

        if not trucks:
            print("\n❌ 附近沒有找到垃圾車路線")
            print("可能原因:")
            print("  1. 搜尋範圍內沒有垃圾車路線經過")
            print("  2. 或訪問官網查看完整時刻表: https://crd-rubbish.epd.ntpc.gov.tw/")
            return None

        analyzer = RouteAnalyzer(lat, lng)
        recommendations = analyzer.analyze_all_routes(trucks, span=2)

        if not recommendations:
            print("❌ 無法分析路線")
            return None

        print(f"\n✅ 找到 {len(recommendations)} 條路線:\n")

        for i, rec in enumerate(recommendations, 1):
            distance_m = rec.nearest_point.distance_meters
            if distance_m < 1000:
                distance_str = f"{distance_m:.0f}m"
            else:
                distance_str = f"{distance_m/1000:.1f}km"

            print(f"[{i}] {rec.truck.line_name}")
            print(f"    車號: {rec.truck.car_no}")
            print(f"    時間: {rec.schedule_info}")
            print(f"    收集點總數: {len(rec.truck.points)} 個")
            print(f"    最近收集點: {rec.nearest_point.point_name} (距離 {distance_str})")
            print(f"    推薦進入點: {rec.enter_point.point_name}")
            print(f"    推薦離開點: {rec.exit_point.point_name}")
            print()

        return recommendations

    except NTPCApiError as e:
        print(f"❌ API 錯誤: {e}")
        return None


def _select_route(
    recommendations: list[RouteRecommendation],
) -> tuple[RouteRecommendation, list[RouteRecommendation]] | None:
    """Select route and find same vehicle's other time periods (Step 3)"""
    print("📋 步驟 3/4: 選擇要追蹤的路線")
    print("-" * 80)
    print("💡 提示: 請選擇一條路線。如果同一輛車有早晚兩班，系統會自動追蹤兩個時段。")
    selection = input("請輸入路線編號 (1-{}): ".format(len(recommendations))).strip()

    if not selection:
        print("❌ 未選擇路線")
        return None

    try:
        index = int(selection) - 1
        if not 0 <= index < len(recommendations):
            print("❌ 選擇無效")
            return None
        selected_rec = recommendations[index]
    except ValueError:
        print("❌ 請輸入有效的數字")
        return None

    selected_car = selected_rec.truck.car_no
    selected_recs = [rec for rec in recommendations if rec.truck.car_no == selected_car]

    if len(selected_recs) > 1:
        print(f"\n✅ 已選擇車號 {selected_car}，找到 {len(selected_recs)} 個時段:")
        for rec in selected_recs:
            print(f"   - {rec.truck.line_name} ({rec.schedule_info})")
    else:
        print(f"\n✅ 已選擇: {selected_rec.truck.line_name}")

    return (selected_rec, selected_recs)


def _get_advanced_settings() -> int:
    """Get advanced settings from user (Step 4)"""
    print("\n⚙️  步驟 4/4: 進階設定")
    print("-" * 80)

    threshold_input = input("提前幾站通知？(0-10，按 Enter 使用預設值 2): ").strip()
    if threshold_input:
        try:
            threshold = int(threshold_input)
            if not 0 <= threshold <= 10:
                print("使用預設值: 2")
                threshold = 2
        except ValueError:
            print("使用預設值: 2")
            threshold = 2
    else:
        threshold = 2

    return threshold


def interactive_setup() -> int:
    """Interactive setup mode for generating configuration"""
    print("\n" + "=" * 80)
    print("🚛 垃圾車追蹤系統 - 互動式設定工具")
    print("=" * 80)
    print()

    location = _get_location_from_user()
    if not location:
        return 1
    lat, lng = location

    recommendations = _query_and_display_routes(lat, lng)
    if not recommendations:
        return 1

    route_selection = _select_route(recommendations)
    if not route_selection:
        return 1
    selected_rec, selected_recs = route_selection

    threshold = _get_advanced_settings()
    trigger_mode = "arriving" if threshold > 0 else "arrived"
    selected_car = selected_rec.truck.car_no

    # Generate config
    print("\n📝 生成配置文件...")
    print("-" * 80)

    config = {
        "system": {"log_level": "INFO", "cache_enabled": False, "cache_ttl": 60},
        "location": {"lat": lat, "lng": lng},
        "tracking": {
            "target_lines": [rec.truck.line_name for rec in selected_recs],
            "enter_point": selected_rec.enter_point.point_name,
            "exit_point": selected_rec.exit_point.point_name,
            "trigger_mode": trigger_mode,
            "approaching_threshold": threshold,
        },
        "api": {
            "ntpc": {
                "base_url": "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI",
                "timeout": 10,
                "retry_count": 3,
                "retry_delay": 2,
            },
            "server": {"host": "0.0.0.0", "port": 5000, "debug": False},
        },
    }

    # Save config
    config_path = Path("config.yaml")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"✅ 配置已保存到: {config_path}")
    except Exception as e:
        print(f"❌ 保存配置失敗: {e}")
        print("\n生成的配置:")
        print(yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False))
        return 1

    # Summary
    print("\n" + "=" * 80)
    print("✅ 設定完成！")
    print("=" * 80)
    print(f"\n📍 位置: ({lat:.6f}, {lng:.6f})")
    print(f"🚛 追蹤路線: {', '.join([rec.truck.line_name for rec in selected_recs])}")
    print(f"🚗 車號: {selected_car}")
    print(f"📥 進入點: {selected_rec.enter_point.point_name}")
    print(f"📤 離開點: {selected_rec.exit_point.point_name}")
    print(f"⏰ 提前通知: {threshold} 站")
    print("\n💡 下一步: 執行 'python3 app.py' 啟動服務")
    print()

    return 0


def _get_coordinates_from_args(args: argparse.Namespace) -> tuple[float, float] | None:
    """Get coordinates from command line arguments"""
    lat = args.lat
    lng = args.lng

    if args.address:
        geocoder = Geocoder()
        try:
            print(f"\n🔍 正在查詢地址座標: {args.address}")
            lat, lng = geocoder.address_to_coordinates(args.address)
            print(f"✅ 座標: ({lat:.6f}, {lng:.6f})")
        except GeocodingError as e:
            print(f"\n❌ 地址查詢失敗: {e}", file=sys.stderr)
            return None

    if lat is None or lng is None:
        print("\n❌ 錯誤: 請提供座標 (--lat --lng) 或地址 (--address)", file=sys.stderr)
        print("或使用 --setup 進入互動式設定模式", file=sys.stderr)
        return None

    return (lat, lng)


def _query_and_display_trucks(lat: float, lng: float, args: argparse.Namespace) -> int:
    """Query and display truck information"""
    try:
        client = NTPCApiClient()

        print(f"\n🔍 Query Location: ({lat}, {lng})")
        print(f"📏 Query Radius: {args.radius} meters")

        trucks = client.get_around_points(lat, lng)

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
  # Query by coordinates
  %(prog)s --lat 25.0199 --lng 121.4705

  # Query by address
  %(prog)s --address "新北市板橋區民生路二段80號"

  # Interactive setup mode
  %(prog)s --setup

  # Advanced options
  %(prog)s --lat 25.0199 --lng 121.4705 --radius 1000
  %(prog)s --lat 25.0199 --lng 121.4705 --next 5
  %(prog)s --lat 25.0199 --lng 121.4705 --line "Area 1 Evening 1"
        """,
    )

    parser.add_argument("--lat", type=float, help="Latitude of query location (e.g., 25.0199)")

    parser.add_argument("--lng", type=float, help="Longitude of query location (e.g., 121.4705)")

    parser.add_argument("--address", type=str, help='Address to query (e.g., "新北市板橋區民生路二段80號")')

    parser.add_argument("--setup", action="store_true", help="Interactive setup mode to generate config.yaml")

    parser.add_argument("--radius", type=int, default=1000, help="Query radius in meters (default: 1000)")

    parser.add_argument(
        "--next", type=int, default=10, help="Number of upcoming collection points to display (default: 10)"
    )

    parser.add_argument("--line", type=str, help='Filter by specific route name (e.g., "Area 1 Evening 1")')

    parser.add_argument("--debug", action="store_true", help="Show debug messages")

    args = parser.parse_args()

    log_level = "DEBUG" if args.debug else "INFO"
    setup_logger(log_level=log_level)

    if args.setup:
        return interactive_setup()

    coordinates = _get_coordinates_from_args(args)
    if not coordinates:
        return 1
    lat, lng = coordinates

    return _query_and_display_trucks(lat, lng, args)


if __name__ == "__main__":
    sys.exit(main())
