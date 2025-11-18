# 🚀 Trash Tracking Add-on 快速開始

## 📦 已完成的 Add-on 套件

你的 Flask Application 已經成功打包成 Home Assistant Add-on！

### ✅ 已建立的檔案

```
trash_tracking_addon/
├── config.yaml              ✅ Add-on 配置與 schema
├── Dockerfile              ✅ Multi-arch 容器建置
├── build.yaml              ✅ 架構建置配置
├── run.sh                  ✅ Bashio 啟動腳本
├── icon.png                ✅ Add-on 圖示（暫時版本）
├── logo.png                ✅ Add-on Logo（暫時版本）
├── README.md               ✅ 主要說明文件
├── DOCS.md                 ✅ 詳細使用指南
├── CHANGELOG.md            ✅ 版本更新記錄
├── ICON_README.md          ✅ 圖示製作指南
├── PACKAGE_SUMMARY.md      ✅ 完整總結文件
├── repository.json         ✅ Repository 元資料
├── .dockerignore           ✅ Docker 建置忽略
├── generate_icon.py        ✅ 圖示產生腳本
└── translations/           ✅ 多語言支援
    ├── en.yaml             ✅ 英文翻譯
    └── zh-Hant.yaml        ✅ 繁體中文翻譯
```

---

## 🎯 三步驟發布到 GitHub

### 步驟 1️⃣: 提交到 Git

```bash
cd /Users/logan/dev/logan/trash_tracking

# 加入所有檔案
git add trash_tracking_addon/
git add docs/ADD_ON_INSTALLATION.md
git add QUICK_START_ADDON.md

# 提交
git commit -m "feat: add Home Assistant Add-on package

Complete add-on structure with:
- Multi-architecture support (5 architectures)
- UI-based configuration
- RESTful API integration
- Comprehensive documentation
- Multi-language support (en, zh-Hant)
"

# 推送
git push origin master
```

### 步驟 2️⃣: 建立版本標籤

```bash
# 建立 v1.0.0 標籤
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial Home Assistant Add-on"

# 推送標籤
git push origin v1.0.0
```

### 步驟 3️⃣: 在 GitHub 建立 Release

1. 前往：https://github.com/iml885203/trash_tracking/releases
2. 點擊 **"Create a new release"**
3. 選擇 tag: `v1.0.0`
4. Title: `v1.0.0 - Initial Release`
5. 填入 Description（參考下方模板）
6. 點擊 **"Publish release"**

#### Release Description 模板

```markdown
## 🎉 Trash Tracking Home Assistant Add-on - 首次發布

### ✨ 功能特色
- ✅ 新北市垃圾車即時追蹤
- ✅ 自訂進入/離開清運點
- ✅ 支援多條路線追蹤
- ✅ 提前到達通知（可設定提前幾站）
- ✅ RESTful API 整合
- ✅ UI 配置介面（無需手動編輯 YAML）
- ✅ 多架構支援（5 種架構）

### 📥 安裝方式

在 Home Assistant 中新增此 Repository：

1. **Supervisor** → **Add-on Store** → ⋮ → **Repositories**
2. 加入：`https://github.com/iml885203/trash_tracking`
3. 找到 "垃圾車追蹤系統" → 點擊 **Install**

### 📖 文檔
- [安裝指南](docs/ADD_ON_INSTALLATION.md)
- [使用文檔](trash_tracking_addon/DOCS.md)
- [配置範例](trash_tracking_addon/README.md)

### 🏗️ 支援架構
- aarch64 (ARM 64-bit)
- amd64 (x86 64-bit)
- armhf (ARM 32-bit HF)
- armv7 (ARM v7)
- i386 (x86 32-bit)

完整更新記錄：[CHANGELOG.md](trash_tracking_addon/CHANGELOG.md)
```

---

## 🧪 本地測試（發布前）

### 方法 1: Docker 測試

```bash
cd /Users/logan/dev/logan/trash_tracking

# 建置容器
docker build -f trash_tracking_addon/Dockerfile -t trash_tracking:test .

# 執行測試
docker run -p 5000:5000 trash_tracking:test

# 測試 API（開新 terminal）
curl http://localhost:5000/health
curl http://localhost:5000/api/trash/status
```

### 方法 2: Home Assistant 本地測試

如果你有運行中的 Home Assistant：

```bash
# 複製到 HA addons 目錄
scp -r trash_tracking_addon/ root@homeassistant.local:/addons/trash_tracking

# 或使用 Samba/SFTP 手動複製
```

然後在 HA UI 中：
1. **Supervisor** → **Add-on Store** → ⋮ → **Reload**
2. 在 **Local add-ons** 找到 "垃圾車追蹤系統"
3. 安裝並測試

---

## 📱 用戶安裝方式（發布後）

### 安裝步驟

1. **新增 Repository**
   - Home Assistant → Supervisor → Add-on Store
   - 右上角 ⋮ → Repositories
   - 加入：`https://github.com/iml885203/trash_tracking`

