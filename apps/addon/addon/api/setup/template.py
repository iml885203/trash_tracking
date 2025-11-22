"""Setup Wizard HTML Template"""

SETUP_WIZARD_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>垃圾車追蹤系統 - 設定精靈</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .step {
            display: none;
            animation: fadeIn 0.3s;
        }
        .step.active {
            display: block;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #e0e0e0;
            color: #333;
            margin-right: 10px;
        }
        .btn-secondary:hover {
            background: #d0d0d0;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .loading.active {
            display: block;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .result h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
        }
        .result-item {
            margin-bottom: 12px;
            padding: 10px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }
        .result-label {
            font-weight: 500;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .result-value {
            color: #333;
            font-size: 16px;
        }
        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .progress {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        .progress-step {
            flex: 1;
            text-align: center;
            position: relative;
            padding: 10px 0;
        }
        .progress-step::before {
            content: '';
            position: absolute;
            top: 15px;
            left: 0;
            right: 0;
            height: 2px;
            background: #e0e0e0;
            z-index: -1;
        }
        .progress-step:first-child::before {
            left: 50%;
        }
        .progress-step:last-child::before {
            right: 50%;
        }
        .progress-circle {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #e0e0e0;
            color: #999;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .progress-step.active .progress-circle {
            background: #667eea;
            color: white;
        }
        .progress-step.completed .progress-circle {
            background: #4caf50;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚛 垃圾車追蹤系統</h1>
        <p class="subtitle">自動設定精靈 - 只需輸入地址，系統自動幫您找到最近的垃圾車路線</p>

        <div class="progress">
            <div class="progress-step active" id="progress-1">
                <div class="progress-circle">1</div>
                <div>輸入地址</div>
            </div>
            <div class="progress-step" id="progress-2">
                <div class="progress-circle">2</div>
                <div>分析路線</div>
            </div>
            <div class="progress-step" id="progress-3">
                <div class="progress-circle">3</div>
                <div>完成設定</div>
            </div>
        </div>

        <!-- Step 1: Address Input -->
        <div id="step1" class="step active">
            <div class="form-group">
                <label for="address">請輸入您的地址</label>
                <input type="text" id="address" placeholder="例如：新北市板橋區中山路一段161號" value="">
            </div>
            <button class="btn btn-primary" onclick="analyzeAddress()">開始分析</button>
        </div>

        <!-- Loading -->
        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p>正在分析附近的垃圾車路線...</p>
        </div>

        <!-- Step 2: Results -->
        <div id="step2" class="step">
            <div id="result-container"></div>
            <div style="margin-top: 20px;">
                <button class="btn btn-secondary" onclick="goBack()">重新輸入</button>
                <button class="btn btn-primary" onclick="saveConfig()">儲存設定</button>
            </div>
        </div>

        <!-- Step 3: Success -->
        <div id="step3" class="step">
            <div class="alert alert-success">
                <h3>✅ 設定已儲存！</h3>
                <p>系統將在重新啟動後套用新設定。</p>
            </div>
            <div style="margin-top: 20px;">
                <button class="btn btn-primary" onclick="location.reload()">重新設定</button>
            </div>
        </div>

        <!-- Error Message -->
        <div id="error" style="display: none;" class="alert alert-error"></div>
    </div>

    <script>
        let configData = null;

        function showStep(stepNum) {
            document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
            document.getElementById('step' + stepNum).classList.add('active');

            document.querySelectorAll('.progress-step').forEach((step, index) => {
                step.classList.remove('active', 'completed');
                if (index + 1 < stepNum) {
                    step.classList.add('completed');
                } else if (index + 1 === stepNum) {
                    step.classList.add('active');
                }
            });
        }

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => { errorDiv.style.display = 'none'; }, 5000);
        }

        async function analyzeAddress() {
            const address = document.getElementById('address').value.trim();
            if (!address) {
                showError('請輸入地址');
                return;
            }

            document.getElementById('step1').style.display = 'none';
            document.getElementById('loading').classList.add('active');

            try {
                const response = await fetch('api/setup/suggest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address: address })
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || '分析失敗');
                }

                configData = data;
                displayResults(data);
                showStep(2);
            } catch (error) {
                showError('分析失敗: ' + error.message);
                document.getElementById('step1').style.display = 'block';
            } finally {
                document.getElementById('loading').classList.remove('active');
            }
        }

        function displayResults(data) {
            const container = document.getElementById('result-container');
            const rec = data.recommendation;
            container.innerHTML = `
                <div class="result">
                    <h3>📍 建議設定</h3>
                    <div class="result-item">
                        <div class="result-label">地址座標</div>
                        <div class="result-value">${rec.latitude.toFixed(6)}, ${rec.longitude.toFixed(6)}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">建議追蹤路線</div>
                        <div class="result-value">${rec.route_selection.route_names.join(', ')}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">進入點</div>
                        <div class="result-value">${rec.route_selection.best_route.enter_point.point_name}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">離開點</div>
                        <div class="result-value">${rec.route_selection.best_route.exit_point.point_name}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">觸發模式</div>
                        <div class="result-value">${rec.trigger_mode === 'arriving' ? '即將到達' : '已經到達'}</div>
                    </div>
                    <div class="result-item">
                        <div class="result-label">提前通知站數</div>
                        <div class="result-value">${rec.threshold} 站</div>
                    </div>
                </div>
            `;
        }

        async function saveConfig() {
            if (!configData) {
                showError('沒有可儲存的設定');
                return;
            }

            try {
                const response = await fetch('api/setup/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(configData)
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || '儲存失敗');
                }

                showStep(3);
            } catch (error) {
                showError('儲存失敗: ' + error.message);
            }
        }

        function goBack() {
            showStep(1);
        }

        document.getElementById('address').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeAddress();
            }
        });
    </script>
</body>
</html>
"""
