# API 規格文件

## 文件說明

本文件描述垃圾車動態偵測系統的 API 規格，包含：
1. 新北市垃圾車 API 的詳細規格（外部 API）
2. 本系統提供給 Home Assistant 的 RESTful API 規格（內部 API）

---

## 1. 新北市垃圾車 API（外部 API）

### 基本資訊

- **名稱**: 新北市垃圾車即時動態查詢 API
- **提供者**: 新北市環保局
- **端點**: `https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints`
- **方法**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`

### 請求參數

| 參數名稱 | 類型 | 必填 | 說明 | 範例 |
|---------|------|------|------|------|
| `lat` | float | 是 | 查詢位置的緯度 | 25.005193869072745 |
| `lng` | float | 是 | 查詢位置的經度 | 121.5099557021958 |

### 請求範例

#### cURL
```bash
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'lat=25.005193869072745' \
  --data-urlencode 'lng=121.5099557021958'
```

#### Python (requests)
```python
import requests

url = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints"
payload = {
    "lat": 25.005193869072745,
    "lng": 121.5099557021958
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)
data = response.json()
```

### 回應格式

#### 回應結構

```json
{
  "TimeStamp": "string",      // API 回應的時間戳記（格式: YYYYMMDDHHmmss）
  "LineCount": integer,        // 附近路線的數量
  "FixedCount": integer,       // 固定點數量
  "Line": [                    // 路線陣列
    {
      "LineID": "string",           // 路線 ID
      "LineName": "string",         // 路線名稱（例如："三區晚9"）
      "Area": "string",             // 行政區域（例如："永和區"）
      "ArrivalRank": integer,       // 目前在路線上的第幾個停靠點
      "Diff": integer,              // 與預定時間的差異（分鐘，正數=延遲，負數=提早）
      "CarNO": "string",            // 垃圾車車牌號碼
      "Location": "string",         // 目前位置的地址描述
      "LocationLat": float,         // 目前位置的緯度
      "LocationLon": float,         // 目前位置的經度
      "BarCode": "string",          // 條碼識別
      "Point": [                    // 該路線的所有停靠點
        {
          "SourcePointID": integer,     // 來源停靠點 ID
          "Vil": "string",              // 里別
          "PointName": "string",        // 停靠點名稱（例如："水源街36巷口"）
          "Lon": float,                 // 停靠點經度
          "Lat": float,                 // 停靠點緯度
          "PointID": integer,           // 停靠點 ID
          "PointRank": integer,         // 該停靠點在路線上的順序（從 1 開始）
          "PointTime": "string",        // 預定到達時間（格式: HH:mm）
          "Arrival": "string",          // 實際到達時間（格式: HH:mm，未到達則為空字串）
          "ArrivalDiff": integer,       // 到達時間差異（分鐘，65535 表示未到達）
          "FixedPoint": integer,        // 是否為固定點（0=否，1=是）
          "PointWeekKnd": "string",     // 週末標記
          "InScope": "string",          // 是否在查詢範圍內（"Y"=是，""=否）
          "LikeCount": integer          // 按讚數量
        }
      ]
    }
  ]
}
```

### 回應範例

```json
{
  "TimeStamp": "20251117211747",
  "LineCount": 3,
  "FixedCount": 0,
  "Line": [
    {
      "LineID": "234042",
      "LineName": "三區晚9",
      "Area": "永和區",
      "ArrivalRank": 35,
      "Diff": 0,
      "CarNO": "KEJ-6632",
      "Location": "新北市永和區水源街28號",
      "LocationLat": 25.0098583333333,
      "LocationLon": 121.526181666667,
      "BarCode": "000013",
      "Point": [
        {
          "SourcePointID": 25022,
          "Vil": "水源里",
          "PointName": "水源街36巷口",
          "Lon": 121.5109786,
          "Lat": 25.00444795,
          "PointID": 912674,
          "PointRank": 34,
          "PointTime": "19:30",
          "Arrival": "19:35",
          "ArrivalDiff": 5,
          "FixedPoint": 0,
          "PointWeekKnd": "",
          "InScope": "Y",
          "LikeCount": 0
        },
        {
          "SourcePointID": 4840,
          "Vil": "水源里",
          "PointName": "水源街28號",
          "Lon": 121.5114427,
          "Lat": 25.00457597,
          "PointID": 912677,
          "PointRank": 35,
          "PointTime": "19:35",
          "Arrival": "19:36",
          "ArrivalDiff": 1,
          "FixedPoint": 0,
          "PointWeekKnd": "",
          "InScope": "Y",
          "LikeCount": 0
        }
      ]
    }
  ]
}
```

### 重要欄位說明

#### Line 物件
- **ArrivalRank**: 垃圾車目前在第幾個停靠點（對應 Point 陣列中的 PointRank）
- **LocationLat/LocationLon**: 垃圾車的即時 GPS 座標

#### Point 物件
- **PointRank**: 停靠點順序，從 1 開始遞增
- **Arrival**:
  - 有值（例如 "19:35"）表示已經到達該點
  - 空字串 `""` 表示尚未到達
- **ArrivalDiff**:
  - 正數: 比預定時間晚到
  - 負數: 比預定時間早到
  - 65535: 尚未到達
- **InScope**:
  - `"Y"`: 該停靠點在查詢座標的範圍內
  - `""`: 不在範圍內

### 錯誤處理

| HTTP 狀態碼 | 說明 |
|------------|------|
| 200 | 請求成功 |
| 400 | 請求參數錯誤（缺少 lat 或 lng） |
| 500 | 伺服器內部錯誤 |
| 503 | 服務暫時無法使用 |

---

## 1.2. 新北市垃圾車 API - GetArrival（替代查詢方式）

### 基本資訊

- **名稱**: 新北市垃圾車路線查詢 API
- **提供者**: 新北市環保局
- **端點**: `https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival`
- **方法**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`

