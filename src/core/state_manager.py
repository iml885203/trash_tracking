"""狀態管理器"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from src.models.truck import TruckLine
from src.models.point import Point
from src.utils.logger import logger
import pytz


class TruckState(Enum):
    """垃圾車狀態"""
    IDLE = "idle"
    NEARBY = "nearby"


class StateManager:
    """狀態管理器"""

    def __init__(self, timezone: str = 'Asia/Taipei'):
        """
        初始化狀態管理器

        Args:
            timezone: 時區設定
        """
        self.current_state = TruckState.IDLE
        self.current_truck: Optional[TruckLine] = None
        self.enter_point: Optional[Point] = None
        self.exit_point: Optional[Point] = None
        self.last_update: Optional[datetime] = None
        self.reason = "系統初始化"
        self.timezone = pytz.timezone(timezone)

        logger.info(f"StateManager 初始化: 狀態={self.current_state.value}")

    def update_state(
        self,
        new_state: str,
        reason: str,
        truck_line: Optional[TruckLine] = None,
        enter_point: Optional[Point] = None,
        exit_point: Optional[Point] = None
    ) -> None:
        """
        更新系統狀態

        Args:
            new_state: 新狀態 ('idle' 或 'nearby')
            reason: 狀態變更原因
            truck_line: 垃圾車資料（當狀態為 nearby 時必填）
            enter_point: 進入清運點資料
            exit_point: 離開清運點資料
        """
        try:
            new_state_enum = TruckState(new_state)
        except ValueError:
            logger.error(f"無效的狀態值: {new_state}")
            return

        # 檢查狀態是否有變更
        state_changed = (self.current_state != new_state_enum)

        if state_changed:
            logger.info(
                f"🔄 狀態變更: {self.current_state.value} → {new_state_enum.value} "
                f"({reason})"
            )
        else:
            logger.debug(f"狀態維持: {self.current_state.value}")

        # 更新狀態
        self.current_state = new_state_enum
        self.reason = reason
        self.current_truck = truck_line
        self.enter_point = enter_point
        self.exit_point = exit_point
        self.last_update = datetime.now(self.timezone)

        # 如果切換為 idle，清除垃圾車資料
        if new_state_enum == TruckState.IDLE:
            if state_changed:
                logger.info("垃圾車已離開，清除追蹤資料")

    def get_status_response(self) -> Dict[str, Any]:
        """
        生成 API 回應

        Returns:
            dict: 狀態回應資料
        """
        response = {
            'status': self.current_state.value,
            'reason': self.reason,
            'truck': None,
            'timestamp': self.last_update.isoformat() if self.last_update else None
        }

        # 如果有垃圾車資料，加入詳細資訊
        if self.current_truck and self.current_state == TruckState.NEARBY:
            response['truck'] = self.current_truck.to_dict(
                enter_point=self.enter_point,
                exit_point=self.exit_point
            )

        return response

    def is_idle(self) -> bool:
        """判斷是否為 idle 狀態"""
        return self.current_state == TruckState.IDLE

    def is_nearby(self) -> bool:
        """判斷是否為 nearby 狀態"""
        return self.current_state == TruckState.NEARBY

    def reset(self) -> None:
        """重置狀態為 idle"""
        logger.info("重置狀態管理器")
        self.current_state = TruckState.IDLE
        self.current_truck = None
        self.enter_point = None
        self.exit_point = None
        self.reason = "手動重置"
        self.last_update = datetime.now(self.timezone)

    def __str__(self) -> str:
        """返回狀態的字串表示"""
        truck_info = ""
        if self.current_truck:
            truck_info = f", 車輛={self.current_truck.line_name}"

        return f"StateManager(狀態={self.current_state.value}{truck_info})"
