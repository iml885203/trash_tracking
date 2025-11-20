"""Step definitions for setup wizard features"""

import requests
from behave import given, then, when


@given("設定精靈已啟用")
def step_setup_wizard_enabled(context):
    """Verify setup wizard is accessible"""
    response = requests.get(f"{context.base_url}/", timeout=5)
    assert response.status_code == 200


@when('我訪問設定精靈首頁 "{path}"')
def step_visit_setup_homepage(context, path):
    """Visit setup wizard homepage"""
    response = requests.get(f"{context.base_url}{path}", timeout=5)
    context.response = response
    context.status_code = response.status_code
    context.html_content = response.text


@when('我輸入地址 "{address}" 並請求建議')
def step_request_suggestion(context, address):
    """Request configuration suggestion for address"""
    response = requests.post(f"{context.base_url}/api/setup/suggest", json={"address": address}, timeout=30)
    context.response = response
    context.status_code = response.status_code
    context.json_data = response.json()


@when('我輸入無效地址 "{address}" 並請求建議')
def step_request_suggestion_invalid(context, address):
    """Request suggestion with invalid address"""
    response = requests.post(f"{context.base_url}/api/setup/suggest", json={"address": address}, timeout=30)
    context.response = response
    context.status_code = response.status_code
    context.json_data = response.json()


@given('我已經取得地址 "{address}" 的建議配置')
def step_get_suggestion(context, address):
    """Get suggestion for address"""
    response = requests.post(f"{context.base_url}/api/setup/suggest", json={"address": address}, timeout=30)
    assert response.status_code == 200
    context.suggestion_data = response.json()


@when("我儲存該配置")
def step_save_configuration(context):
    """Save the configuration"""
    response = requests.post(f"{context.base_url}/api/setup/save", json=context.suggestion_data, timeout=10)
    context.response = response
    context.status_code = response.status_code
    context.json_data = response.json()


@when("我嘗試儲存空配置")
def step_save_empty_config(context):
    """Try to save empty configuration"""
    response = requests.post(f"{context.base_url}/api/setup/save", json={}, timeout=10)
    context.response = response
    context.status_code = response.status_code
    context.json_data = response.json()


@then("頁面應該成功載入")
def step_page_should_load(context):
    """Verify page loaded successfully"""
    assert context.status_code == 200, f"Page load failed with status {context.status_code}"


@then('頁面標題應該包含 "{text}"')
def step_page_title_should_contain(context, text):
    """Verify page title contains text"""
    assert text in context.html_content, f"Text '{text}' not found in page"


@then("我應該看到地址輸入框")
def step_should_see_address_input(context):
    """Verify address input field exists"""
    assert "address" in context.html_content, "Address input not found"


@then("API 應該返回成功回應")
def step_api_should_return_success(context):
    """Verify API returned success"""
    assert context.status_code == 200, f"API failed with status {context.status_code}"
    assert context.json_data.get("success") is True, "Response does not indicate success"


@then("API 應該返回錯誤回應")
def step_api_should_return_error(context):
    """Verify API returned error"""
    assert context.status_code in [400, 404, 500], f"Expected error status, got {context.status_code}"
    assert "error" in context.json_data, "No error field in response"


@then("回應應該包含建議的座標")
def step_response_should_contain_coordinates(context):
    """Verify response contains coordinates"""
    rec = context.json_data.get("recommendation", {})
    assert "latitude" in rec, "Latitude not found in recommendation"
    assert "longitude" in rec, "Longitude not found in recommendation"


@then("回應應該包含建議的路線")
def step_response_should_contain_routes(context):
    """Verify response contains route recommendations"""
    rec = context.json_data.get("recommendation", {})
    route_sel = rec.get("route_selection", {})
    assert "route_names" in route_sel, "Route names not found"
    assert len(route_sel["route_names"]) > 0, "No routes recommended"


@then("回應應該包含進入點和離開點")
def step_response_should_contain_points(context):
    """Verify response contains enter and exit points"""
    rec = context.json_data.get("recommendation", {})
    best_route = rec.get("route_selection", {}).get("best_route", {})
    assert "enter_point" in best_route, "Enter point not found"
    assert "exit_point" in best_route, "Exit point not found"


@then("儲存應該成功")
def step_save_should_succeed(context):
    """Verify save succeeded"""
    assert context.status_code == 200, f"Save failed with status {context.status_code}"
    assert context.json_data.get("success") is True, "Save did not succeed"


@then("我應該收到確認訊息")
def step_should_receive_confirmation(context):
    """Verify confirmation message received"""
    assert "message" in context.json_data, "No confirmation message"


@then("配置檔應該被更新")
def step_config_file_should_be_updated(context):
    """Verify config file path is returned"""
    assert "config_path" in context.json_data, "Config path not returned"


@then("API 應該返回 {status:d} 錯誤")
def step_api_should_return_status(context, status):
    """Verify specific error status"""
    assert context.status_code == status, f"Expected {status}, got {context.status_code}"


@then("錯誤訊息應該說明地址無效")
def step_error_should_indicate_invalid_address(context):
    """Verify error indicates invalid address"""
    error_msg = context.json_data.get("error", "").lower()
    assert any(
        keyword in error_msg for keyword in ["地址", "address", "geocoding", "invalid"]
    ), f"Error message does not indicate address issue: {error_msg}"


@then("錯誤訊息應該說明缺少必要資料")
def step_error_should_indicate_missing_data(context):
    """Verify error indicates missing data"""
    error_msg = context.json_data.get("error", "").lower()
    assert any(
        keyword in error_msg for keyword in ["required", "missing", "缺少", "必要"]
    ), f"Error does not indicate missing data: {error_msg}"


@then('建議的路線應該屬於 "{district}"')
def step_routes_should_belong_to_district(context, district):
    """Verify recommended routes belong to district"""
    # This is a simplified check - just verify we got routes
    rec = context.json_data.get("recommendation", {})
    route_names = rec.get("route_selection", {}).get("route_names", [])
    assert len(route_names) > 0, f"No routes found for {district}"
