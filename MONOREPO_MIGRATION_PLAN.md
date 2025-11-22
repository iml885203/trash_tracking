# Monorepo 遷移計畫

**目標:** 將專案重構為 monorepo 架構，分離核心邏輯和應用程式

**原則:**
- 每個 Task 獨立且可測試
- 完成一個 Task 就 commit
- 保持專案隨時可運行
- 向後相容，不破壞現有功能

---

## 📊 總覽

```
當前結構 → Monorepo 結構

trash_tracking/              trash_tracking/
├── src/                     ├── packages/
│   ├── clients/             │   └── core/
│   ├── models/              │       └── trash_tracking_core/
│   ├── core/                │           ├── clients/
│   ├── utils/               │           ├── models/
│   └── api/                 │           ├── core/
├── app.py                   │           └── utils/
├── cli.py                   ├── apps/
└── tests/                   │   ├── addon/
                             │   ├── cli/
                             │   └── integration/
                             └── tests/
```

---

## 📝 任務清單

### Phase 1: 準備階段（基礎建設）

#### ✅ Task 1.1: 創建 monorepo 目錄結構 ✔️ COMPLETED
**描述:** 建立基本的目錄架構，不移動任何現有程式碼
**完成時間:** 2025-11-23
**Commit:** 23adc27

**操作:**
```bash
mkdir -p packages/core/trash_tracking_core/{clients,models,core,utils}
mkdir -p apps/{addon,cli,integration}
mkdir -p tests/integration_tests
```

**檔案變更:**
- 新增: `packages/core/` 目錄
- 新增: `apps/` 目錄
- 不刪除任何現有檔案

**驗證:**
```bash
tree -L 3 packages/
tree -L 2 apps/
```

**Commit:**
```
chore: create monorepo directory structure

- Add packages/core/ for shared core logic
- Add apps/ for applications (addon, cli, integration)
- No existing code moved yet
```

**風險:** 🟢 無風險，只新增目錄

---

#### ✅ Task 1.2: 建立核心套件配置 ✔️ COMPLETED
**描述:** 創建 core package 的 pyproject.toml 和基本文件
**完成時間:** 2025-11-23
**Commit:** e87719c

**操作:**
```bash
# 創建以下檔案
packages/core/pyproject.toml
packages/core/README.md
packages/core/trash_tracking_core/__init__.py
```

**檔案變更:**
- 新增: `packages/core/pyproject.toml`
- 新增: `packages/core/README.md`
- 新增: `packages/core/trash_tracking_core/__init__.py` (空檔案)
- 不修改現有程式碼

**驗證:**
```bash
cd packages/core
python -m build --version  # 確認可以建置
```

**Commit:**
```
chore: add core package configuration

- Add pyproject.toml for trash-tracking-core package
- Add package README
- Add empty __init__.py for package structure
```

**風險:** 🟢 無風險，獨立於現有程式碼

---

### Phase 2: 複製核心邏輯（保持並存）

#### ⚠️ Task 2.1: 複製 models 到核心套件
**描述:** 複製（不移動）models 到 core package

**操作:**
```bash
cp -r src/models/* packages/core/trash_tracking_core/models/
# 修改 imports: src.models → trash_tracking_core.models
```

**檔案變更:**
- 複製: `src/models/*.py` → `packages/core/trash_tracking_core/models/`
- 修改: `packages/core/trash_tracking_core/models/*.py` 的 imports
- **不刪除** `src/models/`

**驗證:**
```bash
# 測試新的 models 可以 import
cd packages/core
python -c "from trash_tracking_core.models import Point, TruckLine"
```

**Commit:**
```
refactor: copy models to core package

- Copy src/models/ to packages/core/trash_tracking_core/models/
- Update internal imports to use trash_tracking_core
- Keep original src/models/ for backward compatibility
```

**風險:** 🟡 中等，需要修改 imports，但不影響現有程式碼

**依賴:** Task 1.2

---

#### ⚠️ Task 2.2: 複製 clients 到核心套件
**描述:** 複製（不移動）API clients

**操作:**
```bash
cp -r src/clients/* packages/core/trash_tracking_core/clients/
# 修改 imports
```

**檔案變更:**
- 複製: `src/clients/*.py` → `packages/core/trash_tracking_core/clients/`
- 修改: imports from `src.models` → `trash_tracking_core.models`
- **不刪除** `src/clients/`

**驗證:**
```bash
cd packages/core
python -c "from trash_tracking_core.clients import NTPCApiClient"
```

**Commit:**
```
refactor: copy clients to core package

- Copy src/clients/ to packages/core/trash_tracking_core/clients/
- Update imports to use trash_tracking_core.models
- Keep original src/clients/ for backward compatibility
```

