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
    "delay_min": 5.0,
    "delay_max": 12.0,
    "page_delay_min": 8.0,
    "page_delay_max": 15.0,
    "timeout": 30,
    "max_retries": 3,
    "retry_delay_base": 10,
    "retry_delay_max": 60,
    "impersonate_browser": "chrome120",
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ],
    "firewall_indicators": [
        "请求被阻断",
        "访问频率过高",
        "请稍后再试",
        "403",
        "Forbidden",
        "blocked"
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
