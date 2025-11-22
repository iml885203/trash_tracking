# language: zh-TW
功能: Add-on 和 Integration 共存
  作為一個 Home Assistant 使用者
  我想要能夠同時使用 Add-on 和 Integration
  以便保留所有現有功能並獲得更好的整合體驗

  背景:
    假設 垃圾車追蹤 Add-on 已安裝並運行
    而且 Add-on 提供 Setup Wizard 和 REST API

  # ============================================================
  # 場景 1: Add-on 功能完全保留
  # ============================================================
  場景: Add-on 的 Setup Wizard 仍然可用
    假設 垃圾車追蹤 Integration 已安裝
    當 我訪問 Add-on 的 Ingress 頁面
    那麼 Setup Wizard 應該正常載入
    而且 我應該能輸入地址並取得建議
    而且 我應該能儲存配置
    而且 Setup Wizard 功能不應該受 Integration 影響

  場景: Add-on 的 REST API 仍然可用
    假設 垃圾車追蹤 Integration 已安裝
    當 我直接訪問 Add-on API "/api/trash/status"
    那麼 API 應該正常回應
    而且 回應格式應該與之前相同
    而且 API 功能不應該受 Integration 影響

  場景: Add-on 的 CLI 工具仍然可用
    假設 垃圾車追蹤 Integration 已安裝
    當 我在 Add-on 容器中執行 CLI 工具
      """
      python3 cli.py --lat 25.018269 --lng 121.471703
      """
    那麼 CLI 應該正常顯示附近的垃圾車
    而且 CLI 功能不應該受 Integration 影響

  場景: 傳統的 RESTful Sensor 仍然可用
    假設 用戶使用傳統的 RESTful sensor 配置:
      """
      sensor:
        - platform: rest
          name: "Garbage Truck Monitor"
          resource: "http://localhost:5000/api/trash/status"
      """
    而且 垃圾車追蹤 Integration 已安裝
    當 Home Assistant 重新載入配置
    那麼 RESTful sensor 應該仍然可以運作
    而且 不應該與 Integration 的實體衝突

  # ============================================================
  # 場景 2: Integration 作為 Add-on 的前端
  # ============================================================
  場景: Integration 從 Add-on 讀取資料
    假設 Add-on 正在追蹤路線 "A12路線晚上"
    而且 垃圾車追蹤 Integration 已安裝並連接到 Add-on
    當 垃圾車接近並觸發 Add-on 狀態變更
    那麼 Add-on API 應該返回 "nearby" 狀態
    而且 Integration 應該在下次更新時獲取該狀態
    而且 Integration 的實體應該更新為 "nearby"
    而且 資料應該完全一致

  場景: Integration 不修改 Add-on 的行為
    假設 垃圾車追蹤 Integration 已安裝
    當 Integration 輪詢 Add-on API 獲取資料
    那麼 Add-on 的狀態管理不應該被影響
    而且 Add-on 的日誌應該只記錄正常的 API 請求
    而且 Add-on 的效能不應該下降

  場景: Add-on 配置變更後 Integration 自動適應
    假設 垃圾車追蹤 Integration 已安裝
    當 我透過 Add-on Setup Wizard 變更追蹤路線
    而且 我重啟 Add-on 套用新配置
    而且 Integration 下次更新資料
    那麼 Integration 應該獲取新的路線資訊
    而且 實體屬性應該顯示新的路線名稱

  # ============================================================
  # 場景 3: 兩種使用方式的選擇
  # ============================================================
  場景: 用戶可以選擇只使用 Add-on
    假設 用戶只安裝了 Add-on
    而且 用戶使用傳統的 RESTful sensor 配置
    那麼 系統應該正常運作
    而且 用戶可以使用 Setup Wizard 配置
    而且 用戶可以使用自動化控制裝置

  場景: 用戶可以選擇只使用 Integration
    假設 用戶已安裝 Add-on 作為資料源
    而且 用戶已安裝 Integration
    而且 用戶移除了傳統的 RESTful sensor 配置
    那麼 系統應該正常運作
    而且 用戶只需要透過 Integration 實體建立自動化
    而且 用戶不需要手動編寫 sensor 配置

  場景: 用戶可以同時使用兩者
    假設 用戶同時保留 RESTful sensor 和 Integration
    那麼 兩者應該都能正常運作
    而且 資料應該保持一致
    而且 不應該有衝突或錯誤

  # ============================================================
  # 場景 4: 安裝順序的靈活性
  # ============================================================
  場景: 先安裝 Add-on 再安裝 Integration
    當 我先安裝並設定 Add-on
    而且 Add-on 已經在追蹤垃圾車
    而且 我再安裝 Integration
    那麼 Integration 應該立即連接到 Add-on
    而且 Integration 應該顯示目前的垃圾車狀態
    而且 不需要重新配置 Add-on

  場景: 先安裝 Integration 但 Add-on 還沒啟動
    當 我先安裝 Integration
    而且 我輸入 API URL "http://localhost:5000"
    但是 Add-on 還沒有啟動
    那麼 Integration 設定應該失敗
    而且 應該顯示錯誤訊息提示先啟動 Add-on
    當 我啟動 Add-on 後
    而且 我重新設定 Integration
    那麼 Integration 應該成功連接

  # ============================================================
  # 場景 5: 資料一致性
  # ============================================================
  場景: Add-on 和 Integration 顯示相同的資料
    假設 Add-on API 返回垃圾車狀態 "nearby"
    而且 垃圾車路線為 "A12路線晚上"
    當 我查看 RESTful sensor "sensor.garbage_truck_monitor"
    而且 我查看 Integration sensor "sensor.trash_tracking_status"
    那麼 兩個 sensor 的 state 都應該是 "nearby"
    而且 兩個 sensor 的 line_name 屬性都應該是 "A12路線晚上"
    而且 資料應該完全一致

  場景: 時間戳記同步
    假設 Add-on 在 "2025-11-22T20:00:00+08:00" 更新狀態
    當 Integration 在 20:01 更新資料
    那麼 Integration 獲取的 timestamp 應該是 "2025-11-22T20:00:00+08:00"
    而且 實體的 last_updated 應該是 20:01
    而且 用戶應該能區分 "資料產生時間" 和 "實體更新時間"

  # ============================================================
  # 場景 6: Add-on 更新和維護
  # ============================================================
  場景: Add-on 版本更新不影響 Integration
    假設 垃圾車追蹤 Integration 已安裝
    當 Add-on 從版本 2025.11.6 更新到 2025.12.0
    而且 API 介面保持相容
    那麼 Integration 應該繼續正常運作
    而且 不需要重新配置 Integration
    而且 實體應該繼續更新

  場景: Add-on API 介面變更需要 Integration 更新
    假設 Add-on 更新並變更 API 回應格式
    當 Integration 請求舊格式的資料
    那麼 Integration 應該檢測到不相容
    而且 應該在日誌中記錄警告
    而且 應該提示用戶更新 Integration

  場景: Add-on 暫時停止進行維護
    假設 垃圾車追蹤 Integration 已安裝並運行
    當 我停止 Add-on 進行設定變更
    那麼 Integration 實體應該標記為 "不可用"
    當 我重新啟動 Add-on
    而且 Add-on 完全啟動
    那麼 Integration 應該自動重新連接
    而且 實體應該恢復可用狀態

  # ============================================================
  # 場景 7: 移除和清理
  # ============================================================
  場景: 移除 Integration 不影響 Add-on
    假設 Add-on 和 Integration 都在運行
    當 我移除 Integration
    那麼 Add-on 應該繼續正常運作
    而且 Add-on 的 API 應該仍然可用
    而且 Setup Wizard 應該仍然可用
    而且 傳統的 RESTful sensor（如果有）應該仍然可用

  場景: 移除 Add-on 導致 Integration 無法使用
    假設 Add-on 和 Integration 都在運行
    當 我移除 Add-on
    那麼 Integration 應該無法連接到 API
    而且 Integration 實體應該標記為 "不可用"
    而且 應該在日誌中記錄連接失敗
    而且 用戶應該收到通知建議移除 Integration

  # ============================================================
  # 場景 8: 文件和使用者指引
  # ============================================================
  場景: README 文件說明兩種使用方式
    假設 我閱讀專案的 README.md
    那麼 應該清楚說明 Add-on 的功能
    而且 應該清楚說明 Integration 的功能
    而且 應該說明兩者的差異和適用場景
    而且 應該說明如何同時使用兩者

  場景: Integration 文件引導用戶先安裝 Add-on
    假設 我閱讀 Integration 的安裝說明
    那麼 應該明確說明需要先安裝 Add-on
    而且 應該提供 Add-on 的安裝連結
    而且 應該說明如何驗證 Add-on 正常運行
    而且 應該說明 API URL 的設定方式

  # ============================================================
  # 場景 9: 效能影響
  # ============================================================
  場景: Integration 不增加額外的 API 負擔
    假設 Add-on 每 90 秒被 RESTful sensor 輪詢一次
    當 我新增 Integration 也設定為 90 秒更新
    那麼 API 總請求頻率應該合理
    而且 Integration 不應該產生過多負擔

  場景: 多個 Integration 實例共用 Add-on
    假設 我安裝了 2 個 Integration 實例連接到同一個 Add-on
    那麼 Add-on 應該能處理並發請求
    而且 每個 Integration 應該獲得相同的資料
    而且 系統效能不應該明顯下降

  # ============================================================
  # 場景 10: 移轉路徑
  # ============================================================
  場景: 從 RESTful Sensor 移轉到 Integration
    假設 用戶目前使用 Add-on + RESTful sensor 設定
    而且 用戶有 10 個自動化使用 "sensor.garbage_truck_monitor"
    當 用戶安裝 Integration
    那麼 用戶可以逐步將自動化改為使用 Integration 實體
    而且 移轉期間兩種 sensor 可以共存
    而且 完成移轉後可以移除 RESTful sensor 配置

  場景: 提供移轉工具或腳本
    假設 用戶想從 RESTful sensor 移轉到 Integration
    那麼 專案應該提供移轉指南
    而且 應該說明如何更新自動化配置
    而且 應該提供實體名稱對照表
