# API Caching機制

## 概述

為了減少對 NTPC API 的重複呼叫，`NTPCApiClient` 實作了類別層級的記憶體快取機制。

## 特性

### ✅ 類別層級快取

- **共享快取**：所有 `NTPCApiClient` 實例共享同一個快取
- **自動過期**：快取資料 60 秒後自動失效
- **智慧 Key**：座標四捨五入到 4 位小數（約 11 公尺精度），相近位置共享快取

### 📊 效能提升

**情境：3 個 coordinator 追蹤相同位置的不同路線**

未使用快取：
```
00:00 - Coordinator 1 呼叫 API
00:05 - Coordinator 2 呼叫 API
00:10 - Coordinator 3 呼叫 API
----
01:30 - Coordinator 1 呼叫 API
01:35 - Coordinator 2 呼叫 API
01:40 - Coordinator 3 呼叫 API

結果：每 90 秒 × 3 次 API 呼叫 = 大量重複請求
```

使用快取：
```
00:00 - Coordinator 1 呼叫 API → 存入快取
00:05 - Coordinator 2 讀取快取 ✅（避免 API 呼叫）
00:10 - Coordinator 3 讀取快取 ✅（避免 API 呼叫）
----
01:30 - 快取過期 (60 秒 TTL)
01:30 - Coordinator 1 呼叫 API → 更新快取
01:35 - Coordinator 2 讀取快取 ✅
01:40 - Coordinator 3 讀取快取 ✅

結果：每 60 秒最多 1 次 API 呼叫（減少 67% 請求量）
```

## 使用方式

### 預設啟用

```python
client = NTPCApiClient()  # cache_enabled=True（預設）
result = client.get_around_points(25.018, 121.471)
```

### 停用快取

```python
client = NTPCApiClient(cache_enabled=False)
result = client.get_around_points(25.018, 121.471)
```

### 手動清除快取

```python
NTPCApiClient.clear_cache()
```

## 快取 Key 設計

```python
cache_key = f"{lat:.4f},{lng:.4f},{time_filter},{week}"
```

**範例**：
- `25.0183,121.4717,0,None` - 民生路二段80號
- `25.0183,121.4718,0,None` - 鄰近地址（共享快取）
- `25.0183,121.4717,1,None` - 不同時間篩選（不同快取）

### 座標精度說明

- **4 位小數** ≈ 11 公尺精度
- 同一條街上不同門牌號碼通常會共享快取
- 避免因微小座標差異導致快取失效

## 設定

### 快取 TTL（Time To Live）

```python
NTPCApiClient._cache_ttl = 60  # 秒（預設）
```

**考量因素**：
- 垃圾車位置每 60 秒不會有劇烈變化
- 較長的 TTL 可減少 API 呼叫，但資料時效性較差
- 建議值：60-90 秒

## 測試

執行快取相關測試：

```bash
pytest tests/test_api_cache.py -v
```

測試涵蓋：
- 快取啟用/停用
- 快取 key 生成
- 快取命中避免 API 呼叫
- 快取過期機制
- 多實例共享快取

## 架構整合

### Home Assistant Integration

```
Config Entry 1 (路線 A) → Coordinator 1 → NTPCApiClient instance 1
Config Entry 2 (路線 B) → Coordinator 2 → NTPCApiClient instance 2
Config Entry 3 (路線 C) → Coordinator 3 → NTPCApiClient instance 3

                            ↓
                    共享類別層級快取
                            ↓
                相同位置查詢只呼叫一次 API
```

### CLI 工具

CLI 工具每次執行都會建立新的 client 實例，因此快取主要適用於：
- 連續執行多次查詢時
- 測試環境

## 注意事項

1. **記憶體使用**：快取存在記憶體中，Home Assistant 重啟後會清空
2. **座標四捨五入**：相近位置（11 公尺內）會共享快取
3. **時間篩選**：不同 `time_filter` 或 `week` 參數會使用不同快取
4. **自動清理**：過期的快取項目會在下次存取時自動移除

## 效能監控

快取操作會記錄到 log：

```
[DEBUG] Cache hit for key 25.0183,121.4717,0,None (age: 15.2s)
[DEBUG] Cached data for key 25.0183,121.4717,0,None
[DEBUG] Cache expired for key 25.0183,121.4717,0,None (age: 62.5s)
```

透過 log 可以監控：
- 快取命中率
- 快取過期情況
- API 呼叫次數減少幅度
