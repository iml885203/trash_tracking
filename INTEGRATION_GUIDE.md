# 垃圾車追蹤 Integration 實作指南

本文件說明如何將垃圾車追蹤系統從 Add-on 模式擴展為 Add-on + Integration 混合模式。

---

## 📊 專案架構概覽

### 目前架構 (Add-on Only)

```
用戶 → Add-on Setup Wizard (配置)
     → Add-on REST API
     → RESTful Sensor (手動配置在 configuration.yaml)
     → 自動化
```

### 新架構 (Add-on + Integration)

```
用戶 → Add-on Setup Wizard (配置) ─┐
                                   │
     Add-on REST API ←─────────────┤
          ↓                        │
     ┌────────────┬─────────────┐  │
     │            │             │  │
     ↓            ↓             ↓  ↓
 RESTful    Integration    CLI Tool
 Sensor     (新增)         (保留)
 (保留)        │
              ↓
         原生 HA 實體
              ↓
           自動化
```

**關鍵特點:**
- ✅ Add-on 功能完全保留 (Setup Wizard, API, CLI)
- ✅ Integration 作為可選的增強功能
- ✅ 用戶可選擇使用 RESTful Sensor 或 Integration
- ✅ 兩種方式可以共存

---

## 📁 目錄結構

```
trash_tracking/
├── custom_components/trash_tracking/  # 新增: Integration
│   ├── __init__.py                   # Integration 初始化
│   ├── manifest.json                 # Integration 宣告
│   ├── const.py                      # 常數定義
│   ├── config_flow.py                # 設定流程
│   ├── coordinator.py                # 資料協調器
│   ├── sensor.py                     # 感測器實體
│   ├── binary_sensor.py              # 二元感測器
│   ├── strings.json                  # 翻譯字串
│   ├── translations/                 # 多語言翻譯
│   │   ├── en.json
│   │   └── zh-Hant.json
│   └── README.md                     # Integration 使用說明
│
├── features/                         # 新增: Integration BDD 測試
│   ├── integration_config_flow.feature
│   ├── integration_entities.feature
│   └── integration_addon_coexistence.feature
│
├── src/                              # 現有: Add-on 核心程式碼 (保持不變)
│   ├── api/
│   ├── core/
│   ├── models/
│   └── utils/
│
├── app.py                            # 現有: Flask 應用
├── cli.py                            # 現有: CLI 工具
├── config.yaml                       # 現有: Add-on 配置
└── ...
```

---

## 🔄 資料流程

### 1. Add-on 作為資料源

```python
# Add-on (Flask) 提供 REST API
@app.route("/api/trash/status", methods=["GET"])
def get_status():
    status = tracker.get_current_status()
    return jsonify(status), 200
```

**回應格式:**
```json
{
  "status": "nearby",
  "reason": "垃圾車接近進入點: 中山路一段30號",
  "truck": {
    "line_name": "A12路線晚上",
    "car_no": "KES-6950",
    "current_rank": 10,
    "total_points": 69,
    "enter_point": {...},
    "exit_point": {...}
  },
  "timestamp": "2025-11-22T20:00:00+08:00"
}
```

### 2. Integration 消費 API

```python
# custom_components/trash_tracking/coordinator.py
class TrashTrackingCoordinator:
    async def _async_update_data(self):
        # 每 90 秒輪詢一次 Add-on API
        url = f"{self.api_url}/api/trash/status"
        async with self.session.get(url) as response:
            return await response.json()
```

### 3. Integration 建立實體

```python
# custom_components/trash_tracking/sensor.py
class TrashTrackingStatusSensor:
    @property
    def state(self):
        return self.coordinator.data.get("status")  # "nearby" or "idle"

    @property
    def extra_state_attributes(self):
        # 從 API 回應提取所有有用資訊
        return {...}
```

---

## ⚙️ Integration 核心組件說明

### 1. `manifest.json` - Integration 宣告

```json
{
  "domain": "trash_tracking",
  "name": "Trash Tracking",
  "config_flow": true,
  "iot_class": "local_polling",
  "version": "1.0.0"
}
```

