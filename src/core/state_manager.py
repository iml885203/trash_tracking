"""State Manager"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from src.models.truck import TruckLine
from src.models.point import Point
from src.utils.logger import logger
import pytz


class TruckState(Enum):
    """Truck state"""
    IDLE = "idle"
    NEARBY = "nearby"


class StateManager:
    """State manager"""

    def __init__(self, timezone: str = 'Asia/Taipei'):
        """
        Initialize state manager

        Args:
            timezone: Timezone setting
        """
        self.current_state = TruckState.IDLE
        self.current_truck: Optional[TruckLine] = None
        self.enter_point: Optional[Point] = None
        self.exit_point: Optional[Point] = None
        self.last_update: Optional[datetime] = None
        self.reason = "System initialized"
        self.timezone = pytz.timezone(timezone)

        logger.info(f"StateManager initialized: state={self.current_state.value}")

    def update_state(
        self,
        new_state: str,
        reason: str,
        truck_line: Optional[TruckLine] = None,
        enter_point: Optional[Point] = None,
        exit_point: Optional[Point] = None
    ) -> None:
        """
        Update system state

        Args:
            new_state: New state ('idle' or 'nearby')
            reason: Reason for state change
            truck_line: Truck data (required when state is nearby)
            enter_point: Enter point data
            exit_point: Exit point data
        """
        try:
            new_state_enum = TruckState(new_state)
        except ValueError:
            logger.error(f"Invalid state value: {new_state}")
            return

        state_changed = (self.current_state != new_state_enum)

        if state_changed:
            logger.info(
                f"🔄 State changed: {self.current_state.value} → {new_state_enum.value} "
                f"({reason})"
            )
        else:
            logger.debug(f"State maintained: {self.current_state.value}")

        self.current_state = new_state_enum
        self.reason = reason
        self.current_truck = truck_line
        self.enter_point = enter_point
        self.exit_point = exit_point
        self.last_update = datetime.now(self.timezone)

        if new_state_enum == TruckState.IDLE:
            if state_changed:
                logger.info("Truck has left, clearing tracking data")

    def get_status_response(self) -> Dict[str, Any]:
        """
        Generate API response

        Returns:
            dict: Status response data
        """
        response = {
            'status': self.current_state.value,
            'reason': self.reason,
            'truck': None,
            'timestamp': self.last_update.isoformat() if self.last_update else None
        }

        if self.current_truck and self.current_state == TruckState.NEARBY:
            response['truck'] = self.current_truck.to_dict(
                enter_point=self.enter_point,
                exit_point=self.exit_point
            )

        return response

    def is_idle(self) -> bool:
        """Check if state is idle"""
        return self.current_state == TruckState.IDLE

    def is_nearby(self) -> bool:
        """Check if state is nearby"""
        return self.current_state == TruckState.NEARBY

    def reset(self) -> None:
        """Reset state to idle"""
        logger.info("Resetting state manager")
        self.current_state = TruckState.IDLE
        self.current_truck = None
        self.enter_point = None
        self.exit_point = None
        self.reason = "Manual reset"
        self.last_update = datetime.now(self.timezone)

    def __str__(self) -> str:
        """Return string representation of state"""
        truck_info = ""
        if self.current_truck:
            truck_info = f", truck={self.current_truck.line_name}"

        return f"StateManager(state={self.current_state.value}{truck_info})"
