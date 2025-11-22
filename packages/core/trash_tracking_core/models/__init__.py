"""Data models for trash tracking"""

from trash_tracking_core.models.point import Point, PointStatus
from trash_tracking_core.models.truck import TruckLine

__all__ = ["Point", "PointStatus", "TruckLine"]
