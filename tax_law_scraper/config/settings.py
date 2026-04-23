"""
全局配置文件
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
KNOWLEDGE_BASE_DIR = os.path.join(DATA_DIR, "knowledge_base")

DB_PATH = os.path.join(DATA_DIR, "tax_documents.db")

REQUEST_CONFIG = {
    "delay_min": 2.0,
    "delay_max": 5.0,
    "timeout": 30,
    "max_retries": 3,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
}

SCRAPLING_CONFIG = {
    "headless": True,
    "disable_images": True,
    "stealth": True,
}

LOG_CONFIG = {
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "level": "INFO",
}