### 與 GetAroundPoints 的差異

| 特性 | GetAroundPoints | GetArrival |
|-----|-----------------|------------|
| **查詢方式** | 透過座標查詢附近路線 | 透過 LineID 直接查詢特定路線 |
| **輸入參數** | lat, lng（座標） | LineID（逗號分隔的路線 ID） |
| **回傳資料** | 包含路線名稱、區域等完整資訊 | 僅包含路線 ID 和停靠點資訊 |
| **停靠點資訊** | 包含停靠點名稱、座標、里別等 | 僅包含 PointID、到達時間等基本資訊 |
| **使用情境** | 不知道路線 ID，需要探索附近路線 | 已知路線 ID，快速查詢特定路線狀態 |

### 請求參數

| 參數名稱 | 類型 | 必填 | 說明 | 範例 |
|---------|------|------|------|------|
| `LineID` | string | 是 | 路線 ID，多個用逗號分隔 | 234026,234042,234067 |

### 請求範例

#### cURL
```bash
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data 'LineID=234026,234042,234067'
```

#### Python (requests)
```python
import requests

url = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival"
payload = {
    "LineID": "234026,234042,234067"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)
data = response.json()
```

### 回應格式

#### 回應結構

```json
{
  "TimeStamp": "string",      // API 回應的時間戳記（格式: YYYYMMDDHHmmss）
  "LineCount": integer,        // 回傳的路線數量
  "Line": [                    // 路線陣列
    {
      "LineID": "string",           // 路線 ID
      "ArrivalRank": integer,       // 目前在路線上的第幾個停靠點
      "Diff": integer,              // 與預定時間的差異（分鐘）
      "CarNO": "string",            // 垃圾車車牌號碼
      "Location": "string",         // 目前位置的地址描述
      "LocationLat": float,         // 目前位置的緯度
      "LocationLon": float,         // 目前位置的經度
      "BarCode": "string",          // 條碼識別
      "Point": [                    // 該路線的所有停靠點
        {
          "PointID": integer,           // 停靠點 ID
          "PointRank": integer,         // 該停靠點在路線上的順序（從 1 開始）
          "PointTime": "string",        // 預定到達時間（格式: HH:mm）
          "Arrival": "string",          // 實際到達時間（格式: HH:mm，未到達則為空字串）
          "ArrivalDiff": integer        // 到達時間差異（分鐘）
        }
      ]
    }
  ]
}
```

**注意**: 此 API 回傳的 Point 資料不包含停靠點名稱、座標、里別等詳細資訊，僅包含 ID 和時間資訊。

### 回應範例

```json
{
  "TimeStamp": "20251117213304",
  "LineCount": 1,
  "Line": [
    {
      "LineID": "234026",
      "ArrivalRank": 36,
      "Diff": 8,
      "CarNO": "BWM-8152",
      "Location": "新北市永和區福和路1號",
      "LocationLat": 25.00998,
      "LocationLon": 121.526588333333,
      "BarCode": "000004",
      "Point": [
        {
          "PointID": 904739,
          "PointRank": 1,
          "PointTime": "17:40",
          "Arrival": "17:39",
          "ArrivalDiff": -1
        },
        {
          "PointID": 904742,
          "PointRank": 2,
          "PointTime": "17:44",
          "Arrival": "17:42",
          "ArrivalDiff": -2
        }
      ]
    }
  ]
}
```

