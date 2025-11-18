"""Garbage Truck Tracker"""

from typing import Dict, Any, List
from src.clients.ntpc_api import NTPCApiClient, NTPCApiError
from src.core.state_manager import StateManager
from src.core.point_matcher import PointMatcher
from src.models.truck import TruckLine
from src.utils.config import ConfigManager
from src.utils.logger import logger


class TruckTracker:
    """Garbage truck tracker"""

    def __init__(self, config: ConfigManager):
        """
        Initialize garbage truck tracker

        Args:
            config: Configuration manager
        """
        self.config = config

        self.api_client = NTPCApiClient(
            base_url=config.api_base_url,
            timeout=config.api_timeout,
            retry_count=config.get('api.ntpc.retry_count', 3),
            retry_delay=config.get('api.ntpc.retry_delay', 2)
        )

        self.state_manager = StateManager()

        self.point_matcher = PointMatcher(
            enter_point_name=config.enter_point,
            exit_point_name=config.exit_point,
            trigger_mode=config.trigger_mode,
            approaching_threshold=config.approaching_threshold
        )

        logger.info(f"TruckTracker initialized: {config}")

    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current garbage truck status

        Returns:
            dict: Status information containing status, reason, truck, timestamp
        """
        try:
            location = self.config.location
            truck_lines = self.api_client.get_around_points(
                lat=location['lat'],
                lng=location['lng']
            )

            if not truck_lines:
                logger.info("API returned no truck data")
                if self.state_manager.is_idle():
                    return self.state_manager.get_status_response()
                else:
                    self.state_manager.update_state(
                        new_state='idle',
                        reason='No trucks nearby'
                    )
                    return self.state_manager.get_status_response()

            target_lines = self._filter_target_lines(truck_lines)

            if not target_lines:
                logger.info(
                    f"Found {len(truck_lines)} route(s), but none match tracking criteria"
                )
                if not self.state_manager.is_idle():
                    self.state_manager.update_state(
                        new_state='idle',
                        reason='Tracked routes not nearby'
                    )
                return self.state_manager.get_status_response()

            for line in target_lines:
                match_result = self.point_matcher.check_line(line)

                if match_result.should_trigger:
                    self.state_manager.update_state(
                        new_state=match_result.new_state,
                        reason=match_result.reason,
                        truck_line=match_result.truck_line,
                        enter_point=match_result.enter_point,
                        exit_point=match_result.exit_point
                    )
                    break
            else:
                logger.debug("No route triggered state change, maintaining current state")

            return self.state_manager.get_status_response()

        except NTPCApiError as e:
            logger.error(f"NTPC API request failed: {e}")
            response = self.state_manager.get_status_response()
            response['error'] = str(e)
            return response

        except Exception as e:
            logger.error(f"Unexpected error in tracker: {e}", exc_info=True)
            self.state_manager.reset()
            response = self.state_manager.get_status_response()
            response['error'] = f"System error: {str(e)}"
            return response

    def _filter_target_lines(self, truck_lines: List[TruckLine]) -> List[TruckLine]:
        """
        Filter target routes

        Args:
            truck_lines: All truck routes

        Returns:
            List[TruckLine]: Routes matching tracking criteria
        """
        target_line_names = self.config.target_lines

        if not target_line_names:
            logger.debug(f"No target routes specified, tracking all {len(truck_lines)} route(s)")
            return truck_lines

        filtered = [
            line for line in truck_lines
            if line.line_name in target_line_names
        ]

        logger.debug(
            f"Filtering routes: {len(target_line_names)} specified, "
            f"{len(filtered)} found"
        )

        return filtered

    def reset(self) -> None:
        """Reset tracker state"""
        logger.info("Resetting tracker")
        self.state_manager.reset()

    def __str__(self) -> str:
        """Return string representation of tracker"""
        return f"TruckTracker({self.state_manager})"
