"""Garbage Truck Data Model."""

from dataclasses import dataclass
from typing import Optional

from .point import Point


@dataclass
class TruckLine:
    """Garbage truck route data model."""

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
    points: list[Point]

    @classmethod
    def from_dict(cls, data: dict) -> "TruckLine":
        """Create TruckLine object from API response dictionary."""
        points_data = data.get("Point", [])
        points = [Point.from_dict(p) for p in points_data]

        return cls(
            line_id=data.get("LineID", ""),
            line_name=data.get("LineName", ""),
            area=data.get("Area", ""),
            arrival_rank=data.get("ArrivalRank", 0),
            diff=data.get("Diff", 0),
            car_no=data.get("CarNO", ""),
            location=data.get("Location", ""),
            location_lat=data.get("LocationLat", 0.0),
            location_lon=data.get("LocationLon", 0.0),
            bar_code=data.get("BarCode", ""),
            points=points,
        )

    def find_point(self, point_name: str) -> Optional[Point]:
        """Find collection point by name."""
        for point in self.points:
            if point.point_name == point_name:
                return point
        return None

    def get_current_point(self) -> Optional[Point]:
        """Get current collection point where truck is located."""
        for point in self.points:
            if point.point_rank == self.arrival_rank:
                return point
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary format for HA attributes."""
        return {
            "line_name": self.line_name,
            "car_no": self.car_no,
            "current_rank": self.arrival_rank,
            "total_points": len(self.points),
            "arrival_diff": self.diff,
        }
