"""Garbage Truck Data Model"""

from dataclasses import dataclass
from typing import List, Optional
from src.models.point import Point


@dataclass
class TruckLine:
    """Garbage truck route data model"""

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
        Create TruckLine object from API response dictionary

        Args:
            data: Route data from API

        Returns:
            TruckLine: Truck route object
        """
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
        Find collection point by name

        Args:
            point_name: Collection point name

        Returns:
            Point: Found collection point, None if not exists
        """
        for point in self.points:
            if point.point_name == point_name:
                return point
        return None

    def get_current_point(self) -> Optional[Point]:
        """
        Get current collection point where truck is located

        Returns:
            Point: Current collection point, None if not found
        """
        for point in self.points:
            if point.point_rank == self.arrival_rank:
                return point
        return None

    def get_upcoming_points(self) -> List[Point]:
        """
        Get collection points not yet passed (in order)

        Returns:
            List[Point]: List of upcoming collection points
        """
        upcoming = [p for p in self.points if p.point_rank > self.arrival_rank]
        upcoming.sort(key=lambda p: p.point_rank)
        return upcoming

    def to_dict(self, enter_point: Optional[Point] = None,
                exit_point: Optional[Point] = None) -> dict:
        """
        Convert to dictionary format (for API response)

        Args:
            enter_point: Enter point data
            exit_point: Exit point data

        Returns:
            dict: Truck data dictionary
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

        if enter_point:
            result['enter_point'] = enter_point.to_dict()
            result['enter_point']['distance_to_current'] = (
                enter_point.point_rank - self.arrival_rank
            )

        if exit_point:
            result['exit_point'] = exit_point.to_dict()
            result['exit_point']['distance_to_current'] = (
                exit_point.point_rank - self.arrival_rank
            )

        return result

    def __str__(self) -> str:
        """Return string representation of truck"""
        current = self.get_current_point()
        current_name = current.point_name if current else "Unknown"
        return (
            f"{self.line_name} ({self.car_no}) - "
            f"Current location: {current_name} ({self.arrival_rank}/{len(self.points)})"
        )
