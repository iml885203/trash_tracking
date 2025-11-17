FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴清單
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 建立 logs 目錄
RUN mkdir -p logs

# 暴露端口
EXPOSE 5000

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Taipei

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# 啟動應用
CMD ["python", "app.py"]
