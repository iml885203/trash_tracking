"""垃圾車追蹤器"""

from typing import Dict, Any, List
from src.clients.ntpc_api import NTPCApiClient, NTPCApiError
from src.core.state_manager import StateManager
from src.core.point_matcher import PointMatcher
from src.models.truck import TruckLine
from src.utils.config import ConfigManager
from src.utils.logger import logger


class TruckTracker:
    """垃圾車追蹤器"""

    def __init__(self, config: ConfigManager):
        """
        初始化垃圾車追蹤器

        Args:
            config: 設定管理器
        """
        self.config = config

        # 初始化 API 客戶端
        self.api_client = NTPCApiClient(
            base_url=config.api_base_url,
            timeout=config.api_timeout,
            retry_count=config.get('api.ntpc.retry_count', 3),
            retry_delay=config.get('api.ntpc.retry_delay', 2)
        )

        # 初始化狀態管理器
        self.state_manager = StateManager()

        # 初始化清運點匹配器
        self.point_matcher = PointMatcher(
            enter_point_name=config.enter_point,
            exit_point_name=config.exit_point,
            trigger_mode=config.trigger_mode,
            approaching_threshold=config.approaching_threshold
        )

        logger.info(f"TruckTracker 初始化完成: {config}")

    def get_current_status(self) -> Dict[str, Any]:
        """
        取得當前垃圾車狀態

        Returns:
            dict: 包含 status, reason, truck, timestamp 的狀態資訊
        """
        try:
            # 1. 呼叫新北市 API
            location = self.config.location
            truck_lines = self.api_client.get_around_points(
                lat=location['lat'],
                lng=location['lng']
            )

            if not truck_lines:
                logger.info("API 回傳無垃圾車資料")
                # 如果本來就是 idle，維持狀態
                if self.state_manager.is_idle():
                    return self.state_manager.get_status_response()
                # 如果本來是 nearby，可能垃圾車已經離開範圍
                else:
                    self.state_manager.update_state(
                        new_state='idle',
                        reason='無垃圾車在附近'
                    )
                    return self.state_manager.get_status_response()

            # 2. 過濾目標路線
            target_lines = self._filter_target_lines(truck_lines)

            if not target_lines:
                logger.info(
                    f"找到 {len(truck_lines)} 條路線，但無符合追蹤條件的路線"
                )
                # 維持或切換為 idle
                if not self.state_manager.is_idle():
                    self.state_manager.update_state(
                        new_state='idle',
                        reason='追蹤的路線不在附近'
                    )
                return self.state_manager.get_status_response()

            # 3. 檢查每條目標路線的清運點狀態
            for line in target_lines:
                match_result = self.point_matcher.check_line(line)

                if match_result.should_trigger:
                    # 找到觸發條件，更新狀態
                    self.state_manager.update_state(
                        new_state=match_result.new_state,
                        reason=match_result.reason,
                        truck_line=match_result.truck_line,
                        enter_point=match_result.enter_point,
                        exit_point=match_result.exit_point
                    )
                    # 找到一條符合就跳出
                    break
            else:
                # 沒有任何路線觸發狀態變更
                # 如果目前是 nearby 但沒有觸發離開，維持 nearby
                # 如果目前是 idle 且沒有觸發進入，維持 idle
                logger.debug("無路線觸發狀態變更，維持目前狀態")

            # 4. 回傳目前狀態
            return self.state_manager.get_status_response()

        except NTPCApiError as e:
            logger.error(f"新北市 API 請求失敗: {e}")
            # 回傳錯誤但保持上一次的狀態
            response = self.state_manager.get_status_response()
            response['error'] = str(e)
            return response

        except Exception as e:
            logger.error(f"追蹤器發生未預期的錯誤: {e}", exc_info=True)
            # 發生未預期錯誤，重置為 idle
            self.state_manager.reset()
            response = self.state_manager.get_status_response()
            response['error'] = f"系統錯誤: {str(e)}"
            return response

    def _filter_target_lines(self, truck_lines: List[TruckLine]) -> List[TruckLine]:
        """
        過濾目標路線

        Args:
            truck_lines: 所有垃圾車路線

        Returns:
            List[TruckLine]: 符合追蹤條件的路線
        """
        target_line_names = self.config.target_lines

        # 如果沒有指定路線，則追蹤所有路線
        if not target_line_names:
            logger.debug(f"未指定追蹤路線，追蹤所有 {len(truck_lines)} 條路線")
            return truck_lines

        # 過濾出指定的路線
        filtered = [
            line for line in truck_lines
            if line.line_name in target_line_names
        ]

        logger.debug(
            f"過濾路線: 指定 {len(target_line_names)} 條，"
            f"找到 {len(filtered)} 條符合"
        )

        return filtered

    def reset(self) -> None:
        """重置追蹤器狀態"""
        logger.info("重置追蹤器")
        self.state_manager.reset()

    def __str__(self) -> str:
        """返回追蹤器的字串表示"""
        return f"TruckTracker({self.state_manager})"
