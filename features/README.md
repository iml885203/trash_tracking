# BDD 整合測試 (Behavior-Driven Development)

使用 Behave 框架的 BDD 風格整合測試，用 Gherkin 語法撰寫使用者場景。

**特色**：✨ 完全從使用者視角撰寫，非技術人員也能閱讀理解

## 📋 測試場景

### 1. CLI 查詢 (`cli_query.feature`)
從**新北市居民**的角度撰寫：
- ✅ 查詢我家附近的垃圾車
- ✅ 擴大搜尋範圍找垃圾車
- ✅ 只關心特定路線的垃圾車
- ✅ 輸入錯誤的地址

### 2. Integration Config Flow (`config_flow.feature`)
從 **Home Assistant 使用者**的角度撰寫：
- ✅ 第一次設定我家的垃圾車通知
- ✅ 輸入的地址找不到
- ✅ 我住的地方太偏遠沒有垃圾車路線
- ✅ 確認選擇的路線有經過我家附近

## 🚀 運行測試

### 前置需求

```bash
# 安裝 behave
pip install behave
```

### 基本用法

```bash
# 運行所有 feature（使用 mock API）
USE_MOCK_API=true python -m behave features/

# 運行特定 feature
python -m behave features/cli_query.feature

# 運行特定場景
python -m behave features/cli_query.feature:7  # 第 7 行的場景

# 顯示詳細輸出
python -m behave features/ -v

# 只顯示失敗的場景
python -m behave features/ --no-capture

# 使用特定標籤
python -m behave features/ --tags=@real_api
```

### Mock API vs Real API

預設使用 mock API 進行測試（快速且不依賴外部服務）：

```bash
# 使用 mock API（預設）
USE_MOCK_API=true python -m behave features/

# 使用真實 NTPC API
USE_MOCK_API=false python -m behave features/
```

⚠️ **注意**：使用真實 API 時：
- 需要網路連線
- 測試速度較慢
- 可能受外部 API 可用性影響

## 📊 測試報告

### 產生 JUnit XML 報告

```bash
python -m behave features/ --junit --junit-directory reports/
```

### 產生 HTML 報告

```bash
# 安裝 behave-html-formatter
pip install behave-html-formatter

# 產生報告
python -m behave features/ -f html -o reports/report.html
```

### 產生 JSON 報告

```bash
python -m behave features/ -f json -o reports/report.json
```

## 📝 .feature 檔案結構

```gherkin
# language: zh-TW
功能: 功能名稱
  作為一個 [角色]
  我想要 [做什麼]
  以便 [達成目標]

  背景:
    假設 [前置條件]

  場景: 場景名稱
    當 [執行動作]
    那麼 [預期結果]
    而且 [額外驗證]

  場景大綱: 參數化場景
    當 我輸入 "<參數>"
    那麼 結果應該是 "<預期>"

    例子:
      | 參數 | 預期 |
      | 值1  | 結果1 |
      | 值2  | 結果2 |
```

## 🎯 Step Definitions

Step definitions 位於 `features/steps/` 目錄：

- `cli_steps.py` - CLI 查詢相關步驟
- `config_flow_steps.py` - Integration config flow 相關步驟
- `integration_imports_steps.py` - Integration 導入測試步驟

### 新增步驟範例

```python
from behave import given, when, then

@given('系統已啟動')
def step_system_started(context):
    # 設定前置條件
    context.system_ready = True

@when('使用者執行 "{action}"')
def step_user_action(context, action):
    # 執行動作
    context.result = perform_action(action)

@then('結果應該是 "{expected}"')
def step_verify_result(context, expected):
    # 驗證結果
    assert context.result == expected
```

## 🔄 執行順序

1. `environment.py` - `before_all()` (一次)
2. 對每個場景:
   - `environment.py` - `before_scenario()`
   - Feature 背景 (Background)
   - 場景步驟 (Scenario steps)
   - `environment.py` - `after_scenario()`
3. `environment.py` - `after_all()` (一次)

## 🏷️ 標籤 (Tags)

使用標籤來組織和選擇性運行測試：

```gherkin
@real_api
場景: 使用真實 API 測試
  ...

@slow
場景: 慢速測試
  ...
```

```bash
# 只運行 @real_api 標籤
python -m behave features/ --tags=@real_api

# 排除 @slow 標籤
python -m behave features/ --tags=-slow

# 組合條件
python -m behave features/ --tags="@real_api and not @slow"
```

## 📈 最佳實踐

### ✨ 使用者視角優先

1. **使用使用者的語言，不用技術術語**
   - ✅ 好: "當 我查詢附近的垃圾車"
   - ❌ 差: "當 我發送 GET 請求到 /api/trucks"
   - ✅ 好: "那麼 系統應該找到我家的位置座標"
   - ❌ 差: "那麼 geocoding 應該成功"

2. **描述真實的使用情境**
   - ✅ 好: "場景: 輸入錯誤的地址"
   - ❌ 差: "場景: Geocoding fails with invalid address"
   - ✅ 好: "假設 我不小心輸入了錯誤的地址"
   - ❌ 差: "假設 address validation fails"

3. **聚焦使用者價值，不是技術實作**
   - ✅ 好: "我想要設定垃圾車接近時自動通知我"
   - ❌ 差: "我想要配置 integration config flow"

4. **錯誤訊息要清楚易懂**
   - ✅ 好: "那麼 系統應該告訴我地址有問題"
   - ❌ 差: "那麼 應該返回 400 錯誤碼"

### 💡 其他最佳實踐

5. **使用有意義的場景名稱**
   - ✅ 好: "查詢我家附近的垃圾車"
   - ❌ 差: "測試功能 1"

6. **保持步驟簡潔明確**
   - 每個步驟只做一件事
   - 使用清晰的動詞 (假設/當/那麼)

7. **適當使用背景 (Background)**
   - 只放置所有場景共用的步驟
   - 保持背景簡短

## 🔍 除錯技巧

```bash
# 顯示完整錯誤追蹤
python -m behave features/ --no-capture-stderr

# 在失敗時停止
python -m behave features/ --stop

# 只運行失敗的場景
python -m behave features/ --failed

# 乾跑 (不執行步驟，只檢查語法)
python -m behave features/ --dry-run
```

## 📊 與 pytest 比較

| 特性 | Behave (BDD) | pytest |
|------|-------------|--------|
| 測試語法 | Gherkin (自然語言) | Python code |
| 可讀性 | 非技術人員可讀 | 開發者可讀 |
| 適用場景 | 使用者行為測試 | 單元/整合測試 |
| 重用性 | 步驟可重用 | Fixture 重用 |
| 文件化 | Feature 即文件 | 需額外文件 |

## 🎊 總結

BDD 測試的優點：
- ✅ 測試即文件，非技術人員可讀
- ✅ 專注於使用者行為和價值
- ✅ 促進團隊溝通
- ✅ 步驟定義可重用

適合用於：
- 整合測試
- 端到端測試
- 驗收測試
- 需求文件化
