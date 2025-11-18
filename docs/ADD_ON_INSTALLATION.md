# Home Assistant Add-on 安裝與發布指南

本指南說明如何安裝、測試和發布 Trash Tracking Home Assistant Add-on。

## 📋 目錄

- [本地開發測試](#本地開發測試)
- [發布到 GitHub](#發布到-github)
- [用戶安裝方式](#用戶安裝方式)
- [疑難排解](#疑難排解)

---

## 本地開發測試

### 方法 1: 直接複製到 Home Assistant

如果你有 Home Assistant OS 或 Supervised 安裝：

1. **複製 Add-on 資料夾到 `/addons/` 目錄**

   ```bash
   # 在你的開發機器上
   cd /path/to/trash_tracking

   # 複製整個 addon 資料夾到 HA
   scp -r trash_tracking_addon/ root@homeassistant.local:/addons/trash_tracking
   ```

   或者使用 Samba/SFTP 手動複製 `trash_tracking_addon/` 資料夾。

2. **重新載入 Add-on Store**

   - 前往 Home Assistant UI
   - **Supervisor** → **Add-on Store** → 右上角 ⋮ → **Reload**

3. **安裝 Add-on**

   - 在 **Local add-ons** 區域找到 "垃圾車追蹤系統"
   - 點擊進入 → **Install**

4. **配置與啟動**

   - 前往 **Configuration** 標籤
   - 填寫你的配置（座標、清運點等）
   - 點擊 **Save**
   - 前往 **Info** 標籤
   - 點擊 **Start**

5. **檢查日誌**

   - 前往 **Log** 標籤
   - 確認沒有錯誤訊息
   - 應該看到：
     ```
     [INFO] Starting Trash Tracking Add-on...
     [INFO] Starting Flask application...
     * Running on http://0.0.0.0:5000
     ```

### 方法 2: Docker Compose 本地測試

在發布前先用 Docker Compose 測試：

1. **建立測試環境**

   ```bash
   cd trash_tracking

   # 建立測試配置
   cp config.example.yaml config.yaml
   # 編輯 config.yaml 填入你的設定

   # 使用 Docker Compose 啟動
   docker-compose up --build
   ```

2. **測試 API**

   ```bash
   # 健康檢查
   curl http://localhost:5000/health

   # 狀態查詢
   curl http://localhost:5000/api/trash/status
   ```

3. **停止測試**

   ```bash
   docker-compose down
   ```

---

## 發布到 GitHub

### 步驟 1: 準備 GitHub Repository

1. **確認專案結構**

   ```
   trash_tracking/
   ├── trash_tracking_addon/
   │   ├── config.yaml
   │   ├── Dockerfile
   │   ├── build.yaml
   │   ├── run.sh
   │   ├── README.md
   │   ├── DOCS.md
   │   ├── CHANGELOG.md
   │   ├── icon.png
   │   ├── logo.png
   │   ├── repository.json
   │   └── translations/
   │       ├── en.yaml
   │       └── zh-Hant.yaml
   ├── src/
   ├── app.py
   ├── cli.py
   ├── requirements.txt
   └── README.md
   ```

2. **提交到 GitHub**

   ```bash
   git add trash_tracking_addon/
   git commit -m "feat: add Home Assistant Add-on package"
   git push origin master
   ```

### 步驟 2: 建立 GitHub Release

1. **建立版本標籤**

   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **在 GitHub 上建立 Release**

   - 前往 `https://github.com/iml885203/trash_tracking/releases`
   - 點擊 **Create a new release**
   - 選擇 tag `v1.0.0`
   - 標題：`v1.0.0 - Initial Release`
   - 描述：從 `CHANGELOG.md` 複製內容
   - 點擊 **Publish release**

### 步驟 3: 設定 GitHub Container Registry (可選)

如果要自動構建 Docker 映像檔：

1. **建立 GitHub Actions Workflow**

   創建 `.github/workflows/addon-build.yml`：

   ```yaml
   name: Build Add-on

   on:
     push:
       tags:
         - 'v*'
     workflow_dispatch:

   jobs:
     build:
       name: Build add-on
       runs-on: ubuntu-latest
       strategy:
         matrix:
           arch: [aarch64, amd64, armhf, armv7, i386]
       steps:
         - name: Checkout repository
           uses: actions/checkout@v4

         - name: Get version
           id: version
           run: |
             version=$(cat trash_tracking_addon/config.yaml | grep "^version:" | cut -d'"' -f2)
             echo "version=$version" >> $GITHUB_OUTPUT

         - name: Login to GitHub Container Registry
           uses: docker/login-action@v3
           with:
             registry: ghcr.io
             username: ${{ github.repository_owner }}
             password: ${{ secrets.GITHUB_TOKEN }}

         - name: Build and push
           uses: home-assistant/builder@master
           with:
             args: |
               --${{ matrix.arch }} \
               --target trash_tracking_addon \
               --docker-hub ghcr.io/${{ github.repository_owner }}
   ```

2. **啟用 GitHub Actions**

   - 提交 workflow 檔案
   - 前往 **Settings** → **Actions** → **General**
   - 確認 Actions 已啟用

---

## 用戶安裝方式

### 安裝步驟

用戶可以透過以下步驟安裝你的 Add-on：

#### 1. 新增 Repository

1. 前往 Home Assistant
2. **Supervisor** → **Add-on Store** → 右上角 ⋮ → **Repositories**
3. 新增：
   ```
   https://github.com/iml885203/trash_tracking
   ```
4. 點擊 **Add**

#### 2. 安裝 Add-on

1. 回到 **Add-on Store**
2. 重新整理頁面
3. 找到 "垃圾車追蹤系統"
4. 點擊進入 → **Install**

#### 3. 配置

在 **Configuration** 標籤中設定：

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines: []
  enter_point: "民生路二段80號"
  exit_point: "成功路23號"
  trigger_mode: "arriving"
  approaching_threshold: 2
system:
  log_level: "INFO"
```

#### 4. 啟動

- 前往 **Info** 標籤
- 點擊 **Start**
- 確認 **Log** 標籤沒有錯誤

#### 5. Home Assistant 整合

在 `configuration.yaml` 中加入：

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
```

重新載入：**開發者工具** → **YAML** → **重新載入所有 YAML**

---

## 疑難排解

### 問題 1: Add-on 不在 Add-on Store 中顯示

**解決方案**：

1. 確認 repository URL 正確
2. 檢查 `repository.json` 是否在專案根目錄
3. 嘗試手動重新載入：**Add-on Store** → ⋮ → **Reload**
4. 查看 Supervisor 日誌：
   ```bash
   docker logs hassio_supervisor
   ```

### 問題 2: Add-on 無法啟動

**檢查步驟**：

1. **查看 Add-on Log**
   - **Log** 標籤中查看錯誤訊息

2. **常見錯誤**：

   ```
   Error: Invalid configuration
   ```
   → 檢查 Configuration 標籤中的 YAML 格式

   ```
   Error: Port 5000 already in use
   ```
   → 停止其他使用 5000 port 的服務

   ```
   ModuleNotFoundError: No module named 'xxx'
   ```
   → Dockerfile 中缺少依賴，需要更新 `requirements.txt`

3. **手動測試容器**

   ```bash
   # SSH 進入 Home Assistant OS
   ssh root@homeassistant.local

   # 查看容器狀態
   docker ps -a | grep trash_tracking

   # 查看容器日誌
   docker logs addon_trash_tracking

   # 進入容器
   docker exec -it addon_trash_tracking /bin/bash

   # 檢查檔案
   ls -la /app
   cat /app/config.yaml
   ```

### 問題 3: 配置檔案產生錯誤

**檢查 run.sh**：

```bash
# 進入容器
docker exec -it addon_trash_tracking /bin/bash

# 檢查產生的配置
cat /app/config.yaml

# 手動測試 bashio
bashio::config 'location.lat'
```

### 問題 4: API 無法連線

**測試步驟**：

1. **確認 Add-on 正在運行**
   ```bash
   docker ps | grep trash_tracking
   ```

2. **測試 API 連線**
   ```bash
   # 在 HA OS Terminal 或 SSH 中
   curl http://localhost:5000/health
   curl http://localhost:5000/api/trash/status
   ```

3. **檢查防火牆規則**
   - 確認 port 5000 沒有被防火牆封鎖

### 問題 5: Multi-architecture 構建失敗

**解決方案**：

1. **確認 build.yaml 正確**
   ```yaml
   build_from:
     aarch64: "ghcr.io/home-assistant/aarch64-base-python:3.11-alpine3.19"
     # ... 其他架構
   ```

2. **本地測試特定架構**
   ```bash
   docker buildx build \
     --platform linux/amd64 \
     -f trash_tracking_addon/Dockerfile \
     -t trash_tracking:test .
   ```

3. **查看 Home Assistant Builder 日誌**
   ```bash
   docker logs hassio_builder
   ```

---

## 更新 Add-on

### 發布新版本

1. **更新版本號**

   編輯 `trash_tracking_addon/config.yaml`：
   ```yaml
   version: "1.0.1"
   ```

2. **更新 CHANGELOG**

   在 `trash_tracking_addon/CHANGELOG.md` 中加入新版本說明

3. **提交與標籤**
   ```bash
   git add .
   git commit -m "chore: bump version to 1.0.1"
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin master
   git push origin v1.0.1
   ```

4. **建立 GitHub Release**
   - 在 GitHub 上建立新的 Release
   - 選擇 tag `v1.0.1`

5. **用戶更新**
   - 用戶在 Add-on 頁面會看到 "Update" 按鈕
   - 點擊即可更新

---

## 最佳實踐

### 1. 版本控制

- 遵循 [Semantic Versioning](https://semver.org/)
  - `MAJOR.MINOR.PATCH`
  - MAJOR: 破壞性變更
  - MINOR: 新功能（向後相容）
  - PATCH: Bug 修復

### 2. 文件維護

- 每次發布前更新 `CHANGELOG.md`
- README 保持最新
- DOCS 提供詳細範例

### 3. 測試

- 本地測試所有變更
- 在不同架構上測試（如果可能）
- 測試升級路徑

### 4. 安全性

- 定期更新依賴
- 使用 `safety` 掃描漏洞
- 遵循最小權限原則

### 5. 支援

- 監控 GitHub Issues
- 及時回應用戶問題
- 維護 FAQ 文件

---

## 相關資源

- [Home Assistant Add-on 開發文檔](https://developers.home-assistant.io/docs/add-ons)
- [Home Assistant Builder](https://github.com/home-assistant/builder)
- [Bashio 文檔](https://github.com/hassio-addons/bashio)
- [Add-on 範例](https://github.com/home-assistant/addons-example)

---

## 支援

如有問題，請：
- 查看 [GitHub Issues](https://github.com/iml885203/trash_tracking/issues)
- 建立新的 Issue 回報問題
- 參考完整文檔：[DOCS.md](../trash_tracking_addon/DOCS.md)