**風險:** 🟡 中等

**依賴:** Task 2.1 (需要 models)

---

#### ⚠️ Task 2.3: 複製 core logic 到核心套件
**描述:** 複製追蹤邏輯

**操作:**
```bash
cp -r src/core/* packages/core/trash_tracking_core/core/
# 修改 imports
```

**檔案變更:**
- 複製: `src/core/*.py` → `packages/core/trash_tracking_core/core/`
- 修改: 所有 `src.*` imports → `trash_tracking_core.*`
- **不刪除** `src/core/`

**驗證:**
```bash
cd packages/core
python -c "from trash_tracking_core.core import TruckTracker"
```

**Commit:**
```
refactor: copy core logic to core package

- Copy src/core/ to packages/core/trash_tracking_core/core/
- Update all imports to use trash_tracking_core namespace
- Keep original src/core/ for backward compatibility
```

**風險:** 🟡 中等

**依賴:** Task 2.1, 2.2

---

#### ⚠️ Task 2.4: 複製 utils 到核心套件
**描述:** 複製工具函式

**操作:**
```bash
cp -r src/utils/* packages/core/trash_tracking_core/utils/
# 修改 imports，但保留 logger.py 指向原本的位置
```

**檔案變更:**
- 複製: `src/utils/*.py` → `packages/core/trash_tracking_core/utils/`
- 修改: imports
- **不刪除** `src/utils/`

**驗證:**
```bash
cd packages/core
python -c "from trash_tracking_core.utils import Geocoder, RouteAnalyzer"
```

**Commit:**
```
refactor: copy utils to core package

- Copy src/utils/ to packages/core/trash_tracking_core/utils/
- Update imports to use trash_tracking_core
- Keep original src/utils/ for backward compatibility
```

**風險:** 🟡 中等

**依賴:** Task 2.1, 2.2

---

#### ✅ Task 2.5: 更新核心套件的 __init__.py
**描述:** 導出公共 API

**操作:**
```python
# packages/core/trash_tracking_core/__init__.py
from trash_tracking_core.clients import NTPCApiClient
from trash_tracking_core.models import Point, TruckLine
# ... 等
```

**檔案變更:**
- 修改: `packages/core/trash_tracking_core/__init__.py`

**驗證:**
```bash
cd packages/core
python -c "import trash_tracking_core; print(trash_tracking_core.__version__)"
```

**Commit:**
```
feat: add public API exports for core package

- Export all public classes and functions
- Add __version__ attribute
- Document usage in package __init__.py
```

**風險:** 🟢 低

**依賴:** Task 2.1, 2.2, 2.3, 2.4

---

#### ✅ Task 2.6: 安裝核心套件為可編輯模式
**描述:** 讓核心套件可以被其他應用程式使用

**操作:**
```bash
cd packages/core
pip install -e .
```

**檔案變更:**
- 無程式碼變更
- 影響: Python 環境

**驗證:**
```bash
python -c "import trash_tracking_core; print('OK')"
```

**Commit:**
```
chore: make core package installable in editable mode

- Install trash-tracking-core as editable package
- Update development setup instructions
```

**風險:** 🟢 低

**依賴:** Task 2.5

---

### Phase 3: 遷移 Add-on（漸進式）

#### ⚠️ Task 3.1: 創建 apps/addon 結構
**描述:** 建立 Add-on 的新位置，但先不移動程式碼

**操作:**
```bash
mkdir -p apps/addon/{addon/api,addon/config}
cp app.py apps/addon/app_new.py  # 先複製一份
```

**檔案變更:**
- 新增: `apps/addon/` 目錄結構
- 新增: `apps/addon/app_new.py` (app.py 的副本)
- **不刪除** 根目錄的 `app.py`

**Commit:**
```
chore: create addon app structure

- Add apps/addon/ directory
- Copy app.py as reference (not moved yet)
- Prepare for gradual addon migration
```

**風險:** 🟢 低

**依賴:** 無

---

#### 🔴 Task 3.2: 更新 Add-on 使用核心套件
**描述:** 修改 Add-on 的 imports 使用 trash_tracking_core

**操作:**
```python
# 在 app.py 中
# 從: from src.core import TruckTracker
# 改為: from trash_tracking_core import TruckTracker
```

**檔案變更:**
- 修改: `app.py`
- 修改: `src/api/routes.py`
- 修改: `src/api/setup/routes.py`
- 將 `from src.*` 改為 `from trash_tracking_core.*`

**驗證:**
```bash
# 測試 Add-on 啟動
python app.py
curl http://localhost:5000/health
```

