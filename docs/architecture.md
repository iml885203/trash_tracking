# 垃圾車動態偵測系統 - 架構設計文件

## 文件說明

本文件描述垃圾車動態偵測系統的技術架構、模組設計、資料流程與部署方案。

---

## 1. 系統架構概覽

### 1.1 高階架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  RESTful Sensor (每 90 秒輪詢)                         │ │
│  │  • sensor.garbage_truck_monitor                        │ │
│  │  • binary_sensor.garbage_truck_nearby                  │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  Automation                                            │ │
│  │  • 垃圾車抵達 → 燈泡亮起                                 │ │
│  │  • 垃圾車離開 → 燈泡關閉                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP GET /api/trash/status
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Application (Python 3.11+)               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Layer (Flask)                                     │ │
│  │  • GET /api/trash/status                               │ │
│  │  • GET /health                                         │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  Business Logic Layer                                  │ │
│  │  • TruckTracker: 垃圾車追蹤邏輯                         │ │
│  │  • StateManager: 狀態管理（idle/nearby）               │ │
│  │  • PointMatcher: 清運點匹配邏輯                         │ │
│  └─────────────────────┬──────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │  Data Access Layer                                     │ │
│  │  • APIClient: 新北市 API 客戶端                         │ │
│  │  • ConfigManager: 設定檔管理                            │ │
│  │  • Cache: 快取機制（可選）                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP POST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          新北市垃圾車 API (外部服務)                         │
│      https://crd-rubbish.epd.ntpc.gov.tw/WebAPI            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技術堆疊

| 層級 | 技術選擇 | 理由 |
|------|---------|------|
| **Web 框架** | Flask 3.0+ | 輕量、易於開發、RESTful 友善 |
| **程式語言** | Python 3.11+ | Home Assistant 生態、豐富的函式庫 |
| **HTTP 客戶端** | requests | 標準、穩定、易用 |
| **設定管理** | PyYAML | YAML 格式人性化，易於編輯 |
| **日誌處理** | Python logging | 標準庫、無額外依賴 |
| **部署方式** | Docker (可選) | 跨平台、易於部署到 HA OS |
| **時區處理** | pytz | 正確處理台灣時區 |

---

## 2. 模組設計

### 2.1 專案結構

```
trash_light/
├── app.py                      # Flask 應用程式進入點
├── config.yaml                 # 使用者設定檔
├── requirements.txt            # Python 依賴清單
├── Dockerfile                  # Docker 容器化設定
├── .env.example                # 環境變數範本
├── README.md                   # 專案說明
│
├── src/                        # 原始碼目錄
│   ├── __init__.py
│   │
│   ├── api/                    # API 層
│   │   ├── __init__.py
│   │   └── routes.py           # Flask 路由定義
│   │
│   ├── core/                   # 核心業務邏輯
│   │   ├── __init__.py
│   │   ├── tracker.py          # 垃圾車追蹤器
│   │   ├── state_manager.py   # 狀態管理器
│   │   └── point_matcher.py   # 清運點匹配器
│   │
│   ├── clients/                # 外部服務客戶端
│   │   ├── __init__.py
│   │   └── ntpc_api.py         # 新北市 API 客戶端
│   │
│   ├── utils/                  # 工具模組
│   │   ├── __init__.py
│   │   ├── config.py           # 設定管理
│   │   ├── logger.py           # 日誌設定
│   │   └── cache.py            # 快取機制
│   │
│   └── models/                 # 資料模型
│       ├── __init__.py
│       ├── truck.py            # 垃圾車資料模型
│       └── point.py            # 清運點資料模型
│
├── tests/                      # 測試程式碼
│   ├── __init__.py
│   ├── test_tracker.py
│   ├── test_api.py
│   └── test_point_matcher.py
│
└── docs/                       # 文件
    ├── requirements.md         # 需求規格
    ├── api-specification.md   # API 規格
    └── architecture.md         # 架構設計（本文件）
```

### 2.2 核心模組說明

#### 2.2.1 API Layer (`src/api/routes.py`)

**職責**: 處理 HTTP 請求與回應

```python
from flask import Flask, jsonify
from src.core.tracker import TruckTracker

app = Flask(__name__)
tracker = TruckTracker()

@app.route('/api/trash/status', methods=['GET'])
def get_status():
    """取得垃圾車狀態"""
    status = tracker.get_current_status()
    return jsonify(status)

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({"status": "ok"})
```

#### 2.2.2 Truck Tracker (`src/core/tracker.py`)

**職責**: 協調各模組，實現垃圾車追蹤主邏輯

