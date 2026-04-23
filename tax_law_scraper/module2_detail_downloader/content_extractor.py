"""
内容提取和文件下载
"""
import os
import re
import requests
from typing import Dict, List, Optional
from config.settings import REQUEST_CONFIG, KNOWLEDGE_BASE_DIR
from utils.helpers import sanitize_filename, ensure_dir


class ContentExtractor:
    """内容提取类"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def download_file(self, url: str, save_path: str) -> bool:
        """
        下载文件

        Args:
            url: 文件URL
            save_path: 保存路径

        Returns:
            是否成功
        """
        try:
            response = self.session.get(url, timeout=REQUEST_CONFIG['timeout'], stream=True)
            response.raise_for_status()

            ensure_dir(os.path.dirname(save_path))

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            print(f"文件下载失败: {e}")
            return False

    def save_text(self, content: str, save_path: str) -> bool:
        """
        保存文本内容

        Args:
            content: 文本内容
            save_path: 保存路径

        Returns:
            是否成功
        """
        try:
            ensure_dir(os.path.dirname(save_path))

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"文本保存失败: {e}")
            return False

    def generate_save_path(self, category: str, doc_number: str, title: str, ext: str = 'txt') -> str:
        """
        生成保存路径

        Args:
            category: 分类
            doc_number: 发文字号
            title: 标题
            ext: 扩展名

        Returns:
            保存路径
        """
        from config.category_mapping import CATEGORY_NAMES

        category_name = CATEGORY_NAMES.get(category, category)
        safe_doc_number = sanitize_filename(doc_number) if doc_number else '无文号'
        safe_title = sanitize_filename(title)

        filename = f"{safe_doc_number}_{safe_title}.{ext}"
        filename = filename[:200]

        return os.path.join(KNOWLEDGE_BASE_DIR, category_name, filename)

    def clean_content(self, content: str) -> str:
        """
        清理内容

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        return content.strip()
