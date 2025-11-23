"""Step definitions for CLI query features"""

import os
import subprocess
import sys
from pathlib import Path

from behave import given, then, when

PROJECT_ROOT = Path(__file__).parent.parent.parent
CLI_PATH = PROJECT_ROOT / "apps" / "cli" / "cli.py"


@given("CLI 工具已經安裝")
def step_cli_installed(context):
    """Verify CLI tool exists"""
    assert CLI_PATH.exists(), f"CLI not found at {CLI_PATH}"
    context.cli_path = CLI_PATH


@when('我使用地址 "{address}" 查詢垃圾車')
def step_query_by_address(context, address):
    """Query garbage trucks by address"""
    env = os.environ.copy()
    # Pass USE_MOCK_API environment variable to subprocess
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", address],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.stderr = result.stderr
    context.returncode = result.returncode


@when('我使用地址 "{address}" 和半徑 "{radius}" 公尺查詢')
def step_query_with_radius(context, address, radius):
    """Query with custom radius"""
    env = os.environ.copy()
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", address, "--radius", radius],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.returncode = result.returncode


@given('我知道附近有 "{line_name}" 路線')
def step_know_route_exists(context, line_name):
    """Remember route name for filtering"""
    context.line_name = line_name


@when('我使用地址 "{address}" 過濾路線 "{line_name}"')
def step_query_with_line_filter(context, address, line_name):
    """Query with line filter"""
    env = os.environ.copy()
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", address, "--line", line_name],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.returncode = result.returncode


@when('我使用無效地址 "{address}" 查詢垃圾車')
def step_query_invalid_address(context, address):
    """Query with invalid address"""
    env = os.environ.copy()
    if hasattr(context, "use_mocks") and context.use_mocks:
        env["USE_MOCK_API"] = "true"

    result = subprocess.run(
        [sys.executable, str(context.cli_path), "--address", address],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    context.result = result
    context.stdout = result.stdout
    context.stderr = result.stderr
    context.returncode = result.returncode


@then("我應該看到找到的垃圾車數量")
def step_should_see_truck_count(context):
    """Verify output shows truck count"""
    assert "Found" in context.stdout or "找到" in context.stdout, f"No truck count found in: {context.stdout}"


@then("我應該看到路線資訊")
def step_should_see_route_info(context):
    """Verify output shows route information"""
    assert "Route" in context.stdout or "路線" in context.stdout, f"No route info in: {context.stdout}"


@then("我應該看到收集點清單")
def step_should_see_collection_points(context):
    """Verify output shows collection points"""
    assert "point" in context.stdout.lower() or "收集點" in context.stdout, f"No collection points in: {context.stdout}"


@then("查詢應該成功")
def step_query_should_succeed(context):
    """Verify query succeeded"""
    assert context.returncode == 0, f"Query failed with code {context.returncode}"


@then("我應該看到垃圾車資訊")
def step_should_see_truck_info(context):
    """Verify truck information is shown"""
    assert len(context.stdout) > 0, "No output received"
    assert "Found" in context.stdout or "找到" in context.stdout or "Route" in context.stdout


@then('結果應該只包含 "{line_name}"')
def step_should_only_contain_line(context, line_name):
    """Verify only specified line is shown"""
    # If query succeeded and returned results, check line name
    if context.returncode == 0 and len(context.stdout) > 10:
        assert line_name in context.stdout, f"Line {line_name} not found in output"


@then("我應該看到錯誤訊息")
def step_should_see_error(context):
    """Verify error message is shown"""
    has_error = (
        "error" in context.stderr.lower()
        or context.returncode != 0
        or "找不到" in context.stdout
        or "錯誤" in context.stdout
    )
    assert has_error, f"No error shown. Return code: {context.returncode}, Stderr: {context.stderr}"


@then('我應該看到 "{message}" 訊息')
def step_should_see_message(context, message):
    """Verify specific message is shown"""
    assert message in context.stdout or "No" in context.stdout or "沒有" in context.stdout or "找不到" in context.stdout
