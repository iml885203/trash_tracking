# 🚛 垃圾車動態偵測系統 (Trash Tracking)

新北市垃圾車即時追蹤與 Home Assistant 燈泡自動化控制系統。

## 📋 專案簡介

本系統透過呼叫新北市環保局的垃圾車 API，即時追蹤垃圾車位置，並根據使用者設定的「進入清運點」和「離開清運點」，自動觸發 Home Assistant 燈泡的開關。

### 主要功能

- ✅ 即時追蹤新北市垃圾車位置
- ✅ 自訂進入/離開清運點
- ✅ 支援多條路線追蹤
- ✅ 提供 RESTful API 供 Home Assistant 整合
- ✅ 支援 Docker 容器化部署
- ✅ 完整的日誌記錄

### 工作流程

```
垃圾車接近進入清運點 → API 狀態變更為 nearby → HA 自動化觸發 → 燈泡亮起 💡
垃圾車經過離開清運點 → API 狀態變更為 idle → HA 自動化觸發 → 燈泡關閉 🌑
```

---

## 🚀 快速開始

### 環境需求

- Python 3.11+
- Home Assistant (Optional)
- Docker & Docker Compose (Optional)

### 安裝步驟

#### 方法 1: 直接運行 (Python)

```bash
# 1. Clone 專案
git clone https://github.com/your-username/trash_tracking.git
cd trash_tracking

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 修改設定檔
cp config.yaml config.yaml
# 編輯 config.yaml，填入你的座標和清運點名稱

# 5. 啟動服務
python app.py
```

#### 方法 2: Docker Compose (推薦)

```bash
# 1. Clone 專案
git clone https://github.com/your-username/trash_tracking.git
cd trash_tracking

# 2. 修改設定檔
# 編輯 config.yaml

# 3. 啟動容器
docker-compose up -d

# 4. 查看日誌
docker-compose logs -f
```

---

## ⚙️ 設定檔說明

編輯 `config.yaml`：

```yaml
# 你家的座標
location:
  lat: 25.0138
  lng: 121.4627

# 追蹤設定
tracking:
  # 指定路線（留空則追蹤所有路線）
  target_lines:
    - "一區晚1"

  # 進入清運點名稱
  enter_point: "文化路一段188巷口"

  # 離開清運點名稱
  exit_point: "府中路29巷口"

  # 觸發模式: arriving (即將到達) 或 arrived (已到達)
  trigger_mode: "arriving"

  # 提前通知停靠點數
  approaching_threshold: 2
```

### 如何找到清運點名稱？

