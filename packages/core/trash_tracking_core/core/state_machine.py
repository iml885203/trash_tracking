"""Truck State Machine"""

from typing import Optional

from trash_tracking_core.core.state_manager import TruckState
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.tracking_window import TrackingWindow
from trash_tracking_core.models.truck import TruckLine
from trash_tracking_core.utils.logger import logger


class StateTransition:
    """Represents a state transition with associated data"""

    def __init__(
        self,
        new_state: TruckState,
        reason: str,
        truck_line: Optional[TruckLine] = None,
        enter_point: Optional[Point] = None,
        exit_point: Optional[Point] = None,
    ):
        self.new_state = new_state
        self.reason = reason
        self.truck_line = truck_line
        self.enter_point = enter_point
        self.exit_point = exit_point


class TruckStateMachine:
    """
    Encapsulates truck tracking state transition logic.

    Evaluates state transitions based on truck position relative to tracking window.
    """

    def __init__(self, tracking_window: TrackingWindow):
        """
        Initialize state machine with tracking window

        Args:
            tracking_window: Tracking window defining enter and exit points
        """
        self.tracking_window = tracking_window
        logger.info(f"StateMachine initialized: {tracking_window}")

    def evaluate_transition(self, current_state: TruckState, truck_line: TruckLine) -> Optional[StateTransition]:
        """
        Evaluate if a state transition should occur

        Args:
            current_state: Current truck state
            truck_line: Truck line data

        Returns:
            StateTransition if transition should occur, None otherwise
        """
        try:
            points = self.tracking_window.find_points(truck_line)
        except ValueError as e:
            logger.warning("Invalid tracking window for route %s: %s", truck_line.line_name, e)
            return None

        if not points:
            logger.debug(
                "Tracking window points not found in route %s: enter=%s, exit=%s",
                truck_line.line_name,
                self.tracking_window.enter_point_name,
                self.tracking_window.exit_point_name,
            )
            return None

        enter_point, exit_point = points

        if current_state == TruckState.IDLE:
            return self._evaluate_enter_transition(truck_line, enter_point, exit_point)
        elif current_state == TruckState.NEARBY:
            return self._evaluate_exit_transition(truck_line, enter_point, exit_point)

        return None

    def _evaluate_enter_transition(
        self, truck_line: TruckLine, enter_point: Point, exit_point: Point
    ) -> Optional[StateTransition]:
        """
        Evaluate IDLE → NEARBY transition

        Triggers when truck has actually arrived at enter point.

        Args:
            truck_line: Truck line data
            enter_point: Enter point
            exit_point: Exit point

        Returns:
            StateTransition if should transition, None otherwise
        """
        if enter_point.has_passed():
            reason = f"Truck arrived at {enter_point.point_name}"
            logger.info("✅ Trigger enter state: %s - enter point arrival=%s", truck_line.line_name, enter_point.arrival)
            return StateTransition(
                new_state=TruckState.NEARBY,
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point,
            )

        return None

    def _evaluate_exit_transition(
        self, truck_line: TruckLine, enter_point: Point, exit_point: Point
    ) -> Optional[StateTransition]:
        """
        Evaluate NEARBY → IDLE transition

        Triggers when truck has passed exit point (either by arrival mark or rank).

        Args:
            truck_line: Truck line data
            enter_point: Enter point
            exit_point: Exit point

        Returns:
            StateTransition if should transition, None otherwise
        """
        # Check if exit point is marked as passed (based on arrival field)
        if exit_point.has_passed():
            reason = f"Truck passed {exit_point.point_name}"
            logger.info("✅ Trigger exit state: %s - exit point arrival=%s", truck_line.line_name, exit_point.arrival)
            return StateTransition(
                new_state=TruckState.IDLE,
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point,
            )

        # Check if truck's current position has passed exit point (rank-based)
        if truck_line.arrival_rank >= exit_point.point_rank:
            reason = f"Truck passed {exit_point.point_name}"
            logger.debug(
                "Truck current rank (%d) >= exit point rank (%d), triggering exit",
                truck_line.arrival_rank,
                exit_point.point_rank,
            )
            return StateTransition(
                new_state=TruckState.IDLE,
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point,
            )

        return None
