"""Flask API 路由測試"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from src.api.routes import create_app
from src.core.tracker import TruckTracker
from src.utils.config import ConfigManager


class TestFlaskRoutes:
    """Flask 路由測試"""

    @pytest.fixture
    def mock_config(self):
        """建立模擬的配置管理器"""
        config = Mock(spec=ConfigManager)
        config.log_level = "INFO"
        config.enter_point = "民生路二段80號"
        config.exit_point = "成功路23號"
        config.trigger_mode = "arriving"
        config.lat = 25.018269
        config.lng = 121.471703
        config.target_lines = []
        return config

    @pytest.fixture
    def mock_tracker(self):
        """建立模擬的追蹤器"""
        tracker = Mock(spec=TruckTracker)
        return tracker

    @pytest.fixture
    def app(self, mock_config, mock_tracker):
        """建立測試用的 Flask app"""
        with patch('src.api.routes.ConfigManager', return_value=mock_config):
            with patch('src.api.routes.TruckTracker', return_value=mock_tracker):
                with patch('src.api.routes.setup_logger'):
                    app = create_app("config.yaml")
                    app.config['TESTING'] = True

                    # 注入 mock tracker
                    import src.api.routes as routes
                    routes.tracker = mock_tracker
                    routes.config = mock_config

                    yield app

    @pytest.fixture
    def client(self, app):
        """建立測試客戶端"""
        return app.test_client()


class TestHealthCheck(TestFlaskRoutes):
    """健康檢查端點測試"""

    def test_health_check_ok(self, client, mock_tracker):
        """測試健康檢查成功"""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'timestamp' in data
        assert 'config' in data
        assert data['config']['enter_point'] == '民生路二段80號'
        assert data['config']['exit_point'] == '成功路23號'

    def test_health_check_initializing(self, client):
        """測試系統初始化中的健康檢查"""
        import src.api.routes as routes
        routes.tracker = None

        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'initializing'

    def test_health_check_error(self, client, mock_config):
        """測試健康檢查錯誤情況"""
        # 模擬配置存取錯誤
        mock_config.enter_point = property(Mock(side_effect=Exception("Config error")))

        response = client.get('/health')

        # 即使有錯誤，健康檢查也應該回應，只是標記為 error
        assert response.status_code in [200, 500]


class TestGetStatus(TestFlaskRoutes):
    """狀態查詢端點測試"""

    def test_get_status_idle(self, client, mock_tracker):
        """測試 idle 狀態"""
        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'message': '無垃圾車在附近',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }

        response = client.get('/api/trash/status')

        assert response.status_code == 200
        data = response.get_json()
        assert data['state'] == 'idle'
        assert data['message'] == '無垃圾車在附近'
        mock_tracker.get_current_status.assert_called_once()

    def test_get_status_nearby(self, client, mock_tracker):
        """測試 nearby 狀態"""
        mock_tracker.get_current_status.return_value = {
            'state': 'nearby',
            'message': '垃圾車即將到達進入清運點',
            'truck_info': {
                'line_name': 'C08路線下午',
                'car_no': 'KES-6950',
                'arrival_diff': -5
            },
            'timestamp': '2025-11-18T14:00:00+08:00'
        }

        response = client.get('/api/trash/status')

        assert response.status_code == 200
        data = response.get_json()
        assert data['state'] == 'nearby'
        assert 'truck_info' in data
        assert data['truck_info']['line_name'] == 'C08路線下午'

    def test_get_status_with_error(self, client, mock_tracker):
        """測試狀態查詢包含錯誤"""
        mock_tracker.get_current_status.return_value = {
            'error': 'API 連線失敗',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }

        response = client.get('/api/trash/status')

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    def test_get_status_tracker_not_initialized(self, client):
        """測試追蹤器未初始化"""
        import src.api.routes as routes
        routes.tracker = None

        response = client.get('/api/trash/status')

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '系統尚未初始化'

    def test_get_status_exception(self, client, mock_tracker):
        """測試處理狀態時發生異常"""
        mock_tracker.get_current_status.side_effect = Exception("Unexpected error")

        response = client.get('/api/trash/status')

        assert response.status_code == 500
        data = response.get_json()
        assert data['error'] == '內部伺服器錯誤'
        assert 'detail' in data


class TestResetTracker(TestFlaskRoutes):
    """重置追蹤器端點測試"""

    def test_reset_success(self, client, mock_tracker):
        """測試成功重置"""
        mock_tracker.reset.return_value = None

        response = client.post('/api/reset')

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == '追蹤器已重置'
        assert 'timestamp' in data
        mock_tracker.reset.assert_called_once()

    def test_reset_tracker_not_initialized(self, client):
        """測試追蹤器未初始化時重置"""
        import src.api.routes as routes
        routes.tracker = None

        response = client.post('/api/reset')

        assert response.status_code == 500
        data = response.get_json()
        assert data['error'] == '追蹤器尚未初始化'

    def test_reset_exception(self, client, mock_tracker):
        """測試重置時發生異常"""
        mock_tracker.reset.side_effect = Exception("Reset failed")

        response = client.post('/api/reset')

        assert response.status_code == 500
        data = response.get_json()
        assert data['error'] == '重置失敗'
        assert 'detail' in data


class TestErrorHandlers(TestFlaskRoutes):
    """錯誤處理器測試"""

    def test_404_not_found(self, client):
        """測試 404 錯誤處理"""
        response = client.get('/api/nonexistent')

        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == '找不到請求的資源'
        assert data['path'] == '/api/nonexistent'

    def test_method_not_allowed(self, client):
        """測試不允許的 HTTP 方法"""
        # GET 端點使用 POST 方法
        response = client.post('/health')

        assert response.status_code == 405


class TestRequestLogging(TestFlaskRoutes):
    """請求日誌測試"""

    def test_request_logging(self, client, mock_tracker):
        """測試請求和回應日誌"""
        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }

        with patch('src.api.routes.logger') as mock_logger:
            response = client.get('/api/trash/status')

            # 驗證日誌被呼叫
            assert response.status_code == 200
            # logger.debug 應該被呼叫兩次（before_request 和 after_request）
            assert mock_logger.debug.call_count >= 2


class TestAppCreation(TestFlaskRoutes):
    """應用程式建立測試"""

    def test_create_app_success(self, mock_config):
        """測試成功建立應用程式"""
        with patch('src.api.routes.ConfigManager', return_value=mock_config):
            with patch('src.api.routes.TruckTracker'):
                with patch('src.api.routes.setup_logger'):
                    app = create_app("config.yaml")

                    assert isinstance(app, Flask)
                    assert app is not None

    def test_create_app_config_error(self):
        """測試配置錯誤時建立應用程式"""
        from src.utils.config import ConfigError

        with patch('src.api.routes.ConfigManager', side_effect=ConfigError("Invalid config")):
            with pytest.raises(ConfigError):
                create_app("invalid_config.yaml")

    def test_create_app_general_error(self):
        """測試一般錯誤時建立應用程式"""
        with patch('src.api.routes.ConfigManager', side_effect=Exception("Unexpected error")):
            with pytest.raises(Exception):
                create_app("config.yaml")


class TestIntegration(TestFlaskRoutes):
    """整合測試"""

    def test_complete_workflow(self, client, mock_tracker):
        """測試完整的工作流程"""
        # 1. 健康檢查
        response = client.get('/health')
        assert response.status_code == 200

        # 2. 查詢狀態（idle）
        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'message': '無垃圾車在附近',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }
        response = client.get('/api/trash/status')
        assert response.status_code == 200
        assert response.get_json()['state'] == 'idle'

        # 3. 狀態改變為 nearby
        mock_tracker.get_current_status.return_value = {
            'state': 'nearby',
            'message': '垃圾車即將到達',
            'timestamp': '2025-11-18T14:05:00+08:00'
        }
        response = client.get('/api/trash/status')
        assert response.status_code == 200
        assert response.get_json()['state'] == 'nearby'

        # 4. 重置追蹤器
        response = client.post('/api/reset')
        assert response.status_code == 200

        # 5. 再次查詢狀態應該回到 idle
        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'message': '追蹤器已重置',
            'timestamp': '2025-11-18T14:10:00+08:00'
        }
        response = client.get('/api/trash/status')
        assert response.status_code == 200
        assert response.get_json()['state'] == 'idle'
