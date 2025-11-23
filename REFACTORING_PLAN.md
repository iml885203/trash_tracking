# 🔧 Refactoring Plan

**開始時間**: 2025-11-23
**目標**: 提升程式碼品質和可維護性

---

## 📊 當前狀態

- **Pylint**: 8.98/10
- **Flake8**: 0 errors
- **平均複雜度**: A (2.99)
- **測試覆蓋率**: 42.31%

---

## ✅ Phase 1: Quick Wins (快速修復)

### 1.1 修復日誌格式 (26 處)
**問題**: 使用 f-string 而非 lazy formatting，影響性能
**影響檔案**:
- [ ] `packages/core/trash_tracking_core/clients/ntpc_api.py` (8 處)
- [ ] `packages/core/trash_tracking_core/core/tracker.py` (5 處)
- [ ] `packages/core/trash_tracking_core/core/point_matcher.py` (6 處)
- [ ] `packages/core/trash_tracking_core/core/state_manager.py` (3 處)
- [ ] `packages/core/trash_tracking_core/utils/geocoding.py` (4 處)
- [ ] `packages/core/trash_tracking_core/utils/route_analyzer.py` (1 處)

**修復方式**:
```python
# Before
logger.info(f"找到 {len(routes)} 條路線")

# After
logger.info("找到 %d 條路線", len(routes))
```

**預期時間**: 30 分鐘

---

### 1.2 修復異常處理 (11 處)
**問題**: 缺少異常鏈 `from e`，導致丟失原始錯誤追蹤
**影響檔案**:
- [ ] `packages/core/trash_tracking_core/utils/geocoding.py` (2 處)
- [ ] `packages/core/trash_tracking_core/utils/config.py` (3 處)

**修復方式**:
```python
# Before
raise GeocodingError(f'地址查詢失敗: {e}')

# After
raise GeocodingError(f'地址查詢失敗: {e}') from e
```

**預期時間**: 15 分鐘

---

### 1.3 清理小問題
**問題列表**:
- [ ] 移除 3 處不必要的 `pass` 語句
  - `geocoding.py:13`
  - `config.py:13`
  - `ntpc_api.py:18`
- [ ] 修正變數名 `R` → `earth_radius_km` (`route_analyzer.py:57`)
- [ ] 移除不必要的括號 (`config.py:84,86`)
- [ ] 修復 reimport 問題
  - `geocoding.py:131` (re)
  - `state_manager.py:89` (Any, Dict)

**預期時間**: 20 分鐘

---

## 🎯 Phase 2: 測試覆蓋率提升 (未包含在此次重構)

**目標**: 42% → 80%+

重點模組:
- `tracker.py`: 17% → 80%
- `point_matcher.py`: 16% → 80%
- `state_manager.py`: 25% → 80%
- `config.py`: 26% → 80%

**預期時間**: 4-6 小時 (延後處理)

---

## 🔨 Phase 3: 重構高複雜度函數 (未包含在此次重構)

1. `geocoding.py::address_to_coordinates` (C11)
2. `config.py::_validate_config` (C14)
3. `ntpc_api.py::get_around_points` (C13)

**預期時間**: 3-4 小時 (延後處理)

---

## 📝 執行進度

### Phase 1: Quick Wins
- [ ] 1.1 修復日誌格式
- [ ] 1.2 修復異常處理
- [ ] 1.3 清理小問題
- [ ] 執行測試確認
- [ ] 提交變更

---

## 🎉 完成標準

- [x] Pylint 評分 ≥ 9.0
- [x] Flake8 零錯誤
- [x] 所有測試通過
- [x] 程式碼審查通過

---

**注意**: 此計劃完成後將被刪除
