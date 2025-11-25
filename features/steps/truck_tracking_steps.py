"""Step definitions for truck tracking features"""

from behave import given, then, when
from trash_tracking_core.core.point_matcher import PointMatcher
from trash_tracking_core.core.response_builder import StatusResponseBuilder
from trash_tracking_core.core.state_manager import StateManager
from trash_tracking_core.models.point import Point
from trash_tracking_core.models.truck import TruckLine


def create_points(count=30, enter_rank=23, exit_rank=26):
    """Helper to create sample points"""
    points = []
    for i in range(1, count + 1):
        points.append(
            Point(
                source_point_id=i,
                vil=f"Village {i}",
                point_name=f"站點{i}號",
                lon=121.5 + i * 0.001,
                lat=25.0 + i * 0.001,
                point_id=100 + i,
                point_rank=i,
                point_time=f"18:{i:02d}",
                arrival="",
                arrival_diff=65535,
                fixed_point=1,
                point_weekknd="1,2,4,5,6",
                in_scope="Y",
                like_count=0,
            )
        )
    return points


def create_truck(points, arrival_rank):
    """Helper to create a truck at specified rank"""
    return TruckLine(
        line_id="L001",
        line_name="三區晚9",
        area="永和區",
        arrival_rank=arrival_rank,
        diff=0,
        car_no="ABC-1234",
        location=f"站點{arrival_rank}號",
        location_lat=25.0 + arrival_rank * 0.001,
        location_lon=121.5 + arrival_rank * 0.001,
        bar_code="12345",
        points=points,
    )


# ============================================================================
# Given 步驟 - 設定前置條件
# ============================================================================


@given('系統已設定追蹤路線 "{route_name}"')
def step_setup_tracking_route(context, route_name):
    """設定追蹤的路線"""
    context.route_name = route_name
    context.state_manager = StateManager()
    context.response_builder = StatusResponseBuilder()


@given('進入點是 "{enter_point}"')
def step_set_enter_point(context, enter_point):
    """設定進入點"""
    context.enter_point_name = enter_point
    context.enter_rank = 23  # 預設 rank


@given('離開點是 "{exit_point}"')
def step_set_exit_point(context, exit_point):
    """設定離開點"""
    context.exit_point_name = exit_point
    context.exit_rank = 26  # 預設 rank

    # 建立 PointMatcher
    context.points = create_points(count=30, enter_rank=context.enter_rank, exit_rank=context.exit_rank)
    # 用實際名稱設定 enter/exit points
    context.points[context.enter_rank - 1].point_name = context.enter_point_name
    context.points[context.exit_rank - 1].point_name = context.exit_point_name

    context.point_matcher = PointMatcher(
        enter_point_name=context.enter_point_name,
        exit_point_name=context.exit_point_name,
    )


@given("垃圾車目前在進入點之前")
def step_truck_before_enter_point(context):
    """設定垃圾車在進入點之前"""
    context.truck = create_truck(context.points, arrival_rank=context.enter_rank - 1)


@given('狀態目前是 "{state}"')
def step_current_state(context, state):
    """設定目前狀態"""
    if state == "nearby":
        context.state_manager.update_state(new_state="nearby", reason="Truck approaching")
    elif state == "idle":
        context.state_manager.update_state(new_state="idle", reason="Initial state")


@given("垃圾車已通過離開點")
def step_truck_passed_exit(context):
    """設定垃圾車已通過離開點"""
    context.truck = create_truck(context.points, arrival_rank=context.exit_rank + 1)
    # 標記離開點已通過
    context.points[context.exit_rank - 1].arrival = "18:30"
    context.points[context.exit_rank - 1].arrival_diff = 0


@given("垃圾車已經通過離開點")
def step_truck_already_passed_exit(context):
    """設定垃圾車已經通過離開點（用於防止跳動場景）"""
    context.truck = create_truck(context.points, arrival_rank=context.exit_rank + 2)
    # 標記進入點和離開點都已通過
    context.points[context.enter_rank - 1].arrival = "18:20"
    context.points[context.enter_rank - 1].arrival_diff = 0
    context.points[context.exit_rank - 1].arrival = "18:30"
    context.points[context.exit_rank - 1].arrival_diff = 0


@given("垃圾車從第 {from_rank:d} 站跳到第 {to_rank:d} 站")
def step_truck_jumps(context, from_rank, to_rank):
    """設定垃圾車跳站"""
    context.truck = create_truck(context.points, arrival_rank=to_rank)


@given("進入點在第 {rank:d} 站")
def step_enter_at_rank(context, rank):
    """設定進入點的 rank"""
    context.enter_rank = rank
    context.points[rank - 1].point_name = context.enter_point_name


@given("離開點在第 {rank:d} 站")
def step_exit_at_rank(context, rank):
    """設定離開點的 rank"""
    context.exit_rank = rank
    context.points[rank - 1].point_name = context.exit_point_name
    # 重新建立 PointMatcher
    context.point_matcher = PointMatcher(
        enter_point_name=context.enter_point_name,
        exit_point_name=context.exit_point_name,
    )


@given("API 有補回進入點和離開點的 arrival 資料")
def step_api_backfills_arrival(context):
    """模擬 API 補回 arrival 資料"""
    context.points[context.enter_rank - 1].arrival = "18:20"
    context.points[context.enter_rank - 1].arrival_diff = 0
    context.points[context.exit_rank - 1].arrival = "18:30"
    context.points[context.exit_rank - 1].arrival_diff = 0


@given("API 回傳垃圾車在第 {rank:d} 站")
def step_api_returns_truck_at_rank(context, rank):
    """設定 API 回傳的垃圾車位置"""
    context.truck = create_truck(context.points, arrival_rank=rank)
    context.truck_rank = rank


