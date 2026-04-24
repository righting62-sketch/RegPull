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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id VARCHAR(100) NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type VARCHAR(20),
                    file_status VARCHAR(20) DEFAULT 'valid',
                    source_url TEXT,
                    file_size INTEGER,
                    download_time TIMESTAMP,
                    verify_time TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (doc_id) REFERENCES tax_documents(id)
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON tax_documents(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON tax_documents(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_downloaded ON tax_documents(is_downloaded)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_publish_date ON tax_documents(publish_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_df_doc_id ON downloaded_files(doc_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_df_file_status ON downloaded_files(file_status)')

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

    def insert_downloaded_file(self, file_record: Dict) -> bool:
        """
        插入下载文件记录

        Args:
            file_record: 文件记录字典，包含 doc_id, file_path, file_type, file_status, source_url, file_size

        Returns:
            是否插入成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO downloaded_files
                    (doc_id, file_path, file_type, file_status, source_url, file_size, download_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_record.get('doc_id'),
                    file_record.get('file_path'),
                    file_record.get('file_type'),
                    file_record.get('file_status', 'valid'),
                    file_record.get('source_url'),
                    file_record.get('file_size'),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"插入文件记录失败: {e}")
                return False

    def get_files_by_doc_id(self, doc_id: str) -> List[Dict]:
        """
        获取指定文档的所有下载文件

        Args:
            doc_id: 文档ID

        Returns:
            文件记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM downloaded_files WHERE doc_id = ?
            ''', (doc_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_files_by_status(self, file_status: str, category: Optional[str] = None) -> List[Dict]:
        """
        按文件状态获取文件列表

        Args:
            file_status: 文件状态 (valid/invalid/unknown)
            category: 分类筛选（可选）

        Returns:
            文件记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute('''
                    SELECT df.*, td.category, td.title, td.status as doc_status
                    FROM downloaded_files df
                    JOIN tax_documents td ON df.doc_id = td.id
                    WHERE df.file_status = ? AND td.category = ?
                ''', (file_status, category))
            else:
                cursor.execute('''
                    SELECT df.*, td.category, td.title, td.status as doc_status
                    FROM downloaded_files df
                    JOIN tax_documents td ON df.doc_id = td.id
                    WHERE df.file_status = ?
                ''', (file_status,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_files_by_doc_status(self, doc_status: str, category: Optional[str] = None) -> List[Dict]:
        """
        按文档状态（如"全文废止"）获取文件列表

        Args:
            doc_status: 文档状态
            category: 分类筛选（可选）

        Returns:
            文件记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute('''
                    SELECT df.*, td.category, td.title, td.status as doc_status
                    FROM downloaded_files df
                    JOIN tax_documents td ON df.doc_id = td.id
                    WHERE td.status = ? AND td.category = ?
                ''', (doc_status, category))
            else:
                cursor.execute('''
                    SELECT df.*, td.category, td.title, td.status as doc_status
                    FROM downloaded_files df
                    JOIN tax_documents td ON df.doc_id = td.id
                    WHERE td.status = ?
                ''', (doc_status,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_file_status(self, file_path: str, file_status: str, error_message: str = None) -> bool:
        """
        更新文件状态

        Args:
            file_path: 文件路径
            file_status: 新状态
            error_message: 错误信息（可选）

        Returns:
            是否更新成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                if error_message:
                    cursor.execute('''
                        UPDATE downloaded_files
                        SET file_status = ?, verify_time = ?, error_message = ?
                        WHERE file_path = ?
                    ''', (file_status, datetime.now().isoformat(), error_message, file_path))
                else:
                    cursor.execute('''
                        UPDATE downloaded_files
                        SET file_status = ?, verify_time = ?
                        WHERE file_path = ?
                    ''', (file_status, datetime.now().isoformat(), file_path))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"更新文件状态失败: {e}")
                return False

    def get_file_status_statistics(self) -> Dict:
        """
        获取文件状态统计信息

        Returns:
            统计信息字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM downloaded_files')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM downloaded_files WHERE file_status = "valid"')
            valid = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM downloaded_files WHERE file_status = "invalid"')
            invalid = cursor.fetchone()[0]

            cursor.execute('''
                SELECT td.status, COUNT(*) as count
                FROM downloaded_files df
                JOIN tax_documents td ON df.doc_id = td.id
                GROUP BY td.status
            ''')
            by_doc_status = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'total': total,
                'valid': valid,
                'invalid': invalid,
                'by_doc_status': by_doc_status
            }

    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """
        根据ID获取文档信息

        Args:
            doc_id: 文档ID

        Returns:
            文档字典，不存在返回None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tax_documents WHERE id = ?', (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