```python
class TruckTracker:
    """垃圾車追蹤器"""

    def __init__(self, config: dict):
        self.config = config
        self.api_client = NTPCApiClient()
        self.state_manager = StateManager()
        self.point_matcher = PointMatcher(
            enter_point=config['enter_point'],
            exit_point=config['exit_point']
        )

    def get_current_status(self) -> dict:
        """
        取得當前垃圾車狀態

        Returns:
            dict: 包含 status, reason, truck, timestamp 的狀態資訊
        """
        # 1. 呼叫新北市 API
        api_data = self.api_client.get_around_points(
            lat=self.config['lat'],
            lng=self.config['lng']
        )

        # 2. 過濾目標路線
        target_lines = self._filter_target_lines(api_data)

        # 3. 檢查每條路線的清運點狀態
        for line in target_lines:
            match_result = self.point_matcher.check_line(line)

            if match_result['should_trigger']:
                # 更新狀態
                new_state = match_result['new_state']
                self.state_manager.update_state(new_state, line)
                break

        # 4. 回傳目前狀態
        return self.state_manager.get_status_response()
```

#### 2.2.3 State Manager (`src/core/state_manager.py`)

**職責**: 管理系統狀態（idle ↔ nearby）

```python
from enum import Enum
from datetime import datetime

class TruckState(Enum):
    IDLE = "idle"
    NEARBY = "nearby"

class StateManager:
    """狀態管理器"""

    def __init__(self):
        self.current_state = TruckState.IDLE
        self.current_truck = None
        self.last_update = None

    def update_state(self, new_state: TruckState, truck_data: dict = None):
        """
        更新系統狀態

        Args:
            new_state: 新狀態
            truck_data: 垃圾車資料（當狀態為 nearby 時必填）
        """
        if self.current_state != new_state:
            self.current_state = new_state
            self.current_truck = truck_data
            self.last_update = datetime.now()

    def get_status_response(self) -> dict:
        """生成 API 回應"""
        return {
            "status": self.current_state.value,
            "reason": self._get_reason(),
            "truck": self.current_truck,
            "timestamp": self.last_update.isoformat()
        }
```

#### 2.2.4 Point Matcher (`src/core/point_matcher.py`)

**職責**: 判斷垃圾車是否到達進入/離開清運點

```python
class PointMatcher:
    """清運點匹配器"""

    def __init__(self, enter_point: str, exit_point: str,
                 trigger_mode: str = 'arriving', threshold: int = 2):
        self.enter_point = enter_point
        self.exit_point = exit_point
        self.trigger_mode = trigger_mode
        self.threshold = threshold

    def check_line(self, line_data: dict) -> dict:
        """
        檢查路線是否觸發狀態變更

        Args:
            line_data: API 回傳的路線資料

        Returns:
            dict: {
                'should_trigger': bool,
                'new_state': TruckState,
                'reason': str
            }
        """
        current_rank = line_data['ArrivalRank']
        points = line_data['Point']

        # 找到進入點和離開點
        enter_point_data = self._find_point(points, self.enter_point)
        exit_point_data = self._find_point(points, self.exit_point)

        if not enter_point_data or not exit_point_data:
            return {'should_trigger': False}

        # 檢查是否到達進入點
        if self._is_approaching_enter_point(current_rank, enter_point_data):
            return {
                'should_trigger': True,
                'new_state': TruckState.NEARBY,
                'reason': f'垃圾車即將到達 {self.enter_point}'
            }

        # 檢查是否已過離開點
        if self._has_passed_exit_point(exit_point_data):
            return {
                'should_trigger': True,
                'new_state': TruckState.IDLE,
                'reason': f'垃圾車已離開 {self.exit_point}'
            }

        return {'should_trigger': False}

    def _is_approaching_enter_point(self, current_rank: int,
                                     enter_point: dict) -> bool:
        """判斷是否即將到達進入點"""
        enter_rank = enter_point['PointRank']
        distance = enter_rank - current_rank

        if self.trigger_mode == 'arriving':
            return 0 <= distance <= self.threshold
        else:  # arrived
            return enter_point['Arrival'] != ""

    def _has_passed_exit_point(self, exit_point: dict) -> bool:
        """判斷是否已經過離開點"""
        return exit_point['Arrival'] != ""
```

#### 2.2.5 NTPC API Client (`src/clients/ntpc_api.py`)

**職責**: 封裝新北市 API 的呼叫邏輯

```python
import requests
from typing import Optional

class NTPCApiClient:
    """新北市垃圾車 API 客戶端"""

    BASE_URL = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()

    def get_around_points(self, lat: float, lng: float) -> Optional[dict]:
        """
        查詢附近垃圾車

        Args:
            lat: 緯度
            lng: 經度

        Returns:
            dict: API 回傳的資料，失敗時回傳 None
        """
        url = f"{self.BASE_URL}/GetAroundPoints"
        payload = {"lat": lat, "lng": lng}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = self.session.post(
                url,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # 記錄錯誤並回傳 None
            logger.error(f"API 請求失敗: {e}")
            return None
```

