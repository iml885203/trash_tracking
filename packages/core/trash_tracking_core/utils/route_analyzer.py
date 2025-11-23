"""Route Analysis Utilities"""

import math
from dataclasses import dataclass
from typing import List, Optional

from trash_tracking_core.models.truck import TruckLine
from trash_tracking_core.utils.logger import logger


@dataclass
class CollectionPointRecommendation:
    """Collection point recommendation"""

    point_name: str
    distance_meters: float
    rank: int  # Position in route
    scheduled_time: Optional[str]


@dataclass
class RouteRecommendation:
    """Route recommendation with suggested collection points"""

    truck: TruckLine
    nearest_point: CollectionPointRecommendation
    enter_point: CollectionPointRecommendation
    exit_point: CollectionPointRecommendation
    schedule_info: str


class RouteAnalyzer:
    """Analyze truck routes and recommend collection points"""

    def __init__(self, lat: float, lng: float):
        """
        Initialize route analyzer

        Args:
            lat: User's latitude
            lng: User's longitude
        """
        self.user_lat = lat
        self.user_lng = lng

    def calculate_distance(self, point_lat: float, point_lng: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula

        Args:
            point_lat: Point latitude
            point_lng: Point longitude

        Returns:
            float: Distance in meters
        """
        earth_radius_m = 6371000  # Earth radius in meters

        lat1 = math.radians(self.user_lat)
        lat2 = math.radians(point_lat)
        dlat = math.radians(point_lat - self.user_lat)
        dlng = math.radians(point_lng - self.user_lng)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return earth_radius_m * c

    def find_nearest_point(self, truck: TruckLine) -> Optional[CollectionPointRecommendation]:
        """
        Find the nearest collection point in a truck route

        Args:
            truck: Truck route

        Returns:
            CollectionPointRecommendation or None
        """
        if not truck.points:
            return None

        nearest = None
        min_distance = float("inf")

        for point in truck.points:
            if point.lat and point.lon:
                distance = self.calculate_distance(point.lat, point.lon)
                if distance < min_distance:
                    min_distance = distance
                    nearest = CollectionPointRecommendation(
                        point_name=point.point_name,
                        distance_meters=distance,
                        rank=point.point_rank,
                        scheduled_time=point.point_time,
                    )

        return nearest

    def recommend_enter_exit_points(
        self, truck: TruckLine, nearest_point: CollectionPointRecommendation, span: int = 2
    ) -> tuple[Optional[CollectionPointRecommendation], Optional[CollectionPointRecommendation]]:
        """
        Recommend enter and exit collection points

        Strategy:
        - enter_point: nearest point (or slightly before)
        - exit_point: a few stops after enter_point

        Args:
            truck: Truck route
            nearest_point: Nearest collection point
            span: Number of stops between enter and exit (default: 2)

        Returns:
            tuple: (enter_point, exit_point)
        """
        if not nearest_point or not truck.points:
            return (None, None)

        # Find nearest point in points list
        nearest_index = None
        for i, point in enumerate(truck.points):
            if point.point_name == nearest_point.point_name and point.point_rank == nearest_point.rank:
                nearest_index = i
                break

        if nearest_index is None:
            return (None, None)

        # enter_point: use nearest point
        enter_point = nearest_point

        # exit_point: span stops after enter_point
        exit_index = min(nearest_index + span, len(truck.points) - 1)
        exit_pt = truck.points[exit_index]

        if exit_pt.lat and exit_pt.lon:
            distance = self.calculate_distance(exit_pt.lat, exit_pt.lon)
            exit_point = CollectionPointRecommendation(
                point_name=exit_pt.point_name,
                distance_meters=distance,
                rank=exit_pt.point_rank,
                scheduled_time=exit_pt.point_time,
            )
        else:
            exit_point = None

        return (enter_point, exit_point)

    def analyze_route(self, truck: TruckLine, span: int = 2) -> Optional[RouteRecommendation]:
        """
        Analyze a truck route and provide recommendations

        Args:
            truck: Truck route to analyze
            span: Number of stops between enter and exit

        Returns:
            RouteRecommendation or None
        """
        nearest = self.find_nearest_point(truck)
        if not nearest:
            return None

        enter, exit_point = self.recommend_enter_exit_points(truck, nearest, span)
        if not enter or not exit_point:
            return None

        # Generate schedule info
        schedule_times = []
        for point in truck.points:
            if point.point_time:
                schedule_times.append(point.point_time)

        if schedule_times:
            schedule_info = f"{min(schedule_times)} - {max(schedule_times)}"
        else:
            schedule_info = "時間未知"

        return RouteRecommendation(
            truck=truck, nearest_point=nearest, enter_point=enter, exit_point=exit_point, schedule_info=schedule_info
        )

    def analyze_all_routes(self, trucks: List[TruckLine], span: int = 2) -> List[RouteRecommendation]:
        """
        Analyze all truck routes and provide recommendations

        Args:
            trucks: List of truck routes
            span: Number of stops between enter and exit

        Returns:
            List of RouteRecommendation sorted by distance
        """
        recommendations = []

        for truck in trucks:
            recommendation = self.analyze_route(truck, span)
            if recommendation:
                recommendations.append(recommendation)

        # Sort by nearest point distance
        recommendations.sort(key=lambda r: r.nearest_point.distance_meters)

        logger.info("分析了 %s 條路線，產生 {len(recommendations)} 個推薦", len(trucks))

        return recommendations
