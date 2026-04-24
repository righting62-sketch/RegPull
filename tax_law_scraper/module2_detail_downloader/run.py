"""
模块二运行入口 - 增强版反爬虫策略
"""
import os
import json
import argparse
import shutil
import random
import time
from typing import List, Dict, Optional, Tuple
from database.db_manager import TaxDocumentDB
from config.settings import DB_PATH, KNOWLEDGE_BASE_DIR, REQUEST_CONFIG
from config.category_mapping import CATEGORY_NAMES
from utils.helpers import sanitize_filename, ensure_dir
from utils.logger import setup_logger
from .page_fetcher import PageFetcher
from datetime import datetime

try:
    from curl_cffi import requests as curl_requests
    USE_CURL_CFFI = True
except ImportError:
    import requests as curl_requests
    USE_CURL_CFFI = False


class DetailDownloader:
    """详情页下载器 - 增强版"""

    def __init__(self):
        self.db = TaxDocumentDB(DB_PATH)
        self.logger = setup_logger('module2', 'module2.log')
        self.page_fetcher = PageFetcher()
        self.session = curl_requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'User-Agent': random.choice(REQUEST_CONFIG['user_agents'])
        })
        self.download_count = 0
        self.consecutive_failures = 0
        self.current_delay_multiplier = 1.0

    def _calculate_adaptive_delay(self) -> float:
        """计算自适应延迟时间"""
        base_delay = random.uniform(
            REQUEST_CONFIG['delay_min'],
            REQUEST_CONFIG['delay_max']
        )
        
        if self.consecutive_failures > 0:
            multiplier = min(self.current_delay_multiplier * 1.5, 5.0)
            self.current_delay_multiplier = multiplier
        else:
            self.current_delay_multiplier = max(1.0, self.current_delay_multiplier * 0.9)
        
        adaptive_delay = base_delay * self.current_delay_multiplier
        
        return min(adaptive_delay, 30.0)

    def _exponential_backoff(self, retry_count: int) -> float:
        """指数退避算法"""
        base_delay = REQUEST_CONFIG['retry_delay_base']
        max_delay = REQUEST_CONFIG['retry_delay_max']
        
        delay = base_delay * (2 ** retry_count)
        delay = min(delay, max_delay)
        
        jitter = random.uniform(0, delay * 0.3)
        
        return delay + jitter

    def _smart_sleep(self, delay: float, reason: str = ""):
        """智能休眠"""
        if reason:
            print(f"💤 休眠 {delay:.2f} 秒 ({reason})...")
        time.sleep(delay)

    def _document_delay(self):
        """文档间延迟"""
        delay = random.uniform(
            REQUEST_CONFIG['page_delay_min'],
            REQUEST_CONFIG['page_delay_max']
        )
        print(f"💤 文档间休眠 {delay:.2f} 秒以规避风控...\n")
        time.sleep(delay)

    def _check_download_blocked(self, response) -> bool:
        """检查下载是否被拦截"""
        if response.status_code == 403:
            return True
        
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type and len(response.content) < 5000:
            try:
                text = response.text.lower()
                for indicator in REQUEST_CONFIG['firewall_indicators']:
                    if indicator.lower() in text:
                        return True
            except:
                pass
        
        return False

    def process_documents(self, limit: int = None, category: str = None):
        """
        处理文档

        Args:
            limit: 处理数量限制
            category: 分类筛选
        """
        documents = self.db.get_unprocessed_documents(limit, category)

        if not documents:
            print("没有待处理的文档")
            return

        print(f"\n找到 {len(documents)} 个待处理文档")

        success_count = 0
        fail_count = 0

        for i, doc in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}] 处理: {doc['title'][:50]}")

            result = self._process_single_document(doc)

            if result:
                success_count += 1
            else:
                fail_count += 1

            if i < len(documents):
                self._document_delay()

        print(f"\n{'='*60}")
        print(f"✅ 处理完成")
        print(f"   - 成功: {success_count}")
        print(f"   - 失败: {fail_count}")
        print(f"   - 总下载: {self.download_count}")
        
        stats = self.page_fetcher.get_stats()
        print(f"   - 页面请求: {stats['total_requests']}")
        print(f"   - 连续失败: {stats['consecutive_failures']}")
        print(f"   - 延迟倍数: {stats['current_delay_multiplier']:.2f}x")
        print(f"{'='*60}")

    def _process_single_document(self, doc: Dict) -> bool:
        """
        处理单个文档

        Args:
            doc: 文档信息

        Returns:
            是否成功
        """
        try:
            detail_url = doc.get('detail_url', '')
            if not detail_url:
                print("  没有详情页链接")
                self.logger.warning(f"没有详情页链接: {doc['id']}")
                return False

            print(f"  访问: {detail_url[:80]}...")

            saved_paths = []

            content, download_temp_path = self.page_fetcher.fetch_click_and_download(detail_url)

            if content and len(content) > 50:
                content_path = self._generate_save_path(
                    doc['category'],
                    doc['doc_number'],
                    doc['title'],
                    'txt',
                    suffix='_正文',
                    doc_status=doc.get('status', '')
                )
                print(f"  保存正文: {os.path.basename(content_path)}")
                if self._save_text(content, content_path, doc):
                    saved_paths.append(content_path)

            if download_temp_path and os.path.exists(download_temp_path):
                final_path = self._save_downloaded_file(download_temp_path, doc)
                if final_path:
                    saved_paths.append(final_path)

            download_urls_str = doc.get('download_urls', '')
            if download_urls_str:
                download_list = json.loads(download_urls_str)
                for idx, item in enumerate(download_list, 1):
                    url = item.get('url', '')
                    name = item.get('name', f'附件{idx}')

                    if not url:
                        continue

                    ext = self._get_extension(url)
                    save_path = self._generate_save_path(
                        doc['category'],
                        doc['doc_number'],
                        doc['title'],
                        ext,
                        suffix=f'_{name}' if name else f'_附件{idx}',
                        doc_status=doc.get('status', '')
                    )

                    print(f"  下载附件: {name[:30]}")
                    if self._download_file_with_retry(url, save_path, doc=doc, file_type='attachment'):
                        saved_paths.append(save_path)

            if saved_paths:
                local_path = '|'.join(saved_paths)
                self.db.update_download_status(doc['id'], local_path)
                print(f"  ✅ 保存成功: {len(saved_paths)} 个文件")
                return True

            return False

        except Exception as e:
            self.logger.error(f"处理文档失败: {doc['id']}, 错误: {e}")
            print(f"  ❌ 处理失败: {e}")
            return False

    def _save_downloaded_file(self, temp_path: str, doc: Dict) -> Optional[str]:
        """
        保存下载的文件到目标目录

        Args:
            temp_path: 临时文件路径
            doc: 文档信息

        Returns:
            最终保存路径
        """
        try:
            filename = os.path.basename(temp_path)
            ext = os.path.splitext(filename)[1].lstrip('.')
            if not ext:
                ext = 'pdf'

            final_path = self._generate_save_path(
                doc['category'],
                doc['doc_number'],
                doc['title'],
                ext,
                suffix='_文档',
                doc_status=doc.get('status', '')
            )

            ensure_dir(os.path.dirname(final_path))
            shutil.move(temp_path, final_path)

            print(f"  保存文档: {os.path.basename(final_path)}")
            return final_path

        except Exception as e:
            print(f"    保存下载文件失败: {e}")
            return None

    def _get_extension(self, url: str) -> str:
        """
        从URL获取文件扩展名

        Args:
            url: 文件URL

        Returns:
            扩展名
        """
        ext = url.split('.')[-1].lower()
        if ext not in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip', 'rar']:
            ext = 'pdf'
        return ext

    def _get_status_label(self, doc_status: str) -> str:
        """
        根据文档状态获取标签

        Args:
            doc_status: 文档状态

        Returns:
            状态标签
        """
        status_label_map = {
            '全文废止': '【废止】',
            '全文失效': '【失效】',
            '全文有效': '【有效】',
            '部分有效': '【部分有效】',
            '部分废止': '【部分废止】',
            '部分失效': '【部分失效】',
        }
        return status_label_map.get(doc_status, f'【{doc_status}】' if doc_status else '')

    def _generate_save_path(self, category: str, doc_number: str, title: str, ext: str, suffix: str = '', doc_status: str = '') -> str:
        """
        生成保存路径

        Args:
            category: 分类
            doc_number: 发文字号
            title: 标题
            ext: 扩展名
            suffix: 文件名后缀
            doc_status: 文档状态（用于文件标记）

        Returns:
            保存路径
        """
        category_name = CATEGORY_NAMES.get(category, category)
        safe_doc_number = sanitize_filename(doc_number) if doc_number else '无文号'
        safe_title = sanitize_filename(title)

        # 根据状态添加标签
        status_prefix = self._get_status_label(doc_status)

        filename = f"{status_prefix}{safe_doc_number}_{safe_title}{suffix}.{ext}"
        filename = filename[:200]

        return os.path.join(KNOWLEDGE_BASE_DIR, category_name, filename)

    def _save_text(self, content: str, save_path: str, doc: Dict = None) -> bool:
        """
        保存文本内容

        Args:
            content: 文本内容
            save_path: 保存路径
            doc: 文档信息（用于生成元数据）

        Returns:
            是否成功
        """
        try:
            ensure_dir(os.path.dirname(save_path))

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"    文本保存失败: {e}")
            return False

    def _is_effective_status(self, doc_status: str) -> bool:
        """
        判断状态是否为有效状态

        Args:
            doc_status: 文档状态

        Returns:
            是否有效
        """
        # 定义有效状态列表
        effective_statuses = ['全文有效', '部分有效']
        return doc_status in effective_statuses

    def _generate_meta_file(self, file_path: str, doc: Dict, file_type: str):
        """
        生成文件元数据

        Args:
            file_path: 文件路径
            doc: 文档信息
            file_type: 文件类型 (content/document/attachment)
        """
        try:
            doc_status = doc.get('status', '')
            is_effective = self._is_effective_status(doc_status)
            label = self._get_status_label(doc_status)

            meta = {
                'doc_id': doc.get('id'),
                'title': doc.get('title'),
                'doc_number': doc.get('doc_number'),
                'category': doc.get('category'),
                'document_status': doc_status,
                'is_effective': is_effective,
                'label': label,
                'file_type': file_type,
                'file_path': file_path,
                'source_url': doc.get('detail_url'),
                'download_time': datetime.now().isoformat()
            }

            meta_path = f"{file_path}.meta.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            # 同时记录到数据库
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            file_record = {
                'doc_id': doc.get('id'),
                'file_path': file_path,
                'file_type': file_type,
                'file_status': 'valid' if is_effective else 'invalid',
                'source_url': doc.get('detail_url'),
                'file_size': file_size
            }
            self.db.insert_downloaded_file(file_record)

        except Exception as e:
            print(f"    生成元数据失败: {e}")

    def _download_file_with_retry(self, url: str, save_path: str, max_retries: int = None, doc: Dict = None, file_type: str = 'attachment') -> bool:
        """
        下载文件 - 增强版（带重试机制）

        Args:
            url: 文件URL
            save_path: 保存路径
            max_retries: 最大重试次数
            doc: 文档信息（用于生成元数据）
            file_type: 文件类型

        Returns:
            是否成功
        """
        if max_retries is None:
            max_retries = REQUEST_CONFIG['max_retries']

        for retry_count in range(max_retries):
            try:
                ensure_dir(os.path.dirname(save_path))

                headers = {
                    'User-Agent': random.choice(REQUEST_CONFIG['user_agents'])
                }

                request_kwargs = {
                    'url': url,
                    'headers': headers,
                    'timeout': 60,
                    'stream': True
                }

                if USE_CURL_CFFI:
                    request_kwargs['impersonate'] = REQUEST_CONFIG['impersonate_browser']

                response = self.session.get(**request_kwargs)

                if self._check_download_blocked(response):
                    print(f"    ⚠️  下载被拦截 (第 {retry_count + 1}/{max_retries} 次)")
                    self.consecutive_failures += 1
                    
                    if retry_count < max_retries - 1:
                        backoff_delay = self._exponential_backoff(retry_count)
                        self._smart_sleep(backoff_delay, "下载拦截退避")
                        continue
                    else:
                        print(f"    ❌ 已达到最大重试次数")
                        return False

                response.raise_for_status()

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                self.consecutive_failures = 0
                self.download_count += 1
                
                delay = self._calculate_adaptive_delay()
                self._smart_sleep(delay, "下载间隔")

                return True

            except Exception as e:
                self.consecutive_failures += 1
                print(f"    ⚠️  文件下载失败 (第 {retry_count + 1}/{max_retries} 次): {e}")
                
                if retry_count < max_retries - 1:
                    backoff_delay = self._exponential_backoff(retry_count)
                    self._smart_sleep(backoff_delay, "下载重试退避")
                else:
                    print(f"    ❌ 已达到最大重试次数")
                    return False

        return False


