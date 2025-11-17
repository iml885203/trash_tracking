#!/usr/bin/env python3
"""垃圾車查詢 CLI 工具"""

import argparse
import sys
from typing import Optional, List
from src.clients.ntpc_api import NTPCApiClient, NTPCApiError
from src.models.truck import TruckLine
from src.models.point import Point
from src.utils.logger import setup_logger, logger


def format_point_info(point: Point, index: int) -> str:
    """
    格式化清運點資訊

    Args:
        point: 清運點資料
        index: 索引編號

    Returns:
        str: 格式化的字串
    """
    # 狀態標示
    if point.has_passed():
        status = "✅ 已過"
    elif point.arrival:
        status = f"⏰ {point.arrival}"
    else:
        status = "⏳ 未到"

    return f"  {index:2d}. [{status}] {point.point_name}"


def display_truck_info(truck: TruckLine, next_points: int = 10) -> None:
    """
    顯示垃圾車資訊

    Args:
        truck: 垃圾車路線
        next_points: 顯示接下來的地點數量
    """
    print(f"\n{'='*80}")
    print(f"🚛 路線名稱: {truck.line_name}")
    print(f"   車號: {truck.car_no}")
    print(f"   目前位置: {truck.location or '未知'}")
    print(f"   目前停靠點序號: {truck.arrival_rank}/{len(truck.points)}")
    print(f"{'='*80}")

    # 取得未經過的清運點
    upcoming_points = truck.get_upcoming_points()

    if not upcoming_points:
        print("\n   ℹ️  所有清運點都已完成")
        return

    # 限制顯示數量
    points_to_show = upcoming_points[:next_points]

    print(f"\n📍 接下來 {len(points_to_show)} 個清運點:")
    for i, point in enumerate(points_to_show, 1):
        print(format_point_info(point, i))

    # 如果還有更多點
    remaining = len(upcoming_points) - len(points_to_show)
    if remaining > 0:
        print(f"\n   ... 還有 {remaining} 個清運點")

    print()


def main():
    """主程式"""
    # 解析命令列參數
    parser = argparse.ArgumentParser(
        description='查詢新北市垃圾車即時資訊',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s --lat 25.0199 --lng 121.4705
  %(prog)s --lat 25.0199 --lng 121.4705 --radius 1000
  %(prog)s --lat 25.0199 --lng 121.4705 --next 5
  %(prog)s --lat 25.0199 --lng 121.4705 --line "一區晚1"
        """
    )

    parser.add_argument(
        '--lat',
        type=float,
        required=True,
        help='查詢位置的緯度 (例如: 25.0199)'
    )

    parser.add_argument(
        '--lng',
        type=float,
        required=True,
        help='查詢位置的經度 (例如: 121.4705)'
    )

    parser.add_argument(
        '--radius',
        type=int,
        default=1000,
        help='查詢半徑(公尺)，預設 1000'
    )

    parser.add_argument(
        '--next',
        type=int,
        default=10,
        help='顯示接下來的清運點數量，預設 10'
    )

    parser.add_argument(
        '--line',
        type=str,
        help='過濾特定路線名稱 (例如: "一區晚1")'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='顯示除錯訊息'
    )

    args = parser.parse_args()

    # 設定 logger
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logger(log_level=log_level)

    try:
        # 建立 API 客戶端
        client = NTPCApiClient()

        print(f"\n🔍 查詢位置: ({args.lat}, {args.lng})")
        print(f"📏 查詢半徑: {args.radius} 公尺")

        # 查詢垃圾車
        trucks = client.get_around_points(args.lat, args.lng)

        if not trucks:
            print("\n❌ 查詢範圍內沒有垃圾車")
            return 0

        # 過濾路線（如果有指定）
        if args.line:
            trucks = [t for t in trucks if t.line_name == args.line]
            if not trucks:
                print(f"\n❌ 找不到路線: {args.line}")
                return 1

        # 顯示找到的垃圾車數量
        print(f"\n✅ 找到 {len(trucks)} 台垃圾車")

        # 顯示每台垃圾車的資訊
        for truck in trucks:
            display_truck_info(truck, args.next)

        return 0

    except NTPCApiError as e:
        print(f"\n❌ API 錯誤: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  已取消查詢")
        return 130

    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
