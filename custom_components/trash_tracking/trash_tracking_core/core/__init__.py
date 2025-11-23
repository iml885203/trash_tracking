"""Core logic for trash tracking"""

from trash_tracking_core.core.point_matcher import MatchResult, PointMatcher
from trash_tracking_core.core.state_manager import StateManager, TruckState
from trash_tracking_core.core.tracker import TruckTracker

__all__ = ["TruckTracker", "StateManager", "TruckState", "PointMatcher", "MatchResult"]
