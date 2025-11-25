"""Tracking Window Value Object"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..models.point import Point
    from ..models.truck import TruckLine


@dataclass(frozen=True)
class TrackingWindow:
    """
    Represents a tracking window between enter and exit collection points.

    This value object encapsulates the enter/exit point pair that defines
    when a truck should be considered "nearby" vs "idle".
    """

    enter_point_name: str
    exit_point_name: str

    def __post_init__(self):
        if self.enter_point_name == self.exit_point_name:
            raise ValueError("Enter and exit points must be different")

    def find_points(self, truck_line: "TruckLine") -> Optional[tuple["Point", "Point"]]:
        """
        Find both enter and exit points in a truck line.

        Args:
            truck_line: Truck route to search

        Returns:
            tuple: (enter_point, exit_point) if both found, None otherwise

        Raises:
            ValueError: If exit point rank is not greater than enter point rank
        """
        enter_point = truck_line.find_point(self.enter_point_name)
        exit_point = truck_line.find_point(self.exit_point_name)

        if not enter_point or not exit_point:
            return None

        if exit_point.point_rank <= enter_point.point_rank:
            raise ValueError(
                f"Exit point rank {exit_point.point_rank} must be > enter point rank {enter_point.point_rank}"
            )

        return (enter_point, exit_point)

    def __str__(self) -> str:
        """Return string representation"""
        return f"TrackingWindow(enter={self.enter_point_name}, exit={self.exit_point_name})"
