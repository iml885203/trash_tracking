"""Auto Suggest Configuration Use Case"""

from typing import List

from trash_tracking_core.clients.ntpc_api import NTPCApiClient
from addon.use_cases.dtos import ConfigRecommendation, RouteSelection
from addon.use_cases.exceptions import NoRoutesFoundError, RouteAnalysisError
from trash_tracking_core.utils.geocoding import Geocoder
from trash_tracking_core.utils.route_analyzer import RouteAnalyzer, RouteRecommendation


class AutoSuggestConfigUseCase:
    """
    Use Case: Automatically suggest configuration based on address

    Business Logic:
    1. Geocode address to coordinates
    2. Query nearby truck routes (all time periods)
    3. Analyze and rank routes by distance
    4. Select the nearest route and its variants (same vehicle)
    5. Generate configuration with sensible defaults

    This is pure business logic with no UI dependencies.
    """

    def __init__(
        self,
        geocoder: Geocoder,
        api_client: NTPCApiClient,
    ):
        self.geocoder = geocoder
        self.api_client = api_client

    def execute(self, address: str) -> ConfigRecommendation:
        """
        Execute the use case

        Args:
            address: User's address

        Returns:
            ConfigRecommendation: Recommended configuration

        Raises:
            GeocodingError: If address cannot be geocoded
            NoRoutesFoundError: If no routes found nearby
            RouteAnalysisError: If route analysis fails
        """
        # Step 1: Geocode address
        lat, lng = self.geocoder.address_to_coordinates(address)

        # Step 2: Query routes (all time periods)
        trucks = self.api_client.get_around_points(lat, lng, time_filter=0)
        if not trucks:
            raise NoRoutesFoundError("No garbage truck routes found near this location")

        # Step 3: Analyze routes
        analyzer = RouteAnalyzer(lat, lng)
        recommendations = analyzer.analyze_all_routes(trucks, span=2)

        if not recommendations:
            raise RouteAnalysisError("Unable to analyze routes")

        # Step 4: Select best route (business rule)
        route_selection = self._select_best_route(recommendations)

        # Step 5: Generate configuration (business rule)
        return self._generate_config(lat, lng, route_selection)

    def _select_best_route(self, recommendations: List[RouteRecommendation]) -> RouteSelection:
        """
        Business Rule: Select the nearest route and include same vehicle variants

        Strategy:
        - Pick the route with the nearest collection point
        - Include all other time periods for the same vehicle

        Args:
            recommendations: Analyzed route recommendations (sorted by distance)

        Returns:
            RouteSelection: Selected route and its variants
        """
        best = recommendations[0]
        vehicle_number = best.truck.car_no

        # Find all routes with same vehicle number
        same_vehicle_routes = [rec for rec in recommendations if rec.truck.car_no == vehicle_number]

        return RouteSelection(best_route=best, all_routes=same_vehicle_routes)

    def _generate_config(
        self, latitude: float, longitude: float, route_selection: RouteSelection
    ) -> ConfigRecommendation:
        """
        Business Rule: Generate configuration with default values

        Default Values:
        - threshold: 2 stops ahead (approaching notification)
        - trigger_mode: "arriving" (notify before arrival)

        Args:
            latitude: Location latitude
            longitude: Location longitude
            route_selection: Selected routes

        Returns:
            ConfigRecommendation: Configuration recommendation
        """
        return ConfigRecommendation(
            latitude=latitude,
            longitude=longitude,
            route_selection=route_selection,
            threshold=2,  # Business rule: default 2 stops ahead
            trigger_mode="arriving",  # Business rule: notify before arrival
        )
