"""Trash Tracking Core Package - Shared logic for all applications."""

__version__ = "0.1.0"

# Import all public APIs
from .clients import NTPCApiClient, NTPCApiError
from .core import MatchResult, PointMatcher, StateManager, TruckState, TruckTracker
from .models import Point, PointStatus, TruckLine
from .utils import (
    CollectionPointRecommendation,
    ConfigError,
    ConfigManager,
    Geocoder,
    GeocodingError,
    RouteAnalyzer,
    RouteRecommendation,
    logger,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "NTPCApiClient",
    "NTPCApiError",
    # Models
    "Point",
    "PointStatus",
    "TruckLine",
    # Core
    "TruckTracker",
    "StateManager",
    "TruckState",
    "PointMatcher",
    "MatchResult",
    # Utils
    "ConfigManager",
    "ConfigError",
    "logger",
    "Geocoder",
    "GeocodingError",
    "RouteAnalyzer",
    "RouteRecommendation",
    "CollectionPointRecommendation",
]
