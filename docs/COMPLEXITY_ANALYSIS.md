# 程式碼複雜度分析報告

生成時間：2025-11-23

## 概述

使用 flake8 (complexity threshold = 8) 分析整個專案，找出複雜度較高的函式。

## 複雜度超過閾值的函式

### 1. `TruckTracker.get_current_status()` - 複雜度 10

**檔案**: `packages/core/trash_tracking_core/core/tracker.py:43`

**問題**：
- 多層 if-else 嵌套
- 多個 exception 處理分支
- 職責過多：API 呼叫、過濾、狀態更新、錯誤處理

**建議重構**：
```python
# 拆分成多個方法
def get_current_status(self) -> Dict[str, Any]:
    try:
        return self._fetch_and_process_trucks()
    except NTPCApiError as e:
        return self._handle_api_error(e)
    except Exception as e:
        return self._handle_unexpected_error(e)

def _fetch_and_process_trucks(self) -> Dict[str, Any]:
    truck_lines = self._fetch_truck_data()
    if not truck_lines:
        return self._handle_no_trucks()

    target_lines = self._filter_target_lines(truck_lines)
    if not target_lines:
        return self._handle_no_target_lines(len(truck_lines))

    self._process_matching_lines(target_lines)
    return self.state_manager.get_status_response()

def _handle_no_trucks(self) -> Dict[str, Any]:
    """Handle case when no trucks found"""
    ...

def _handle_no_target_lines(self, total_lines: int) -> Dict[str, Any]:
    """Handle case when no target lines found"""
    ...

def _handle_api_error(self, error: NTPCApiError) -> Dict[str, Any]:
    """Handle API errors"""
    ...

def _handle_unexpected_error(self, error: Exception) -> Dict[str, Any]:
    """Handle unexpected errors"""
    ...
```

**優先級**: 中（目前程式碼可讀性尚可，但可進一步改善）

---

### 2. `Geocoder.address_to_coordinates()` - 複雜度 9

**檔案**: `packages/core/trash_tracking_core/utils/geocoding.py:48`

**問題**：
- 串聯多個 API fallback 邏輯
- 多層錯誤處理
- 長錯誤訊息建構

**建議重構**：
```python
# 使用責任鏈模式
def address_to_coordinates(self, address: str, timeout: int = 10) -> Tuple[float, float]:
    cleaned_address = self._clean_address(address)

    # 定義 API 嘗試順序
    api_attempts = [
        ('NLSC', self._query_nlsc),
        ('Nominatim', self._query_nominatim),
        ('Simplified', self._try_simplified_addresses),
        ('TGOS', self._query_tgos),
    ]

    for api_name, query_func in api_attempts:
        try:
            result = query_func(cleaned_address, timeout)
            if result is not None and len(result) == 2:
                logger.info(f"{api_name} API succeeded")
                return result
        except Exception as e:
            logger.debug(f"{api_name} failed: {e}")
            continue

    # 所有 API 都失敗
    raise GeocodingError(self._build_error_message(address, cleaned_address))

def _build_error_message(self, original: str, cleaned: str) -> str:
    """Build user-friendly error message"""
    simplified = self._simplify_address(cleaned)
    return f"""無法找到地址的座標: {original}

建議解決方法：
1. 使用 Google Maps 查詢你的地址，右鍵點擊位置，複製座標
2. 然後使用座標執行: python3 cli.py --lat 緯度 --lng 經度
3. 或嘗試簡化地址，例如: {simplified}
4. 或使用互動式設定手動輸入座標: python3 cli.py --setup"""
```

**優先級**: 中（目前程式碼邏輯清楚，但可讀性可改善）

---

## 檔案大小分析

### 超過 200 行的檔案

1. **geocoding.py** - 280 行
   - 職責：地址轉座標
   - 狀態：包含多個 API fallback，合理長度

2. **config_flow.py** - 263 行
   - 職責：Home Assistant 設定流程
   - 狀態：3 個步驟的 wizard，合理長度

3. **ntpc_api.py** - 241 行
   - 職責：NTPC API 客戶端（包含 cache）
   - 狀態：合理長度

4. **coordinator.py** - 225 行
   - 職責：HA data coordinator（含排程邏輯）
   - 狀態：合理長度

5. **route_analyzer.py** - 207 行
   - 職責：路線分析與推薦
   - 狀態：合理長度

**結論**：沒有檔案超過 300 行，檔案大小控制良好。

---

## 整體評估

### ✅ 良好的部分

1. **模組化設計**：檔案職責清楚，沒有巨大檔案
2. **測試覆蓋**：有單元測試和 BDD 測試
3. **複雜度控制**：只有 2 個函式複雜度稍高 (9-10)
4. **程式碼品質**：通過 flake8, black, isort 檢查

### ⚠️ 可改善的部分

1. **tracker.py**：`get_current_status()` 可以拆分
2. **geocoding.py**：`address_to_coordinates()` 可以重構為責任鏈模式

### 📊 統計數據

- **總檔案數**：~40 個 Python 檔案
- **平均檔案大小**：~110 行
- **複雜度 > 8 的函式**：2 個
- **複雜度 > 10 的函式**：0 個

---

## 建議

### 短期（可選）

1. 添加 `# noqa: C901` 註解到複雜函式，明確標示已知複雜度
2. 為複雜函式添加更詳細的 docstring 說明邏輯

### 中期（當需要修改時）

1. 重構 `TruckTracker.get_current_status()` 拆分為多個小函式
2. 重構 `Geocoder.address_to_coordinates()` 使用責任鏈模式

### 長期（持續改善）

1. 持續監控複雜度，新增功能時注意保持低複雜度
2. 定期執行 `flake8 --max-complexity=8` 檢查

---

## 結論

**整體評價：良好** ✅

專案程式碼品質良好，沒有嚴重的複雜度問題。只有 2 個函式複雜度稍高（9-10），
但都在可接受範圍內，且程式碼可讀性尚佳。建議在未來修改這些函式時考慮重構，
但目前不需要緊急重構。