---

## 3. 資料流程

### 3.1 狀態轉換流程

```
                        ┌──────────────┐
                        │ 系統啟動      │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                   ┌────│  idle 狀態    │◄────┐
                   │    │ (燈泡關閉)     │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ HA 每 90 秒   │
                   │           │ 輪詢 API      │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ 查詢新北市API │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ 檢查進入清運點 │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ 是           │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ nearby 狀態   │      │
                   │    │ (燈泡亮起)     │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ 持續輪詢      │
                   │           ▼              │
                   │    ┌──────────────┐      │
                   │    │ 檢查離開清運點 │      │
                   │    └──────┬───────┘      │
                   │           │              │
                   │           │ 是           │
                   └───────────┴──────────────┘
```

### 3.2 API 呼叫流程

```
Home Assistant              Flask App              NTPC API
     │                         │                      │
     │  GET /api/trash/status  │                      │
     ├────────────────────────>│                      │
     │                         │                      │
     │                         │  POST /GetAroundPoints
     │                         ├─────────────────────>│
     │                         │                      │
     │                         │   JSON Response      │
     │                         │<─────────────────────┤
     │                         │                      │
     │                         │ 處理邏輯：            │
     │                         │ 1. 過濾路線          │
     │                         │ 2. 匹配清運點         │
     │                         │ 3. 更新狀態          │
     │                         │                      │
     │   JSON Response         │                      │
     │<────────────────────────┤                      │
     │                         │                      │
```

---

## 4. 設定檔設計

### 4.1 config.yaml 結構

```yaml
# 系統設定
system:
  log_level: INFO           # 日誌等級：DEBUG, INFO, WARNING, ERROR
  cache_enabled: false      # 是否啟用快取（未來功能）
  cache_ttl: 60            # 快取存活時間（秒）

# 查詢位置（你家的座標）
location:
  lat: 25.005193869072745
  lng: 121.5099557021958

# 垃圾車追蹤設定
tracking:
  # 指定追蹤的路線（留空陣列則追蹤所有路線）
  target_lines:
    - "三區晚9"
    # - "三區晚11"

  # 進入清運點
  enter_point: "水源街36巷口"

  # 離開清運點
  exit_point: "水源街28號"

  # 觸發模式
  # arriving: 即將到達進入點時觸發
  # arrived: 已經到達進入點時觸發
  trigger_mode: "arriving"

  # 提前通知停靠點數（僅當 trigger_mode=arriving 時有效）
  approaching_threshold: 2

# API 設定
api:
  # 新北市 API 設定
  ntpc:
    base_url: "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI"
    timeout: 10             # 請求逾時（秒）
    retry_count: 3          # 重試次數
    retry_delay: 2          # 重試延遲（秒）

  # Flask 服務設定
  server:
    host: "0.0.0.0"
    port: 5000
    debug: false

# Home Assistant 整合設定（文件參考）
home_assistant:
  scan_interval: 90         # HA 輪詢間隔（秒）
  light_entity_id: "light.notification_bulb"  # 控制的燈泡 entity ID
```

### 4.2 設定檔驗證

系統啟動時會驗證以下項目：
- 必填欄位是否存在
- 座標格式是否正確
- 進入點和離開點不可相同
- trigger_mode 必須為 'arriving' 或 'arrived'

---

## 5. 錯誤處理策略

### 5.1 外部 API 錯誤

| 錯誤類型 | 處理方式 |
|---------|---------|
| 連線逾時 | 重試 3 次，失敗後維持上一次狀態 |
| HTTP 4xx | 記錄錯誤，回傳錯誤訊息給 HA |
| HTTP 5xx | 記錄錯誤，維持上一次狀態 |
| JSON 解析失敗 | 記錄錯誤，維持上一次狀態 |

### 5.2 內部邏輯錯誤

| 錯誤類型 | 處理方式 |
|---------|---------|
| 找不到清運點 | 記錄警告，回傳 idle 狀態 |
| 設定檔錯誤 | 啟動時拋出例外，拒絕啟動 |
| 狀態異常 | 重置為 idle 狀態 |

---

## 6. 部署架構

### 6.1 Docker 部署

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 暴露端口
EXPOSE 5000

