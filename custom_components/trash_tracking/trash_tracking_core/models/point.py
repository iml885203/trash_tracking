"""Collection Point Data Model"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class PointStatus(Enum):
    """Collection point status"""

    PASSED = "passed"
    ARRIVING = "arriving"
    SCHEDULED = "scheduled"


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
    def from_dict(cls, data: dict) -> "Point":
        """
        Create Point object from API response dictionary

        Args:
            data: Collection point data from API

        Returns:
            Point: Collection point object
        """
        return cls(
            source_point_id=data.get("SourcePointID"),
            vil=data.get("Vil", ""),
            point_name=data.get("PointName", ""),
            lon=data.get("Lon", 0.0),
            lat=data.get("Lat", 0.0),
            point_id=data.get("PointID"),
            point_rank=data.get("PointRank", 0),
            point_time=data.get("PointTime", ""),
            arrival=data.get("Arrival", ""),
            arrival_diff=data.get("ArrivalDiff", 65535),
            fixed_point=data.get("FixedPoint", 0),
            point_weekknd=data.get("PointWeekKnd", ""),
            in_scope=data.get("InScope", ""),
            like_count=data.get("LikeCount", 0),
        )

    def to_dict(self) -> dict:
        """
        Convert to dictionary format

        Returns:
            dict: Collection point data dictionary
        """
        return {
            "name": self.point_name,
            "rank": self.point_rank,
            "point_time": self.point_time,
            "arrival": self.arrival,
            "arrival_diff": self.arrival_diff,
            "passed": self.has_passed(),
            "in_scope": self.is_in_scope(),
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

    def get_status(self) -> PointStatus:
        """
        Domain Logic: Determine point status

        Returns:
            PointStatus: Current status of the point
        """
        if self.has_passed():
            return PointStatus.PASSED
        elif self.arrival:
            return PointStatus.ARRIVING
        else:
            return PointStatus.SCHEDULED

    def get_estimated_arrival(self, truck_delay_minutes: int) -> Optional[datetime]:
        """
        Domain Logic: Calculate estimated arrival time

        Args:
            truck_delay_minutes: Current truck delay in minutes

        Returns:
            Optional[datetime]: Estimated arrival time, None if no schedule
        """
        if not self.point_time:
            return None

        try:
            scheduled_time = datetime.strptime(self.point_time, "%H:%M")
            estimated_time = scheduled_time + timedelta(minutes=truck_delay_minutes)
            return estimated_time
        except ValueError:
            return None

    def get_delay_description(self, truck_delay_minutes: int) -> str:
        """
        Domain Logic: Get human-readable delay description

        Args:
            truck_delay_minutes: Current truck delay in minutes

        Returns:
            str: Delay description (e.g., "5min late", "on time", "3min early")
        """
        if truck_delay_minutes > 0:
            return f"{truck_delay_minutes}min late"
        elif truck_delay_minutes < 0:
            return f"{abs(truck_delay_minutes)}min early"
        else:
            return "on time"

    def get_weekdays(self) -> list[int]:
        """
        Parse point_weekknd field to get list of weekdays

        The API uses different formats:
        - Numeric format: "1,3,5" means Monday, Wednesday, Friday
        - Letter codes: "NRF", "NF" means Mon, Tue, Thu, Fri, Sat (no Wed, Sun)
        - "0" or "7" means Sunday
        - "1" = Monday, "2" = Tuesday, ..., "6" = Saturday

        Returns:
            list[int]: List of weekday numbers (0=Sunday, 1=Monday, ..., 6=Saturday)
                      Empty list if parsing fails
        """
        if not self.point_weekknd:
            return []

        # Check for letter code formats first
        weekknd = self.point_weekknd.strip().upper()

        # NTPC uses letter codes for collection schedules
        # Based on actual API testing:
        # "NRF" and "NF" = Monday, Tuesday, Thursday, Friday, Saturday (no Wednesday, Sunday)
        if weekknd in ("NRF", "NF"):
            return [1, 2, 4, 5, 6]  # Mon, Tue, Thu, Fri, Sat

        # Try numeric format
        try:
            weekdays = []
            parts = self.point_weekknd.split(",")

            for part in parts:
                day = int(part.strip())
                # API format: 0 or 7 = Sunday, 1 = Monday, ..., 6 = Saturday
                # Convert to consistent format: 0 = Sunday, 1-6 = Monday-Saturday
                if day == 7:
                    day = 0
                weekdays.append(day)

            return sorted(set(weekdays))  # Remove duplicates and sort

        except (ValueError, AttributeError):
            # If parsing fails, return empty list
            return []

    def __str__(self) -> str:
        """Return string representation of collection point"""
        status = "Arrived" if self.has_passed() else "Not arrived"
        return f"{self.point_name} (rank: {self.point_rank}, {status})"
