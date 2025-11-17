"""日誌模組"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "trash_tracking",
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    設定並返回 logger 實例

    Args:
        name: Logger 名稱
        log_level: 日誌等級 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日誌檔案路徑，若為 None 則只輸出到 console

    Returns:
        logging.Logger: 設定好的 logger 實例
    """
    logger = logging.getLogger(name)

    # 避免重複添加 handler
    if logger.handlers:
        return logger

    # 設定日誌等級
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # 設定日誌格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (可選)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 預設 logger 實例
logger = setup_logger()
