"""Step implementations for config flow testing"""

import sys
from pathlib import Path

from behave import given, then, when

# IMPORTANT: Force import from custom_components instead of packages/core
# We need to remove any existing trash_tracking_core from sys.modules first
# to ensure we test the embedded version (not the pip-installed one)
import sys
for key in list(sys.modules.keys()):
    if key.startswith('trash_tracking_core'):
        del sys.modules[key]

# Add trash_tracking_core to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "custom_components" / "trash_tracking"))

from trash_tracking_core.clients.ntpc_api import NTPCApiClient, NTPCApiError  # noqa: E402
from trash_tracking_core.utils.geocoding import Geocoder, GeocodingError  # noqa: E402
from trash_tracking_core.utils.route_analyzer import RouteAnalyzer  # noqa: E402

# DEBUG: Verify we're using the embedded version
import trash_tracking_core
expected_path = str(project_root / "custom_components" / "trash_tracking" / "trash_tracking_core")
actual_path = str(Path(trash_tracking_core.__file__).parent)
assert actual_path == expected_path, (
    f"ERROR: Loading wrong trash_tracking_core!\n"
    f"Expected: {expected_path}\n"
    f"Actual: {actual_path}\n"
    f"This test must use the embedded version in custom_components"
)


# ============================================================================
# Given 步驟 - 設定前置條件
# ============================================================================


@given("垃圾車追蹤整合已經安裝")
def step_integration_installed(context):
    """驗證整合模組可以使用"""
    context.geocoder = Geocoder()
    context.api_client = NTPCApiClient()


# 注意："我住在" 和 "我不小心輸入錯誤的地址" 步驟定義在 cli_steps.py 中
# Behave 會自動共用這些步驟定義

@given("我住在偏遠地區（座標 緯度 {lat:f} 經度 {lng:f}）")
def step_live_at_remote_location(context, lat, lng):
    """設定偏遠地區的座標"""
    context.latitude = lat
    context.longitude = lng


# ============================================================================
# When 步驟 - 使用者執行的動作
# ============================================================================


@when("我在設定頁面輸入我家地址")
def step_input_address_in_setup(context):
    """在設定頁面輸入地址（內部會進行地址轉座標）"""
    try:
        context.latitude, context.longitude = context.geocoder.address_to_coordinates(context.address)
        context.geocoding_error = None
    except Exception as e:
        context.geocoding_error = e


@when("我嘗試送出地址進行設定")
def step_submit_address(context):
    """嘗試送出地址（預期可能失敗）"""
    try:
        context.latitude, context.longitude = context.geocoder.address_to_coordinates(context.address)
        context.geocoding_error = None
    except GeocodingError as e:
        context.geocoding_error = e


@when("系統查詢我家附近的垃圾車路線")
def step_system_queries_routes(context):
    """系統自動查詢附近的垃圾車路線"""
    try:
        context.routes = context.api_client.get_around_points(
            context.latitude, context.longitude, time_filter=0, week=1
        )
        context.api_error = None
    except NTPCApiError as e:
        context.api_error = e
        context.routes = []


@when("系統查詢附近的垃圾車路線")
def step_query_nearby_routes(context):
    """查詢附近路線（與上面的步驟功能相同，但用詞稍有不同）"""
    step_system_queries_routes(context)


@when("系統分析這些路線並產生推薦")
def step_system_analyzes_routes(context):
    """系統分析路線並產生推薦"""
    analyzer = RouteAnalyzer(context.latitude, context.longitude)
    context.recommendations = analyzer.analyze_all_routes(context.routes)


@when("我完成整個設定流程")
def step_complete_setup_flow(context):
    """完成整個設定流程（地址→座標→路線→推薦→選擇）"""
    # 1. 地址轉座標
    context.latitude, context.longitude = context.geocoder.address_to_coordinates(context.address)

    # 2. 查詢路線
    context.routes = context.api_client.get_around_points(context.latitude, context.longitude, 0, 1)

    # 3. 分析並產生推薦
    analyzer = RouteAnalyzer(context.latitude, context.longitude)
    context.recommendations = analyzer.analyze_all_routes(context.routes)

    # 4. 選擇第一個推薦
    if context.recommendations:
        context.selected_recommendation = context.recommendations[0]