### 優缺點分析

#### 優點
1. **更輕量**: 回傳資料較少，網路傳輸更快
2. **更精確**: 直接查詢指定路線，無需過濾
3. **效能更好**: 伺服器負擔較小，回應速度可能更快

#### 缺點
1. **需要事先知道 LineID**: 必須先透過 GetAroundPoints 取得路線 ID
2. **缺少停靠點詳細資訊**: 無法取得停靠點名稱，需要額外維護 PointID 對應表
3. **無法探索新路線**: 如果路線變更或新增，無法自動偵測

### 使用建議

#### 建議使用 GetAroundPoints（目前採用）
- 適合不確定路線 ID 的情況
- 可以根據停靠點名稱（如 "水源街36巷口"）進行匹配
- 路線變更時無需修改設定

#### 可考慮使用 GetArrival 的情況
- 路線 ID 固定且不會變更
- 需要追蹤多條特定路線
- 對網路流量或回應速度有嚴格要求
- 願意維護 PointID 與停靠點名稱的對應表

### 整合範例

如果決定使用 GetArrival API，需要修改的地方：

```python
# 設定檔中改為儲存 LineID 和 PointID
tracking:
  target_line_ids:
    - "234042"  # 三區晚9
  enter_point_id: 912674  # 水源街36巷口的 PointID
  exit_point_id: 912677   # 水源街28號的 PointID

# API 客戶端修改
def get_line_status(self, line_ids: List[str]) -> dict:
    url = f"{self.BASE_URL}/GetArrival"
    payload = {"LineID": ",".join(line_ids)}
    response = self.session.post(url, data=payload, headers=self.headers)
    return response.json()
```

---

## 2. 系統內部 API（給 Home Assistant 使用）

### 基本資訊

- **名稱**: 垃圾車狀態查詢 API
- **端點**: `http://localhost:5000/api/trash/status`
- **方法**: `GET`
- **Content-Type**: `application/json`

### 請求參數

無需參數，直接 GET 請求即可。

### 請求範例

#### cURL
```bash
curl http://localhost:5000/api/trash/status
```

#### Python (requests)
```python
import requests

response = requests.get("http://localhost:5000/api/trash/status")
data = response.json()
```

### 回應格式

#### 狀態: idle（無垃圾車在附近）

```json
{
  "status": "idle",
  "reason": "無垃圾車在附近",
  "truck": null,
  "timestamp": "2025-11-17T21:00:00+08:00"
}
```

#### 狀態: nearby（垃圾車在附近）

```json
{
  "status": "nearby",
  "reason": "垃圾車即將到達進入清運點",
  "truck": {
    "line_name": "三區晚9",
    "line_id": "234042",
    "car_no": "KEJ-6632",
    "area": "永和區",
    "current_location": "新北市永和區水源街14巷口",
    "current_lat": 25.0098583,
    "current_lon": 121.5261817,
    "current_rank": 32,
    "total_points": 71,
    "arrival_diff": 0,
    "enter_point": {
      "name": "水源街36巷口",
      "rank": 34,
      "point_time": "19:30",
      "arrival": "",
      "arrival_diff": 65535,
      "passed": false,
      "distance_to_current": 2
    },
    "exit_point": {
      "name": "水源街28號",
      "rank": 35,
      "point_time": "19:35",
      "arrival": "",
      "arrival_diff": 65535,
      "passed": false,
      "distance_to_current": 3
    }
  },
  "timestamp": "2025-11-17T21:00:00+08:00"
}
```

### 回應欄位說明

#### 根層級欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `status` | string | 系統狀態：`idle` 或 `nearby` |
| `reason` | string | 狀態原因的文字說明 |
| `truck` | object \| null | 垃圾車詳細資訊，無垃圾車時為 null |
| `timestamp` | string | API 回應時間（ISO 8601 格式） |

#### truck 物件欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `line_name` | string | 路線名稱 |
| `line_id` | string | 路線 ID |
| `car_no` | string | 車牌號碼 |
| `area` | string | 行政區域 |
| `current_location` | string | 目前位置描述 |
| `current_lat` | float | 目前緯度 |
| `current_lon` | float | 目前經度 |
| `current_rank` | integer | 目前在第幾個停靠點 |
| `total_points` | integer | 路線總停靠點數 |
| `arrival_diff` | integer | 與預定時間的差異（分鐘） |
| `enter_point` | object | 進入清運點詳細資訊 |
| `exit_point` | object | 離開清運點詳細資訊 |

