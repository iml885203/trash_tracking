# language: zh-TW
功能: API 垃圾車狀態查詢
  作為一個 Home Assistant 使用者
  我想要透過 API 查詢垃圾車狀態
  以便自動化我的家庭設備

  背景:
    假設 API 伺服器正在運行
    而且 追蹤器已經初始化

  場景: 查詢系統健康狀態
    當 我查詢 "/health" 端點
    那麼 回應狀態碼應該是 200
    而且 回應應該包含 "status" 欄位
    而且 status 應該是 "ok"

  場景: 查詢垃圾車狀態（閒置）
    假設 追蹤器已被重置
    當 我查詢 "/api/trash/status" 端點
    那麼 回應應該包含 "status" 欄位
    而且 回應應該包含 "reason" 欄位

  場景: 重置追蹤器
    當 我發送 POST 請求到 "/api/reset"
    那麼 回應狀態碼應該是 200
    而且 回應應該包含 "message" 欄位
    而且 message 應該包含 "reset"

  場景: 查詢不存在的端點
    當 我查詢 "/api/invalid_endpoint" 端點
    那麼 回應狀態碼應該是 404
    而且 回應應該包含錯誤訊息

  場景: 併發請求處理
    當 我同時發送 5 個請求到 "/api/trash/status"
    那麼 所有請求都應該成功
    而且 所有回應都應該包含 "status" 欄位
