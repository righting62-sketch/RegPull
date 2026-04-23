"""
模块二运行入口
"""
import os
import json
import argparse
import shutil
from typing import List, Dict, Optional, Tuple
from database.db_manager import TaxDocumentDB
from config.settings import DB_PATH, KNOWLEDGE_BASE_DIR
from config.category_mapping import CATEGORY_NAMES
from utils.helpers import sanitize_filename, ensure_dir
from utils.logger import setup_logger
from .page_fetcher import PageFetcher
import requests


class DetailDownloader:
    """详情页下载器"""

    def __init__(self):
        self.db = TaxDocumentDB(DB_PATH)
        self.logger = setup_logger('module2', 'module2.log')
        self.page_fetcher = PageFetcher()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

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

        print(f"\n处理完成: 成功 {success_count}, 失败 {fail_count}")

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
                    suffix='_正文'
                )
                print(f"  保存正文: {os.path.basename(content_path)}")
                if self._save_text(content, content_path):
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
                        suffix=f'_{name}' if name else f'_附件{idx}'
                    )

                    print(f"  下载附件: {name[:30]}")
                    if self._download_file(url, save_path):
                        saved_paths.append(save_path)

            if saved_paths:
                local_path = '|'.join(saved_paths)
                self.db.update_download_status(doc['id'], local_path)
                print(f"  保存成功: {len(saved_paths)} 个文件")
                return True

            return False

        except Exception as e:
            self.logger.error(f"处理文档失败: {doc['id']}, 错误: {e}")
            print(f"  处理失败: {e}")
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
                suffix='_文档'
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

    def _generate_save_path(self, category: str, doc_number: str, title: str, ext: str, suffix: str = '') -> str:
        """
        生成保存路径

        Args:
            category: 分类
            doc_number: 发文字号
            title: 标题
            ext: 扩展名
            suffix: 文件名后缀

        Returns:
            保存路径
        """
        category_name = CATEGORY_NAMES.get(category, category)
        safe_doc_number = sanitize_filename(doc_number) if doc_number else '无文号'
        safe_title = sanitize_filename(title)

        filename = f"{safe_doc_number}_{safe_title}{suffix}.{ext}"
        filename = filename[:200]

        return os.path.join(KNOWLEDGE_BASE_DIR, category_name, filename)

    def _save_text(self, content: str, save_path: str) -> bool:
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
            print(f"    文本保存失败: {e}")
            return False

    def _download_file(self, url: str, save_path: str) -> bool:
        """
        下载文件

        Args:
            url: 文件URL
            save_path: 保存路径

        Returns:
            是否成功
        """
        try:
            ensure_dir(os.path.dirname(save_path))

            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            print(f"    文件下载失败: {e}")
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
