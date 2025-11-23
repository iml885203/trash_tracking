# 排程優化實作計畫

## 🎯 目標
根據垃圾車路線的實際運行時間表（星期幾、時間範圍），智慧決定何時呼叫 API，避免在垃圾車不會來的時段浪費 API 呼叫。

## 📊 預期效益
- **API 呼叫減少 ~94%**（從每天 960 次 → 每週 420 次）
- 電池省電（對於使用行動裝置運行 HA 的使用者）
- 減少 NTPC API 伺服器負擔

## 📋 實作任務清單

### 1. ✅ 在 const.py 新增排程相關常數
**檔案**: `custom_components/trash_tracking/const.py`

新增常數：
- `CONF_SCHEDULE_WEEKDAYS` - 星期幾列表
- `CONF_SCHEDULE_TIME_START` - 最早收集時間
- `CONF_SCHEDULE_TIME_END` - 最晚收集時間
- `SCHEDULE_BUFFER_MINUTES` - 時間 buffer（預設 30 分鐘）

### 2. ✅ 在 Point model 新增解析 weekday 的輔助方法
**檔案**: `packages/core/trash_tracking_core/models/point.py`

新增方法：
```python
def get_weekdays(self) -> list[int]:
    """解析 point_weekknd 欄位，返回星期幾列表"""
    # "1,3,5" -> [1, 3, 5]
```

### 3. ✅ 在 config_flow.py 實作排程資訊擷取邏輯
**檔案**: `custom_components/trash_tracking/config_flow.py`

新增函式：
```python
def _extract_schedule(self, route_recommendation) -> dict:
    """從路線推薦中提取排程資訊"""
    # 收集所有 points 的 weekday 和 time
    # 返回 {weekdays: [...], time_start: "...", time_end: "..."}
```

在 `async_step_points()` 完成時儲存排程資訊到 `entry.data`

### 4. ✅ 在 coordinator.py 實作智慧更新檢查邏輯
**檔案**: `custom_components/trash_tracking/coordinator.py`

新增方法：
```python
def _should_update_now(self) -> bool:
    """根據排程判斷現在是否應該呼叫 API"""
    # 檢查星期幾
    # 檢查時間範圍（含 buffer）
```

修改 `_async_update_data()` 在開頭檢查：
```python
if not self._should_update_now():
    return idle_state_without_api_call
```

### 5. ✅ 同步更新到 HA integration 的 embedded core
**檔案**: `custom_components/trash_tracking/trash_tracking_core/`

使用 `cp` 或 `rsync` 同步修改過的 core 檔案

### 6. ✅ 撰寫排程功能的單元測試
**檔案**: `tests/test_schedule_optimization.py`

測試項目：
- Point.get_weekdays() 正常解析
- _extract_schedule() 正確提取資訊
- _should_update_now() 各種情境：
  - 在排程內 → True
  - 不在星期幾內 → False
  - 不在時間範圍內 → False
  - 沒有排程資訊 → True（向後相容）
  - 邊界情況（buffer 邊緣）

### 7. ✅ 撰寫 BDD 測試場景
**檔案**: `features/schedule_optimization.feature`

場景：
- 設定時發現路線只在特定日期運行
- 在排程時段內正常更新
- 在排程時段外跳過 API 呼叫
- 沒有排程資訊時正常運作（向後相容）

### 8. ✅ 更新文檔說明排程優化功能
**檔案**:
- `docs/SCHEDULE_OPTIMIZATION.md` - 新增排程優化文檔
- `README.md` - 更新 Features 章節提及排程優化
- `CLAUDE.md` - 更新專案說明

### 9. ✅ 執行完整測試確保 CI 通過並清理 legacy
**任務**：
- 執行所有單元測試：`pytest tests/ -v`
- 執行所有 BDD 測試：`behave features/`
- 執行 code quality 檢查：`flake8`, `black`, `isort`, `mypy`
- 確認沒有 legacy code 或文檔遺留
- **刪除此計畫檔案** (`SCHEDULE_OPTIMIZATION_PLAN.md`)

## 🔍 技術細節

### 星期幾對應
- **API 格式**: `"1,3,5"` (1=Monday, 7=Sunday, 0=Sunday alternative)
- **Python weekday()**: 0=Monday, 6=Sunday
- **轉換公式**: `python_weekday + 1`, Sunday 特殊處理

### 時間範圍處理
- 從所有 collection points 找出最早和最晚時間
- 加上前後 30 分鐘 buffer
- 跨日情況需要特殊處理（如 23:00-01:00）

### 向後相容
- 如果 `CONF_SCHEDULE_WEEKDAYS` 不存在 → 總是更新（舊設定）
- 如果無法解析排程資訊 → 總是更新（安全回退）

## 📝 提交訊息範本

```
feat: add intelligent schedule-based API polling

Optimize API calls by only polling during scheduled truck operation times.
Reduces API calls by ~94% based on actual route schedules.

- Add schedule extraction from route data (weekdays + time range)
- Implement smart update check in coordinator
- Add 30-minute buffer before/after scheduled time
- Maintain backward compatibility for existing configs
- Add comprehensive tests for schedule logic

Benefits:
- Weekly API calls reduced from ~6,720 to ~420 for typical route
- Better battery life for mobile HA instances
- Reduced load on NTPC API servers
```

## ⚠️ 注意事項

1. **測試覆蓋率**: 確保所有邊界情況都有測試
2. **Log 訊息**: 清楚記錄為何跳過更新（方便除錯）
3. **文檔完整**: 讓使用者了解排程優化如何運作
4. **向後相容**: 現有設定必須能正常運作

## 🎉 完成標準

- [ ] 所有單元測試通過
- [ ] 所有 BDD 測試通過
- [ ] CI pipeline 全綠
- [ ] 文檔更新完成
- [ ] 無 legacy code 遺留
- [ ] **刪除此計畫檔案**
