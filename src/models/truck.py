"""垃圾車資料模型"""

from dataclasses import dataclass
from typing import List, Optional
from src.models.point import Point


@dataclass
class TruckLine:
    """垃圾車路線資料模型"""

    line_id: str
    line_name: str
    area: str
    arrival_rank: int
    diff: int
    car_no: str
    location: str
    location_lat: float
    location_lon: float
    bar_code: str
    points: List[Point]

    @classmethod
    def from_dict(cls, data: dict) -> 'TruckLine':
        """
        從 API 回傳的字典建立 TruckLine 物件

        Args:
            data: API 回傳的路線資料

        Returns:
            TruckLine: 垃圾車路線物件
        """
        # 解析所有清運點
        points_data = data.get('Point', [])
        points = [Point.from_dict(p) for p in points_data]

        return cls(
            line_id=data.get('LineID', ''),
            line_name=data.get('LineName', ''),
            area=data.get('Area', ''),
            arrival_rank=data.get('ArrivalRank', 0),
            diff=data.get('Diff', 0),
            car_no=data.get('CarNO', ''),
            location=data.get('Location', ''),
            location_lat=data.get('LocationLat', 0.0),
            location_lon=data.get('LocationLon', 0.0),
            bar_code=data.get('BarCode', ''),
            points=points
        )

    def find_point(self, point_name: str) -> Optional[Point]:
        """
        根據名稱尋找清運點

        Args:
            point_name: 清運點名稱

        Returns:
            Point: 找到的清運點，若不存在則返回 None
        """
        for point in self.points:
            if point.point_name == point_name:
                return point
        return None

    def get_current_point(self) -> Optional[Point]:
        """
        取得目前垃圾車所在的清運點

        Returns:
            Point: 目前清運點，若找不到則返回 None
        """
        for point in self.points:
            if point.point_rank == self.arrival_rank:
                return point
        return None

    def get_upcoming_points(self) -> List[Point]:
        """
        取得尚未經過的清運點（依序排列）

        Returns:
            List[Point]: 未經過的清運點列表
        """
        # 篩選出尚未經過的清運點
        upcoming = [p for p in self.points if not p.has_passed()]

        # 依照 point_rank 排序
        upcoming.sort(key=lambda p: p.point_rank)

        return upcoming

    def to_dict(self, enter_point: Optional[Point] = None,
                exit_point: Optional[Point] = None) -> dict:
        """
        轉換為字典格式（供 API 回傳）

        Args:
            enter_point: 進入清運點資料
            exit_point: 離開清運點資料

        Returns:
            dict: 垃圾車資料字典
        """
        current_point = self.get_current_point()

        result = {
            'line_name': self.line_name,
            'line_id': self.line_id,
            'car_no': self.car_no,
            'area': self.area,
            'current_location': self.location,
            'current_lat': self.location_lat,
            'current_lon': self.location_lon,
            'current_rank': self.arrival_rank,
            'total_points': len(self.points),
            'arrival_diff': self.diff
        }

        # 加入進入清運點資訊
        if enter_point:
            result['enter_point'] = enter_point.to_dict()
            result['enter_point']['distance_to_current'] = (
                enter_point.point_rank - self.arrival_rank
            )

        # 加入離開清運點資訊
        if exit_point:
            result['exit_point'] = exit_point.to_dict()
            result['exit_point']['distance_to_current'] = (
                exit_point.point_rank - self.arrival_rank
            )

        return result

    def __str__(self) -> str:
        """返回垃圾車的字串表示"""
        current = self.get_current_point()
        current_name = current.point_name if current else "未知"
        return (
            f"{self.line_name} ({self.car_no}) - "
            f"目前位置: {current_name} ({self.arrival_rank}/{len(self.points)})"
        )
