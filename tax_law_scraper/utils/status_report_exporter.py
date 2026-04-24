"""
状态映射报告导出工具
用于导出文件与文档状态的映射关系报告
"""
import os
import json
import csv
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import TaxDocumentDB
from config.settings import DB_PATH, KNOWLEDGE_BASE_DIR


class StatusReportExporter:
    """状态映射报告导出器"""

    def __init__(self, db_path: str = DB_PATH):
        self.db = TaxDocumentDB(db_path)

    def export_json_report(self, output_path: str, category: str = None, doc_status: str = None) -> bool:
        """
        导出JSON格式的状态映射报告

        Args:
            output_path: 输出文件路径
            category: 分类筛选（可选）
            doc_status: 文档状态筛选（可选）

        Returns:
            是否导出成功
        """
        try:
            report = self._generate_report_data(category, doc_status)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"导出JSON报告失败: {e}")
            return False

    def export_csv_report(self, output_path: str, category: str = None, doc_status: str = None) -> bool:
        """
        导出CSV格式的状态映射报告

        Args:
            output_path: 输出文件路径
            category: 分类筛选（可选）
            doc_status: 文档状态筛选（可选）

        Returns:
            是否导出成功
        """
        try:
            report = self._generate_report_data(category, doc_status)
            files_data = report.get('files', [])

            if not files_data:
                print("没有数据可导出")
                return False

            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # 写入表头
                headers = ['doc_id', 'title', 'doc_number', 'category', 'document_status',
                          'is_effective', 'file_path', 'file_type', 'file_status',
                          'download_time', 'source_url']
                writer.writerow(headers)

                # 写入数据
                for file_info in files_data:
                    writer.writerow([
                        file_info.get('doc_id', ''),
                        file_info.get('title', ''),
                        file_info.get('doc_number', ''),
                        file_info.get('category', ''),
                        file_info.get('document_status', ''),
                        '是' if file_info.get('is_effective') else '否',
                        file_info.get('file_path', ''),
                        file_info.get('file_type', ''),
                        file_info.get('file_status', ''),
                        file_info.get('download_time', ''),
                        file_info.get('source_url', '')
                    ])

            return True
        except Exception as e:
            print(f"导出CSV报告失败: {e}")
            return False

    def _generate_report_data(self, category: str = None, doc_status: str = None) -> Dict:
        """
        生成报告数据

        Args:
            category: 分类筛选
            doc_status: 文档状态筛选

        Returns:
            报告数据字典
        """
        files_data = []

        # 获取文件列表
        if doc_status:
            files = self.db.get_files_by_doc_status(doc_status, category)
        else:
            files = self.db.get_files_by_status('valid', category)
            files.extend(self.db.get_files_by_status('invalid', category))

        for file_record in files:
            doc_id = file_record.get('doc_id')
            doc = self.db.get_document_by_id(doc_id)

            if doc:
                files_data.append({
                    'doc_id': doc_id,
                    'title': doc.get('title', ''),
                    'doc_number': doc.get('doc_number', ''),
                    'category': doc.get('category', ''),
                    'document_status': doc.get('status', ''),
                    'is_effective': doc.get('status') != '全文废止',
                    'file_path': file_record.get('file_path', ''),
                    'file_type': file_record.get('file_type', ''),
                    'file_status': file_record.get('file_status', ''),
                    'download_time': file_record.get('download_time', ''),
                    'source_url': file_record.get('source_url', '')
                })

        # 统计信息
        total_files = len(files_data)
        effective_files = sum(1 for f in files_data if f['is_effective'])
        abolished_files = total_files - effective_files

        category_stats = {}
        for f in files_data:
            cat = f['category']
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'effective': 0, 'abolished': 0}
            category_stats[cat]['total'] += 1
            if f['is_effective']:
                category_stats[cat]['effective'] += 1
            else:
                category_stats[cat]['abolished'] += 1

        return {
            'generated_at': datetime.now().isoformat(),
            'filters': {
                'category': category,
                'doc_status': doc_status
            },
            'statistics': {
                'total_files': total_files,
                'effective_files': effective_files,
                'abolished_files': abolished_files,
                'by_category': category_stats
            },
            'files': files_data
        }

    def print_summary(self, category: str = None):
        """
        打印状态映射摘要

        Args:
            category: 分类筛选
        """
        stats = self.db.get_file_status_statistics()
        doc_stats = self.db.get_statistics()

        print("\n" + "=" * 60)
        print("文件状态映射摘要")
        print("=" * 60)
        print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"筛选分类: {category if category else '全部'}")
        print("-" * 60)

        print("\n【文件统计】")
        print(f"  总文件数: {stats.get('total', 0)}")
        print(f"  有效文件: {stats.get('valid', 0)}")
        print(f"  失效文件: {stats.get('invalid', 0)}")

        print("\n【按文档状态统计】")
        for status, count in stats.get('by_doc_status', {}).items():
            status_label = '【废止】' if status == '全文废止' else ''
            print(f"  {status}{status_label}: {count} 个文件")

        print("\n【文档统计】")
        print(f"  总文档数: {doc_stats.get('total', 0)}")
        print(f"  已下载: {doc_stats.get('downloaded', 0)}")
        print(f"  待处理: {doc_stats.get('pending', 0)}")

        print("=" * 60)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='状态映射报告导出工具')
    parser.add_argument('--summary', action='store_true', help='打印摘要信息')
    parser.add_argument('--export-json', type=str, help='导出JSON报告到指定路径')
    parser.add_argument('--export-csv', type=str, help='导出CSV报告到指定路径')
    parser.add_argument('--category', type=str, help='按分类筛选')
    parser.add_argument('--status', type=str, help='按文档状态筛选（如：全文废止）')

    args = parser.parse_args()

    exporter = StatusReportExporter()

    if args.summary or (not args.export_json and not args.export_csv):
        exporter.print_summary(args.category)

    if args.export_json:
        if exporter.export_json_report(args.export_json, args.category, args.status):
            print(f"\nJSON报告已导出: {args.export_json}")

    if args.export_csv:
        if exporter.export_csv_report(args.export_csv, args.category, args.status):
            print(f"\nCSV报告已导出: {args.export_csv}")


if __name__ == '__main__':
    main()
