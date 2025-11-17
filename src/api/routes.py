"""Flask API 路由"""

from flask import Flask, jsonify, request
from typing import Dict, Any
from src.core.tracker import TruckTracker
from src.utils.config import ConfigManager, ConfigError
from src.utils.logger import setup_logger, logger
from datetime import datetime
import pytz


# 全域變數
app = Flask(__name__)
tracker: TruckTracker = None
config: ConfigManager = None


def create_app(config_path: str = "config.yaml") -> Flask:
    """
    建立並設定 Flask 應用程式

    Args:
        config_path: 設定檔路徑

    Returns:
        Flask: 設定好的 Flask app
    """
    global tracker, config

    try:
        # 載入設定
        config = ConfigManager(config_path)

        # 設定 logger
        log_level = config.log_level
        setup_logger(log_level=log_level, log_file="logs/app.log")

        logger.info("=" * 50)
        logger.info("垃圾車動態偵測系統啟動")
        logger.info("=" * 50)
        logger.info(f"設定: {config}")

        # 初始化追蹤器
        tracker = TruckTracker(config)

        logger.info("Flask 應用程式初始化完成")

    except ConfigError as e:
        logger.error(f"設定檔錯誤: {e}")
        raise

    except Exception as e:
        logger.error(f"應用程式初始化失敗: {e}", exc_info=True)
        raise

    return app


@app.route('/api/trash/status', methods=['GET'])
def get_status() -> tuple:
    """
    取得垃圾車狀態

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        logger.debug("收到狀態查詢請求")

        if tracker is None:
            return jsonify({
                'error': '系統尚未初始化',
                'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
            }), 500

        # 取得目前狀態
        status = tracker.get_current_status()

        # 如果回應中有錯誤，回傳 503
        if 'error' in status:
            logger.warning(f"狀態查詢包含錯誤: {status['error']}")
            return jsonify(status), 503

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"處理狀態請求時發生錯誤: {e}", exc_info=True)
        return jsonify({
            'error': '內部伺服器錯誤',
            'detail': str(e),
            'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
        }), 500


@app.route('/health', methods=['GET'])
def health_check() -> tuple:
    """
    健康檢查端點

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        health_status = {
            'status': 'ok' if tracker is not None else 'initializing',
            'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
        }

        if config:
            health_status['config'] = {
                'enter_point': config.enter_point,
                'exit_point': config.exit_point,
                'trigger_mode': config.trigger_mode
            }

        return jsonify(health_status), 200

    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset_tracker() -> tuple:
    """
    重置追蹤器狀態（開發/測試用）

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        if tracker is None:
            return jsonify({'error': '追蹤器尚未初始化'}), 500

        tracker.reset()
        logger.info("追蹤器狀態已重置")

        return jsonify({
            'message': '追蹤器已重置',
            'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
        }), 200

    except Exception as e:
        logger.error(f"重置追蹤器失敗: {e}")
        return jsonify({
            'error': '重置失敗',
            'detail': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error) -> tuple:
    """404 錯誤處理"""
    return jsonify({
        'error': '找不到請求的資源',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error) -> tuple:
    """500 錯誤處理"""
    logger.error(f"內部伺服器錯誤: {error}")
    return jsonify({
        'error': '內部伺服器錯誤',
        'detail': str(error)
    }), 500


# 請求日誌
@app.before_request
def log_request():
    """記錄每個請求"""
    logger.debug(f"{request.method} {request.path}")


@app.after_request
def log_response(response):
    """記錄每個回應"""
    logger.debug(f"{request.method} {request.path} - {response.status_code}")
    return response
