# 垃圾車追蹤 Home Assistant Integration

這是垃圾車追蹤系統的 Home Assistant 原生整合元件,提供更好的整合體驗。

## 📋 概述

此 Integration 作為 [垃圾車追蹤 Add-on](https://github.com/iml885203/homeassistant-addons) 的前端介面,將 Add-on 提供的 REST API 轉換為 Home Assistant 原生實體。

### ✨ Integration 優勢

相較於使用 RESTful Sensor,Integration 提供:

- ✅ **原生實體**: 自動建立 sensor 和 binary_sensor
- ✅ **裝置整合**: 所有實體歸屬於同一個裝置
- ✅ **更簡潔的配置**: 不需要手動編寫 YAML
- ✅ **Options Flow**: 可在 UI 中調整設定
- ✅ **更好的錯誤處理**: 自動重連和狀態管理

### ⚠️ 前提條件

**必須先安裝並設定垃圾車追蹤 Add-on**,此 Integration 才能運作。

1. 安裝 [垃圾車追蹤 Add-on](https://github.com/iml885203/homeassistant-addons)
2. 使用 Add-on 的 Setup Wizard 完成配置
3. 確認 Add-on 正常運行 (可訪問 http://localhost:5000/health)
4. 然後安裝此 Integration

---

## 🚀 安裝方式

### 方法 1: HACS (推薦)

1. 在 HACS 中點擊 **Integrations**
2. 點擊右上角的 **⋮** → **Custom repositories**
3. 新增:
   - URL: `https://github.com/iml885203/trash_tracking`
   - Category: `Integration`
4. 搜尋 "Trash Tracking" 並安裝
5. 重啟 Home Assistant

### 方法 2: 手動安裝

```bash
cd /config
mkdir -p custom_components
cp -r trash_tracking custom_components/
```

重啟 Home Assistant

---

## ⚙️ 設定

### 步驟 1: 新增 Integration

1. 前往 **設定** → **裝置與服務**
2. 點擊 **+ 新增整合**
3. 搜尋 "**Trash Tracking**"
4. 輸入配置:
   - **API URL**: `http://localhost:5000` (預設值,如果 Add-on 在同一台機器)
   - **掃描間隔**: `90` 秒 (建議值)
5. 點擊 **提交**

### 步驟 2: 驗證實體

Integration 會自動建立以下實體:

```
sensor.trash_tracking_status          # 狀態: idle/nearby
sensor.trash_tracking_truck_info      # 垃圾車資訊
binary_sensor.trash_truck_nearby      # 垃圾車接近 (用於自動化)
```

---

## 📊 實體說明

### 1. `sensor.trash_tracking_status`

**狀態值:**
- `idle`: 無垃圾車在附近
- `nearby`: 垃圾車接近中

**屬性:**
```yaml
reason: "垃圾車接近進入點: 中山路一段30號"
line_name: "A12路線晚上"
car_no: "KES-6950"
current_rank: 10
total_points: 69
arrival_diff: -5
enter_point: "中山路一段30號"
exit_point: "中山路一段102號"
area: "板橋區"
current_location: "中山路一段20號"
```

### 2. `sensor.trash_tracking_truck_info`

**狀態值:** `A12路線晚上 (KES-6950)` 或 `無垃圾車`

**屬性:**
```yaml
路線名稱: "A12路線晚上"
車牌號碼: "KES-6950"
當前站點: 10
總站點數: 69
延遲時間: "早 5 分鐘"
進入點: "中山路一段30號"
進入點時間: "19:00"
離開點: "中山路一段102號"
離開點時間: "19:15"
```

### 3. `binary_sensor.trash_truck_nearby`

**狀態:**
- `on`: 垃圾車接近
- `off`: 無垃圾車

**用途:** 觸發自動化的最佳實體

---

## 🏠 使用範例

### 儀表板卡片

```yaml
type: entities
title: 垃圾車追蹤
entities:
  - entity: binary_sensor.trash_truck_nearby
    name: 垃圾車接近
  - entity: sensor.trash_tracking_status
    name: 追蹤狀態
  - entity: sensor.trash_tracking_truck_info
    name: 車輛資訊
```

### 自動化 - 垃圾車接近時開燈

```yaml
alias: "垃圾車接近 - 開燈提醒"
trigger:
  - platform: state
    entity_id: binary_sensor.trash_truck_nearby
    to: "on"
action:
  - service: light.turn_on
    target:
      entity_id: light.notification_bulb
    data:
      brightness: 255
      rgb_color: [255, 0, 0]
  - service: notify.mobile_app
    data:
      title: "垃圾車提醒"
      message: >
        垃圾車 {{ state_attr('sensor.trash_tracking_truck_info', '路線名稱') }}
        即將到達 {{ state_attr('sensor.trash_tracking_status', 'enter_point') }}
```

### 自動化 - 垃圾車離開時關燈

```yaml
alias: "垃圾車離開 - 關燈"
trigger:
  - platform: state
    entity_id: binary_sensor.trash_truck_nearby
    to: "off"
action:
  - service: light.turn_off
    target:
      entity_id: light.notification_bulb
```

### 條件自動化 - 僅在晚上觸發

```yaml
alias: "垃圾車接近 - 僅晚上提醒"
trigger:
  - platform: state
    entity_id: binary_sensor.trash_truck_nearby
    to: "on"
condition:
  - condition: time
    after: "17:00:00"
    before: "22:00:00"
action:
  - service: notify.mobile_app
    data:
      title: "記得倒垃圾!"
      message: "垃圾車 {{ state_attr('sensor.trash_tracking_status', 'line_name') }} 即將到達"
```

---

## 🔧 進階設定

### 調整掃描間隔

1. 前往 **設定** → **裝置與服務**
2. 找到 "Trash Tracking" Integration
3. 點擊 **設定選項**
4. 調整掃描間隔 (建議 60-120 秒)

### 多個追蹤點

如果你需要追蹤多個不同地點,可以:

1. 在不同的機器/容器上運行多個 Add-on 實例
2. 新增多個 Integration,每個連接到不同的 API URL

```
Integration 1 → http://localhost:5000 (家裡)
Integration 2 → http://192.168.1.100:5000 (辦公室)
```

---

## 🤝 與 Add-on 的關係

```
┌─────────────────────────────────────────┐
│   垃圾車追蹤 Add-on (資料源)              │
│                                          │
│  • Setup Wizard (配置介面)               │
│  • REST API (提供資料)                   │
│  • CLI Tool (命令列工具)                 │
│  • 追蹤邏輯 (核心功能)                   │
└──────────────┬──────────────────────────┘
               │ REST API
               │ (http://localhost:5000/api/trash/status)
               ↓
┌─────────────────────────────────────────┐
│   垃圾車追蹤 Integration (前端)          │
│                                          │
│  • 輪詢 Add-on API                       │
│  • 建立 HA 實體                          │
│  • 裝置整合                              │
│  • 更好的 UI 體驗                        │
└─────────────────────────────────────────┘
```

**重要提醒:**
- Integration 不會修改 Add-on 的行為
- 所有配置仍需在 Add-on 的 Setup Wizard 中完成
- Integration 只是讀取 API 資料並轉換為 HA 實體

---

## 📖 從 RESTful Sensor 移轉

如果你目前使用傳統的 RESTful sensor 配置:

```yaml
# 舊的配置 (configuration.yaml)
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://localhost:5000/api/trash/status"
    scan_interval: 90
```

移轉到 Integration:

1. 安裝此 Integration
2. 逐步更新自動化:
   - 將 `sensor.garbage_truck_monitor` 改為 `sensor.trash_tracking_status`
   - 將條件改為使用 `binary_sensor.trash_truck_nearby`
3. 確認所有自動化正常運作後
4. 從 `configuration.yaml` 移除 RESTful sensor 配置
5. 重啟 Home Assistant

**實體對照表:**

| 舊實體 (RESTful Sensor) | 新實體 (Integration) |
|------------------------|---------------------|
| `sensor.garbage_truck_monitor` | `sensor.trash_tracking_status` |
| `binary_sensor.garbage_truck_nearby` (手動建立) | `binary_sensor.trash_truck_nearby` (自動) |
| - | `sensor.trash_tracking_truck_info` (新增) |

---

## ❓ 故障排除

### Integration 顯示"不可用"

**檢查清單:**
1. 確認 Add-on 正在運行
2. 訪問 http://localhost:5000/health 檢查 API 健康狀態
3. 檢查 Integration 設定的 API URL 是否正確
4. 查看 Home Assistant 日誌

### 實體沒有更新

1. 檢查掃描間隔設定
2. 手動重新載入 Integration
3. 檢查 Add-on 是否有追蹤到垃圾車

### 無法連接到 API

```
錯誤: cannot_connect
```

**解決方法:**
1. 確認 Add-on 已啟動
2. 如果 Add-on 在不同機器,檢查防火牆設定
3. 嘗試在瀏覽器訪問 API URL

---

## 📝 版本歷史

### v1.0.0
- ✨ 初始版本
- ✅ 支援基本的 API 連接
- ✅ 建立 sensor 和 binary_sensor 實體
- ✅ Options Flow 支援

---

## 🙏 致謝

- 新北市環保局提供垃圾車 API
- Home Assistant 社群
- 所有貢獻者

---

## 📄 授權

MIT License

---

## 🔗 相關連結

- [垃圾車追蹤 Add-on](https://github.com/iml885203/homeassistant-addons)
- [主專案](https://github.com/iml885203/trash_tracking)
- [回報問題](https://github.com/iml885203/trash_tracking/issues)
