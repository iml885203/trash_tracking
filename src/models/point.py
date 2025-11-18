"""Collection Point Data Model"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Point:
    """Collection point data model"""

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
        Create Point object from API response dictionary

        Args:
            data: Collection point data from API

        Returns:
            Point: Collection point object
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
        Convert to dictionary format

        Returns:
            dict: Collection point data dictionary
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
        Check if truck has passed this point

        Returns:
            bool: True if passed, False if not arrived
        """
        return self.arrival != "" and self.arrival_diff != 65535

    def is_in_scope(self) -> bool:
        """
        Check if this point is within query range

        Returns:
            bool: True if in range
        """
        return self.in_scope == "Y"

    def __str__(self) -> str:
        """Return string representation of collection point"""
        status = "Arrived" if self.has_passed() else "Not arrived"
        return f"{self.point_name} (rank: {self.point_rank}, {status})"
