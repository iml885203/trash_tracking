# Trash Tracking Core

核心邏輯套件，提供垃圾車追蹤的共用功能。

## 功能

- **API Clients**: 新北市環保局 API 客戶端
- **Models**: 垃圾車和收集點資料模型
- **Core Logic**: 追蹤邏輯、狀態管理、收集點匹配
- **Utils**: 地理編碼、路線分析工具

## 使用

```python
from trash_tracking_core.clients import NTPCApiClient
from trash_tracking_core.core import TruckTracker
from trash_tracking_core.models import TruckLine, Point

# 使用 API 客戶端
client = NTPCApiClient()
trucks = client.get_around_points(lat=25.018269, lng=121.471703)

# 使用追蹤器
tracker = TruckTracker(config)
status = tracker.get_current_status()
```

## 開發

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試
pytest

# 執行型別檢查
mypy trash_tracking_core/

# 格式化程式碼
black trash_tracking_core/
```
