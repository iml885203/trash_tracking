"""清運點資料模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Point:
    """清運點資料模型"""

    source_point_id: int
    vil: str
    point_name: str
    lon: float
    lat: float
    point_id: int
    point_rank: int
    point_time: str
    arrival: str
    arrival_diff: int
    fixed_point: int
    point_weekknd: str
    in_scope: str
    like_count: int

    @classmethod
    def from_dict(cls, data: dict) -> 'Point':
        """
        從 API 回傳的字典建立 Point 物件

        Args:
            data: API 回傳的清運點資料

        Returns:
            Point: 清運點物件
        """
        return cls(
            source_point_id=data.get('SourcePointID'),
            vil=data.get('Vil', ''),
            point_name=data.get('PointName', ''),
            lon=data.get('Lon', 0.0),
            lat=data.get('Lat', 0.0),
            point_id=data.get('PointID'),
            point_rank=data.get('PointRank', 0),
            point_time=data.get('PointTime', ''),
            arrival=data.get('Arrival', ''),
            arrival_diff=data.get('ArrivalDiff', 65535),
            fixed_point=data.get('FixedPoint', 0),
            point_weekknd=data.get('PointWeekKnd', ''),
            in_scope=data.get('InScope', ''),
            like_count=data.get('LikeCount', 0)
        )

    def to_dict(self) -> dict:
        """
        轉換為字典格式

        Returns:
            dict: 清運點資料字典
        """
        return {
            'name': self.point_name,
            'rank': self.point_rank,
            'point_time': self.point_time,
            'arrival': self.arrival,
            'arrival_diff': self.arrival_diff,
            'passed': self.has_passed(),
            'in_scope': self.is_in_scope()
        }

    def has_passed(self) -> bool:
        """
        判斷垃圾車是否已經過此點

        Returns:
            bool: True 表示已經過，False 表示未到達
        """
        return self.arrival != "" and self.arrival_diff != 65535

    def is_in_scope(self) -> bool:
        """
        判斷此點是否在查詢範圍內

        Returns:
            bool: True 表示在範圍內
        """
        return self.in_scope == "Y"

    def __str__(self) -> str:
        """返回清運點的字串表示"""
        status = "已到達" if self.has_passed() else "未到達"
        return f"{self.point_name} (順序: {self.point_rank}, {status})"
