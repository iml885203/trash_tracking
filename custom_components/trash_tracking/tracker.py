"""Garbage Truck Tracker Logic."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .models.point import Point
from .models.truck import TruckLine

_LOGGER = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Match result from point matcher."""

    should_trigger: bool
    new_state: Optional[str] = None
    reason: str = ""
    truck_line: Optional[TruckLine] = None
    enter_point: Optional[Point] = None
    exit_point: Optional[Point] = None


class PointMatcher:
    """Collection point matcher."""

    def __init__(
        self,
        enter_point_name: str,
        exit_point_name: str,
        trigger_mode: str = "arriving",
        approaching_threshold: int = 2,
    ):
        """Initialize collection point matcher."""
        self.enter_point_name = enter_point_name
        self.exit_point_name = exit_point_name
        self.trigger_mode = trigger_mode
        self.approaching_threshold = approaching_threshold

    def check_line(self, truck_line: TruckLine) -> MatchResult:
        """Check if route triggers state change."""
        enter_point = truck_line.find_point(self.enter_point_name)
        exit_point = truck_line.find_point(self.exit_point_name)

        if not enter_point:
            return MatchResult(should_trigger=False)

        if not exit_point:
            return MatchResult(should_trigger=False)

        if exit_point.point_rank <= enter_point.point_rank:
            _LOGGER.warning(
                f"Invalid point order: exit point rank ({exit_point.point_rank}) "
                f"<= enter point rank ({enter_point.point_rank})"
            )
            return MatchResult(should_trigger=False)

        # Check if should trigger enter state
        if self._should_trigger_enter(truck_line, enter_point):
            reason = f"Truck approaching enter point: {self.enter_point_name}"
            return MatchResult(
                should_trigger=True,
                new_state="nearby",
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point,
            )

        # Check if should trigger exit state
        if self._should_trigger_exit(truck_line, exit_point):
            reason = f"Truck passed exit point: {self.exit_point_name}"
            return MatchResult(
                should_trigger=True,
                new_state="idle",
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point,
            )

        return MatchResult(should_trigger=False)

    def _should_trigger_enter(self, truck_line: TruckLine, enter_point: Point) -> bool:
        """Check if should trigger enter state."""
        current_rank = truck_line.arrival_rank
        enter_rank = enter_point.point_rank

        if self.trigger_mode == "arriving":
            # Trigger when N stops ahead
            stops_until_enter = enter_rank - current_rank
            return 0 < stops_until_enter <= self.approaching_threshold
        else:  # arrived mode
            # Trigger when truck arrives at enter point
            return current_rank == enter_rank

    def _should_trigger_exit(self, truck_line: TruckLine, exit_point: Point) -> bool:
        """Check if should trigger exit state."""
        current_rank = truck_line.arrival_rank
        exit_rank = exit_point.point_rank

        # Trigger when truck has passed exit point
        return current_rank > exit_rank


class StateManager:
    """Manage tracker state."""

    def __init__(self):
        """Initialize state manager."""
        self.current_state = "idle"
        self.reason = "Initialized"
        self.truck_info: Optional[dict[str, Any]] = None
        self.timestamp = datetime.now().isoformat()

    def is_idle(self) -> bool:
        """Check if current state is idle."""
        return self.current_state == "idle"

    def update_state(
        self,
        new_state: str,
        reason: str,
        truck_line: Optional[TruckLine] = None,
        enter_point: Optional[Point] = None,
        exit_point: Optional[Point] = None,
    ):
        """Update tracker state."""
        self.current_state = new_state
        self.reason = reason
        self.timestamp = datetime.now().isoformat()

        if truck_line and enter_point and exit_point:
            self.truck_info = {
                **truck_line.to_dict(),
                "enter_point": enter_point.to_dict(),
                "exit_point": exit_point.to_dict(),
            }
        else:
            self.truck_info = None

        _LOGGER.info(f"State updated: {new_state} - {reason}")

    def get_status_response(self) -> dict[str, Any]:
        """Get current status as dictionary."""
        return {
            "status": self.current_state,
            "reason": self.reason,
            "truck": self.truck_info,
            "timestamp": self.timestamp,
        }

    def reset(self):
        """Reset state to idle."""
        self.current_state = "idle"
        self.reason = "Reset"
        self.truck_info = None
        self.timestamp = datetime.now().isoformat()
