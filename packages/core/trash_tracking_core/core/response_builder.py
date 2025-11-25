"""Status Response Builder"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from trash_tracking_core.core.state_manager import StateManager


class StatusResponseBuilder:
    """Builds status response dictionaries from StateManager state"""

    def build(self, state_manager: "StateManager") -> dict[str, Any]:
        """
        Build status response from current state

        Args:
            state_manager: State manager containing current state

        Returns:
            dict: Status response with status, reason, truck, and timestamp
        """
        response = {
            "status": state_manager.current_state.value,
            "reason": state_manager.reason,
            "truck": None,
            "timestamp": state_manager.last_update.isoformat() if state_manager.last_update else None,
        }

        if state_manager.current_truck and state_manager.is_nearby():
            response["truck"] = state_manager.current_truck.to_dict(
                enter_point=state_manager.enter_point, exit_point=state_manager.exit_point
            )

        return response
