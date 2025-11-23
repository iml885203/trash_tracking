"""Core logic for trash tracking"""

from .point_matcher import MatchResult, PointMatcher
from .state_manager import StateManager, TruckState
from .tracker import TruckTracker

__all__ = ["TruckTracker", "StateManager", "TruckState", "PointMatcher", "MatchResult"]
