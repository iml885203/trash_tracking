"""Core logic for trash tracking"""

from ..core.point_matcher import MatchResult, PointMatcher
from ..core.state_manager import StateManager, TruckState
from ..core.tracker import TruckTracker

__all__ = ["TruckTracker", "StateManager", "TruckState", "PointMatcher", "MatchResult"]
