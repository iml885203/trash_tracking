"""Data Transfer Objects for Use Cases"""

from dataclasses import dataclass
from typing import List

from trash_tracking_core.utils.route_analyzer import RouteRecommendation


@dataclass
class RouteSelection:
    """Selected route with same vehicle variants"""

    best_route: RouteRecommendation
    all_routes: List[RouteRecommendation]

    @property
    def vehicle_number(self) -> str:
        return self.best_route.truck.car_no

    @property
    def route_names(self) -> List[str]:
        return [rec.truck.line_name for rec in self.all_routes]


@dataclass
class ConfigRecommendation:
    """Configuration recommendation result"""

    latitude: float
    longitude: float
    route_selection: RouteSelection
    threshold: int = 2
    trigger_mode: str = "arriving"

    def to_dict(self) -> dict:
        """Convert to configuration dictionary"""
        return {
            "system": {"log_level": "INFO", "cache_enabled": False, "cache_ttl": 60},
            "location": {"lat": self.latitude, "lng": self.longitude},
            "tracking": {
                "target_lines": self.route_selection.route_names,
                "enter_point": self.route_selection.best_route.enter_point.point_name,
                "exit_point": self.route_selection.best_route.exit_point.point_name,
                "trigger_mode": self.trigger_mode,
                "approaching_threshold": self.threshold,
            },
            "api": {
                "ntpc": {
                    "base_url": "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI",
                    "timeout": 10,
                    "retry_count": 3,
                    "retry_delay": 2,
                },
                "server": {"host": "0.0.0.0", "port": 5000, "debug": False},
            },
        }
