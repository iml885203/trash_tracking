"""Collection Point Matcher"""

from typing import Optional

from ..models.point import Point
from ..models.truck import TruckLine
from ..utils.logger import logger


class MatchResult:
    """Match result"""

    def __init__(
        self,
        should_trigger: bool,
        new_state: Optional[str] = None,
        reason: str = "",
        truck_line: Optional[TruckLine] = None,
        enter_point: Optional[Point] = None,
        exit_point: Optional[Point] = None,
    ):
        self.should_trigger = should_trigger
        self.new_state = new_state
        self.reason = reason
        self.truck_line = truck_line
        self.enter_point = enter_point
        self.exit_point = exit_point


class PointMatcher:
    """Collection point matcher"""

    def __init__(
        self,
        enter_point_name: str,
        exit_point_name: str,
    ):
        """
        Initialize collection point matcher

        Args:
            enter_point_name: Enter point name
            exit_point_name: Exit point name
        """
        self.enter_point_name = enter_point_name
        self.exit_point_name = exit_point_name

        logger.info(f"PointMatcher initialized: " f"enter_point={enter_point_name}, " f"exit_point={exit_point_name}")

    def check_line(self, truck_line: TruckLine, current_state: str = "idle") -> MatchResult:
        """
        Check if route triggers state change

        Args:
            truck_line: Truck route data
            current_state: Current tracking state (idle or nearby)

        Returns:
            MatchResult: Match result
        """
        enter_point = truck_line.find_point(self.enter_point_name)
        exit_point = truck_line.find_point(self.exit_point_name)

        if not enter_point:
            logger.debug("Enter point not found in route %s: %s", truck_line.line_name, self.enter_point_name)
            return MatchResult(should_trigger=False)

        if not exit_point:
            logger.debug("Exit point not found in route %s: %s", truck_line.line_name, self.exit_point_name)
            return MatchResult(should_trigger=False)

        if exit_point.point_rank <= enter_point.point_rank:
            logger.warning(
                f"Invalid point order in route {truck_line.line_name}: "
                f"exit point ({exit_point.point_name}, rank={exit_point.point_rank}) "
                f"must come after enter point ({enter_point.point_name}, rank={enter_point.point_rank})"
            )
            return MatchResult(should_trigger=False)

        if current_state == "nearby":
            if self._should_trigger_exit(truck_line, exit_point):
                reason = f"Truck has passed exit point: {self.exit_point_name}"
                logger.info(
                    "✅ Trigger exit state: %s - exit point arrival=%s", truck_line.line_name, exit_point.arrival
                )
                return MatchResult(
                    should_trigger=True,
                    new_state="idle",
                    reason=reason,
                    truck_line=truck_line,
                    enter_point=enter_point,
                    exit_point=exit_point,
                )
            return MatchResult(should_trigger=False)

        if self._should_trigger_enter(truck_line, enter_point):
            reason = f"Truck approaching enter point: {self.enter_point_name}"
            logger.info(
                f"✅ Trigger enter state: {truck_line.line_name} - "
                f"current rank={truck_line.arrival_rank}, "
                f"enter point rank={enter_point.point_rank}"
            )
            return MatchResult(
                should_trigger=True,
                new_state="nearby",
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point,
            )

        return MatchResult(should_trigger=False)

    def _should_trigger_enter(self, truck_line: TruckLine, enter_point: Point) -> bool:
        """
        Determine if enter state should be triggered

        Triggers when truck has actually arrived at enter point.

        Args:
            truck_line: Truck route
            enter_point: Enter point

        Returns:
            bool: True if should trigger
        """
        # Trigger only when truck has actually arrived at enter point
        return enter_point.has_passed()

    def _should_trigger_exit(self, truck_line: TruckLine, exit_point: Point) -> bool:
        """
        Determine if exit state should be triggered

        Args:
            truck_line: Truck route
            exit_point: Exit point

        Returns:
            bool: True if should trigger
        """
        # Check if exit point is marked as passed (based on arrival field)
        if exit_point.has_passed():
            logger.debug("Exit point %s marked as passed (arrival=%s)", exit_point.point_name, exit_point.arrival)
            return True

        # Check if truck's current position has passed exit point (rank-based)
        # This handles cases where API data might not have arrival info
        if truck_line.arrival_rank >= exit_point.point_rank:
            logger.debug(
                "Truck current rank (%d) >= exit point rank (%d), triggering exit",
                truck_line.arrival_rank,
                exit_point.point_rank,
            )
            return True

        return False

    def __str__(self) -> str:
        """Return string representation of matcher"""
        return f"PointMatcher(" f"enter={self.enter_point_name}, " f"exit={self.exit_point_name})"
