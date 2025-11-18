# CI/CD 設置指南

本文檔說明如何設置和配置專案的 CI/CD 流程，包括 GitHub Actions 和 SonarQube 整合。

## 目錄

1. [GitHub Actions 設置](#github-actions-設置)
2. [SonarQube 整合](#sonarqube-整合)
3. [程式碼品質工具](#程式碼品質工具)
4. [本地開發環境](#本地開發環境)

---

## GitHub Actions 設置

### 1. CI/CD Pipeline 概述

專案使用 GitHub Actions 進行持續整合和持續部署，每次 push 或 pull request 都會自動執行以下檢查：

- **程式碼品質檢查**：flake8, black, isort, mypy
- **單元測試**：pytest 測試所有模組
- **測試覆蓋率**：生成並上傳覆蓋率報告
- **安全掃描**：bandit, safety, pip-audit
- **SonarQube 分析**：代碼質量和技術債務分析
- **Docker 建置測試**：確保 Docker 映像可正常建置

### 2. 必要的 GitHub Secrets

在 GitHub repository 設置中需要配置以下 secrets：

#### Codecov (可選)
```
CODECOV_TOKEN=<your-codecov-token>
```
獲取方式：
1. 訪問 https://codecov.io
2. 使用 GitHub 帳號登入
3. 新增專案並獲取 token

#### SonarQube (必需，如果使用 SonarQube)
```
SONAR_TOKEN=<your-sonar-token>
SONAR_HOST_URL=<your-sonarqube-server-url>
```

獲取方式：

**選項 1：使用 SonarCloud (推薦用於開源專案)**
1. 訪問 https://sonarcloud.io
2. 使用 GitHub 帳號登入
3. 新增組織和專案
4. 生成 token: Account > Security > Generate Tokens
5. 設置 secrets:
   - `SONAR_TOKEN`: 生成的 token
   - `SONAR_HOST_URL`: `https://sonarcloud.io`

**選項 2：自架 SonarQube Server**
1. 部署 SonarQube Server (使用 Docker)：
   ```bash
   docker run -d --name sonarqube \
     -p 9000:9000 \
     -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
     sonarqube:community
   ```
2. 訪問 http://localhost:9000 (預設帳號：admin/admin)
3. 建立新專案並生成 token
4. 設置 secrets:
   - `SONAR_TOKEN`: 生成的 token
   - `SONAR_HOST_URL`: 你的 SonarQube Server URL

### 3. Workflow 檔案結構

```
.github/
└── workflows/
    └── ci.yml    # 主要的 CI/CD workflow
```

### 4. 觸發條件

- **Push 事件**：推送到 `master` 或 `develop` 分支
- **Pull Request 事件**：對 `master` 或 `develop` 分支的 PR

### 5. 工作流程說明

#### Job 1: test
- 執行環境：Ubuntu Latest
- Python 版本：3.11, 3.12 (矩陣建置)
- 步驟：
  1. Checkout 程式碼
  2. 設置 Python 環境
  3. 快取依賴
  4. 安裝依賴
  5. Lint 檢查 (flake8)
  6. 格式檢查 (black)
  7. Import 排序檢查 (isort)
  8. 型別檢查 (mypy)
  9. 執行測試並生成覆蓋率報告
  10. 上傳覆蓋率到 Codecov
  11. SonarQube 掃描
  12. 上傳測試結果

#### Job 2: security
- 安全性掃描：
  - `bandit`: Python 代碼安全漏洞掃描
  - `safety`: 依賴套件已知漏洞檢查
  - `pip-audit`: PyPI 套件安全審計

#### Job 3: docker
- 測試 Docker 映像建置
- 驗證應用程式在容器中可正常運行

---

## SonarQube 整合

### 1. 專案配置

SonarQube 配置檔案位於：`sonar-project.properties`

主要配置項：
```properties
sonar.projectKey=trash_tracking
sonar.projectName=Trash Tracking System
sonar.projectVersion=1.0.0

sonar.sources=src,cli.py,app.py
sonar.tests=tests

sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=test-results.xml
```

### 2. Quality Gate 設定

建議的 Quality Gate 標準：
- 覆蓋率: >= 80%
- 重複代碼: <= 3%
- 可維護性評級: A
- 可靠性評級: A
- 安全性評級: A
- 技術債務比率: <= 5%

### 3. 查看分析結果

1. 推送程式碼後，GitHub Actions 會自動執行 SonarQube 掃描
2. 訪問你的 SonarQube Server/SonarCloud 查看詳細報告
3. 在 GitHub PR 中會顯示 Quality Gate 狀態

---

## 程式碼品質工具

### 1. Flake8 (Linting)

配置檔案：`.flake8`

執行命令：
```bash
flake8 src tests cli.py app.py
```

主要檢查：
- PEP 8 風格違規
- 語法錯誤
- 未使用的變數
- 程式複雜度

### 2. Black (格式化)

配置檔案：`pyproject.toml` -> `[tool.black]`

執行命令：
```bash
# 檢查
black --check src tests cli.py app.py

# 自動格式化
black src tests cli.py app.py
```

### 3. isort (Import 排序)

配置檔案：`pyproject.toml` -> `[tool.isort]`

執行命令：
```bash
# 檢查
isort --check-only src tests cli.py app.py

# 自動排序
isort src tests cli.py app.py
```

### 4. mypy (型別檢查)

配置檔案：`pyproject.toml` -> `[tool.mypy]`

執行命令：
```bash
mypy src --ignore-missing-imports
```

### 5. 一鍵執行所有檢查

建立 `Makefile` 或使用以下腳本：

```bash
#!/bin/bash
# check_code.sh

echo "Running flake8..."
flake8 src tests cli.py app.py

echo "Running black..."
black --check src tests cli.py app.py

echo "Running isort..."
isort --check-only src tests cli.py app.py

echo "Running mypy..."
mypy src --ignore-missing-imports

echo "Running tests..."
pytest tests/ --cov=src --cov-report=term-missing

echo "All checks passed!"
```

---

## 本地開發環境

### 1. 安裝開發依賴

```bash
pip install -r requirements-dev.txt
```

### 2. Pre-commit Hooks (建議)

安裝 pre-commit：
```bash
pip install pre-commit
```

建立 `.pre-commit-config.yaml`：
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

啟用 pre-commit：
```bash
pre-commit install
```

### 3. 本地測試流程

推送前的檢查清單：

```bash
# 1. 執行程式碼格式化
black src tests cli.py app.py
isort src tests cli.py app.py

# 2. 執行 linting
flake8 src tests cli.py app.py

# 3. 執行型別檢查
mypy src --ignore-missing-imports

# 4. 執行測試
pytest tests/ --cov=src --cov-report=html

# 5. 檢查覆蓋率報告
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
```

### 4. 測試覆蓋率目標

- **整體目標**: >= 80%
- **關鍵模組**: >= 90%
  - `src/models/`
  - `src/core/state_manager.py`
  - `src/api/routes.py`

---

## 常見問題

### Q1: CI 失敗：flake8 錯誤

**解決方案**：
```bash
# 在本地執行並修正
flake8 src tests cli.py app.py

# 常見問題：
# - E501: 行太長 (使用 black 自動格式化)
# - F401: 未使用的 import (手動移除)
# - E402: import 位置錯誤 (移到檔案開頭)
```

### Q2: CI 失敗：black 格式檢查

**解決方案**：
```bash
# 自動格式化
black src tests cli.py app.py

# 提交變更
git add .
git commit -m "style: apply black formatting"
```

### Q3: CI 失敗：測試覆蓋率不足

**解決方案**：
```bash
# 查看哪些程式碼缺少測試
pytest tests/ --cov=src --cov-report=term-missing

# 為缺少覆蓋的模組新增測試
# 目標：達到 80% 以上覆蓋率
```

### Q4: SonarQube Quality Gate 失敗

**可能原因**：
- 程式碼重複率過高
- 技術債務過多
- 安全漏洞
- 覆蓋率不足

**解決方案**：
1. 登入 SonarQube 查看詳細報告
2. 根據建議修正問題
3. 重新提交

---

## 持續改進

### 監控指標

定期檢查以下指標：
- 測試覆蓋率趨勢
- 程式碼複雜度
- 技術債務
- 安全漏洞數量
- 建置時間

### 優化建議

1. **減少建置時間**：
   - 使用快取（已啟用）
   - 並行執行測試
   - 優化 Docker 建置

2. **提升程式碼品質**：
   - 定期重構
   - 降低程式複雜度
   - 增加測試覆蓋率

3. **加強安全性**：
   - 定期更新依賴套件
   - 修復安全漏洞
   - 使用最新的基礎映像

---

## 參考資源

- [GitHub Actions 文檔](https://docs.github.com/en/actions)
- [SonarQube 文檔](https://docs.sonarqube.org/)
- [pytest 文檔](https://docs.pytest.org/)
- [Black 文檔](https://black.readthedocs.io/)
- [Flake8 文檔](https://flake8.pycqa.org/)
