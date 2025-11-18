# Home Assistant OS 部署指南

本指南專門針對 **Home Assistant OS** 環境的部署。

## 📋 前提條件

- ✅ Home Assistant OS 已安裝並運行
- ✅ 可以透過 SSH 連線到 HA OS（需要安裝 SSH & Web Terminal add-on）
- ✅ 可以編輯 HA 的 `configuration.yaml`

---

## 🚀 方案 A：在 HA OS 上運行 Docker 容器（推薦）

### 步驟 1：啟用 SSH 存取

#### 1.1 安裝 SSH Add-on

1. 在 Home Assistant 中前往：**設定** → **附加元件**
2. 搜尋並安裝 "**Terminal & SSH**" 或 "**Advanced SSH & Web Terminal**"
3. 啟動 Add-on
4. 如果使用 Advanced SSH，記得設定密碼或 SSH key

#### 1.2 透過 SSH 連線到 HA OS

```bash
# 方法 1: 使用 Web Terminal（直接在 HA UI 中）
# 在 Add-on 頁面點擊 "開啟 Web UI"

# 方法 2: 使用 SSH 客戶端
ssh root@你的HA_IP
# 或
ssh root@homeassistant.local
```

### 步驟 2：準備專案檔案

#### 2.1 連線到 HA OS 後，建立專案目錄

```bash
# 進入 config 目錄（這樣可以在 File Editor 中編輯）
cd /config

# 建立專案目錄
mkdir trash_tracking
cd trash_tracking
```

#### 2.2 建立必要檔案

**建立 `config.yaml`**：

```bash
cat > config.yaml << 'EOF'
# 垃圾車動態偵測系統 - 設定檔

# 系統設定
system:
  log_level: INFO
  cache_enabled: false
  cache_ttl: 60

# 查詢位置（你家的座標）
# 📍 請修改為你家的實際座標
location:
  lat: 25.018269          # 🔴 改成你的緯度
  lng: 121.471703         # 🔴 改成你的經度

# 垃圾車追蹤設定
tracking:
  # 指定追蹤的路線（留空則追蹤所有路線）
  target_lines: []
    # - "C08路線下午"      # 🔴 取消註解並改成你的路線名稱

  # 進入清運點（燈泡亮起）
  enter_point: "民生路二段80號"     # 🔴 改成你的進入點

  # 離開清運點（燈泡關閉）
  exit_point: "成功路23號"          # 🔴 改成你的離開點

  # 觸發模式
  trigger_mode: "arriving"

  # 提前通知停靠點數
  approaching_threshold: 2

# API 設定
api:
  ntpc:
    base_url: "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI"
    timeout: 10
    retry_count: 3
    retry_delay: 2

  server:
    host: "0.0.0.0"
    port: 5000
    debug: false
EOF
```

**建立 `docker-compose.yml`**：

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  trash_tracking:
    image: ghcr.io/你的用戶名/trash_tracking:latest  # 🔴 如果你有建立 image
    # 或者使用本地建置：
    # build: .
    container_name: trash_tracking
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Taipei
      - PYTHONUNBUFFERED=1
    network_mode: host  # 使用 host 網路模式，讓 HA 可以直接存取
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOF
```

### 步驟 3：下載專案程式碼

#### 方法 1：使用 Git（如果 HA OS 有安裝）

```bash
# 返回上一層
cd /config

# Clone 專案
git clone https://github.com/iml885203/trash_tracking.git trash_tracking_src

