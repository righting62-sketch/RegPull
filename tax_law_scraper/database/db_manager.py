"""
数据库模型定义
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager


class TaxDocumentDB:
    """税务文档数据库管理类"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tax_documents (
                    id VARCHAR(100) PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    doc_number VARCHAR(100),
                    status VARCHAR(20),
                    publish_date DATE,
                    detail_url VARCHAR(500),
                    download_urls TEXT,
                    is_downloaded BOOLEAN DEFAULT 0,
                    local_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON tax_documents(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON tax_documents(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_downloaded ON tax_documents(is_downloaded)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_publish_date ON tax_documents(publish_date)')

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def insert_document(self, doc: Dict) -> bool:
        """
        插入文档记录

        Args:
            doc: 文档字典

        Returns:
            是否插入成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO tax_documents 
                    (id, category, title, doc_number, status, publish_date, detail_url, download_urls)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doc.get('id'),
                    doc.get('category'),
                    doc.get('title'),
                    doc.get('doc_number'),
                    doc.get('status'),
                    doc.get('publish_date'),
                    doc.get('detail_url'),
                    doc.get('download_urls')
                ))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"插入文档失败: {e}")
                return False

    def batch_insert_documents(self, docs: List[Dict]) -> int:
        """
        批量插入文档记录

        Args:
            docs: 文档列表

        Returns:
            成功插入的数量
        """
        success_count = 0
        for doc in docs:
            if self.insert_document(doc):
                success_count += 1
        return success_count

    def get_unprocessed_documents(self, limit: Optional[int] = None, category: Optional[str] = None) -> List[Dict]:
        """
        获取未处理的文档

        Args:
            limit: 限制数量
            category: 分类筛选

        Returns:
            未处理的文档列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = 'SELECT * FROM tax_documents WHERE is_downloaded = 0'
            params = []

            if category:
                sql += ' AND category = ?'
                params.append(category)

            if limit:
                sql += f' LIMIT {limit}'

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def update_download_status(self, doc_id: str, local_path: str) -> bool:
        """
        更新下载状态

        Args:
            doc_id: 文档ID
            local_path: 本地路径

        Returns:
            是否更新成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE tax_documents 
                    SET is_downloaded = 1, local_path = ?, updated_at = ?
                    WHERE id = ?
                ''', (local_path, datetime.now().isoformat(), doc_id))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"更新下载状态失败: {e}")
                return False

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM tax_documents')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM tax_documents WHERE is_downloaded = 1')
            downloaded = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM tax_documents WHERE is_downloaded = 0')
            pending = cursor.fetchone()[0]

            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM tax_documents 
                GROUP BY category
            ''')
            by_category = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'total': total,
                'downloaded': downloaded,
                'pending': pending,
                'by_category': by_category
            }

    def document_exists(self, doc_id: str) -> bool:
        """
        检查文档是否存在

        Args:
            doc_id: 文档ID

        Returns:
            是否存在
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM tax_documents WHERE id = ?', (doc_id,))
            return cursor.fetchone() is not None