def run_module2(limit: int = None, category: str = None, show_stats: bool = False):
    """
    运行模块二

    Args:
        limit: 处理数量限制
        category: 分类筛选
        show_stats: 是否显示统计
    """
    if show_stats:
        db = TaxDocumentDB(DB_PATH)
        stats = db.get_statistics()
        print("\n数据库统计:")
        print(f"  总记录数: {stats['total']}")
        print(f"  已下载: {stats['downloaded']}")
        print(f"  待处理: {stats['pending']}")
        print("\n按分类统计:")
        for cat, count in stats['by_category'].items():
            cat_name = CATEGORY_NAMES.get(cat, cat)
            print(f"  {cat_name}: {count}")
        return

    print("\n" + "=" * 60)
    print("模块二：详情页下载器")
    print("=" * 60)

    if category:
        print(f"分类: {CATEGORY_NAMES.get(category, category)}")
    else:
        print("分类: 全部")

    if limit:
        print(f"数量限制: {limit}")

    print(f"使用 curl_cffi: {'✓' if USE_CURL_CFFI else '✗'}")
    print("=" * 60)

    downloader = DetailDownloader()
    downloader.process_documents(limit=limit, category=category)

    print("\n处理完成!")


def main():
    """独立运行时的主函数"""
    parser = argparse.ArgumentParser(description="模块二：详情页下载器")

    parser.add_argument(
        "-l", "--limit",
        type=int,
        help="处理数量限制"
    )

    parser.add_argument(
        "-c", "--category",
        choices=list(CATEGORY_NAMES.keys()),
        help=f"指定分类，可选: {list(CATEGORY_NAMES.keys())}"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )

    args = parser.parse_args()
    run_module2(args.limit, args.category, args.stats)


if __name__ == "__main__":
    main()