**Commit:**
```
refactor(addon): migrate addon to use core package

- Update imports from src.* to trash_tracking_core.*
- Add trash-tracking-core as dependency
- Verify addon still works correctly
```

**風險:** 🔴 高 - 會影響現有 Add-on 運作

**依賴:** Task 2.6

**回退計畫:** `git revert` 即可恢復

---

#### ⚠️ Task 3.3: 移動 Add-on 檔案到 apps/addon
**描述:** 將 Add-on 相關檔案移動到新位置

**操作:**
```bash
mv app.py apps/addon/
mv config.example.yaml apps/addon/
mv Dockerfile apps/addon/
mv docker-compose.yml apps/addon/
cp -r src/api apps/addon/addon/
```

**檔案變更:**
- 移動: `app.py` → `apps/addon/app.py`
- 移動: `config.example.yaml` → `apps/addon/`
- 移動: `Dockerfile` → `apps/addon/`
- 複製: `src/api/` → `apps/addon/addon/api/`
- 更新: 路徑引用

**驗證:**
```bash
cd apps/addon
python app.py
```

**Commit:**
```
refactor(addon): move addon files to apps/addon

- Move app.py, Dockerfile, config to apps/addon/
- Move API routes to apps/addon/addon/api/
- Update all path references
```

**風險:** 🟡 中等

**依賴:** Task 3.2

---

#### ✅ Task 3.4: 創建 Add-on pyproject.toml
**描述:** 為 Add-on 應用程式添加依賴管理

**操作:**
```toml
# apps/addon/pyproject.toml
[project]
name = "trash-tracking-addon"
dependencies = [
    "trash-tracking-core",
    "flask>=3.0.0",
]
```

**檔案變更:**
- 新增: `apps/addon/pyproject.toml`

**Commit:**
```
chore(addon): add addon package configuration

- Add pyproject.toml with dependencies
- Specify dependency on trash-tracking-core
```

**風險:** 🟢 低

**依賴:** Task 3.3

---

### Phase 4: 遷移 CLI

#### ✅ Task 4.1: 移動 CLI 到 apps/cli
**描述:** 移動 CLI 工具

**操作:**
```bash
mkdir -p apps/cli/cli
mv cli.py apps/cli/
# 更新 imports
```

**檔案變更:**
- 移動: `cli.py` → `apps/cli/cli.py`
- 修改: imports from `src.*` → `trash_tracking_core.*`

**驗證:**
```bash
cd apps/cli
python cli.py --help
```

**Commit:**
```
refactor(cli): move CLI to apps/cli and use core package

- Move cli.py to apps/cli/
- Update imports to use trash_tracking_core
- Verify CLI functionality
```

**風險:** 🟡 中等

**依賴:** Task 2.6

---

#### ✅ Task 4.2: 創建 CLI pyproject.toml
**描述:** CLI 的依賴管理

**操作:**
```toml
# apps/cli/pyproject.toml
[project]
name = "trash-tracking-cli"
dependencies = ["trash-tracking-core"]
```

**檔案變更:**
- 新增: `apps/cli/pyproject.toml`

**Commit:**
```
chore(cli): add CLI package configuration

- Add pyproject.toml for CLI app
- Specify dependency on trash-tracking-core
```

**風險:** 🟢 低

**依賴:** Task 4.1

---

### Phase 5: 清理舊結構

#### 🔴 Task 5.1: 刪除舊的 src/ 目錄
**描述:** 移除已遷移到 core package 的程式碼

**操作:**
```bash
# 僅刪除已遷移的部分
rm -rf src/models/
rm -rf src/clients/
rm -rf src/core/
# 保留 src/api/ 和 src/use_cases/ 因為它們是 addon 特有的
```

**檔案變更:**
- 刪除: `src/models/`, `src/clients/`, `src/core/`
- 保留: `src/api/`, `src/use_cases/` (addon 特有邏輯)
- 或者全部移到 `apps/addon/addon/`

**驗證:**
```bash
# 確認 addon 和 cli 仍然可以運行
cd apps/addon && python app.py
cd apps/cli && python cli.py --help
```

**Commit:**
```
chore: remove migrated code from src/

- Remove src/models/, src/clients/, src/core/
- These are now in packages/core/trash_tracking_core/
- Addon and CLI now use core package
```

**風險:** 🔴 高 - 刪除程式碼

**依賴:** Task 3.2, 4.1

**回退計畫:** Git revert

---

#### ✅ Task 5.2: 更新根目錄 README
**描述:** 更新文件說明新的 monorepo 結構

**操作:**
- 更新 `README.md` 說明新架構
- 更新安裝和開發說明

