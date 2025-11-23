"""Data models for trash tracking"""

from .models.point import Point, PointStatus
from .models.truck import TruckLine

__all__ = ["Point", "PointStatus", "TruckLine"]