**關鍵欄位:**
- `config_flow: true` - 啟用 UI 設定
- `iot_class: local_polling` - 本地輪詢模式
- `requirements: []` - 無額外依賴 (使用 aiohttp 內建)

### 2. `config_flow.py` - 設定流程

**Step 1: 輸入 API URL**
```python
async def async_step_user(self, user_input):
    # 驗證 API 連接
    await validate_api_connection(self.hass, user_input[CONF_API_URL])

    # 防止重複新增
    await self.async_set_unique_id(user_input[CONF_API_URL])

    # 建立 entry
    return self.async_create_entry(title="Trash Tracking", data=user_input)
```

**Options Flow (調整設定)**
```python
class TrashTrackingOptionsFlowHandler:
    async def async_step_init(self, user_input):
        # 允許用戶修改掃描間隔
        return self.async_show_form(...)
```

### 3. `coordinator.py` - 資料更新協調器

```python
class TrashTrackingCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_url, scan_interval):
        super().__init__(
            hass,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        # 從 Add-on API 獲取資料
        # 處理錯誤和重試
        # 返回資料給所有實體
```

**優勢:**
- 集中管理資料更新
- 自動錯誤處理和重試
- 多個實體共用同一個資料源

### 4. `sensor.py` + `binary_sensor.py` - 實體

**實體架構:**
```python
class TrashTrackingStatusSensor(CoordinatorEntity, SensorEntity):
    # CoordinatorEntity: 自動監聽 coordinator 更新
    # SensorEntity: Home Assistant 感測器基類

    @property
    def state(self):
        # 從 coordinator.data 讀取狀態
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self):
        # 提供額外屬性 (路線名稱、車牌等)
        return {...}
```

---

## 🧪 測試策略

### BDD Feature 檔案

已建立 3 個 feature 檔案:

1. **`integration_config_flow.feature`** (80+ 場景)
   - 基本安裝流程
   - 多步驟智能設定
   - Options Flow
   - 錯誤處理

2. **`integration_entities.feature`** (40+ 場景)
   - 實體建立
   - 資料更新
   - 自動化整合
   - 效能測試

3. **`integration_addon_coexistence.feature`** (30+ 場景)
   - Add-on 功能保留
   - 資料一致性
   - 共存測試
   - 移轉路徑

### 執行測試

```bash
# 安裝測試依賴
pip install -r requirements-dev.txt

# 執行 BDD 測試
behave features/integration_*.feature

# 執行特定場景
behave features/integration_config_flow.feature:12  # 第 12 行的場景
```

---

## 📦 安裝和部署

### 開發環境測試

```bash
# 1. 複製 Integration 到 Home Assistant
cp -r custom_components/trash_tracking /config/custom_components/

# 2. 重啟 Home Assistant
ha core restart

# 3. 檢查日誌
tail -f /config/home-assistant.log | grep trash_tracking
```

### 生產部署

**選項 A: 手動安裝**
- 用戶手動複製檔案到 `custom_components/`

**選項 B: HACS**
1. 建立 `hacs.json`:
```json
{
  "name": "Trash Tracking",
  "render_readme": true,
  "domains": ["sensor", "binary_sensor"]
}
```

2. 提交到 HACS default repository

**選項 C: GitHub Release**
- 打包為 zip 檔案
- 建立 GitHub Release
- 用戶透過 HACS 自訂 repository 安裝

---

## 🔧 維護和更新

### 版本管理

```
Add-on Version: 2025.11.6
Integration Version: 1.0.0
```

**相容性:**
- Integration 需要 Add-on >= 2025.11.0
- API 介面需要保持向後相容

### API 變更處理

如果 Add-on 的 API 格式變更:

```python
# coordinator.py 中增加版本檢查
async def _async_update_data(self):
    data = await response.json()

    # 檢查 API 版本
    if "version" in data and data["version"] < "2.0":
        _LOGGER.warning("Add-on API version is outdated")

    return data
```

### 日誌和除錯

