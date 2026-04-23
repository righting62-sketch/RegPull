"""
任务生成主逻辑 - 增强版反爬虫策略
"""
import json
import random
import time
from typing import List, Dict
from .api_fetcher import APIFetcher
from database.db_manager import TaxDocumentDB
from config.category_mapping import CATEGORY_MAPPING, CATEGORY_NAMES
from config.settings import DB_PATH, REQUEST_CONFIG
from utils.helpers import generate_doc_id, parse_date
from utils.logger import setup_logger


class TaskGenerator:
    """任务生成器 - 增强版"""

    def __init__(self):
        self.api_fetcher = APIFetcher()
        self.db = TaxDocumentDB(DB_PATH)
        self.logger = setup_logger('module1', 'module1.log')
        self.total_pages_processed = 0
        self.total_items_saved = 0

    def _page_delay(self):
        """页面间延迟"""
        delay = random.uniform(
            REQUEST_CONFIG['page_delay_min'],
            REQUEST_CONFIG['page_delay_max']
        )
        print(f"💤 页面间休眠 {delay:.2f} 秒以规避风控...\n")
        time.sleep(delay)

    def _print_progress(self, current: int, total: int, success: int):
        """打印进度"""
        progress = (current / total * 100) if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r进度: [{bar}] {progress:.1f}% | 已处理: {current}/{total} | 已入库: {success}", end='')
        if current == total:
            print()

    def generate_tasks(self, category_key: str = None, max_pages: int = None):
        """
        生成任务

        Args:
            category_key: 分类键，为None时处理所有分类
            max_pages: 最大页数，为None时使用配置的总页数
        """
        categories = {category_key: CATEGORY_MAPPING[category_key]} if category_key else CATEGORY_MAPPING

        for cat_key, cat_info in categories.items():
            self.logger.info(f"开始处理分类: {cat_info['name']}")
            print(f"\n{'='*60}")
            print(f"分类: {cat_info['name']}")
            print(f"Channel ID: {cat_info['channel_id']}")
            print(f"{'='*60}")

            channel_id = cat_info['channel_id']
            total_pages = max_pages if max_pages else cat_info['total_pages']

            total_count = 0
            success_count = 0
            failed_pages = []

            for page in range(1, total_pages + 1):
                print(f"\n⏳ 正在获取第 {page}/{total_pages} 页...")

                response = self.api_fetcher.fetch_list(channel_id, page)

                if not response:
                    self.logger.warning(f"第 {page} 页获取失败")
                    failed_pages.append(page)
                    print(f"⚠️  第 {page} 页获取失败")
                    continue

                items = self.api_fetcher.parse_list_response(response)

                if not items:
                    self.logger.info(f"第 {page} 页无数据，停止翻页")
                    print(f"✅ 第 {page} 页无数据，停止翻页")
                    break

                page_total = self.api_fetcher.get_total_count(response)
                total_count = page_total

                print(f"📄 本页获取 {len(items)} 条，总计 {page_total} 条")

                for item in items:
                    doc = self._parse_item(item, cat_key)
                    if doc and self.db.insert_document(doc):
                        success_count += 1

                self._print_progress(page, total_pages, success_count)
                
                self.total_pages_processed += 1
                self.total_items_saved += success_count

                if page < total_pages:
                    self._page_delay()

            stats = self.api_fetcher.get_stats()
            print(f"\n{'='*60}")
            print(f"✅ 分类处理完成")
            print(f"   - 成功入库: {success_count} 条")
            print(f"   - 失败页面: {len(failed_pages)} 页 {failed_pages if failed_pages else ''}")
            print(f"   - 总请求数: {stats['total_requests']}")
            print(f"   - 连续失败: {stats['consecutive_failures']}")
            print(f"   - 当前延迟倍数: {stats['current_delay_multiplier']:.2f}x")
            print(f"   - 使用 curl_cffi: {'✓' if stats['using_curl_cffi'] else '✗'}")
            print(f"{'='*60}\n")
            
            self.logger.info(f"分类 {cat_info['name']} 处理完成，共入库 {success_count} 条")

    def _parse_item(self, item: Dict, category_key: str) -> Dict:
        """
        解析单个条目

        Args:
            item: API返回的单个条目
            category_key: 分类键

        Returns:
            文档字典
        """
        try:
            title = item.get('title', '')

            detail_url = item.get('url', '')
            if detail_url.startswith('http://'):
                detail_url = detail_url.replace('http://', 'https://')
            detail_url = detail_url.replace('www.chinatax.gov.cn', 'fgk.chinatax.gov.cn')

            doc_number = self._extract_metadata(item, 'writtentext', '')
            publish_date = self._extract_metadata(item, 'writtendate', '')
            status = self._extract_metadata(item, 'aging', '有效')

            download_urls = self._extract_download_urls(item)

            doc_id = generate_doc_id(category_key, doc_number, title)

            return {
                'id': doc_id,
                'category': category_key,
                'title': title,
                'doc_number': doc_number,
                'status': status,
                'publish_date': parse_date(publish_date),
                'detail_url': detail_url,
                'download_urls': download_urls
            }

        except Exception as e:
            self.logger.error(f"解析条目失败: {e}")
            return None

    def _extract_metadata(self, item: Dict, key: str, default: str = '') -> str:
        """
        从元数据中提取值

        Args:
            item: API返回的单个条目
            key: 元数据键
            default: 默认值

        Returns:
            元数据值
        """
        domain_meta_list = item.get('domainMetaList', [])

        for domain_meta in domain_meta_list:
            result_list = domain_meta.get('resultList', [])
            for result in result_list:
                if result.get('key') == key:
                    return result.get('value', default)

        return default

    def _extract_download_urls(self, item: Dict) -> str:
        """
        提取下载链接

        Args:
            item: API返回的单个条目

        Returns:
            下载链接JSON字符串
        """
        download_list = []

        res_list = item.get('resList', [])
        for res in res_list:
            file_url = res.get('url', '')
            file_name = res.get('fileName', res.get('title', ''))
            if file_url:
                if file_url.startswith('/'):
                    file_url = f"https://fgk.chinatax.gov.cn{file_url}"
                download_list.append({
                    'url': file_url,
                    'name': file_name
                })

        text_attach = self._extract_metadata(item, 'texteditionattach', '')
        if text_attach:
            if text_attach.startswith('/'):
                text_attach = f"https://fgk.chinatax.gov.cn{text_attach}"
            download_list.append({
                'url': text_attach,
                'name': '文字版'
            })

        image_attach = self._extract_metadata(item, 'imageeditionattach', '')
        if image_attach:
            if image_attach.startswith('/'):
                image_attach = f"https://fgk.chinatax.gov.cn{image_attach}"
            download_list.append({
                'url': image_attach,
                'name': '图片版'
            })

        return json.dumps(download_list, ensure_ascii=False) if download_list else ''

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息
        """
        return self.db.get_statistics()
