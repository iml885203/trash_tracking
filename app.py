"""Garbage Truck Tracking System - Main Entry Point"""

import sys

from src.api.routes import create_app
from trash_tracking_core.utils.config import ConfigError, ConfigManager
from trash_tracking_core.utils.logger import logger

# Create Flask app for WSGI servers (gunicorn, etc.)
try:
    app = create_app(config_path="config.yaml")
except Exception as e:
    logger.error(f"Failed to create app: {e}", exc_info=True)
    sys.exit(1)


def main():
    """Main entry point for development server"""
    try:
        config = ConfigManager("config.yaml")
        host = config.server_host
        port = config.server_port
        debug = config.server_debug

        logger.info(f"Starting Flask development server: {host}:{port} (debug={debug})")
        logger.info("Press Ctrl+C to stop service")
        logger.warning("⚠️  This is a development server. Use a production WSGI server for deployment.")

        app.run(host=host, port=port, debug=debug)

    except ConfigError as e:
        logger.error(f"❌ Config error: {e}")
        logger.error("Please check config.yaml file")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nShutdown signal received, stopping service...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
