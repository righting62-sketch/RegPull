"""
日志工具
"""
import logging
import os
from config.settings import LOG_CONFIG, LOGS_DIR


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件名

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_CONFIG['level']))

    formatter = logging.Formatter(
        LOG_CONFIG['format'],
        datefmt=LOG_CONFIG['datefmt']
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        os.makedirs(LOGS_DIR, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(LOGS_DIR, log_file),
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