```python
# 在所有關鍵點加入日誌
_LOGGER.debug("Fetching data from: %s", url)
_LOGGER.info("Integration setup complete")
_LOGGER.error("API returned status %s", response.status)
```

用戶可在 Home Assistant 中設定日誌級別:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.trash_tracking: debug
```

---

## 📊 效能考量

### 資源使用

**Add-on:**
- CPU: ~2-5% (追蹤邏輯)
- Memory: ~50 MB
- Network: 每 90 秒呼叫一次 NTPC API

**Integration:**
- CPU: <1% (只是輪詢本地 API)
- Memory: ~10 MB
- Network: 每 90 秒呼叫一次 Add-on API (本地)

**總計:** 對系統影響極小

### 優化建議

1. **掃描間隔:** 預設 90 秒已是最佳值
2. **快取:** Add-on 可考慮加入快取機制
3. **並發:** coordinator 自動處理多實體共用資料

---

## 🎯 使用者選擇矩陣

| 使用者類型 | 推薦方式 | 原因 |
|----------|---------|-----|
| 技術新手 | **Integration** | UI 設定,自動化更簡單 |
| 進階使用者 | **Integration** | 更好的整合體驗 |
| 偏好 YAML | RESTful Sensor | 完全控制配置 |
| 多點追蹤 | **Integration** | 支援多實例 |
| 需要自訂 | RESTful Sensor + Template | 完全彈性 |

**兩種方式可以共存** - 用戶可以同時保留 RESTful Sensor 和 Integration!

---

## ✅ 完成檢查清單

### Integration 功能

- [x] manifest.json
- [x] __init__.py (setup/unload)
- [x] const.py
- [x] config_flow.py (basic + options)
- [x] coordinator.py
- [x] sensor.py (2 個 sensor)
- [x] binary_sensor.py (1 個 binary_sensor)
- [x] strings.json
- [x] translations/ (en + zh-Hant)
- [x] README.md

### 測試

- [x] BDD feature 檔案 (3 個)
- [ ] Unit tests (可選)
- [ ] Integration tests (可選)

### 文件

- [x] Integration README
- [x] 實作指南 (本檔案)
- [ ] 更新主 README (說明 Integration 選項)
- [ ] CHANGELOG

### 發布

- [ ] 測試 Integration 功能
- [ ] 建立 GitHub Release
- [ ] 提交到 HACS
- [ ] 更新文件連結

---

## 🚀 下一步

1. **測試 Integration**
   ```bash
   # 在開發環境測試所有功能
   - 安裝 Integration
   - 驗證實體建立
   - 測試自動化
   - 檢查錯誤處理
   ```

2. **撰寫使用者文件**
   - 更新主 README
   - 新增 Integration 安裝教學
   - 提供移轉指南

3. **發布版本**
   - 打 tag: `integration-v1.0.0`
   - 建立 Release
   - 宣傳新功能

---

## 💡 常見問題

### Q: Integration 和 Add-on 的關係?
A: Integration 是 Add-on 的"前端",負責將 API 資料轉換為 HA 實體。Add-on 仍是核心,提供所有追蹤邏輯和配置介面。

### Q: 必須兩個都安裝嗎?
A: 必須先安裝 Add-on。Integration 是可選的,提供更好的整合體驗。

### Q: 會不會增加系統負擔?
A: 幾乎不會。Integration 只是輪詢本地 API,資源消耗極小。

### Q: 可以只用 Integration 不用 Add-on 嗎?
A: 不行。Integration 需要 Add-on 提供的 API。但未來可以考慮將所有邏輯移到 Integration。

### Q: 如何從 RESTful Sensor 移轉?
A: 參考 Integration README 的移轉章節。兩者可以共存,逐步移轉自動化即可。

---

## 📞 支援

- GitHub Issues: https://github.com/iml885203/trash_tracking/issues
- Discussions: https://github.com/iml885203/trash_tracking/discussions

---

**建立日期:** 2025-11-22
**作者:** @iml885203
**版本:** 1.0.0
