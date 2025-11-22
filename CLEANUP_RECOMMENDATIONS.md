# 清理建議報告

**檢查日期:** 2025-11-22
**目的:** 移除遺留程式碼和文件,準備部署

---

## 📋 發現的問題

### 🔴 必須處理的項目

#### 1. 重複的配置檔案範例
**發現:**
- `config.example.yaml` (1873 bytes)
- `config.yaml.example` (1873 bytes)

**問題:** 兩個檔案內容完全相同

**建議:**
```bash
# 刪除其中一個,只保留 config.example.yaml
rm config.yaml.example
```

**理由:**
- 只需要一個範例檔案
- `config.example.yaml` 是更常見的命名慣例

---

#### 2. 舊的 venv 目錄
**發現:**
- `venv/` (28 KB) - 建立失敗的舊虛擬環境
- `.venv/` (221 MB) - uv 建立的新虛擬環境

**問題:** `venv/` 是之前建立失敗的虛擬環境,現在使用 `.venv/`

**建議:**
```bash
# 刪除舊的 venv 目錄
rm -rf venv/
```

**理由:**
- `.gitignore` 已經忽略 `venv/`
- 不需要兩個虛擬環境
- 節省空間

---

#### 3. 用戶特定配置檔案
**發現:**
- `config.yaml` (616 bytes) - 包含你的個人配置

**內容:**
```yaml
location:
  lat: 25.0084129
  lng: 121.4603453
tracking:
  enter_point: 中山路一段30號
  exit_point: 中山路一段102號
  target_lines:
    - A12路線晚上
    - A12路線下午(2.5.6版)
    # ... 你的個人路線
```

**問題:** 這是你的個人配置,不應該提交到 Git

**建議:**
```bash
# 不需要刪除,但確認 .gitignore 已經忽略它
grep "config.yaml" .gitignore
# 應該看到: config.yaml
```

**理由:**
- `.gitignore` 已經正確忽略 `config.yaml`
- 這是預期行為 - 每個用戶應該有自己的配置

**狀態:** ✅ 已正確處理 (被 .gitignore 忽略)

---

### 🟡 可選清理項目

#### 4. Integration 測試相關文件整合
**發現:** 4 個 Integration 相關的 Markdown 文件

```
INTEGRATION_GUIDE.md           - 技術實作指南
INTEGRATION_SUMMARY.md         - 實作總結
INTEGRATION_TEST_REPORT.md    - 測試報告
TESTING_COMPLETE.md            - 測試完成報告
```

**問題:** 文件有些重複和重疊

**建議選項 A (保留全部):**
保持現狀,作為開發歷程記錄

**建議選項 B (整合):**
```bash
# 建立單一文件
mkdir -p docs/integration/
mv INTEGRATION_GUIDE.md docs/integration/
mv INTEGRATION_TEST_REPORT.md docs/integration/
mv TESTING_COMPLETE.md docs/integration/

# 將 INTEGRATION_SUMMARY.md 內容整合到 README.md 的 Integration 章節
# 然後刪除
rm INTEGRATION_SUMMARY.md
```

**建議:** 選項 A (保留全部)
- 這些文件互補,不完全重複
- 有助於理解 Integration 開發過程
- 可以作為文件參考

---

## 🟢 正確的項目 (不需要刪除)

### 1. DEVELOPMENT.md
**狀態:** ✅ 保留
**理由:** 開發指南,對貢獻者有用

### 2. docs/ 目錄
**內容:**
- `architecture.md` - 架構文件
- `api-specification.md` - API 規格
- `CI_CD_SETUP.md` - CI/CD 設定
- `VERSIONING.md` - 版本管理
- `SETUP_PAT.md` - PAT 設定

**狀態:** ✅ 全部保留
**理由:** 都是有用的技術文件

### 3. custom_components/trash_tracking/
**狀態:** ✅ 保留
**理由:** 新建立的 Integration,核心功能

### 4. features/ 目錄
**內容:** BDD 測試檔案

**狀態:** ✅ 保留
**理由:** 測試和文件

---

## ⚠️ 需要注意的項目

### README.md 中的過時引用

**問題:** README 引用了不存在的 `trash_tracking_addon/` 目錄

