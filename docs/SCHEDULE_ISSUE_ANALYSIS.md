# Schedule-Based API Polling Issue Analysis

## 問題描述

**時間**: 2025-11-24 00:07 (週一上午)
**現象**: 雖然配置的路線是中午和晚上收集，但在早上 00:07 仍然看到 "Successfully queried NTPC API" 的日誌

**預期行為**: API 應該只在收集時間範圍內（加上緩衝時間）被呼叫

## 可能原因分析

### 1. 舊的配置沒有 schedule 資料

**位置**: `coordinator.py:87-88`
```python
# If no schedule info (old configs), always update for backward compatibility
if not self._schedule_weekdays:
    return True
```

**問題**:
- 如果整合是在 schedule 功能加入**之前**安裝的，`entry.data` 中不會有 `CONF_SCHEDULE_WEEKDAYS`
- `self._schedule_weekdays` 會是空列表 `[]`
- 空列表會被判斷為 False，導致 `_should_update_now()` 總是返回 `True`

**驗證方法**:
檢查 Home Assistant 的 `.storage/core.config_entries` 文件，找到 `trash_tracking` 的 entry，查看是否有以下欄位：
```json
{
  "data": {
    "schedule_weekdays": [1, 3, 5],  // ← 這個欄位是否存在？
    "schedule_time_start": "18:00",
    "schedule_time_end": "19:00"
  }
}
```

### 2. Weekday 格式轉換錯誤

**位置**: `coordinator.py:92-97`
```python
# Python: 0=Monday, 6=Sunday
# API: 0=Sunday, 1=Monday, ..., 6=Saturday
# Convert Python weekday to API format
python_weekday = now.weekday()  # 0-6 (Mon-Sun)
api_weekday = python_weekday + 1 if python_weekday < 6 else 0  # Convert to API format
```

**潛在問題**:
Python 的 `weekday()` 返回：
- 0 = 週一 (Monday)
- 1 = 週二 (Tuesday)
- ...
- 6 = 週日 (Sunday)

轉換後的 `api_weekday`：
- 週一: `0 + 1 = 1` ✓
- 週二: `1 + 1 = 2` ✓
- ...
- 週日: `6 → 0` ✓

**驗證**:
如果今天是週一 (2025-11-24)，`api_weekday` 應該是 `1`。
如果你的配置中 `schedule_weekdays` 不包含 `1`，應該會跳過 API 呼叫。

### 3. 時間範圍檢查邏輯錯誤

**位置**: `coordinator.py:125`
```python
if not (start_with_buffer <= current_time <= end_with_buffer):
    # Skip API call
    return False
```

**潛在問題**:
如果開始時間晚於結束時間（跨午夜），例如：
- `start_time = "23:00"`
- `end_time = "01:00"`

這個邏輯會失效，因為 `23:00 <= 00:07 <= 01:00` 會返回 False。

### 4. 多路線配置問題

**問題**: 如果你加入了**多個路線**（每個路線一個 entry），每個路線都有各自的 schedule。

**驗證**:
- 檢查是否有多個 `trash_tracking` integration entries
- 某個路線可能是早上收集的，而你看到的 log 來自那個路線

## 診斷步驟

### Step 1: 檢查 Home Assistant 日誌

