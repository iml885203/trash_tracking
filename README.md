# 🚛 垃圾車追蹤系統 (Trash Tracking)

[![GitHub release](https://img.shields.io/github/v/release/iml885203/trash_tracking)](https://github.com/iml885203/trash_tracking/releases)
[![License](https://img.shields.io/github/license/iml885203/trash_tracking)](LICENSE)
[![CI](https://github.com/iml885203/trash_tracking/actions/workflows/ci.yml/badge.svg)](https://github.com/iml885203/trash_tracking/actions)

新北市垃圾車即時追蹤與 Home Assistant 自動化整合系統。

## 📋 專案簡介

透過新北市環保局的垃圾車 API，即時追蹤垃圾車位置，當垃圾車接近或經過你設定的清運點時，自動觸發 Home Assistant 設備（如燈泡、通知等）。

### ✨ 主要功能

- 🚛 **即時追蹤**：新北市垃圾車位置追蹤
- 📍 **自訂清運點**：設定進入/離開清運點
- 🎯 **多路線支援**：可追蹤多條垃圾車路線
- ⏰ **提前通知**：可設定提前幾個停靠點通知
- 🏠 **Home Assistant 整合**：RESTful API 無縫整合
- 🐳 **容器化部署**：支援 Docker 和 Home Assistant Add-on
- 🔧 **CLI 工具**：命令列查詢垃圾車即時位置

### 🎬 工作流程

```
垃圾車接近進入清運點 → API 狀態變更為 nearby → HA 自動化觸發 → 💡 燈泡亮起
垃圾車經過離開清運點 → API 狀態變更為 idle → HA 自動化觸發 → 🌑 燈泡關閉
```

---

## 🚀 快速開始

### 方法 1️⃣：Home Assistant Add-on（推薦）

**最簡單的安裝方式**，適合所有 Home Assistant 使用者。

#### 安裝步驟

1. **新增 Add-on Repository**
   - 在 Home Assistant 中前往：**Supervisor** → **Add-on Store**
   - 點擊右上角 ⋮ → **Repositories**
   - 新增：`https://github.com/iml885203/trash_tracking`
   - 點擊 **Add**

2. **安裝 Add-on**
   - 在 Add-on Store 中找到 "**垃圾車追蹤系統**"
   - 點擊 **Install**

3. **配置 Add-on**
   - 前往 **Configuration** 標籤
   - 填寫你的座標和清運點名稱（參考下方說明）
   - 點擊 **Save**

4. **啟動 Add-on**
   - 前往 **Info** 標籤
   - 點擊 **Start**

5. **設定 Home Assistant 整合**
   - 參考 Add-on 的 **Documentation** 標籤
   - 或查看 [完整使用指南](trash_tracking_addon/DOCS.md)

#### 如何找到清運點名稱？

**使用 Add-on 內建 CLI 工具**（最簡單）：

```bash
# 在 Home Assistant 的 Terminal add-on 中執行
docker exec -it addon_*_trash_tracking python3 cli.py --lat 你的緯度 --lng 你的經度
```

**或使用新北市官網**：
- 前往 [新北市垃圾車即時動態](https://crd-rubbish.epd.ntpc.gov.tw/)
- 輸入地址查詢清運點名稱

#### 📖 詳細文檔

- 📘 [完整使用指南](trash_tracking_addon/DOCS.md) - 配置範例、疑難排解
- 📗 [Add-on 說明](trash_tracking_addon/README.md) - Add-on 功能介紹
- 📙 [快速開始](QUICK_START_ADDON.md) - 發布與安裝指南

---

### 方法 2️⃣：Docker Compose（進階使用者）

適合想要自己管理容器的進階使用者。

```bash
# 1. Clone 專案
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# 2. 編輯配置檔
cp config.example.yaml config.yaml
# 編輯 config.yaml，填入你的座標和清運點

# 3. 啟動服務
docker-compose up -d

# 4. 查看日誌
docker-compose logs -f
```

配置範例：

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

---

### 方法 3️⃣：Python 直接運行（開發者）

適合開發測試或沒有 Docker 環境的情況。

```bash
# 1. Clone 專案
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# 2. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 編輯配置
cp config.example.yaml config.yaml
# 編輯 config.yaml

# 5. 啟動服務
python3 app.py
```

---

## 🔌 Home Assistant 整合

無論使用哪種部署方式，都需要在 Home Assistant 中設定整合。

### 基本設定

編輯 `configuration.yaml`：

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

# Automation - 垃圾車到達時開燈
automation:
  - alias: "垃圾車抵達 - 開啟通知燈"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'on'
    action:
      - service: light.turn_on
        target:
          entity_id: light.notification_bulb  # 改成你的燈泡
        data:
          brightness: 255
          rgb_color: [255, 0, 0]

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

更多範例請參考：[trash_tracking_addon/DOCS.md](trash_tracking_addon/DOCS.md)

---

## 🖥️ CLI 命令列工具

快速查詢附近垃圾車的即時位置。

### 基本使用

```bash
# 查詢指定座標附近的垃圾車
python3 cli.py --lat 25.018269 --lng 121.471703

# 指定查詢半徑
python3 cli.py --lat 25.018269 --lng 121.471703 --radius 1500

# 只顯示接下來 5 個清運點
python3 cli.py --lat 25.018269 --lng 121.471703 --next 5

# 過濾特定路線
python3 cli.py --lat 25.018269 --lng 121.471703 --line "C08路線下午"

# 顯示除錯訊息
python3 cli.py --lat 25.018269 --lng 121.471703 --debug
```

### 輸出範例

```
🔍 查詢位置: (25.018269, 121.471703)
📏 查詢半徑: 1000 公尺

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

### CLI 參數說明

| 參數 | 必填 | 說明 | 預設值 |
|------|------|------|--------|
| `--lat` | ✅ | 查詢位置的緯度 | - |
| `--lng` | ✅ | 查詢位置的經度 | - |
| `--radius` | ❌ | 查詢半徑（公尺） | 1000 |
| `--next` | ❌ | 顯示接下來的清運點數量 | 10 |
| `--line` | ❌ | 過濾特定路線名稱 | - |
| `--debug` | ❌ | 顯示除錯訊息 | false |

---

## 📡 API 端點

服務啟動後提供以下 API：

### `GET /health`

健康檢查端點。

**回應範例**：
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

### `GET /api/trash/status`

取得垃圾車追蹤狀態。

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
    "enter_point": {
      "name": "民生路二段80號",
      "rank": 12,
      "time": "14:00"
    },
    "exit_point": {
      "name": "成功路23號",
      "rank": 15,
      "time": "14:15"
    }
  },
  "timestamp": "2025-11-18T14:05:00+08:00"
}
```

### `POST /api/reset`

重置追蹤器狀態（測試用）。

完整 API 規格：[docs/api-specification.md](docs/api-specification.md)

---

## ⚙️ 配置說明

### 完整配置範例

```yaml
# 系統設定
system:
  log_level: INFO  # DEBUG, INFO, WARNING, ERROR
  cache_enabled: false
  cache_ttl: 60

# 查詢位置（你家的座標）
location:
  lat: 25.018269
  lng: 121.471703

# 垃圾車追蹤設定
tracking:
  # 指定追蹤的路線（留空則追蹤所有路線）
  target_lines:
    - "C08路線下午"
    - "C15路線下午"

  # 進入清運點（燈泡亮起）
  enter_point: "民生路二段80號"

  # 離開清運點（燈泡關閉）
  exit_point: "成功路23號"

  # 觸發模式
  # arriving: 提前通知（垃圾車即將到達時觸發）
  # arrived: 實際到達（垃圾車已經到達時觸發）
  trigger_mode: "arriving"

  # 提前通知停靠點數（arriving 模式才有效）
  # 2 表示垃圾車距離進入點前 2 個停靠點時觸發
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
```

### 觸發模式說明

#### `arriving` 模式（推薦）

提前通知，有時間準備垃圾。

```yaml
trigger_mode: "arriving"
approaching_threshold: 2  # 提前 2 個停靠點通知
```

**範例**：
- 進入點：民生路二段80號（第 12 站）
- 垃圾車目前在第 10 站
- 距離進入點還有 2 站 → **觸發通知** ✅

#### `arrived` 模式

垃圾車剛到達時才通知，比較緊急。

```yaml
trigger_mode: "arrived"
approaching_threshold: 0  # 此參數無效
```

---

## 🏗️ 專案架構

```
trash_tracking/
├── src/                        # 核心程式碼
│   ├── api/                    # API 相關
│   │   ├── client.py          # 新北市 API 客戶端
│   │   └── routes.py          # Flask API 路由
│   ├── core/                   # 核心邏輯
│   │   ├── config.py          # 配置管理
│   │   ├── logger.py          # 日誌系統
│   │   ├── point_matcher.py  # 清運點匹配邏輯
│   │   └── state_manager.py  # 狀態管理
│   └── models/                 # 資料模型
│       ├── point.py           # 清運點模型
│       └── truck.py           # 垃圾車模型
├── tests/                      # 測試程式
├── docs/                       # 文檔
├── trash_tracking_addon/       # Home Assistant Add-on 套件
├── app.py                      # Flask 應用程式入口
├── cli.py                      # CLI 工具
├── config.yaml                 # 配置檔案範例
├── requirements.txt            # Python 依賴
├── Dockerfile                  # Docker 映像檔
└── docker-compose.yml          # Docker Compose 配置
```

完整架構說明：[docs/architecture.md](docs/architecture.md)

---

## 🧪 測試

專案包含完整的測試套件（91 個測試，~70% 覆蓋率）。

### 運行測試

```bash
# 安裝開發依賴
pip install -r requirements-dev.txt

# 運行所有測試
pytest

# 運行測試並顯示覆蓋率
pytest --cov=src --cov-report=html

# 運行特定測試
pytest tests/test_point_matcher.py -v
```

### 程式碼品質檢查

```bash
# Linting
flake8 src/ tests/

# 程式碼格式化
black src/ tests/
isort src/ tests/

# 類型檢查
mypy src/

# 安全掃描
bandit -r src/
safety check
```

詳細 CI/CD 設定：[docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md)

---

## 📚 文檔

### 使用者文檔
- 📘 [Add-on 完整使用指南](trash_tracking_addon/DOCS.md) - **推薦閱讀**
- 📗 [Add-on 說明](trash_tracking_addon/README.md)
- 📙 [快速開始](QUICK_START_ADDON.md)
- 📕 [安裝與發布指南](docs/ADD_ON_INSTALLATION.md)

### 開發者文檔
- 🔵 [專案架構](docs/architecture.md)
- 🔵 [API 規格](docs/api-specification.md)
- 🔵 [需求文件](docs/requirements.md)
- 🔵 [CI/CD 設定](docs/CI_CD_SETUP.md)

---

## 🤝 貢獻

歡迎提交 Pull Request 或回報 Issue！

### 貢獻指南

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 開發設定

```bash
# Clone 專案
git clone https://github.com/iml885203/trash_tracking.git
cd trash_tracking

# 安裝開發依賴
pip install -r requirements-dev.txt

# 安裝 pre-commit hooks
pre-commit install

# 運行測試
pytest

# 運行程式碼檢查
flake8 src/ tests/
black --check src/ tests/
mypy src/
```

---

## 🐛 問題回報

如遇到問題，請：
1. 查看 [Issue 列表](https://github.com/iml885203/trash_tracking/issues)
2. 建立新的 Issue，並提供：
   - Home Assistant 版本（如使用 Add-on）
   - 錯誤訊息和日誌
   - 配置資訊（去除敏感資料）

---

## 📄 授權

本專案採用 MIT License - 詳見 [LICENSE](LICENSE) 檔案

---

## 🙏 致謝

- 新北市環保局提供的垃圾車 API
- Home Assistant 社群
- 所有貢獻者

---

## 📞 聯絡

- GitHub: [@iml885203](https://github.com/iml885203)
- Project: [trash_tracking](https://github.com/iml885203/trash_tracking)
- Issues: [回報問題](https://github.com/iml885203/trash_tracking/issues)

---

**⭐ 如果這個專案對你有幫助，請給個星星！**
