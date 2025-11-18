# Home Assistant 部署完整指南

本指南將協助你完整部署垃圾車追蹤系統到 Home Assistant，並設定自動化燈泡控制。

## 📋 目錄

1. [部署前準備](#部署前準備)
2. [步驟一：配置設定檔](#步驟一配置設定檔)
3. [步驟二：部署服務](#步驟二部署服務)
4. [步驟三：設定 Home Assistant 整合](#步驟三設定-home-assistant-整合)
5. [步驟四：測試與驗證](#步驟四測試與驗證)
6. [疑難排解](#疑難排解)

---

## 部署前準備

### 1. 確認系統需求

- ✅ Home Assistant 已安裝並運行
- ✅ Docker 和 Docker Compose 已安裝（或 Python 3.11+）
- ✅ 可以存取 Home Assistant 的 `configuration.yaml`

### 2. 確認網路連線

- HA 所在的主機可以連線到部署垃圾車追蹤服務的主機
- 預設 API 端口：`5000`

### 3. 取得必要資訊

準備好以下資訊：

| 項目 | 說明 | 範例 |
|------|------|------|
| 📍 **家裡座標** | 緯度、經度 | lat: 25.018269, lng: 121.471703 |
| 🚛 **垃圾車路線名稱** | 你要追蹤的路線 | "C08路線下午" |
| 📌 **進入清運點** | 垃圾車到達時開燈的點 | "民生路二段80號" |
| 📌 **離開清運點** | 垃圾車經過時關燈的點 | "成功路23號" |
| 💡 **燈泡 Entity ID** | HA 中的燈泡 | light.notification_bulb |

---

## 步驟一：配置設定檔

### 1.1 找到你家附近的垃圾車清運點

使用 CLI 工具查詢：

```bash
# 查詢你家座標附近的垃圾車
python3 cli.py --lat 你的緯度 --lng 你的經度 --radius 1000

# 範例
python3 cli.py --lat 25.018269 --lng 121.471703 --radius 1000
```

**輸出範例**：
```
🔍 查詢位置: (25.018269, 121.471703)
📏 查詢半徑: 1000 公尺

✅ 找到 3 台垃圾車

================================================================================
🚛 路線名稱: C08路線下午
   車號: KES-6950
   目前停靠點序號: 10/69

📍 接下來 10 個清運點:
   1. [⏳ 預定 14:00] 民生路二段80號        ← 可以用這個當進入點
   2. [⏳ 預定 14:05] 民生路二段100號
   3. [⏳ 預定 14:10] 成功路23號          ← 可以用這個當離開點
   ...
```

**重點**：
- 記下**完整的清運點名稱**（包括空格和符號）
- 確認離開點在進入點**之後**

### 1.2 編輯 config.yaml

編輯專案根目錄的 `config.yaml`：

```yaml
# 查詢位置（你家的座標）
location:
  lat: 25.018269          # 改成你家的緯度
  lng: 121.471703         # 改成你家的經度

# 垃圾車追蹤設定
tracking:
  # 指定追蹤的路線（可選，留空則追蹤所有路線）
  target_lines:
    - "C08路線下午"       # 改成你要追蹤的路線名稱，可以多條

  # 進入清運點（燈泡亮起）
  enter_point: "民生路二段80號"     # 改成你的進入點名稱

  # 離開清運點（燈泡關閉）
  exit_point: "成功路23號"          # 改成你的離開點名稱

  # 觸發模式
  # arriving: 提前通知（垃圾車即將到達時觸發）
  # arrived: 實際到達（垃圾車已經到達時觸發）
  trigger_mode: "arriving"

  # 提前通知停靠點數（arriving 模式才有效）
  # 2 表示垃圾車距離進入點前 2 個停靠點時觸發
  approaching_threshold: 2
```

**觸發模式選擇**：
- **arriving** (推薦)：提前通知，有時間準備垃圾
  - `approaching_threshold: 2` → 提前 2 個停靠點通知
  - `approaching_threshold: 3` → 提前 3 個停靠點通知
- **arrived**：垃圾車剛到達時才通知，比較緊急

---

## 步驟二：部署服務

### 選項 A：使用 Docker Compose（推薦）

#### 1. 確認 Docker 環境

```bash
docker --version
docker-compose --version
```

#### 2. 啟動服務

```bash
# 進入專案目錄
cd trash_tracking

# 啟動服務（背景執行）
docker-compose up -d

# 查看日誌
docker-compose logs -f trash_tracking
```

#### 3. 驗證服務運行

```bash
# 測試 API 端點
curl http://localhost:5000/health

# 應該回傳類似：
# {"status":"ok","timestamp":"2025-11-18T14:00:00+08:00","config":{...}}
```

#### 4. 查看即時狀態

```bash
# 查詢垃圾車狀態
curl http://localhost:5000/api/trash/status

# 回應範例（idle 狀態）：
# {
#   "status": "idle",
#   "reason": "無垃圾車在附近",
#   "truck": null,
#   "timestamp": "2025-11-18T14:00:00+08:00"
# }

# 回應範例（nearby 狀態）：
# {
#   "status": "nearby",
#   "reason": "垃圾車即將到達進入清運點: 民生路二段80號",
#   "truck": {
#     "line_name": "C08路線下午",
#     "car_no": "KES-6950",
#     ...
#   },
#   "timestamp": "2025-11-18T14:05:00+08:00"
# }
```

### 選項 B：直接使用 Python（不使用 Docker）

```bash
# 1. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 啟動服務
python3 app.py

# 服務會在 http://0.0.0.0:5000 啟動
```

---

## 步驟三：設定 Home Assistant 整合

### 3.1 編輯 configuration.yaml

找到 Home Assistant 的 `configuration.yaml`，通常在：
- Home Assistant OS: `/config/configuration.yaml`
- Docker: 你的 HA 資料目錄下

加入以下配置：

```yaml
# ==========================================
# 垃圾車追蹤系統整合
# ==========================================

# 1. RESTful Sensor - 查詢垃圾車狀態
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://你的服務IP:5000/api/trash/status"
    # 如果服務在同一台主機上，使用 localhost
    # 如果在不同主機，改成實際 IP，例如：http://192.168.1.100:5000/api/trash/status
    scan_interval: 90  # 每 90 秒查詢一次
    json_attributes:
      - reason
      - truck
      - timestamp
    value_template: "{{ value_json.status }}"

# 2. Binary Sensor - 判斷垃圾車是否在附近
binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "垃圾車在附近"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence
        icon_template: >-
          {% if is_state('sensor.garbage_truck_monitor', 'nearby') %}
            mdi:truck
          {% else %}
            mdi:truck-outline
          {% endif %}

# 3. Automation - 自動化規則
automation:
  # 垃圾車抵達 - 開啟通知燈
  - alias: "垃圾車抵達 - 開啟通知燈"
    description: "垃圾車即將到達時，自動開啟通知燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb  # 🔴 改成你的燈泡 entity_id
        data:
          brightness: 255
          color_name: "red"      # 紅色提示（如果燈泡支援顏色）
      # 可選：發送通知到手機
      - service: notify.mobile_app_你的手機名稱
        data:
          title: "🚛 垃圾車來了！"
          message: "垃圾車即將到達 {{ state_attr('sensor.garbage_truck_monitor', 'truck')['enter_point']['name'] }}"

  # 垃圾車離開 - 關閉通知燈
  - alias: "垃圾車離開 - 關閉通知燈"
    description: "垃圾車經過後，自動關閉通知燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb  # 🔴 改成你的燈泡 entity_id
      # 可選：發送通知
      - service: notify.mobile_app_你的手機名稱
        data:
          title: "✅ 垃圾車已離開"
          message: "通知燈已關閉"
```

**重要提示**：
1. **修改服務 URL**：
   - 如果服務和 HA 在同一台機器：`http://localhost:5000/api/trash/status`
   - 如果在不同機器：`http://192.168.x.x:5000/api/trash/status`

2. **修改燈泡 Entity ID**：
   - 在 HA 的開發者工具 → 狀態 中找到你的燈泡
   - 複製完整的 entity_id，例如：`light.bedroom_lamp`

### 3.2 檢查配置是否有效

```bash
# 在 HA 中檢查配置
# 開發者工具 → YAML → 檢查配置

# 或使用命令列
ha core check
```

### 3.3 重新載入 Home Assistant

```bash
# 方法 1: 在 HA UI 中
# 開發者工具 → YAML → 重新載入所有 YAML 配置

# 方法 2: 重啟 Home Assistant
ha core restart
```

---

## 步驟四：測試與驗證

### 4.1 檢查 Sensor 是否正常

1. 前往 **開發者工具** → **狀態**
2. 搜尋 `sensor.garbage_truck_monitor`
3. 應該會看到狀態為 `idle` 或 `nearby`

### 4.2 檢查 Binary Sensor

1. 搜尋 `binary_sensor.garbage_truck_nearby`
2. 狀態應該是 `on` 或 `off`

### 4.3 測試自動化

#### 方法 1：等待真實垃圾車到達

- 等待設定的時間，垃圾車接近時應該會自動觸發

#### 方法 2：手動觸發測試

```bash
# 1. 暫時修改 config.yaml 的 trigger_mode 為 arrived
# 2. 重啟服務
docker-compose restart

# 3. 使用 CLI 工具確認垃圾車位置
python3 cli.py --lat 你的緯度 --lng 你的經度

# 4. 觀察 HA 中的 sensor 狀態變化
```

#### 方法 3：使用 API 重置功能

```bash
# 重置追蹤器狀態
curl -X POST http://localhost:5000/api/reset

# 這會將狀態重置為 idle
```

### 4.4 檢查自動化觸發歷史

1. 前往 **設定** → **自動化與場景**
2. 找到 "垃圾車抵達" 自動化
3. 點擊查看觸發歷史

---

## 疑難排解

### 問題 1：Sensor 顯示 "unavailable"

**可能原因**：
- API 服務未啟動
- 網路無法連線

**解決方案**：
```bash
# 1. 檢查服務狀態
docker-compose ps

# 2. 查看服務日誌
docker-compose logs -f trash_tracking

# 3. 測試 API 連線
curl http://localhost:5000/health

# 4. 如果服務在不同主機，確認防火牆開放 5000 port
```

### 問題 2：狀態一直是 "idle"

**可能原因**：
- 清運點名稱不正確
- 垃圾車路線不在附近
- 座標設定錯誤

**解決方案**：
```bash
# 1. 使用 CLI 確認垃圾車位置
python3 cli.py --lat 你的緯度 --lng 你的經度 --debug

# 2. 檢查清運點名稱是否完全一致（包括空格）
# 3. 確認垃圾車路線有包含你設定的清運點

# 4. 查看服務日誌
docker-compose logs -f trash_tracking
```

### 問題 3：燈泡沒有自動開關

**可能原因**：
- 燈泡 entity_id 錯誤
- 自動化未啟用

**解決方案**：
```bash
# 1. 確認燈泡 entity_id
# 在 HA 開發者工具 → 狀態 中搜尋你的燈泡

# 2. 檢查自動化是否啟用
# 設定 → 自動化與場景 → 確認開關是開啟狀態

# 3. 手動測試自動化
# 設定 → 自動化與場景 → 點擊 "執行" 按鈕
```

### 問題 4：API 查詢失敗

**錯誤訊息**：`新北市 API 請求失敗`

**解決方案**：
```bash
# 1. 檢查網路連線
ping crd-rubbish.epd.ntpc.gov.tw

# 2. 增加重試次數（config.yaml）
api:
  ntpc:
    retry_count: 5
    retry_delay: 3

# 3. 重啟服務
docker-compose restart
```

### 問題 5：Docker 容器不斷重啟

**解決方案**：
```bash
# 查看錯誤日誌
docker-compose logs trash_tracking

# 常見問題：
# - config.yaml 格式錯誤 → 檢查 YAML 格式
# - Port 被占用 → 修改 docker-compose.yml 中的 port
```

---

## 進階配置

### 多個燈泡控制

```yaml
automation:
  - alias: "垃圾車抵達 - 多燈泡控制"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      # 客廳燈
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness: 255
          color_name: "red"
      # 臥室燈
      - service: light.turn_on
        target:
          entity_id: light.bedroom
        data:
          brightness: 200
          color_name: "orange"
```

### 語音通知

```yaml
automation:
  - alias: "垃圾車抵達 - 語音通知"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: tts.google_translate_say
        entity_id: media_player.google_home
        data:
          message: "垃圾車來了，請準備垃圾"
```

### 只在特定時間啟用

```yaml
automation:
  - alias: "垃圾車抵達 - 僅晚上通知"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    condition:
      # 只在晚上 6 點到 10 點之間通知
      - condition: time
        after: "18:00:00"
        before: "22:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb
        data:
          brightness: 255
          color_name: "red"
```

---

## 維護建議

### 日誌管理

```bash
# 查看日誌
docker-compose logs -f trash_tracking

# 清理舊日誌（logs 目錄會持續增長）
rm -rf logs/*.log.old
```

### 更新服務

```bash
# 1. 拉取最新程式碼
git pull

# 2. 重新建置並啟動
docker-compose up -d --build

# 3. 檢查狀態
docker-compose ps
```

### 備份配置

```bash
# 備份 config.yaml
cp config.yaml config.yaml.backup

# 備份 HA 配置
cp /config/configuration.yaml /config/configuration.yaml.backup
```

---

## 常見問題 FAQ

**Q1: 需要一直保持服務運行嗎？**
A: 是的，服務需要持續運行才能即時追蹤垃圾車。使用 Docker 的 `restart: unless-stopped` 可以確保服務自動重啟。

**Q2: 查詢頻率太高會不會被 API 封鎖？**
A: 預設 90 秒查詢一次是安全的頻率。不建議設定低於 30 秒。

**Q3: 可以追蹤多個地點嗎？**
A: 目前單一實例只能追蹤一個地點。如需追蹤多個地點，可以運行多個服務實例（修改 port）。

**Q4: 為什麼有時候會漏掉通知？**
A: 可能原因：
- 垃圾車提前或延後很多
- API 查詢時垃圾車剛好在兩個查詢之間經過
- 建議使用 `arriving` 模式並增加 `approaching_threshold`

---

## 需要協助？

- 📖 查看專案 README: [README.md](../README.md)
- 🐛 回報問題: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 討論區: [GitHub Discussions](https://github.com/your-repo/discussions)
