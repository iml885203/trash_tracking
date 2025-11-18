"""Garbage Truck Tracking System - Main Entry Point"""

import sys
from src.api.routes import create_app
from src.utils.config import ConfigManager, ConfigError
from src.utils.logger import logger


def main():
    """Main entry point"""
    try:
        app = create_app(config_path="config.yaml")

        config = ConfigManager("config.yaml")
        host = config.server_host
        port = config.server_port
        debug = config.server_debug

        logger.info(f"Starting Flask server: {host}:{port} (debug={debug})")
        logger.info("Press Ctrl+C to stop service")

        app.run(
            host=host,
            port=port,
            debug=debug
        )

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