@given("垃圾車資料持續可用")
def step_truck_data_available(context):
    """設定垃圾車資料可用"""
    context.truck = create_truck(context.points, arrival_rank=context.exit_rank)
    # 標記進入點已通過
    context.points[context.enter_rank - 1].arrival = "18:20"
    context.points[context.enter_rank - 1].arrival_diff = 0


# ============================================================================
# When 步驟 - 執行動作
# ============================================================================


@when("垃圾車到達進入點")
def step_truck_arrives_enter(context):
    """模擬垃圾車到達進入點"""
    context.truck = create_truck(context.points, arrival_rank=context.enter_rank)
    # 標記進入點已到達
    context.points[context.enter_rank - 1].arrival = "18:20"
    context.points[context.enter_rank - 1].arrival_diff = 0

    # 執行檢查
    context.match_result = context.point_matcher.check_line(
        context.truck, current_state=context.state_manager.current_state
    )

    if context.match_result.should_trigger:
        context.state_manager.update_state(
            new_state=context.match_result.new_state,
            reason=context.match_result.reason,
            truck_line=context.truck,
        )


@when("系統檢查垃圾車狀態")
def step_system_checks_state(context):
    """系統檢查垃圾車狀態"""
    context.match_result = context.point_matcher.check_line(
        context.truck, current_state=context.state_manager.current_state
    )

    if context.match_result.should_trigger:
        context.state_manager.update_state(
            new_state=context.match_result.new_state,
            reason=context.match_result.reason,
            truck_line=context.truck,
        )


@when("系統再次檢查垃圾車狀態")
def step_system_rechecks_state(context):
    """系統再次檢查（用於驗證不會重複觸發）"""
    context.previous_state = context.state_manager.current_state

    context.match_result = context.point_matcher.check_line(
        context.truck, current_state=context.state_manager.current_state
    )

    if context.match_result.should_trigger:
        context.state_manager.update_state(
            new_state=context.match_result.new_state,
            reason=context.match_result.reason,
            truck_line=context.truck,
        )


@when("系統處理 API 回應")
def step_system_processes_api(context):
    """系統處理 API 回應並更新 truck info"""
    # 找到 enter/exit points
    enter_point = context.points[context.enter_rank - 1]
    exit_point = context.points[context.exit_rank - 1]

    # 更新狀態（即使沒有觸發，也要更新 truck info）
    context.state_manager.update_state(
        new_state=context.state_manager.current_state.value,
        reason=context.state_manager.reason,
        truck_line=context.truck,
        enter_point=enter_point,
        exit_point=exit_point,
    )

    context.response = context.response_builder.build(context.state_manager)


@when('狀態從 "{from_state}" 變成 "{to_state}"')
def step_state_changes(context, from_state, to_state):
    """模擬狀態變更"""
    enter_point = context.points[context.enter_rank - 1]
    exit_point = context.points[context.exit_rank - 1]

    # 先設定為 from_state
    context.state_manager.update_state(
        new_state=from_state,
        reason="Test setup",
        truck_line=context.truck,
        enter_point=enter_point,
        exit_point=exit_point,
    )

    # 再變成 to_state
    context.state_manager.update_state(
        new_state=to_state,
        reason="Test transition",
        truck_line=context.truck,
        enter_point=enter_point,
        exit_point=exit_point,
    )

    context.response = context.response_builder.build(context.state_manager)


# ============================================================================
# Then 步驟 - 驗證結果
# ============================================================================


@then('狀態應該變成 "{expected_state}"')
def step_state_should_be(context, expected_state):
    """驗證狀態"""
    actual_state = context.state_manager.current_state.value
    assert actual_state == expected_state, f"預期狀態 {expected_state}，但實際是 {actual_state}"


@then('狀態應該維持 "{expected_state}"')
def step_state_should_remain(context, expected_state):
    """驗證狀態維持不變"""
    actual_state = context.state_manager.current_state.value
    assert actual_state == expected_state, f"預期狀態維持 {expected_state}，但實際是 {actual_state}"


@then("不應該觸發狀態變更")
def step_should_not_trigger(context):
    """驗證沒有觸發狀態變更"""
    assert context.match_result.should_trigger is False, "不應該觸發狀態變更，但觸發了"


@then("不應該因為進入點有 arrival 就觸發 nearby")
def step_should_not_trigger_nearby(context):
    """驗證不會因為進入點有 arrival 就觸發"""
    assert context.match_result.should_trigger is False, "不應該觸發 nearby"
    if context.match_result.should_trigger:
        assert context.match_result.new_state != "nearby", "不應該變成 nearby"


@then("Truck Info 應該顯示第 {rank:d} 站的位置")
def step_truck_info_shows_rank(context, rank):
    """驗證 Truck Info 顯示正確位置"""
    assert context.response["truck"] is not None, "Truck Info 不應該是 None"
    assert (
        context.response["truck"]["current_rank"] == rank
    ), f"Truck Info 應該顯示第 {rank} 站，但顯示 {context.response['truck']['current_rank']}"


@then("不管狀態是 idle 或 nearby")
def step_regardless_of_state(context):
    """驗證不管狀態如何，truck info 都應該有資料"""
    # 這個步驟主要是描述性的，實際驗證在前一步已完成
    pass


@then("Truck Info 應該持續顯示垃圾車位置")
def step_truck_info_keeps_showing(context):
    """驗證 Truck Info 持續顯示位置"""
    assert context.response["truck"] is not None, "Truck Info 不應該是 None"


@then('不應該變成 "No truck nearby"')
def step_should_not_be_no_truck(context):
    """驗證不會變成 No truck nearby"""
    assert context.response["truck"] is not None, 'Truck Info 不應該變成 "No truck nearby"'
