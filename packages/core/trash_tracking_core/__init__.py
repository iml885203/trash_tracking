"""Trash Tracking Core Package - Shared logic for all applications."""

__version__ = "0.1.0"

# Import all public APIs
from trash_tracking_core.clients import NTPCApiClient, NTPCApiError
from trash_tracking_core.core import (
    MatchResult,
    PointMatcher,
    StateManager,
    TruckState,
    TruckTracker,
)
from trash_tracking_core.models import Point, PointStatus, TruckLine
from trash_tracking_core.utils import (
    AddressGeocoder,
    CollectionPointRecommendation,
    ConfigError,
    ConfigManager,
    GeocodingError,
    GeocodingProvider,
    RouteAnalyzer,
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
    "AddressGeocoder",
    "GeocodingError",
    "GeocodingProvider",
    "RouteAnalyzer",
    "CollectionPointRecommendation",
]
