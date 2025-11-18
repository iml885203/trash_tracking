# 垃圾車追蹤系統 - 完整文檔

## 📋 快速開始

### 1. 安裝 Add-on

1. 在 Home Assistant 中前往 **Supervisor** → **Add-on Store**
2. 右上角三個點 → **Repositories**
3. 加入：`https://github.com/iml885203/trash_tracking`
4. 找到 "垃圾車追蹤系統" 並安裝

### 2. 配置 Add-on

點擊 **Configuration** 標籤：

```yaml
location:
  lat: 25.018269          # 🔴 改成你家的緯度
  lng: 121.471703         # 🔴 改成你家的經度
tracking:
  target_lines: []        # 留空追蹤所有路線，或指定特定路線
  enter_point: "民生路二段80號"    # 🔴 改成你的進入點
  exit_point: "成功路23號"         # 🔴 改成你的離開點
  trigger_mode: "arriving"
  approaching_threshold: 2
```

### 3. 啟動 Add-on

點擊 **Start** 按鈕

### 4. 設定 Home Assistant

編輯 `configuration.yaml`：

```yaml
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

binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "垃圾車在附近"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence

automation:
  - alias: "垃圾車到達開燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb  # 🔴 改成你的燈泡
        data:
          brightness: 255
          rgb_color: [255, 0, 0]
```

重新載入設定：**開發者工具** → **YAML** → **重新載入所有 YAML**

## 🔍 如何找到清運點名稱

### 方法 1: 使用 Add-on 內建 CLI

1. 前往 **Supervisor** → **System** → **Terminal**
2. 執行：
```bash
docker exec -it $(docker ps | grep trash_tracking | awk '{print $1}') \
  python3 cli.py --lat 你的緯度 --lng 你的經度
```

範例輸出：
```
✅ 找到 3 台垃圾車

🚛 路線名稱: C08路線下午
   車號: KES-6950

📍 接下來 10 個清運點:
   1. [⏳ 預定 14:00] 民生路二段80號    ← 用這個當進入點
   2. [⏳ 預定 14:05] 民生路二段100號
   3. [⏳ 預定 14:10] 成功路23號        ← 用這個當離開點
```

### 方法 2: 使用新北市官網

訪問：https://crd-rubbish.epd.ntpc.gov.tw/

## ⚙️ 配置選項說明

### location（必填）

你家的 GPS 座標

- `lat`: 緯度（float）
- `lng`: 經度（float）

**如何取得座標**：
- Google Maps：右鍵點擊地圖 → 顯示座標
- 或使用手機 GPS 應用程式

### tracking（必填）

追蹤設定

- `target_lines`: 要追蹤的路線名稱列表
  - 留空 `[]` = 追蹤所有經過的路線
  - 指定路線 = 只追蹤特定路線
  - 範例：`["C08路線下午", "C15路線下午"]`

- `enter_point`: 進入清運點名稱（string）
  - 垃圾車到達此點時，狀態變為 `nearby`
  - 必須與 API 回傳的名稱完全一致

- `exit_point`: 離開清運點名稱（string）
  - 垃圾車經過此點後，狀態變為 `idle`
  - 必須在路線順序上位於 enter_point 之後

- `trigger_mode`: 觸發模式
  - `arriving`: 即將到達時觸發（推薦）
  - `arrived`: 已經到達時觸發

- `approaching_threshold`: 提前通知停靠點數（0-10）
  - 僅在 `trigger_mode: arriving` 時有效
  - 範例：設為 2 = 提前 2 個停靠點通知
  - 設為 0 = 剛好到達時通知

### system（可選）

系統設定

- `log_level`: 日誌等級
  - `DEBUG`: 詳細除錯訊息
  - `INFO`: 一般資訊（預設）
  - `WARNING`: 警告訊息
  - `ERROR`: 僅錯誤訊息

### api（可選）

API 設定

- `ntpc.timeout`: API 請求逾時時間（秒，5-30）
- `ntpc.retry_count`: 重試次數（1-10）
- `ntpc.retry_delay`: 重試延遲（秒，1-10）

## 🎯 使用範例

### 範例 1: 基本配置（單一路線）

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines:
    - "C08路線下午"
  enter_point: "民生路二段80號"
  exit_point: "成功路23號"
  trigger_mode: "arriving"
  approaching_threshold: 2
```

### 範例 2: 追蹤所有路線

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines: []  # 留空
  enter_point: "民生路二段80號"
  exit_point: "成功路23號"
  trigger_mode: "arriving"
  approaching_threshold: 3  # 提前 3 個停靠點
```