2. **安裝 Add-on**
   - 在 Add-on Store 中找到 "垃圾車追蹤系統"
   - 點擊 Install

3. **配置**
   - Configuration 標籤中設定座標和清運點
   - 儲存配置

4. **啟動**
   - Info 標籤 → Start
   - 檢查 Log 標籤確認正常運行

5. **Home Assistant 整合**
   - 在 `configuration.yaml` 加入 sensor 和 binary_sensor
   - 建立 automation
   - 重新載入 YAML

詳細步驟請參考：`trash_tracking_addon/DOCS.md`

---

## 🔍 重要檔案說明

### config.yaml
定義 Add-on 的基本資訊、配置選項和 schema 驗證

### Dockerfile
Multi-architecture 容器建置檔案，基於 Home Assistant 官方 Python 映像檔

### run.sh
Bashio 啟動腳本，負責：
- 從 HA UI 讀取用戶配置
- 產生 `/app/config.yaml`
- 啟動 Flask 應用程式

### DOCS.md
詳細的使用者文檔，包含：
- 安裝步驟
- 配置說明
- 範例程式碼
- 疑難排解

### translations/
多語言支援檔案，讓配置 UI 顯示翻譯文字

---

## 📝 配置範例

### 基本配置（單一路線）

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
system:
  log_level: "INFO"
```

### 追蹤所有路線

```yaml
location:
  lat: 25.018269
  lng: 121.471703
tracking:
  target_lines: []  # 空陣列 = 追蹤所有路線
  enter_point: "民生路二段80號"
  exit_point: "成功路23號"
  trigger_mode: "arriving"
  approaching_threshold: 3
```

---

## 🎨 圖示改善（可選）

當前使用暫時圖示（文字 "TRUCK"），建議後續改善：

### 快速改善方式

1. **使用 Canva**（推薦新手）
   - 前往：https://www.canva.com/
   - 建立 256x256 設計
   - 搜尋垃圾車和位置圖示
   - 匯出 PNG

2. **使用 AI 生成**
   - DALL-E, Midjourney 等工具
   - Prompt: "256x256 icon of a garbage truck with location pin, flat design, green theme, transparent background"

3. **參考現有 Add-ons**
   - https://github.com/hassio-addons/repository
   - 參考其他 Add-on 的圖示設計

詳細指南：`trash_tracking_addon/ICON_README.md`

---

## ❓ 常見問題

### Q: Add-on 安裝後在哪裡？
A: **Supervisor** → **Add-on Store** → 往下捲找 "垃圾車追蹤系統"

### Q: 如何知道清運點名稱？
A: 使用內建 CLI 工具：
```bash
docker exec -it addon_trash_tracking python3 cli.py --lat 你的緯度 --lng 你的經度
```

### Q: 支援哪些架構？
A: 支援 5 種架構：aarch64, amd64, armhf, armv7, i386

### Q: API 在哪個 port？
A: `http://localhost:5000`

### Q: 如何更新 Add-on？
A: 用戶在 Add-on 頁面會看到 "Update" 按鈕

### Q: 如何除錯？
A: 查看 Add-on 的 Log 標籤，或設定 `log_level: "DEBUG"`

---

## 📚 完整文檔

| 文件 | 說明 |
|------|------|
| `PACKAGE_SUMMARY.md` | **📦 完整總結（推薦閱讀）** |
| `docs/ADD_ON_INSTALLATION.md` | **🔧 安裝與發布指南** |
| `trash_tracking_addon/DOCS.md` | **📖 用戶使用文檔** |
| `trash_tracking_addon/README.md` | 主要說明 |
| `trash_tracking_addon/CHANGELOG.md` | 版本記錄 |
| `trash_tracking_addon/ICON_README.md` | 圖示指南 |

---

## ✅ 發布檢查清單

- [ ] 已完成本地測試
- [ ] git commit 並 push
- [ ] 建立 v1.0.0 tag
- [ ] 在 GitHub 建立 Release
- [ ] （可選）測試用戶安裝流程
- [ ] （可選）改善圖示
- [ ] （可選）設定 GitHub Actions 自動構建

---

## 🎊 完成！

你的 Flask Application 現在已經是一個完整的 Home Assistant Add-on！

**下一步建議**：
1. ✅ 執行本地 Docker 測試
2. ✅ 提交到 GitHub
3. ✅ 建立 v1.0.0 Release
4. ✅ 在實際 HA 環境測試安裝
5. ⭐ 改善圖示設計（可選）
6. ⭐ 設定 CI/CD 自動構建（可選）

---

**維護者**: Logan ([@iml885203](https://github.com/iml885203))
**專案**: https://github.com/iml885203/trash_tracking
**授權**: MIT License
