"""Flask API routes tests"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from src.api.routes import create_app
from src.core.tracker import TruckTracker
from src.utils.config import ConfigManager


class TestFlaskRoutes:
    """Flask routes tests"""

    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=ConfigManager)
        config.log_level = "INFO"
        config.enter_point = "Minsheng Rd. Sec. 2, No. 80"
        config.exit_point = "Chenggong Rd. No. 23"
        config.trigger_mode = "arriving"
        config.lat = 25.018269
        config.lng = 121.471703
        config.target_lines = []
        return config

    @pytest.fixture
    def mock_tracker(self):
        tracker = Mock(spec=TruckTracker)
        return tracker

    @pytest.fixture
    def app(self, mock_config, mock_tracker):
        with patch('src.api.routes.ConfigManager', return_value=mock_config):
            with patch('src.api.routes.TruckTracker', return_value=mock_tracker):
                with patch('src.api.routes.setup_logger'):
                    app = create_app("config.yaml")
                    app.config['TESTING'] = True

                    import src.api.routes as routes
                    routes.tracker = mock_tracker
                    routes.config = mock_config

                    yield app

    @pytest.fixture
    def client(self, app):
        return app.test_client()


class TestHealthCheck(TestFlaskRoutes):
    """Health check endpoint tests"""

    def test_health_check_ok(self, client, mock_tracker):
        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'timestamp' in data
        assert 'config' in data
        assert data['config']['enter_point'] == 'Minsheng Rd. Sec. 2, No. 80'
        assert data['config']['exit_point'] == 'Chenggong Rd. No. 23'

    def test_health_check_initializing(self, client):
        import src.api.routes as routes
        routes.tracker = None

        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'initializing'

    def test_health_check_error(self, client, mock_config):
        mock_config.enter_point = property(Mock(side_effect=Exception("Config error")))

        response = client.get('/health')

        assert response.status_code in [200, 500]


class TestGetStatus(TestFlaskRoutes):
    """Status query endpoint tests"""

    def test_get_status_idle(self, client, mock_tracker):
        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'message': 'No trash trucks nearby',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }

        response = client.get('/api/trash/status')

        assert response.status_code == 200
        data = response.get_json()
        assert data['state'] == 'idle'
        assert data['message'] == 'No trash trucks nearby'
        mock_tracker.get_current_status.assert_called_once()

    def test_get_status_nearby(self, client, mock_tracker):
        mock_tracker.get_current_status.return_value = {
            'state': 'nearby',
            'message': 'Trash truck approaching entry point',
            'truck_info': {
                'line_name': 'C08 Afternoon Route',
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
        assert data['truck_info']['line_name'] == 'C08 Afternoon Route'

    def test_get_status_with_error(self, client, mock_tracker):
        mock_tracker.get_current_status.return_value = {
            'error': 'API connection failed',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }

        response = client.get('/api/trash/status')

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    def test_get_status_tracker_not_initialized(self, client):
        import src.api.routes as routes
        routes.tracker = None

        response = client.get('/api/trash/status')

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == '系統尚未初始化'

    def test_get_status_exception(self, client, mock_tracker):
        mock_tracker.get_current_status.side_effect = Exception("Unexpected error")

        response = client.get('/api/trash/status')

        assert response.status_code == 500
        data = response.get_json()
        assert data['error'] == '內部伺服器錯誤'
        assert 'detail' in data


class TestResetTracker(TestFlaskRoutes):
    """Reset tracker endpoint tests"""

    def test_reset_success(self, client, mock_tracker):
        mock_tracker.reset.return_value = None

        response = client.post('/api/reset')

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == '追蹤器已重置'
        assert 'timestamp' in data
        mock_tracker.reset.assert_called_once()

    def test_reset_tracker_not_initialized(self, client):
        import src.api.routes as routes
        routes.tracker = None

        response = client.post('/api/reset')

        assert response.status_code == 500
        data = response.get_json()
        assert data['error'] == '追蹤器尚未初始化'

    def test_reset_exception(self, client, mock_tracker):
        mock_tracker.reset.side_effect = Exception("Reset failed")

        response = client.post('/api/reset')

        assert response.status_code == 500
        data = response.get_json()
        assert data['error'] == '重置失敗'
        assert 'detail' in data


class TestErrorHandlers(TestFlaskRoutes):
    """Error handlers tests"""

    def test_404_not_found(self, client):
        response = client.get('/api/nonexistent')

        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == '找不到請求的資源'
        assert data['path'] == '/api/nonexistent'

    def test_method_not_allowed(self, client):
        response = client.post('/health')

        assert response.status_code == 405


class TestRequestLogging(TestFlaskRoutes):
    """Request logging tests"""

    def test_request_logging(self, client, mock_tracker):
        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }

        with patch('src.api.routes.logger') as mock_logger:
            response = client.get('/api/trash/status')

            assert response.status_code == 200
            assert mock_logger.debug.call_count >= 2


class TestAppCreation(TestFlaskRoutes):
    """App creation tests"""

    def test_create_app_success(self, mock_config):
        with patch('src.api.routes.ConfigManager', return_value=mock_config):
            with patch('src.api.routes.TruckTracker'):
                with patch('src.api.routes.setup_logger'):
                    app = create_app("config.yaml")

                    assert isinstance(app, Flask)
                    assert app is not None

    def test_create_app_config_error(self):
        from src.utils.config import ConfigError

        with patch('src.api.routes.ConfigManager', side_effect=ConfigError("Invalid config")):
            with pytest.raises(ConfigError):
                create_app("invalid_config.yaml")

    def test_create_app_general_error(self):
        with patch('src.api.routes.ConfigManager', side_effect=Exception("Unexpected error")):
            with pytest.raises(Exception):
                create_app("config.yaml")


class TestIntegration(TestFlaskRoutes):
    """Integration tests"""

    def test_complete_workflow(self, client, mock_tracker):
        response = client.get('/health')
        assert response.status_code == 200

        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'message': 'No trash trucks nearby',
            'timestamp': '2025-11-18T14:00:00+08:00'
        }
        response = client.get('/api/trash/status')
        assert response.status_code == 200
        assert response.get_json()['state'] == 'idle'

        mock_tracker.get_current_status.return_value = {
            'state': 'nearby',
            'message': 'Trash truck approaching',
            'timestamp': '2025-11-18T14:05:00+08:00'
        }
        response = client.get('/api/trash/status')
        assert response.status_code == 200
        assert response.get_json()['state'] == 'nearby'

        response = client.post('/api/reset')
        assert response.status_code == 200

        mock_tracker.get_current_status.return_value = {
            'state': 'idle',
            'message': 'Tracker reset',
            'timestamp': '2025-11-18T14:10:00+08:00'
        }
        response = client.get('/api/trash/status')
        assert response.status_code == 200
        assert response.get_json()['state'] == 'idle'