# 複製檔案
cp -r trash_tracking_src/* trash_tracking/
```

#### 方法 2：手動上傳檔案

1. 在你的電腦上 Clone 專案
2. 使用 **File Editor** add-on 或 **Samba Share** 上傳檔案到 `/config/trash_tracking/`

#### 方法 3：使用 curl 下載（如果專案有 release）

```bash
cd /config/trash_tracking

# 下載必要檔案
curl -O https://raw.githubusercontent.com/iml885203/trash_tracking/master/app.py
curl -O https://raw.githubusercontent.com/iml885203/trash_tracking/master/Dockerfile
# ... 下載其他檔案
```

### 步驟 4：建置並啟動容器

```bash
cd /config/trash_tracking

# 建置 Docker image
docker compose build

# 啟動服務
docker compose up -d

# 查看日誌
docker compose logs -f
```

**預期輸出**：
```
垃圾車動態偵測系統啟動
設定: ...
Flask 應用程式初始化完成
 * Running on http://0.0.0.0:5000
```

### 步驟 5：驗證服務運行

```bash
# 測試健康檢查
curl http://localhost:5000/health

# 測試狀態 API
curl http://localhost:5000/api/trash/status
```

---

## 🏠 設定 Home Assistant 整合

### 方法 1：編輯 configuration.yaml

在 HA 中前往：**設定** → **附加元件** → **File Editor**

編輯 `/config/configuration.yaml`，加入：

```yaml
# ==========================================
# 垃圾車追蹤系統
# ==========================================

# RESTful Sensor
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://localhost:5000/api/trash/status"  # HA OS 上使用 localhost
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
        icon_template: >-
          {% if is_state('sensor.garbage_truck_monitor', 'nearby') %}
            mdi:truck
          {% else %}
            mdi:truck-outline
          {% endif %}

# Automation
automation:
  # 垃圾車抵達 - 開燈
  - alias: "垃圾車抵達 - 開啟通知燈"
    description: "垃圾車即將到達時開燈"
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
          rgb_color: [255, 0, 0]  # 紅色

  # 垃圾車離開 - 關燈
  - alias: "垃圾車離開 - 關閉通知燈"
    description: "垃圾車經過後關燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb  # 🔴 改成你的燈泡
```

### 方法 2：使用 UI 配置（推薦新手）

#### 2.1 設定 RESTful Sensor

1. 前往：**設定** → **裝置與服務**
2. 點擊右下角 **+ 新增整合**
3. 搜尋 **RESTful**
4. 填入資訊：
   - **Resource**: `http://localhost:5000/api/trash/status`
   - **Name**: `Garbage Truck Monitor`
   - **Method**: GET
   - **Scan Interval**: 90

#### 2.2 建立 Template Binary Sensor

在 `configuration.yaml` 中加入：

```yaml
template:
  - binary_sensor:
      - name: "垃圾車在附近"
        state: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence
```

#### 2.3 建立自動化

1. 前往：**設定** → **自動化與場景**
2. 點擊 **+ 建立自動化**
3. 選擇 **從頭建立**

**垃圾車抵達自動化**：
- **觸發條件**：
  - 類型：狀態
  - 實體：`binary_sensor.garbage_truck_nearby`
  - 從：off
  - 到：on
- **動作**：
  - 類型：呼叫服務
  - 服務：`light.turn_on`
  - 目標：選擇你的燈泡
  - 資料：
    ```yaml
    brightness: 255
    rgb_color:
      - 255
      - 0
      - 0
    ```

**垃圾車離開自動化**：
- **觸發條件**：
  - 實體：`binary_sensor.garbage_truck_nearby`
  - 到：off
- **動作**：
  - 服務：`light.turn_off`
  - 目標：你的燈泡

### 重新載入設定

```
開發者工具 → YAML → 檢查配置 → 重新載入所有 YAML 配置
```

---

## 🔍 使用 CLI 工具找到清運點

在部署服務之前，先用 CLI 找到正確的清運點名稱：

### 方法 1：在 HA OS 上執行（如果有 Python）

```bash
# SSH 到 HA OS
cd /config/trash_tracking

# 查詢垃圾車
python3 cli.py --lat 你的緯度 --lng 你的經度
```

### 方法 2：在你的電腦上執行

```bash
# 在你的電腦上
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

python3 cli.py --lat 25.018269 --lng 121.471703 --radius 1000
```

**範例輸出**：
```
🔍 查詢位置: (25.018269, 121.471703)

✅ 找到 3 台垃圾車

================================================================================
🚛 路線名稱: C08路線下午
   車號: KES-6950
   目前停靠點序號: 10/69
   ✅ 提早狀態: 早 5 分鐘

📍 接下來 10 個清運點:
   1. [⏳ 預定 14:00 (預計 13:55, 早5分)] 民生路二段80號
   2. [⏳ 預定 14:05 (預計 14:00, 早5分)] 民生路二段100號
   3. [⏳ 預定 14:10 (預計 14:05, 早5分)] 成功路23號
   ...
```

**記下**：
- 路線名稱：`C08路線下午`
- 進入點：`民生路二段80號`
- 離開點：`成功路23號`

---

## 🧪 測試與驗證

### 1. 檢查 Docker 容器狀態

```bash
# SSH 到 HA OS
docker ps

# 應該看到 trash_tracking 容器在運行
```

### 2. 查看服務日誌

```bash
cd /config/trash_tracking
docker compose logs -f
```

### 3. 測試 API

```bash
curl http://localhost:5000/health
curl http://localhost:5000/api/trash/status
```

### 4. 在 HA 中檢查 Sensor

1. 前往：**開發者工具** → **狀態**
2. 搜尋：`sensor.garbage_truck_monitor`
3. 應該看到狀態為 `idle` 或 `nearby`

### 5. 測試自動化

**手動觸發**：
1. 前往：**設定** → **自動化與場景**
2. 找到你的自動化
3. 點擊 **執行** 測試

---

## 🔧 疑難排解

### 問題 1：Docker 命令找不到

HA OS 的 Docker 可能需要特殊路徑：

```bash
# 嘗試使用完整路徑
/usr/bin/docker ps

# 或建立別名
alias docker='/usr/bin/docker'
alias docker-compose='/usr/bin/docker-compose'
```

### 問題 2：Port 5000 被占用

```bash
# 檢查哪個服務占用 port 5000
netstat -tulpn | grep 5000

# 修改 docker-compose.yml 使用其他 port
ports:
  - "5001:5000"  # 外部用 5001，內部還是 5000

# 同時修改 HA configuration.yaml 中的 resource
resource: "http://localhost:5001/api/trash/status"
```

### 問題 3：無法連線到容器

```bash
# 確認網路模式
# 在 docker-compose.yml 中使用 host 模式
network_mode: host
```

### 問題 4：檔案權限問題

```bash
# 修正權限
chmod -R 755 /config/trash_tracking
chown -R root:root /config/trash_tracking
```

### 問題 5：容器不斷重啟

```bash
# 查看錯誤日誌
docker logs trash_tracking

# 常見原因：
# - config.yaml 格式錯誤
# - 缺少必要檔案
# - Python 套件安裝失敗
```

---

## 📱 進階功能

### 手機通知

在自動化中加入：

```yaml
action:
  - service: notify.mobile_app_你的手機
    data:
      title: "🚛 垃圾車來了！"
      message: >
        垃圾車即將到達
        {{ state_attr('sensor.garbage_truck_monitor', 'truck')['enter_point']['name'] }}
      data:
        priority: high
        ttl: 0
        notification_icon: "mdi:truck"
```

### 語音播報（Google Home）

```yaml
action:
  - service: tts.google_translate_say
    target:
      entity_id: media_player.google_home
    data:
      message: "垃圾車來了，請準備垃圾"
```

### 多條件觸發（只在晚上通知）

```yaml
automation:
  - alias: "垃圾車抵達 - 僅晚上通知"
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
```

---

## 🔄 維護與更新

### 更新服務

```bash
cd /config/trash_tracking

# 拉取最新程式碼
git pull

# 重新建置並啟動
docker compose down
docker compose build
docker compose up -d
```

### 查看日誌

```bash
# 即時日誌
docker compose logs -f

# 最近 100 行
docker compose logs --tail=100
```

### 備份設定

```bash
# 備份 config.yaml
cp /config/trash_tracking/config.yaml /config/backup/config.yaml.$(date +%Y%m%d)
```

---

## ✅ 快速設置檢查清單

- [ ] SSH add-on 已安裝並啟用
- [ ] 專案檔案已上傳到 `/config/trash_tracking/`
- [ ] `config.yaml` 已正確配置（座標、清運點名稱）
- [ ] Docker 容器成功啟動
- [ ] API 健康檢查通過 (`curl http://localhost:5000/health`)
- [ ] HA `configuration.yaml` 已加入 sensor 設定
- [ ] HA 配置已重新載入，無錯誤
- [ ] Sensor 在開發者工具中可見
- [ ] 自動化已建立並啟用
- [ ] 燈泡 entity_id 已正確設定
- [ ] 測試自動化可手動觸發

---

需要協助？查看主要文檔：[HOME_ASSISTANT_DEPLOYMENT.md](./HOME_ASSISTANT_DEPLOYMENT.md)
