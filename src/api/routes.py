"""Flask API Routes"""

from flask import Flask, jsonify, request
from typing import Dict, Any
from src.core.tracker import TruckTracker
from src.utils.config import ConfigManager, ConfigError
from src.utils.logger import setup_logger, logger
from datetime import datetime
import pytz


app = Flask(__name__)
tracker: TruckTracker = None
config: ConfigManager = None


def create_app(config_path: str = "config.yaml") -> Flask:
    """
    Create and configure Flask application

    Args:
        config_path: Configuration file path

    Returns:
        Flask: Configured Flask app
    """
    global tracker, config

    try:
        config = ConfigManager(config_path)

        log_level = config.log_level
        setup_logger(log_level=log_level, log_file="logs/app.log")

        logger.info("=" * 50)
        logger.info("Garbage Truck Tracking System Starting")
        logger.info("=" * 50)
        logger.info(f"Config: {config}")

        tracker = TruckTracker(config)

        logger.info("Flask application initialized successfully")

    except ConfigError as e:
        logger.error(f"Config error: {e}")
        raise

    except Exception as e:
        logger.error(f"Application initialization failed: {e}", exc_info=True)
        raise

    return app


@app.route('/api/trash/status', methods=['GET'])
def get_status() -> tuple:
    """
    Get garbage truck status

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        logger.debug("Status query request received")

        if tracker is None:
            return jsonify({
                'error': 'System not initialized',
                'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
            }), 500

        status = tracker.get_current_status()

        if 'error' in status:
            logger.warning(f"Status query contains error: {status['error']}")
            return jsonify(status), 503

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Error processing status request: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'detail': str(e),
            'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
        }), 500


@app.route('/health', methods=['GET'])
def health_check() -> tuple:
    """
    Health check endpoint

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
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset_tracker() -> tuple:
    """
    Reset tracker state (for development/testing)

    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        if tracker is None:
            return jsonify({'error': 'Tracker not initialized'}), 500

        tracker.reset()
        logger.info("Tracker state reset")

        return jsonify({
            'message': 'Tracker reset',
            'timestamp': datetime.now(pytz.timezone('Asia/Taipei')).isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Tracker reset failed: {e}")
        return jsonify({
            'error': 'Reset failed',
            'detail': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error) -> tuple:
    """404 error handler"""
    return jsonify({
        'error': 'Resource not found',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error) -> tuple:
    """500 error handler"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'detail': str(error)
    }), 500


@app.before_request
def log_request():
    """Log each request"""
    logger.debug(f"{request.method} {request.path}")


@app.after_request
def log_response(response):
    """Log each response"""
    logger.debug(f"{request.method} {request.path} - {response.status_code}")
    return response