### 範例 3: 多路線追蹤

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines:
    - "C08路線下午"
    - "C15路線下午"
    - "C17路線下午"
  enter_point: "民生路二段80號"
  exit_point: "成功路23號"
  trigger_mode: "arriving"
  approaching_threshold: 2
```

### 範例 4: 實際到達模式

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines: []
  enter_point: "民生路二段80號"
  exit_point: "成功路23號"
  trigger_mode: "arrived"  # 實際到達才通知
  approaching_threshold: 0  # 此參數無效
```

## 🏠 Home Assistant 整合範例

### 完整自動化範例

```yaml
automation:
  # 1. 垃圾車到達 - 開啟通知燈
  - alias: "垃圾車到達 - 開燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      # 開啟紅色燈泡
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          rgb_color: [255, 0, 0]
      # 發送手機通知
      - service: notify.mobile_app_iphone
        data:
          title: "🚛 垃圾車來了！"
          message: "垃圾車即將到達，請準備垃圾"
          data:
            push:
              sound: "US-EN-Morgan-Freeman-Garbage-Truck.wav"

  # 2. 垃圾車離開 - 關閉通知燈
  - alias: "垃圾車離開 - 關燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
      - service: notify.mobile_app_iphone
        data:
          title: "✅ 垃圾車已離開"
          message: "通知燈已關閉"

  # 3. 只在晚上通知
  - alias: "垃圾車到達 - 僅晚上"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    condition:
      - condition: time
        after: "18:00:00"
        before: "22:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          rgb_color: [255, 0, 0]
```

### Lovelace 卡片範例

```yaml
type: entities
title: 垃圾車追蹤
entities:
  - entity: binary_sensor.garbage_truck_nearby
    name: 垃圾車狀態
  - entity: sensor.garbage_truck_monitor
    name: 詳細資訊
    type: attribute
    attribute: reason
```

## 🔧 疑難排解

### 問題 1: Add-on 無法啟動

**檢查步驟**：

1. 查看 Log：
```
Supervisor → Add-ons → 垃圾車追蹤系統 → Log
```

2. 常見錯誤：
```
Error: Invalid configuration
```
→ 檢查 YAML 格式，確認縮排正確

```
Error: Port 5000 already in use
```
→ 其他服務占用 5000 port，需要停止該服務

### 問題 2: Sensor 一直 unavailable

**解決方案**：

1. 確認 Add-on 正在運行：
```bash
# 在 Terminal add-on 中執行
docker ps | grep trash_tracking
```

2. 測試 API：
```bash
curl http://localhost:5000/health
```

3. 檢查 configuration.yaml 中的 URL 是否正確

### 問題 3: 狀態一直是 idle

**可能原因**：

1. 座標設定錯誤
2. 清運點名稱不正確
3. 垃圾車還沒到達

**檢查方式**：

```bash
# 查看附近是否有垃圾車
docker exec -it $(docker ps | grep trash_tracking | awk '{print $1}') \
  python3 cli.py --lat 你的緯度 --lng 你的經度 --debug
```

### 問題 4: 清運點名稱不確定

**解決方案**：

啟用 DEBUG 模式查看詳細資訊：

```yaml
system:
  log_level: "DEBUG"
```

然後查看 Add-on Log，會顯示所有找到的清運點。

## 📊 API 參考

### GET `/api/trash/status`

取得垃圾車狀態

**回應欄位**：
- `status`: `idle` 或 `nearby`
- `reason`: 狀態原因說明
- `truck`: 垃圾車資訊（僅 nearby 時）
- `timestamp`: 時間戳記

### GET `/health`

健康檢查

**回應**：
```json
{
  "status": "ok",
  "timestamp": "2025-11-18T14:00:00+08:00",
  "config": {
    "enter_point": "民生路二段80號",
    "exit_point": "成功路23號",
    "trigger_mode": "arriving"
  }
}
```

### POST `/api/reset`

重置追蹤器（測試用）

## 💡 進階技巧

### 使用條件判斷避免誤觸發

```yaml
automation:
  - alias: "垃圾車到達 - 智慧通知"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    condition:
      # 只在家時才通知
      - condition: state
        entity_id: person.logan
        state: 'home'
      # 只在晚餐時間
      - condition: time
        after: "18:00:00"
        before: "21:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
```

### 語音播報

```yaml
action:
  - service: tts.google_translate_say
    entity_id: media_player.google_home
    data:
      message: "垃圾車來了，請準備倒垃圾"
```

## 📱 支援

- GitHub: https://github.com/iml885203/trash_tracking
- Issues: https://github.com/iml885203/trash_tracking/issues
