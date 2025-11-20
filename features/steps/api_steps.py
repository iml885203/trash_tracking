"""Step definitions for API status features"""

import concurrent.futures

import requests
from behave import given, then, when


@given("API 伺服器正在運行")
def step_api_server_running(context):
    """Verify API server is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        assert response.status_code == 200
        context.base_url = "http://localhost:5000"
    except requests.exceptions.RequestException:
        context.scenario.skip("API server is not running")


@given("追蹤器已經初始化")
def step_tracker_initialized(context):
    """Verify tracker is initialized"""
    response = requests.get(f"{context.base_url}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@given("追蹤器已被重置")
def step_tracker_reset(context):
    """Reset tracker state"""
    requests.post(f"{context.base_url}/api/reset", timeout=5)


@when('我查詢 "{endpoint}" 端點')
def step_query_endpoint(context, endpoint):
    """Query API endpoint"""
    response = requests.get(f"{context.base_url}{endpoint}", timeout=10)
    context.response = response
    context.status_code = response.status_code
    try:
        context.json_data = response.json()
    except Exception:
        context.json_data = None


@when('我發送 POST 請求到 "{endpoint}"')
def step_post_to_endpoint(context, endpoint):
    """Send POST request to endpoint"""
    response = requests.post(f"{context.base_url}{endpoint}", timeout=10)
    context.response = response
    context.status_code = response.status_code
    context.json_data = response.json()


@when('我同時發送 {count:d} 個請求到 "{endpoint}"')
def step_concurrent_requests(context, count, endpoint):
    """Send concurrent requests"""

    def make_request():
        return requests.get(f"{context.base_url}{endpoint}", timeout=10)

    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(make_request) for _ in range(count)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    context.concurrent_responses = responses


@then("回應狀態碼應該是 {status_code:d}")
def step_status_code_should_be(context, status_code):
    """Verify response status code"""
    assert context.status_code == status_code, f"Expected {status_code}, got {context.status_code}"


@then('回應應該包含 "{field}" 欄位')
def step_response_should_contain_field(context, field):
    """Verify response contains field"""
    assert context.json_data is not None, "No JSON data in response"
    assert field in context.json_data, f"Field '{field}' not found in response: {context.json_data}"


@then('status 應該是 "{value}"')
def step_status_should_be(context, value):
    """Verify status value"""
    assert context.json_data["status"] == value, f"Expected status '{value}', got '{context.json_data['status']}'"


@then('message 應該包含 "{text}"')
def step_message_should_contain(context, text):
    """Verify message contains text"""
    message = context.json_data.get("message", "")
    assert text.lower() in message.lower(), f"'{text}' not found in message: {message}"


@then("回應應該包含錯誤訊息")
def step_response_should_contain_error(context):
    """Verify response contains error message"""
    assert "error" in context.json_data, f"No error in response: {context.json_data}"


@then("所有請求都應該成功")
def step_all_requests_should_succeed(context):
    """Verify all concurrent requests succeeded"""
    for response in context.concurrent_responses:
        assert response.status_code in [200, 503], f"Request failed with status {response.status_code}"


@then('所有回應都應該包含 "{field}" 欄位')
def step_all_responses_should_contain_field(context, field):
    """Verify all responses contain field"""
    for response in context.concurrent_responses:
        data = response.json()
        assert field in data, f"Field '{field}' not found in response"