在 Home Assistant 中啟用 debug logging：

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.trash_tracking: debug
```

重啟後查看日誌，應該會看到以下訊息之一：

**情況 A: 沒有 schedule 資料**
```
[custom_components.trash_tracking] Today (Monday, weekday=1) not in schedule [], skipping API call
```
→ 表示 `schedule_weekdays` 是空的

**情況 B: 不在收集日**
```
[custom_components.trash_tracking] Today (Monday, weekday=1) not in schedule [3, 5], skipping API call
```
→ 表示週一不在收集日中

**情況 C: 不在時間範圍內**
```
[custom_components.trash_tracking] Current time 00:07 not in schedule range 11:30-19:30 (with 30 min buffer), skipping API call
```
→ 表示現在不在收集時間內

**情況 D: 在 schedule 內**
```
[custom_components.trash_tracking] Within schedule, proceeding with API call
[custom_components.trash_tracking] Successfully queried NTPC API
```
→ 表示邏輯認為現在應該呼叫 API

### Step 2: 檢查配置資料

方法 1 - 透過 Home Assistant UI：
1. 進入 Settings → Devices & Services
2. 找到 Trash Tracking
3. 點擊 "配置的條目" 數量
4. 記錄每個路線的名稱和配置

方法 2 - 檢查 storage 文件：
```bash
# 在 Home Assistant 容器或主機上執行
cat /config/.storage/core.config_entries | jq '.data.entries[] | select(.domain=="trash_tracking")'
```

### Step 3: 重新配置整合

如果是舊配置沒有 schedule 資料的問題：

1. 刪除現有的 Trash Tracking 整合
2. 重新加入整合
3. Schedule 資料會在配置時自動提取

## 修復建議

### 選項 1: 遷移工具 (推薦)

創建一個遷移腳本，在 `__init__.py` 中檢查並更新舊的 config entries：

```python
async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry to new format."""
    if entry.version == 1:
        # Check if schedule fields exist
        if CONF_SCHEDULE_WEEKDAYS not in entry.data:
            # Need to re-query API to get schedule info
            # ... fetch route and extract schedule

            new_data = {**entry.data}
            new_data[CONF_SCHEDULE_WEEKDAYS] = extracted_weekdays
            new_data[CONF_SCHEDULE_TIME_START] = extracted_start
            new_data[CONF_SCHEDULE_TIME_END] = extracted_end

            hass.config_entries.async_update_entry(entry, data=new_data)

        return True

    return False
```

### 選項 2: 改進向後兼容邏輯

修改 `coordinator.py` 中的邏輯：

```python
def _should_update_now(self) -> bool:
    """Check if we should update now based on schedule."""
    # If no schedule info (old configs), log a warning
    if not self._schedule_weekdays:
        _LOGGER.warning(
            "No schedule information found in config. "
            "Consider re-adding this integration to enable schedule-based polling. "
            "API will be called every %d seconds.",
            DEFAULT_SCAN_INTERVAL
        )
        return True  # Backward compatibility

    # ... rest of the logic
```

### 選項 3: 提供手動配置選項

在 config flow 中添加 "advanced options" 讓用戶手動設定 schedule（適用於 API 資料不準確的情況）。

## 臨時解決方案

如果需要立即停止非時間內的 API 呼叫：

1. **刪除並重新加入整合** - 最簡單的方法
2. **手動編輯 config_entries** - 需要停止 HA，編輯 `.storage/core.config_entries`，添加 schedule 欄位
3. **禁用整合** - 在非收集時間禁用整合

## 測試清單

- [ ] 檢查 HA 日誌中的 debug 訊息
- [ ] 確認 config_entries 中是否有 `schedule_weekdays` 欄位
- [ ] 確認 schedule 的 weekday 格式是否正確 (0=Sunday, 1-6=Monday-Saturday)
- [ ] 確認時間範圍是否正確
- [ ] 測試跨午夜的時間範圍
- [ ] 確認是否有多個路線配置

## 相關代碼位置

- **Schedule 提取邏輯**: `custom_components/trash_tracking/config_flow.py:42-75`
- **Schedule 檢查邏輯**: `custom_components/trash_tracking/coordinator.py:79-141`
- **Weekday 轉換**: `custom_components/trash_tracking/coordinator.py:92-97`
- **時間範圍檢查**: `custom_components/trash_tracking/coordinator.py:109-133`

## 下一步

1. 請檢查 Home Assistant 的 debug 日誌，確認是哪種情況
2. 根據日誌輸出來定位問題根源
3. 根據分析結果選擇適當的修復方案