# ============================================================================
# Then 步驟 - 驗證結果
# ============================================================================


@then("系統應該找到我家的位置座標")
def step_should_find_coordinates(context):
    """驗證成功取得座標"""
    assert context.geocoding_error is None, f"地址轉換失敗: {context.geocoding_error}"
    assert hasattr(context, "latitude"), "未找到緯度資訊"
    assert hasattr(context, "longitude"), "未找到經度資訊"
    # 驗證座標在合理範圍內（台灣地區）
    assert 21.0 <= context.latitude <= 26.0, f"緯度 {context.latitude} 不在台灣範圍"
    assert 119.0 <= context.longitude <= 122.0, f"經度 {context.longitude} 不在台灣範圍"


@then("應該至少找到 {min_count:d} 條路線")
def step_should_find_at_least_routes(context, min_count):
    """驗證至少找到指定數量的路線"""
    actual = len(context.routes) if context.routes else 0
    assert actual >= min_count, f"預期至少 {min_count} 條路線，實際找到 {actual} 條"


@then("應該找到 {expected_count:d} 條路線")
def step_should_find_exact_routes(context, expected_count):
    """驗證找到確切數量的路線"""
    actual = len(context.routes) if context.routes else 0
    assert actual == expected_count, f"預期 {expected_count} 條路線，實際找到 {actual} 條"


@then("我應該看到路線推薦清單")
def step_should_see_recommendations(context):
    """驗證有產生路線推薦"""
    assert hasattr(context, "recommendations"), "沒有產生推薦清單"
    assert context.recommendations, "推薦清單是空的"
    assert len(context.recommendations) > 0, "推薦清單應該至少有一個推薦"


@then("每個推薦都應該包含垃圾車資訊")
def step_each_recommendation_has_truck(context):
    """驗證每個推薦都有垃圾車資訊"""
    for i, rec in enumerate(context.recommendations, 1):
        assert hasattr(rec, "truck"), f"第 {i} 個推薦缺少垃圾車資訊"
        assert rec.truck is not None, f"第 {i} 個推薦的垃圾車資訊是空的"
        assert hasattr(rec.truck, "line_name"), f"第 {i} 個推薦的垃圾車缺少路線名稱"


@then("每個推薦都應該有進入點（垃圾車接近時提醒）")
def step_each_recommendation_has_enter_point(context):
    """驗證每個推薦都有進入點"""
    for i, rec in enumerate(context.recommendations, 1):
        assert hasattr(rec, "enter_point"), f"第 {i} 個推薦缺少進入點"
        assert rec.enter_point is not None, f"第 {i} 個推薦的進入點是空的"
        assert hasattr(rec.enter_point, "point_name"), f"第 {i} 個推薦的進入點缺少名稱"


@then("每個推薦都應該有離開點（垃圾車離開後停止提醒）")
def step_each_recommendation_has_exit_point(context):
    """驗證每個推薦都有離開點"""
    for i, rec in enumerate(context.recommendations, 1):
        assert hasattr(rec, "exit_point"), f"第 {i} 個推薦缺少離開點"
        assert rec.exit_point is not None, f"第 {i} 個推薦的離開點是空的"
        assert hasattr(rec.exit_point, "point_name"), f"第 {i} 個推薦的離開點缺少名稱"


@then("每個推薦都應該有最近的收集點")
def step_each_recommendation_has_nearest_point(context):
    """驗證每個推薦都有最近的收集點"""
    for i, rec in enumerate(context.recommendations, 1):
        assert hasattr(rec, "nearest_point"), f"第 {i} 個推薦缺少最近收集點"
        assert rec.nearest_point is not None, f"第 {i} 個推薦的最近收集點是空的"
        assert hasattr(rec.nearest_point, "point_name"), f"第 {i} 個推薦的最近收集點缺少名稱"


