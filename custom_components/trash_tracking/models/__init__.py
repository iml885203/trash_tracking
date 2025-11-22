"""Data models for Trash Tracking Integration."""

from .point import Point, PointStatus
from .truck import TruckLine

__all__ = ["Point", "PointStatus", "TruckLine"]