# 啟動應用
CMD ["python", "app.py"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  trash_light:
    build: .
    container_name: trash_light
    ports:
      - "5000:5000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Taipei
    restart: unless-stopped
```

### 6.2 Home Assistant Add-on 部署

專案可打包為 Home Assistant Add-on，直接透過 Add-on Store 安裝。

#### config.json (Add-on 設定)
```json
{
  "name": "Garbage Truck Light",
  "version": "1.0.0",
  "slug": "garbage_truck_light",
  "description": "新北市垃圾車動態偵測與燈泡控制",
  "arch": ["armhf", "armv7", "aarch64", "amd64", "i386"],
  "startup": "application",
  "boot": "auto",
  "ports": {
    "5000/tcp": 5000
  },
  "options": {
    "location": {
      "lat": 25.005193869072745,
      "lng": 121.5099557021958
    },
    "tracking": {
      "enter_point": "水源街36巷口",
      "exit_point": "水源街28號"
    }
  },
  "schema": {
    "location": {
      "lat": "float",
      "lng": "float"
    },
    "tracking": {
      "target_lines": ["str?"],
      "enter_point": "str",
      "exit_point": "str",
      "trigger_mode": "list(arriving|arrived)?",
      "approaching_threshold": "int?"
    }
  }
}
```

---

## 7. 效能考量

### 7.1 效能指標

| 指標 | 目標值 | 測量方式 |
|------|--------|---------|
| API 回應時間 | < 2 秒 | 使用 Flask 內建計時 |
| 記憶體使用 | < 512 MB | Docker stats 監控 |
| CPU 使用 | < 10% | Docker stats 監控 |

### 7.2 最佳化策略

1. **減少 API 呼叫**:
   - HA 輪詢間隔設為 90 秒（可調整）
   - 避免重複查詢同一時間的資料

2. **快取機制**（未來功能）:
   - 快取新北市 API 回應 60 秒
   - 減少對外部 API 的負擔

3. **連線池**:
   - 使用 `requests.Session()` 重用 TCP 連線

---

## 8. 安全考量

### 8.1 資料隱私
- 使用者座標僅用於查詢 API，不記錄或傳送到其他地方
- 日誌中不包含敏感資訊

### 8.2 API 安全
- 限制 API 僅監聽 localhost（除非需要遠端存取）
- 未來可加入 API Key 認證機制

### 8.3 依賴管理
- 定期更新 Python 套件，修補安全漏洞
- 使用 `pip-audit` 掃描已知漏洞

---

## 9. 監控與日誌

### 9.1 日誌格式

```
2025-11-17 21:00:00 [INFO] TruckTracker: 開始查詢垃圾車狀態
2025-11-17 21:00:01 [INFO] NTPCApiClient: API 請求成功 (200)
2025-11-17 21:00:01 [INFO] PointMatcher: 找到路線 "三區晚9"
2025-11-17 21:00:01 [INFO] PointMatcher: 垃圾車即將到達進入點 "水源街36巷口"
2025-11-17 21:00:01 [INFO] StateManager: 狀態變更: idle -> nearby
2025-11-17 21:00:01 [INFO] Flask: 200 GET /api/trash/status
```

### 9.2 健康檢查

提供 `/health` 端點供監控系統查詢：

```bash
curl http://localhost:5000/health
# Response: {"status": "ok", "timestamp": "2025-11-17T21:00:00"}
```

---

## 10. 擴充性設計

### 10.1 支援多使用者

未來可擴充為多使用者版本，每個使用者有獨立的設定：

```python
class MultiUserTracker:
    def __init__(self):
        self.trackers = {}  # user_id -> TruckTracker

    def get_status(self, user_id: str) -> dict:
        if user_id not in self.trackers:
            self.trackers[user_id] = self._create_tracker(user_id)
        return self.trackers[user_id].get_current_status()
```

### 10.2 支援其他縣市

架構設計可支援其他縣市的垃圾車 API：

```python
class APIClientFactory:
    @staticmethod
    def create(city: str):
        if city == "ntpc":
            return NTPCApiClient()
        elif city == "taipei":
            return TaipeiApiClient()
        # ... 其他縣市
```

---

## 11. 測試策略

### 11.1 單元測試

- 測試 PointMatcher 的邏輯判斷
- 測試 StateManager 的狀態轉換
- Mock 外部 API 呼叫

### 11.2 整合測試

- 測試 Flask API 端點
- 測試完整的資料流程

### 11.3 端對端測試

- 使用真實的新北市 API 測試
- 驗證 Home Assistant 整合

---

## 12. 已知限制與改進方向

### 12.1 已知限制

1. **單執行緒設計**: 目前不支援多使用者並發
2. **無持久化**: 系統重啟後狀態遺失
3. **無認證機制**: API 未實作認證
4. **依賴外部 API**: 若新北市 API 異常則無法運作

### 12.2 改進方向

1. **加入資料庫**: 儲存歷史記錄，供統計分析
2. **WebSocket 推送**: 主動推送狀態變更到 HA
3. **Web 管理介面**: 提供圖形化設定介面
4. **地圖視覺化**: 顯示垃圾車即時位置
5. **多通知管道**: 支援 LINE、Telegram 推播

---

**文件版本**: v1.0
**最後更新**: 2025-11-17
**維護者**: Logan
**專案名稱**: trash_light
