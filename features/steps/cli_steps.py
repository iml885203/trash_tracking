"""Step definitions for CLI query features"""

import os
import subprocess
import sys
from pathlib import Path

from behave import given, then, when

PROJECT_ROOT = Path(__file__).parent.parent.parent
CLI_PATH = PROJECT_ROOT / "apps" / "cli" / "cli.py"


# ============================================================================
# Given 步驟 - 設定前置條件
# ============================================================================


@given("我已經安裝了垃圾車查詢工具")
def step_cli_tool_installed(context):
    """驗證 CLI 工具存在"""
    assert CLI_PATH.exists(), f"找不到 CLI 工具：{CLI_PATH}"
    context.cli_path = CLI_PATH


@given('我住在 "{address}"')
def step_i_live_at(context, address):
    """記錄使用者的地址"""
    context.address = address


@given('我不小心輸入了錯誤的地址 "{address}"')
def step_input_wrong_address(context, address):
    """記錄錯誤的地址"""
    context.address = address


@given('我只想追蹤 "{line_name}" 這條路線')
def step_only_track_line(context, line_name):
    """記錄想要追蹤的路線"""
    context.target_line = line_name


# ============================================================================
# When 步驟 - 使用者執行的動作
# ============================================================================


@when("我查詢附近的垃圾車")
def step_query_nearby_trucks(context):
    """查詢附近的垃圾車（使用預設搜尋範圍）"""
    env = os.environ.copy()
    # 傳遞 USE_MOCK_API 環境變數
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", context.address],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.stderr = result.stderr
    context.returncode = result.returncode


@when("我擴大搜尋範圍到 {distance:d} 公里")
def step_expand_search_radius(context, distance):
    """擴大搜尋範圍（公里轉公尺）"""
    radius_meters = distance * 1000
    env = os.environ.copy()
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", context.address, "--radius", str(radius_meters)],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.returncode = result.returncode


@when("我查詢這條路線的垃圾車")
def step_query_specific_line(context):
    """查詢特定路線的垃圾車"""
    env = os.environ.copy()
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", context.address, "--line", context.target_line],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.returncode = result.returncode


@when("我嘗試查詢垃圾車")
def step_try_to_query_trucks(context):
    """嘗試查詢垃圾車（預期可能失敗）"""
    env = os.environ.copy()
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", context.address],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.stderr = result.stderr
    context.returncode = result.returncode


# ============================================================================
# Then 步驟 - 驗證結果
# ============================================================================


@then("我應該看到找到幾台垃圾車")
def step_should_see_truck_count(context):
    """驗證輸出顯示找到的垃圾車數量"""
    output = context.stdout.lower()
    # 支援中英文輸出
    has_count = "found" in output or "找到" in output or "台" in output or "條" in output
    assert has_count, f"輸出中沒有看到垃圾車數量資訊：\n{context.stdout}"


@then("我應該看到垃圾車的路線名稱")
def step_should_see_route_name(context):
    """驗證輸出顯示路線資訊"""
    output = context.stdout.lower()
    # 支援中英文輸出
    has_route = "route" in output or "路線" in output or "line" in output
    assert has_route, f"輸出中沒有看到路線資訊：\n{context.stdout}"


@then("查詢應該成功")
def step_query_should_succeed(context):
    """驗證查詢成功（返回碼為 0）"""
    assert context.returncode == 0, f"查詢失敗，返回碼：{context.returncode}\n錯誤訊息：{context.stderr}"


@then("我應該看到垃圾車資訊")
def step_should_see_truck_info(context):
    """驗證顯示了垃圾車資訊"""
    assert len(context.stdout) > 0, "沒有任何輸出"
    output = context.stdout.lower()
    # 檢查是否包含垃圾車相關資訊
    has_truck_info = any(
        keyword in output for keyword in ["found", "找到", "route", "路線", "truck", "垃圾車", "garbage"]
    )
    assert has_truck_info, f"輸出中沒有看到垃圾車資訊：\n{context.stdout}"


@then('結果應該只顯示 "{line_name}" 的資訊')
def step_should_only_show_line(context, line_name):
    """驗證只顯示指定路線的資訊"""
    # 如果查詢成功且有結果，檢查是否包含指定路線
    if context.returncode == 0 and len(context.stdout) > 100:
        assert line_name in context.stdout, f"輸出中沒有找到路線「{line_name}」：\n{context.stdout}"


@then("系統應該告訴我地址有問題")
def step_should_show_address_error(context):
    """驗證系統顯示地址錯誤訊息"""
    has_error = (
        context.returncode != 0  # 返回碼不為 0
        or "error" in context.stderr.lower()  # stderr 包含錯誤
        or "錯誤" in context.stdout  # stdout 包含中文錯誤
        or "失敗" in context.stdout  # 失敗訊息
        or "找不到" in context.stdout  # 找不到地址
    )
    assert has_error, f"預期應該顯示地址錯誤，但查詢似乎成功了\n返回碼：{context.returncode}\nStdout：{context.stdout}\nStderr：{context.stderr}"