1. 前往[新北市垃圾車即時動態查詢網站](https://crd-rubbish.epd.ntpc.gov.tw/)
2. 輸入你家地址，查看附近的垃圾車路線
3. 找到你想追蹤的路線，記下清運點的名稱
4. 填入 `config.yaml` 的 `enter_point` 和 `exit_point`

**注意**：清運點名稱必須與 API 回傳的完全一致（包括空格和符號）

---

## 🔌 Home Assistant 整合

### Step 1: 確保系統運行

```bash
# 測試 API
curl http://localhost:5000/health
curl http://localhost:5000/api/trash/status
```

### Step 2: 編輯 Home Assistant 設定

在 `configuration.yaml` 中加入：

```yaml
# RESTful Sensor - 查詢垃圾車狀態
sensor:
  - platform: rest
    name: "Garbage Truck Monitor"
    resource: "http://localhost:5000/api/trash/status"
    scan_interval: 90  # 每 90 秒查詢一次
    json_attributes:
      - reason
      - truck
      - timestamp
    value_template: "{{ value_json.status }}"

# Binary Sensor - 判斷垃圾車是否在附近
binary_sensor:
  - platform: template
    sensors:
      garbage_truck_nearby:
        friendly_name: "垃圾車在附近"
        value_template: "{{ is_state('sensor.garbage_truck_monitor', 'nearby') }}"
        device_class: presence

# Automation - 自動化規則
automation:
  # 垃圾車抵達 - 開燈
  - alias: "垃圾車抵達 - 開啟通知燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb  # 改成你的燈泡 entity_id
        data:
          brightness: 255
          color_name: "red"

  # 垃圾車離開 - 關燈
  - alias: "垃圾車離開 - 關閉通知燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
```

### Step 3: 重新啟動 Home Assistant

```bash
# 檢查設定
ha core check

# 重新啟動
ha core restart
```

---

## 📡 API 端點

### GET `/api/trash/status`

取得垃圾車狀態

**回應範例 (nearby)**:
```json
{
  "status": "nearby",
  "reason": "垃圾車即將到達進入清運點: 文化路一段188巷口",
  "truck": {
    "line_name": "一區晚1",
    "car_no": "ABC-1234",
    "current_location": "新北市板橋區文化路一段150號",
    "enter_point": {
      "name": "文化路一段188巷口",
      "rank": 12,
      "arrival": "",
      "passed": false,
      "distance_to_current": 2
    }
  },
  "timestamp": "2025-11-17T21:30:00+08:00"
}
```

**回應範例 (idle)**:
```json
{
  "status": "idle",
  "reason": "無垃圾車在附近",
  "truck": null,
  "timestamp": "2025-11-17T21:30:00+08:00"
}
```

### GET `/health`

健康檢查

**回應**:
```json
{
  "status": "ok",
  "timestamp": "2025-11-17T21:30:00+08:00"
}
```

---

## 🐳 Docker 部署

### 使用 Docker Compose

```bash
# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f trash_tracking

# 停止服務
docker-compose down

# 重新啟動
docker-compose restart
```

### 手動 Docker 指令

```bash
# 建置映像
docker build -t trash_tracking .

# 運行容器
docker run -d \
  --name trash_tracking \
  -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  -e TZ=Asia/Taipei \
  trash_tracking

# 查看日誌
docker logs -f trash_tracking
```

---

## 📂 專案結構

```
trash_tracking/
├── app.py                      # 主程式進入點
├── config.yaml                 # 設定檔
├── requirements.txt            # Python 依賴
├── Dockerfile                  # Docker 映像定義
├── docker-compose.yml          # Docker Compose 設定
│
├── src/                        # 原始碼
│   ├── api/                    # API 層
│   │   └── routes.py           # Flask 路由
│   │
│   ├── core/                   # 核心業務邏輯
│   │   ├── tracker.py          # 垃圾車追蹤器
│   │   ├── state_manager.py   # 狀態管理
│   │   └── point_matcher.py   # 清運點匹配
│   │
│   ├── clients/                # 外部 API 客戶端
│   │   └── ntpc_api.py         # 新北市 API
│   │
│   ├── models/                 # 資料模型
│   │   ├── truck.py            # 垃圾車模型
│   │   └── point.py            # 清運點模型
│   │
│   └── utils/                  # 工具模組
│       ├── config.py           # 設定管理
│       └── logger.py           # 日誌設定
│
├── docs/                       # 文件
│   ├── requirements.md         # 需求規格
│   ├── api-specification.md   # API 規格
│   └── architecture.md         # 架構設計
│
├── logs/                       # 日誌目錄
└── tests/                      # 測試程式碼
```

---

## 🔧 疑難排解

### 問題 1: 找不到清運點

**錯誤**: 路線中找不到進入/離開清運點

**解決方法**:
1. 確認清運點名稱與 API 回傳的完全一致
2. 使用以下指令測試 API：
   ```bash
   curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --data-urlencode 'lat=你的緯度' \
     --data-urlencode 'lng=你的經度' | jq
   ```
3. 在回傳的 JSON 中搜尋 `PointName` 欄位

### 問題 2: API 一直回傳 idle

**可能原因**:
- 清運點名稱錯誤
- 目標路線不在附近
- 垃圾車尚未進入範圍

**解決方法**:
1. 查看日誌： `tail -f logs/app.log`
2. 確認 `target_lines` 設定正確
3. 調整 `trigger_mode` 和 `approaching_threshold`

### 問題 3: Home Assistant 無法連接

**解決方法**:
1. 確認服務運行： `curl http://localhost:5000/health`
2. 檢查防火牆設定
3. 如果使用 Docker，確認 port mapping 正確

---

## 📝 開發相關

### 運行測試

```bash
pytest tests/
```

### 查看日誌

```bash
# 檔案日誌
tail -f logs/app.log

# Docker 日誌
docker-compose logs -f
```

---

## 📖 相關文件

- [需求規格書](docs/requirements.md)
- [API 規格文件](docs/api-specification.md)
- [架構設計文件](docs/architecture.md)

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

## 📄 授權

MIT License

---

## 👤 作者

Logan

---

## 🙏 致謝

- 新北市環保局提供的垃圾車 API
- Home Assistant 社群

---

**最後更新**: 2025-11-17