@then("地址轉換應該失敗")
def step_geocoding_should_fail(context):
    """驗證地址轉換失敗（config flow 專用 - 檢查 GeocodingError）"""
    assert context.geocoding_error is not None, "預期應該有地址錯誤，但卻成功了"
    assert isinstance(context.geocoding_error, GeocodingError), "錯誤類型應該是 GeocodingError"


@then("系統應該告訴我這個區域目前沒有垃圾車路線資料")
def step_should_show_no_routes_message(context):
    """驗證系統告知沒有路線資料"""
    # 驗證確實沒有路線
    actual = len(context.routes) if context.routes else 0
    assert actual == 0, f"預期沒有路線，但實際找到 {actual} 條"


@then("系統推薦的路線應該有收集點清單")
def step_recommended_route_has_points(context):
    """驗證推薦的路線有收集點清單"""
    assert hasattr(context, "selected_recommendation"), "沒有選擇的推薦"
    assert hasattr(context.selected_recommendation.truck, "points"), "垃圾車缺少收集點清單"
    assert len(context.selected_recommendation.truck.points) > 0, "收集點清單是空的"


@then("進入點應該在這條路線的收集點清單中")
def step_enter_point_in_route_points(context):
    """驗證進入點存在於收集點清單中"""
    enter_name = context.selected_recommendation.enter_point.point_name
    point_names = [p.point_name for p in context.selected_recommendation.truck.points]
    assert enter_name in point_names, f"進入點「{enter_name}」不在收集點清單中"


@then("離開點應該在這條路線的收集點清單中")
def step_exit_point_in_route_points(context):
    """驗證離開點存在於收集點清單中"""
    exit_name = context.selected_recommendation.exit_point.point_name
    point_names = [p.point_name for p in context.selected_recommendation.truck.points]
    assert exit_name in point_names, f"離開點「{exit_name}」不在收集點清單中"


@when("系統解析第一個推薦的收集點收集日期")
def step_parse_collection_weekdays(context):
    """解析收集點的收集日期（測試 get_weekdays 方法）"""
    assert hasattr(context, "recommendations"), "沒有推薦清單"
    assert len(context.recommendations) > 0, "推薦清單是空的"

    # 取得第一個推薦的垃圾車路線
    recommendation = context.recommendations[0]
    assert hasattr(recommendation, "truck"), "推薦缺少垃圾車資訊"
    assert hasattr(recommendation.truck, "points"), "垃圾車缺少收集點清單"
    assert len(recommendation.truck.points) > 0, "收集點清單是空的"

    # 取得第一個收集點（這是真正的 Point 物件，包含 get_weekdays 方法）
    point = recommendation.truck.points[0]

    # 驗證 get_weekdays 方法存在（這是關鍵測試！）
    assert hasattr(point, "get_weekdays"), (
        f"Point 物件缺少 get_weekdays() 方法。"
        f"這表示 custom_components/trash_tracking/trash_tracking_core/ "
        f"沒有從 packages/core/ 正確同步"
    )

    # 呼叫 get_weekdays() 並儲存結果
    context.parsed_weekdays = point.get_weekdays()


@then("系統應該能夠取得星期資訊")
def step_should_get_weekday_info(context):
    """驗證成功取得星期資訊"""
    assert hasattr(context, "parsed_weekdays"), "沒有解析星期資訊"
    assert context.parsed_weekdays is not None, "星期資訊不應該是 None"


@then("星期資訊應該是有效的數字列表")
def step_weekday_should_be_list(context):
    """驗證星期資訊是列表格式"""
    assert isinstance(context.parsed_weekdays, list), f"星期資訊應該是 list，但得到 {type(context.parsed_weekdays)}"
    # 如果有資料，驗證每個元素都是整數
    if context.parsed_weekdays:
        for day in context.parsed_weekdays:
            assert isinstance(day, int), f"星期應該是整數，但得到 {type(day)}"


@then("星期資訊的數字應該在 0 到 6 之間")
def step_weekday_numbers_in_range(context):
    """驗證星期數字在有效範圍內（0=週日, 1-6=週一到週六）"""
    if context.parsed_weekdays:
        for day in context.parsed_weekdays:
            assert 0 <= day <= 6, f"星期數字 {day} 不在有效範圍 0-6 之間"
