"""垃圾車動態偵測系統 - 主程式"""

import sys
from src.api.routes import create_app
from src.utils.config import ConfigManager, ConfigError
from src.utils.logger import logger


def main():
    """主程式進入點"""
    try:
        # 建立 Flask 應用程式
        app = create_app(config_path="config.yaml")

        # 取得伺服器設定
        config = ConfigManager("config.yaml")
        host = config.server_host
        port = config.server_port
        debug = config.server_debug

        logger.info(f"啟動 Flask 伺服器: {host}:{port} (debug={debug})")
        logger.info("按 Ctrl+C 停止服務")

        # 啟動服務
        app.run(
            host=host,
            port=port,
            debug=debug
        )

    except ConfigError as e:
        logger.error(f"❌ 設定檔錯誤: {e}")
        logger.error("請檢查 config.yaml 檔案")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n收到中斷信號，正在關閉服務...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
