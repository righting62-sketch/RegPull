"""
辅助函数
"""
import re
import os
import random
import time
from datetime import datetime


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = filename.strip('._')
    return filename[:200]


def random_delay(min_delay: float = 2.0, max_delay: float = 5.0):
    """
    随机延迟

    Args:
        min_delay: 最小延迟（秒）
        max_delay: 最大延迟（秒）
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def get_random_user_agent(user_agents: list) -> str:
    """
    获取随机User-Agent

    Args:
        user_agents: User-Agent列表

    Returns:
        随机选择的User-Agent
    """
    return random.choice(user_agents)


def parse_date(date_str: str) -> str:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串

    Returns:
        标准化的日期字符串 (YYYY-MM-DD)
    """
    if not date_str:
        return ""

    patterns = [
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'\1-\2-\3'),
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', r'\1-\2-\3'),
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', r'\1-\2-\3'),
    ]

    for pattern, replacement in patterns:
        match = re.search(pattern, date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    return date_str


def ensure_dir(dir_path: str):
    """
    确保目录存在

    Args:
        dir_path: 目录路径
    """
    os.makedirs(dir_path, exist_ok=True)


def generate_doc_id(category: str, doc_number: str, title: str) -> str:
    """
    生成文档唯一ID

    Args:
        category: 分类
        doc_number: 发文字号
        title: 标题

    Returns:
        文档ID
    """
    content = f"{category}_{doc_number}_{title}"
    import hashlib
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