**檔案變更:**
- 修改: `README.md`

**Commit:**
```
docs: update README for monorepo structure

- Document new monorepo layout
- Update installation instructions
- Add development workflow for monorepo
```

**風險:** 🟢 低

**依賴:** Task 5.1

---

### Phase 6: 創建 Integration（新功能）

#### ✅ Task 6.1: 創建 Integration 基礎結構
**描述:** 建立 Integration 應用程式框架

**操作:**
```bash
mkdir -p apps/integration/custom_components/trash_tracking
# 創建基本檔案
```

**檔案變更:**
- 新增: `apps/integration/custom_components/trash_tracking/`
- 新增: `manifest.json`, `__init__.py` 等基本檔案

**Commit:**
```
feat(integration): create integration app structure

- Add apps/integration/ directory
- Create custom_components/trash_tracking/ structure
- Add basic manifest.json and __init__.py
```

**風險:** 🟢 低 - 全新功能

**依賴:** Task 2.6

---

#### ⚠️ Task 6.2: 實作 Integration Config Flow
**描述:** 實作多步驟設定流程

**操作:**
- 創建 `config_flow.py`
- 實作地址輸入 → 路線選擇 → 收集點選擇

**檔案變更:**
- 新增: `apps/integration/custom_components/trash_tracking/config_flow.py`

**Commit:**
```
feat(integration): implement multi-step config flow

- Add address input step with geocoding
- Add route selection step
- Add collection points selection step
- Use trash_tracking_core for logic
```

**風險:** 🟡 中等 - 新功能實作

**依賴:** Task 6.1

---

#### ⚠️ Task 6.3: 實作 Integration Coordinator
**描述:** 實作資料更新協調器

**操作:**
- 創建 `coordinator.py`
- 使用 `trash_tracking_core` 的追蹤邏輯

**檔案變更:**
- 新增: `apps/integration/custom_components/trash_tracking/coordinator.py`

**Commit:**
```
feat(integration): implement data update coordinator

- Add TrashTrackingCoordinator
- Use NTPCApiClient from core package
- Implement tracking logic using PointMatcher
```

**風險:** 🟡 中等

**依賴:** Task 6.2

---

#### ⚠️ Task 6.4: 實作 Integration Sensors
**描述:** 實作感測器實體

**操作:**
- 創建 `sensor.py`, `binary_sensor.py`

**檔案變更:**
- 新增: `sensor.py`, `binary_sensor.py`

**Commit:**
```
feat(integration): implement sensor entities

- Add status sensor and truck info sensor
- Add binary sensor for nearby detection
- Connect to coordinator for data updates
```

**風險:** 🟡 中等

**依賴:** Task 6.3

---

## 📊 任務依賴圖

```
Phase 1 (準備)
1.1 → 1.2

Phase 2 (複製核心)
1.2 → 2.1 → 2.2 → 2.3 → 2.5 → 2.6
         ↓
        2.4 ↗

Phase 3 (遷移 Addon)
2.6 → 3.1 → 3.2 → 3.3 → 3.4

Phase 4 (遷移 CLI)
2.6 → 4.1 → 4.2

Phase 5 (清理)
3.2 + 4.1 → 5.1 → 5.2

Phase 6 (新 Integration)
2.6 → 6.1 → 6.2 → 6.3 → 6.4
```

---

## 🎯 執行策略建議

### 策略 A: 保守漸進式（推薦）
**順序:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

**優點:**
- ✅ 每步都可驗證
- ✅ 隨時可回退
- ✅ 風險可控

**缺點:**
- ⏰ 時間較長（需要多次測試）

### 策略 B: 並行開發
**順序:** Phase 1 → Phase 2 → (Phase 3 + Phase 6 並行) → Phase 4 → Phase 5

**優點:**
- ⏱️ 節省時間
- 🚀 Integration 可以更快開發

**缺點:**
- ⚠️ 複雜度較高
- ⚠️ 可能需要解決衝突

---

## ✅ 檢查清單

每個 Task 完成後檢查：

- [ ] 程式碼變更已提交
- [ ] Commit message 清楚描述變更
- [ ] 相關測試通過
- [ ] 文件已更新（如需要）
- [ ] 沒有破壞現有功能

---

## 🔄 回退計畫

如果任何 Task 出現問題：

```bash
# 方法 1: Revert 最後一個 commit
git revert HEAD

# 方法 2: Reset 到之前的 commit
git reset --hard <commit-hash>

# 方法 3: 創建修復 commit
# 修正問題後 commit
```

---

**最後更新:** 2025-11-23
**狀態:** 規劃中
