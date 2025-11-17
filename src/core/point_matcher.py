"""清運點匹配器"""

from typing import Optional, Dict, Any
from src.models.truck import TruckLine
from src.models.point import Point
from src.utils.logger import logger


class MatchResult:
    """匹配結果"""

    def __init__(
        self,
        should_trigger: bool,
        new_state: Optional[str] = None,
        reason: str = "",
        truck_line: Optional[TruckLine] = None,
        enter_point: Optional[Point] = None,
        exit_point: Optional[Point] = None
    ):
        self.should_trigger = should_trigger
        self.new_state = new_state
        self.reason = reason
        self.truck_line = truck_line
        self.enter_point = enter_point
        self.exit_point = exit_point


class PointMatcher:
    """清運點匹配器"""

    def __init__(
        self,
        enter_point_name: str,
        exit_point_name: str,
        trigger_mode: str = 'arriving',
        approaching_threshold: int = 2
    ):
        """
        初始化清運點匹配器

        Args:
            enter_point_name: 進入清運點名稱
            exit_point_name: 離開清運點名稱
            trigger_mode: 觸發模式 ('arriving' 或 'arrived')
            approaching_threshold: 提前通知停靠點數
        """
        self.enter_point_name = enter_point_name
        self.exit_point_name = exit_point_name
        self.trigger_mode = trigger_mode
        self.approaching_threshold = approaching_threshold

        logger.info(
            f"PointMatcher 初始化: "
            f"進入點={enter_point_name}, "
            f"離開點={exit_point_name}, "
            f"模式={trigger_mode}, "
            f"提前={approaching_threshold}個停靠點"
        )

    def check_line(self, truck_line: TruckLine) -> MatchResult:
        """
        檢查路線是否觸發狀態變更

        Args:
            truck_line: 垃圾車路線資料

        Returns:
            MatchResult: 匹配結果
        """
        # 找到進入點和離開點
        enter_point = truck_line.find_point(self.enter_point_name)
        exit_point = truck_line.find_point(self.exit_point_name)

        # 如果找不到清運點，記錄警告並返回
        if not enter_point:
            logger.debug(
                f"路線 {truck_line.line_name} 中找不到進入清運點: "
                f"{self.enter_point_name}"
            )
            return MatchResult(should_trigger=False)

        if not exit_point:
            logger.debug(
                f"路線 {truck_line.line_name} 中找不到離開清運點: "
                f"{self.exit_point_name}"
            )
            return MatchResult(should_trigger=False)

        # 驗證順序（離開點必須在進入點之後）
        if exit_point.point_rank <= enter_point.point_rank:
            logger.warning(
                f"路線 {truck_line.line_name} 的清運點順序錯誤: "
                f"離開點 ({exit_point.point_name}, rank={exit_point.point_rank}) "
                f"必須在進入點 ({enter_point.point_name}, rank={enter_point.point_rank}) 之後"
            )
            return MatchResult(should_trigger=False)

        # 檢查是否應該觸發「進入」狀態
        if self._should_trigger_enter(truck_line, enter_point):
            reason = f"垃圾車即將到達進入清運點: {self.enter_point_name}"
            logger.info(
                f"✅ 觸發進入狀態: {truck_line.line_name} - "
                f"目前位置 rank={truck_line.arrival_rank}, "
                f"進入點 rank={enter_point.point_rank}"
            )
            return MatchResult(
                should_trigger=True,
                new_state='nearby',
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point
            )

        # 檢查是否應該觸發「離開」狀態
        if self._should_trigger_exit(truck_line, exit_point):
            reason = f"垃圾車已經過離開清運點: {self.exit_point_name}"
            logger.info(
                f"✅ 觸發離開狀態: {truck_line.line_name} - "
                f"離開點 arrival={exit_point.arrival}"
            )
            return MatchResult(
                should_trigger=True,
                new_state='idle',
                reason=reason,
                truck_line=truck_line,
                enter_point=enter_point,
                exit_point=exit_point
            )

        # 沒有觸發任何狀態變更
        return MatchResult(should_trigger=False)

    def _should_trigger_enter(
        self,
        truck_line: TruckLine,
        enter_point: Point
    ) -> bool:
        """
        判斷是否應該觸發進入狀態

        Args:
            truck_line: 垃圾車路線
            enter_point: 進入清運點

        Returns:
            bool: True 表示應該觸發
        """
        current_rank = truck_line.arrival_rank
        enter_rank = enter_point.point_rank

        if self.trigger_mode == 'arriving':
            # 模式：即將到達
            # 計算距離進入點的停靠點數
            distance = enter_rank - current_rank

            # 距離在 0 到 threshold 之間，且尚未到達
            if 0 <= distance <= self.approaching_threshold:
                if not enter_point.has_passed():
                    return True

        else:  # arrived
            # 模式：已經到達
            if enter_point.has_passed():
                return True

        return False

    def _should_trigger_exit(
        self,
        truck_line: TruckLine,
        exit_point: Point
    ) -> bool:
        """
        判斷是否應該觸發離開狀態

        Args:
            truck_line: 垃圾車路線
            exit_point: 離開清運點

        Returns:
            bool: True 表示應該觸發
        """
        # 垃圾車已經經過離開點
        return exit_point.has_passed()

    def __str__(self) -> str:
        """返回匹配器的字串表示"""
        return (
            f"PointMatcher("
            f"進入={self.enter_point_name}, "
            f"離開={self.exit_point_name}, "
            f"模式={self.trigger_mode})"
        )