#### enter_point / exit_point 物件欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | string | 清運點名稱 |
| `rank` | integer | 該點在路線上的順序 |
| `point_time` | string | 預定到達時間（HH:mm） |
| `arrival` | string | 實際到達時間（HH:mm），未到達則為空字串 |
| `arrival_diff` | integer | 到達時間差異（65535 表示未到達） |
| `passed` | boolean | 垃圾車是否已經過該點 |
| `distance_to_current` | integer | 距離垃圾車目前位置的停靠點數 |

### HTTP 狀態碼

| 狀態碼 | 說明 |
|--------|------|
| 200 | 請求成功 |
| 500 | 伺服器內部錯誤 |
| 503 | 無法連接新北市 API |

### 錯誤回應格式

```json
{
  "error": "錯誤訊息",
  "detail": "詳細錯誤說明",
  "timestamp": "2025-11-17T21:00:00+08:00"
}
```

---

## 3. 整合範例：Home Assistant 設定

### configuration.yaml

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
        attribute_templates:
          line_name: "{{ state_attr('sensor.garbage_truck_monitor', 'truck')['line_name'] if state_attr('sensor.garbage_truck_monitor', 'truck') else 'N/A' }}"
          car_no: "{{ state_attr('sensor.garbage_truck_monitor', 'truck')['car_no'] if state_attr('sensor.garbage_truck_monitor', 'truck') else 'N/A' }}"
          current_location: "{{ state_attr('sensor.garbage_truck_monitor', 'truck')['current_location'] if state_attr('sensor.garbage_truck_monitor', 'truck') else 'N/A' }}"
```

### Automation 範例

```yaml
# 自動化：垃圾車抵達 - 開燈
automation:
  - alias: "垃圾車抵達 - 開啟通知燈"
    description: "當垃圾車進入指定清運點範圍時，打開燈泡"
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
          color_name: "red"
      - service: notify.mobile_app
        data:
          title: "🚛 垃圾車來了！"
          message: "{{ state_attr('sensor.garbage_truck_monitor', 'reason') }}"

  - alias: "垃圾車離開 - 關閉通知燈"
    description: "當垃圾車離開指定清運點範圍時，關閉燈泡"
    trigger:
      - platform: state
        entity_id: binary_sensor.garbage_truck_nearby
        to: 'off'
    action:
      - service: light.turn_off
        target:
          entity_id: light.notification_bulb
```

---

## 4. API 測試指南

### 測試新北市 API - GetAroundPoints

```bash
# 測試查詢永和區附近垃圾車
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetAroundPoints' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'lat=25.005193869072745' \
  --data-urlencode 'lng=121.5099557021958' | jq
```

### 測試新北市 API - GetArrival

```bash
# 測試查詢特定路線（使用從 GetAroundPoints 取得的 LineID）
curl --location 'https://crd-rubbish.epd.ntpc.gov.tw/WebAPI/GetArrival' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data 'LineID=234026,234042,234067' | jq

# 比較兩個 API 回傳的資料差異
# 注意：GetArrival 的 Point 物件不包含 PointName、Lat、Lon 等欄位
```

### 測試系統內部 API

```bash
# 啟動 Flask 服務後測試
curl http://localhost:5000/api/trash/status | jq

# 測試錯誤處理（當服務未啟動時）
curl http://localhost:5000/api/trash/status
```

### Python 測試腳本

```python
import requests
import json

def test_system_api():
    """測試系統內部 API"""
    url = "http://localhost:5000/api/trash/status"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 驗證必要欄位
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] in ["idle", "nearby"]

        if data["status"] == "nearby":
            assert "truck" in data
            assert data["truck"] is not None

        print("✅ API 測試通過")

    except requests.exceptions.RequestException as e:
        print(f"❌ API 請求失敗: {e}")
    except AssertionError as e:
        print(f"❌ 資料格式驗證失敗: {e}")

if __name__ == "__main__":
    test_system_api()
```

---

## 5. API 限制與注意事項

### 新北市 API 限制
1. **查詢頻率**: 建議不超過每分鐘 1 次，避免對伺服器造成負擔
2. **回應大小**: 可能回傳大量路線資料，建議使用 gzip 壓縮
3. **即時性**: 垃圾車位置更新可能有 1-2 分鐘延遲
4. **可用性**: 無 SLA 保證，可能因維護而暫停服務

### 系統內部 API 限制
1. **單執行緒**: 目前設計為單一使用者使用
2. **無認證**: 未實作 API 認證機制
3. **狀態儲存**: 僅保存記憶體中的狀態，重啟後遺失

---

**文件版本**: v1.0
**最後更新**: 2025-11-17
**維護者**: Logan