**發現的引用:**
```markdown
- Or see [Complete User Guide](trash_tracking_addon/DOCS.md)
- 📘 [Complete User Guide](trash_tracking_addon/DOCS.md)
- 📗 [Add-on Overview](trash_tracking_addon/README.md)
- More examples: [trash_tracking_addon/DOCS.md]
├── trash_tracking_addon/       # Home Assistant Add-on package
```

**說明:**
- Add-on 的檔案在另一個 repository: `/home/dodoro/dev/homeassistant-addons/trash-tracking/`
- 這個專案是主要的**應用程式**
- Add-on 是在**不同 repository** 中的包裝

**建議:** 更新 README.md 連結指向正確的 repository

```markdown
# 舊的 (錯誤)
[Complete User Guide](trash_tracking_addon/DOCS.md)

# 新的 (正確)
[Complete User Guide](https://github.com/iml885203/homeassistant-addons/blob/master/trash-tracking/DOCS.md)
```

---

## 📊 清理總結

### 必須刪除 (2 項)
- ❌ `config.yaml.example` - 重複檔案
- ❌ `venv/` - 舊的虛擬環境

### 建議整合 (0-1 項)
- 🟡 `INTEGRATION_SUMMARY.md` - 可選,建議保留

### 必須更新 (1 項)
- 📝 `README.md` - 更新 Add-on 文件連結

### 正確保留 (所有其他項目)
- ✅ 所有 Integration 檔案
- ✅ 所有文件
- ✅ 所有測試
- ✅ 所有核心程式碼

---

## 🚀 執行清理的指令

### 步驟 1: 刪除重複和舊檔案

```bash
cd /home/dodoro/dev/trash_tracking

# 刪除重複的配置範例
rm config.yaml.example

# 刪除舊的 venv
rm -rf venv/

# 確認刪除
ls -la | grep -E "config|venv"
```

### 步驟 2: 更新 README.md

需要手動編輯 `README.md`,將所有 `trash_tracking_addon/` 引用改為:
- GitHub URL: `https://github.com/iml885203/homeassistant-addons/blob/master/trash-tracking/`
- 或者從 README 中移除這些引用,因為是不同的 repository

### 步驟 3: 驗證

```bash
# 檢查沒有 broken links
grep -n "trash_tracking_addon" README.md

# 檢查目錄結構
tree -L 2 -I '.venv|.git|__pycache__'
```

---

## 📁 清理後的專案結構

```
trash_tracking/                      # 主應用程式
├── custom_components/trash_tracking/  # ✨ Integration (新增)
├── src/                              # 核心應用程式
├── features/                         # BDD 測試
├── docs/                             # 技術文件
├── tests/                            # 單元測試
├── app.py                            # Flask 應用
├── cli.py                            # CLI 工具
├── config.example.yaml               # 配置範例
├── Dockerfile                        # Docker 建構
├── docker-compose.yml                # Docker Compose
├── requirements.txt                  # 生產依賴
├── requirements-dev.txt              # 開發依賴
├── README.md                         # 主文件 (需更新連結)
├── DEVELOPMENT.md                    # 開發指南
├── INTEGRATION_GUIDE.md              # Integration 技術文件
├── INTEGRATION_TEST_REPORT.md        # 測試報告
├── TESTING_COMPLETE.md               # 測試完成
└── ...

homeassistant-addons/                # Add-on repository (分開的)
└── trash-tracking/                  # Add-on 包裝
    ├── DOCS.md                      # Add-on 使用文件
    ├── README.md                    # Add-on 說明
    └── config.yaml                  # Add-on 配置
```

---

## ✅ 清理檢查清單

- [ ] 刪除 `config.yaml.example`
- [ ] 刪除 `venv/` 目錄
- [ ] 更新 README.md 中的 Add-on 連結
- [ ] 確認 `.gitignore` 正確忽略 `config.yaml`
- [ ] 驗證沒有 broken links
- [ ] 確認所有 Integration 檔案完整

---

**建議:** 先執行必須清理的項目,README 更新可以之後慢慢處理。

**準備部署:** 清理後專案結構會更清晰,準備發布 Integration。
