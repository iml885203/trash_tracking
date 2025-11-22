# language: zh-TW
功能: Home Assistant Integration 實體
  作為一個 Home Assistant 使用者
  我想要使用原生的感測器和二元感測器
  以便更方便地建立自動化和儀表板

  背景:
    假設 垃圾車追蹤 Integration 已成功安裝
    而且 Integration 連接到 Add-on API "http://localhost:5000"
    而且 Add-on 已設定追蹤路線

  # ============================================================
  # 場景 1: 感測器實體
  # ============================================================
  場景: 建立垃圾車狀態感測器
    當 Integration 初始化完成
    那麼 應該建立實體 "sensor.trash_tracking_status"
    而且 實體的裝置類別應該是 "enum"
    而且 實體的圖示應該是 "mdi:trash-can"
    而且 實體的狀態應該是 "idle" 或 "nearby"

  場景: 狀態感測器顯示 idle
    假設 Add-on API 返回狀態 "idle"
    當 Integration 更新資料
    那麼 "sensor.trash_tracking_status" 的狀態應該是 "idle"
    而且 屬性 "reason" 應該包含 "無垃圾車在附近"
    而且 屬性 "truck" 應該是 null

  場景: 狀態感測器顯示 nearby
    假設 Add-on API 返回狀態 "nearby"
    而且 垃圾車資訊包含路線名稱 "A12路線晚上"
    當 Integration 更新資料
    那麼 "sensor.trash_tracking_status" 的狀態應該是 "nearby"
    而且 屬性 "line_name" 應該是 "A12路線晚上"
    而且 屬性 "car_no" 應該存在
    而且 屬性 "enter_point" 應該存在
    而且 屬性 "exit_point" 應該存在

  場景: 建立垃圾車資訊感測器
    當 Integration 初始化完成
    那麼 應該建立實體 "sensor.trash_tracking_truck_info"
    而且 實體的圖示應該是 "mdi:truck"

  場景: 垃圾車資訊感測器 - 無垃圾車時
    假設 Add-on API 返回狀態 "idle"
    當 Integration 更新資料
    那麼 "sensor.trash_tracking_truck_info" 的狀態應該是 "無垃圾車"
    而且 額外屬性應該是空的

  場景: 垃圾車資訊感測器 - 有垃圾車時
    假設 Add-on API 返回垃圾車資訊:
      | 欄位         | 值            |
      | line_name    | A12路線晚上    |
      | car_no       | KES-6950      |
      | current_rank | 10            |
      | total_points | 69            |
      | arrival_diff | -5            |
    當 Integration 更新資料
    那麼 "sensor.trash_tracking_truck_info" 的狀態應該是 "A12路線晚上 (KES-6950)"
    而且 屬性 "路線名稱" 應該是 "A12路線晚上"
    而且 屬性 "車牌號碼" 應該是 "KES-6950"
    而且 屬性 "當前站點" 應該是 10
    而且 屬性 "總站點數" 應該是 69
    而且 屬性 "延遲時間" 應該是 "-5 分鐘"

  # ============================================================
  # 場景 2: 二元感測器實體
  # ============================================================
  場景: 建立垃圾車接近二元感測器
    當 Integration 初始化完成
    那麼 應該建立實體 "binary_sensor.trash_truck_nearby"
    而且 實體的裝置類別應該是 "presence"
    而且 實體的圖示應該是 "mdi:bell-ring"

  場景: 垃圾車接近時二元感測器為 on
    假設 Add-on API 返回狀態 "nearby"
    當 Integration 更新資料
    那麼 "binary_sensor.trash_truck_nearby" 應該是 "on"

  場景: 垃圾車離開時二元感測器為 off
    假設 Add-on API 返回狀態 "idle"
    當 Integration 更新資料
    那麼 "binary_sensor.trash_truck_nearby" 應該是 "off"

  場景: 二元感測器狀態變化觸發自動化
    假設 我有一個自動化監聽 "binary_sensor.trash_truck_nearby"
    而且 垃圾車目前不在附近 (狀態為 off)
    當 垃圾車接近 (狀態變為 on)
    那麼 自動化應該被觸發
    而且 我應該收到通知

  # ============================================================
  # 場景 3: 實體屬性和元資料
  # ============================================================
  場景: 實體包含正確的唯一 ID
    當 Integration 建立實體
    那麼 每個實體應該有唯一的 unique_id
    而且 unique_id 應該包含 Integration 的 entry_id
    而且 unique_id 格式應該是 "{entry_id}_{entity_type}"

  場景: 實體包含友善名稱
    當 Integration 建立實體
    那麼 "sensor.trash_tracking_status" 的友善名稱應該是 "垃圾車狀態"
    而且 "sensor.trash_tracking_truck_info" 的友善名稱應該是 "垃圾車資訊"
    而且 "binary_sensor.trash_truck_nearby" 的友善名稱應該是 "垃圾車接近"

  場景: 實體歸屬於同一個裝置
    當 Integration 建立實體
    那麼 所有實體應該歸屬於同一個裝置
    而且 裝置名稱應該包含路線資訊
    而且 裝置製造商應該是 "Trash Tracking"
    而且 裝置型號應該是 "NTPC Garbage Truck Tracker"

  # ============================================================
  # 場景 4: 資料更新和協調
  # ============================================================
  場景: 定期更新實體資料
    假設 Integration 設定掃描間隔為 90 秒
    當 時間經過 90 秒
    那麼 Integration 應該向 Add-on API 請求最新資料
    而且 所有實體的狀態應該更新

  場景: 更新失敗時實體保持舊狀態
    假設 實體目前狀態為 "nearby"
    當 Add-on API 暫時無法連接
    而且 Integration 嘗試更新資料
    那麼 實體應該保持 "nearby" 狀態
    而且 實體應該標記為 "不可用" 或保持可用（依設計）

  場景: API 恢復後實體自動更新
    假設 Add-on API 曾經無法連接
    而且 實體保持舊狀態
    當 Add-on API 恢復正常
    而且 下一次更新週期到達
    那麼 實體應該成功更新到最新狀態
    而且 不可用標記應該被移除

  # ============================================================
  # 場景 5: 實體在 UI 中的呈現
  # ============================================================
  場景: 在儀表板中顯示實體
    假設 我在 Home Assistant 儀表板編輯器
    當 我搜尋 "trash"
    那麼 應該找到垃圾車追蹤的所有實體
    而且 我應該能將它們加入儀表板卡片

  場景: 實體卡片顯示完整資訊
    假設 我在儀表板中加入了 "sensor.trash_tracking_truck_info"
    而且 垃圾車正在接近
    當 我查看卡片
    那麼 應該顯示路線名稱和車牌號碼
    而且 應該顯示當前站點資訊
    而且 應該顯示進入點和離開點
    而且 應該顯示延遲時間

  場景: 在歷史記錄中追蹤狀態變化
    假設 垃圾車在過去 24 小時內接近過 3 次
    當 我查看 "binary_sensor.trash_truck_nearby" 的歷史記錄
    那麼 應該看到 3 次 on → off 的狀態變化
    而且 每次變化應該有時間戳記

  # ============================================================
  # 場景 6: 與自動化整合
  # ============================================================
  場景: 使用二元感測器觸發開燈自動化
    假設 我建立自動化:
      """
      trigger:
        - platform: state
          entity_id: binary_sensor.trash_truck_nearby
          to: 'on'
      action:
        - service: light.turn_on
          target:
            entity_id: light.notification_bulb
      """
    當 垃圾車接近並觸發 binary_sensor
    那麼 燈光應該被開啟

  場景: 使用狀態感測器屬性發送通知
    假設 我建立自動化使用模板:
      """
      {{ state_attr('sensor.trash_tracking_status', 'line_name') }}
      {{ state_attr('sensor.trash_tracking_status', 'enter_point') }}
      """
    當 垃圾車接近
    那麼 通知訊息應該包含路線名稱
    而且 通知訊息應該包含進入點名稱

  場景: 多條件自動化 - 僅在特定時間觸發
    假設 我建立自動化:
      """
      trigger:
        - platform: state
          entity_id: binary_sensor.trash_truck_nearby
          to: 'on'
      condition:
        - condition: time
          after: '17:00:00'
          before: '22:00:00'
      """
    當 垃圾車在下午 6 點接近
    那麼 自動化應該被觸發
    當 垃圾車在中午 12 點接近
    那麼 自動化不應該被觸發

  # ============================================================
  # 場景 7: 效能和資源使用
  # ============================================================
  場景: Integration 不應過度消耗資源
    假設 Integration 已運行 24 小時
    當 我檢查系統資源使用情況
    那麼 CPU 使用率應該低於 5%
    而且 記憶體使用應該低於 50 MB
    而且 API 請求頻率應該符合設定的掃描間隔

  場景: 快速回應狀態查詢
    當 我在 Home Assistant 中查詢實體狀態
    那麼 回應時間應該少於 100 毫秒
    而且 不應該阻塞其他操作

  # ============================================================
  # 場景 8: 多語言支援
  # ============================================================
  場景大綱: 實體名稱支援多語言
    假設 Home Assistant 語言設定為 "<語言>"
    當 Integration 建立實體
    那麼 實體的友善名稱應該使用 "<語言>" 顯示

    例子:
      | 語言  |
      | zh-TW |
      | en    |

  # ============================================================
  # 場景 9: 錯誤狀態處理
  # ============================================================
  場景: API 返回錯誤時的實體行為
    假設 Add-on API 返回 503 錯誤
    當 Integration 嘗試更新資料
    那麼 實體應該保持上次的有效狀態
    而且 日誌應該記錄錯誤
    而且 實體不應該顯示錯誤的資料

  場景: 首次安裝時沒有歷史資料
    假設 我剛剛安裝 Integration
    當 Integration 首次獲取資料
    那麼 實體應該顯示初始狀態
    而且 不應該有 "unknown" 狀態
    而且 應該立即可用
