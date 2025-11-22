# ⚡ 快速部署指令

## 🚀 一鍵部署

### 方法 1: 本地複製（推薦）

```bash
# 如果 Home Assistant 在同一台機器
cp -r /home/dodoro/dev/trash_tracking/custom_components/trash_tracking \
      /config/custom_components/

# 重啟 Home Assistant
ha core restart
```

### 方法 2: 遠端複製

```bash
# 如果 Home Assistant 在另一台機器
scp -r /home/dodoro/dev/trash_tracking/custom_components/trash_tracking \
       user@homeassistant:/config/custom_components/

# SSH 到 Home Assistant 重啟
ssh user@homeassistant "ha core restart"
```

### 方法 3: Docker 環境

```bash
# 找到 Home Assistant 容器 ID
docker ps | grep homeassistant

# 複製檔案到容器
docker cp /home/dodoro/dev/trash_tracking/custom_components/trash_tracking \
          <container_id>:/config/custom_components/

# 重啟容器
docker restart <container_id>
```

---

## ✅ 驗證部署

```bash
# 檢查檔案是否存在
ls -la /config/custom_components/trash_tracking/

# 應該看到這些檔案：
# __init__.py
# manifest.json
# config_flow.py
# coordinator.py
# sensor.py
# binary_sensor.py
# const.py
# strings.json
# translations/en.json
# translations/zh-Hant.json
# README.md
```

---

## 🧪 快速測試

### 1. 確認 Add-on 運行

```bash
curl http://localhost:5000/health
```

### 2. 在 Home Assistant UI 中新增 Integration

1. 設定 → 裝置與服務 → + 新增整合
2. 搜尋：`Trash Tracking`
3. 輸入 API URL: `http://localhost:5000`
4. 完成！

---

## 📋 檢查清單

- [ ] Integration 檔案已複製到 `/config/custom_components/trash_tracking/`
- [ ] Home Assistant 已重啟
- [ ] Add-on 正在運行
- [ ] 可以在 UI 中找到 Integration
- [ ] 成功新增 Integration
- [ ] 3 個實體已建立

---

## 🐛 快速排錯

### 找不到 Integration？

```bash
# 檢查日誌
tail -f /config/home-assistant.log | grep trash_tracking

# 確認 manifest.json 格式正確
cat /config/custom_components/trash_tracking/manifest.json

# 再次重啟
ha core restart
```

### 無法連接 API？

```bash
# 測試 Add-on API
curl http://localhost:5000/health
curl http://localhost:5000/api/trash/status

# 檢查 Add-on 狀態
ha addons info addon_*_trash_tracking
```

---

## 📖 完整測試指南

詳細測試步驟請參考：[MANUAL_TEST_GUIDE.md](MANUAL_TEST_GUIDE.md)
