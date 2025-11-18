# Home Assistant Add-on: 垃圾車追蹤系統

![Logo](icon.png)

新北市垃圾車即時追蹤與 Home Assistant 自動化整合。

## 關於

這個 Add-on 會即時追蹤新北市垃圾車的位置，當垃圾車接近或經過你設定的清運點時，自動更新狀態供 Home Assistant 自動化使用。

## 功能特色

- ✅ 即時追蹤新北市垃圾車位置
- ✅ 自訂進入/離開清運點
- ✅ 支援多條路線追蹤
- ✅ 提供 RESTful API
- ✅ 自動整合到 Home Assistant
- ✅ 可透過 UI 配置，無需編輯 YAML

## 安裝

### 方法 1: 從本地安裝（開發/測試）

1. 前往 **Supervisor** → **Add-on Store** → 右上角三個點 → **Repositories**
2. 加入 repository URL（如果有的話）
3. 或者手動複製 `trash_tracking_addon` 資料夾到 `/addons/` 目錄

### 方法 2: 從 GitHub 安裝

1. 在 **Add-on Store** 中加入 repository:
   ```
   https://github.com/你的用戶名/trash_tracking
   ```
2. 重新整理頁面
3. 找到 "垃圾車追蹤系統" 並點擊安裝

## 配置

### 基本配置

在 Add-on 配置頁面中設定：

```yaml
location:
  lat: 25.018269          # 你家的緯度
  lng: 121.471703         # 你家的經度
tracking:
  target_lines:           # 要追蹤的路線（可留空追蹤全部）
    - "C08路線下午"
  enter_point: "民生路二段80號"    # 垃圾車到達時的清運點
  exit_point: "成功路23號"         # 垃圾車離開時的清運點
  trigger_mode: "arriving"          # arriving 或 arrived
  approaching_threshold: 2          # 提前幾個停靠點通知
system:
  log_level: "INFO"                 # DEBUG, INFO, WARNING, ERROR
api:
  ntpc:
    timeout: 10
    retry_count: 3
    retry_delay: 2
```

### 如何找到清運點名稱？

#### 使用內建 CLI 工具

1. 安裝並啟動 Add-on
2. 前往 **Supervisor** → **System** → **Terminal**
3. 執行：
   ```bash
   docker exec -it addon_trash_tracking python3 cli.py --lat 你的緯度 --lng 你的經度
   ```

#### 使用新北市官網

1. 前往 [新北市垃圾車即時動態](https://crd-rubbish.epd.ntpc.gov.tw/)
2. 輸入你的地址
3. 找到清運點的完整名稱

**重要**：清運點名稱必須與 API 回傳的完全一致（包括空格）

### 觸發模式說明

- **arriving**（推薦）: 提前通知
  - 垃圾車距離進入點前 N 個停靠點時觸發
  - N 由 `approaching_threshold` 設定
  - 例如設為 2，表示提前 2 個停靠點通知

- **arrived**: 實際到達通知
  - 垃圾車剛到達進入點時才觸發
  - 時間較緊急

## 使用方式

### 1. 啟動 Add-on

1. 安裝完成後，點擊 **START**
2. 檢查 **Log** 標籤，確認啟動成功
3. 應該會看到：
   ```
   [INFO] Starting Trash Tracking Add-on...
   [INFO] Starting Flask application...
   * Running on http://0.0.0.0:5000
   ```

### 2. 設定 Home Assistant Sensor

Add-on 啟動後，API 會在 `http://localhost:5000` 提供服務。

在 `configuration.yaml` 中加入：

```yaml
# RESTful Sensor
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://localhost:5000/api/trash/status"
    scan_interval: 90
    json_attributes:
      - reason
      - truck
      - timestamp
    value_template: "{{ value_json.status }}"

# Binary Sensor
binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "垃圾車在附近"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence
```

### 3. 建立自動化

```yaml
automation:
  # 垃圾車到達 - 開燈
  - alias: "垃圾車抵達通知"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          rgb_color: [255, 0, 0]

  # 垃圾車離開 - 關燈
  - alias: "垃圾車離開"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
```

## API 端點

### GET `/api/trash/status`

取得垃圾車狀態

**回應範例（idle）**：
```json
{
  "status": "idle",
  "reason": "無垃圾車在附近",
  "truck": null,
  "timestamp": "2025-11-18T14:00:00+08:00"
}
```

**回應範例（nearby）**：
```json
{
  "status": "nearby",
  "reason": "垃圾車即將到達進入清運點: 民生路二段80號",
  "truck": {
    "line_name": "C08路線下午",
    "car_no": "KES-6950",
    "current_rank": 10,
    "total_points": 69,
    "arrival_diff": -5,
    "enter_point": {...},
    "exit_point": {...}
  },
  "timestamp": "2025-11-18T14:05:00+08:00"
}
```

### GET `/health`

健康檢查

### POST `/api/reset`

重置追蹤器狀態（測試用）

## 疑難排解

### Add-on 無法啟動

1. 檢查 Log：
   - 前往 Add-on 頁面 → **Log** 標籤
   - 查看錯誤訊息

2. 常見問題：
   - **配置錯誤**：檢查 YAML 格式是否正確
   - **Port 衝突**：確認 5000 port 沒被其他服務占用
   - **網路問題**：確認可以連線到新北市 API

### Sensor 顯示 unavailable

1. 確認 Add-on 正在運行
2. 測試 API：
   ```bash
   curl http://localhost:5000/health
   ```
3. 檢查 `configuration.yaml` 中的 resource URL

### 狀態一直是 idle

1. 確認座標設定正確
2. 使用 CLI 工具確認附近有垃圾車：
   ```bash
   docker exec -it addon_trash_tracking python3 cli.py --lat 你的緯度 --lng 你的經度
   ```
3. 檢查清運點名稱是否完全一致
4. 確認垃圾車路線有包含你設定的清運點

### 檢視詳細日誌

將 log_level 設為 DEBUG：

```yaml
system:
  log_level: "DEBUG"
```

## 支援

- 📖 完整文檔：[GitHub Repository](https://github.com/你的用戶名/trash_tracking)
- 🐛 問題回報：[GitHub Issues](https://github.com/你的用戶名/trash_tracking/issues)
- 💬 討論區：[GitHub Discussions](https://github.com/你的用戶名/trash_tracking/discussions)

## 授權

MIT License

## 貢獻者

- Logan ([@iml885203](https://github.com/iml885203))

## 更新日誌

### 1.0.0
- 初始發布
- 支援新北市垃圾車追蹤
- Home Assistant 整合
- RESTful API
