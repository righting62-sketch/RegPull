"""
文件状态验证工具
用于验证文件元数据与数据库状态的一致性
"""
import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database.db_manager import TaxDocumentDB
from config.settings import DB_PATH, KNOWLEDGE_BASE_DIR


class FileStatusValidator:
    """文件状态验证器"""

    def __init__(self, db_path: str = DB_PATH):
        self.db = TaxDocumentDB(db_path)
        self.inconsistencies: List[Dict] = []

    def validate_all_files(self, knowledge_base_dir: str = KNOWLEDGE_BASE_DIR) -> Dict:
        """
        验证所有文件的元数据与数据库状态一致性

        Args:
            knowledge_base_dir: 知识库根目录

        Returns:
            验证结果统计
        """
        self.inconsistencies = []
        total_files = 0
        valid_files = 0
        invalid_meta = 0
        missing_meta = 0
        inconsistent_status = 0

        # 遍历知识库目录
        for root, dirs, files in os.walk(knowledge_base_dir):
            for file in files:
                if file.endswith('.meta.json'):
                    continue

                total_files += 1
                file_path = os.path.join(root, file)
                meta_path = f"{file_path}.meta.json"

                # 检查元数据文件是否存在
                if not os.path.exists(meta_path):
                    missing_meta += 1
                    self.inconsistencies.append({
                        'file_path': file_path,
                        'issue': 'missing_meta',
                        'message': '缺少元数据文件'
                    })
                    continue

                # 验证元数据内容
                result = self._validate_single_file(file_path, meta_path)
                if result['valid']:
                    valid_files += 1
                else:
                    if result['issue'] == 'invalid_meta':
                        invalid_meta += 1
                    elif result['issue'] == 'inconsistent_status':
                        inconsistent_status += 1
                    self.inconsistencies.append(result)

        return {
            'total_files': total_files,
            'valid_files': valid_files,
            'invalid_meta': invalid_meta,
            'missing_meta': missing_meta,
            'inconsistent_status': inconsistent_status,
            'inconsistencies': self.inconsistencies
        }

    def _validate_single_file(self, file_path: str, meta_path: str) -> Dict:
        """
        验证单个文件的元数据

        Args:
            file_path: 文件路径
            meta_path: 元数据文件路径

        Returns:
            验证结果
        """
        try:
            # 读取元数据
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            doc_id = meta.get('doc_id')
            meta_status = meta.get('document_status')
            meta_is_effective = meta.get('is_effective')

            if not doc_id:
                return {
                    'file_path': file_path,
                    'valid': False,
                    'issue': 'invalid_meta',
                    'message': '元数据缺少 doc_id'
                }

            # 查询数据库
            doc = self.db.get_document_by_id(doc_id)
            if not doc:
                return {
                    'file_path': file_path,
                    'valid': False,
                    'issue': 'invalid_meta',
                    'message': f'数据库中不存在 doc_id: {doc_id}'
                }

            # 验证状态一致性
            db_status = doc.get('status', '')
            expected_is_effective = db_status != '全文废止'

            if meta_status != db_status or meta_is_effective != expected_is_effective:
                return {
                    'file_path': file_path,
                    'valid': False,
                    'issue': 'inconsistent_status',
                    'message': f'状态不一致: 元数据[{meta_status}/{meta_is_effective}] vs 数据库[{db_status}/{expected_is_effective}]',
                    'meta_status': meta_status,
                    'db_status': db_status,
                    'doc_id': doc_id
                }

            return {'file_path': file_path, 'valid': True}

        except json.JSONDecodeError as e:
            return {
                'file_path': file_path,
                'valid': False,
                'issue': 'invalid_meta',
                'message': f'元数据JSON解析失败: {e}'
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'valid': False,
                'issue': 'invalid_meta',
                'message': f'验证失败: {e}'
            }

    def fix_inconsistencies(self, auto_fix: bool = False) -> List[Dict]:
        """
        修复不一致的元数据

        Args:
            auto_fix: 是否自动修复（False则只返回修复建议）

        Returns:
            修复结果列表
        """
        fixed = []

        for inconsistency in self.inconsistencies:
            issue = inconsistency.get('issue')
            file_path = inconsistency.get('file_path')

            if issue == 'missing_meta':
                # 尝试从数据库重新生成元数据
                if auto_fix:
                    result = self._regenerate_meta(file_path)
                    fixed.append(result)
                else:
                    fixed.append({
                        'file_path': file_path,
                        'action': 'regenerate_meta',
                        'message': '建议从数据库重新生成元数据文件'
                    })

            elif issue == 'inconsistent_status':
                # 更新元数据中的状态
                if auto_fix:
                    result = self._update_meta_status(file_path, inconsistency)
                    fixed.append(result)
                else:
                    fixed.append({
                        'file_path': file_path,
                        'action': 'update_status',
                        'message': f"建议更新状态: {inconsistency.get('meta_status')} -> {inconsistency.get('db_status')}"
                    })

            elif issue == 'invalid_meta':
                fixed.append({
                    'file_path': file_path,
                    'action': 'manual_check',
                    'message': f"需要手动检查: {inconsistency.get('message')}"
                })

        return fixed

    def _regenerate_meta(self, file_path: str) -> Dict:
        """重新生成元数据文件"""
        try:
            # 从文件名提取doc_id（假设文件名包含doc_id或有其他映射方式）
            # 这里简化处理，实际可能需要更复杂的逻辑
            return {
                'file_path': file_path,
                'success': False,
                'message': '自动重新生成元数据需要额外的文件到doc_id的映射信息'
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'success': False,
                'message': f'重新生成元数据失败: {e}'
            }

    def _update_meta_status(self, file_path: str, inconsistency: Dict) -> Dict:
        """更新元数据中的状态"""
        try:
            meta_path = f"{file_path}.meta.json"

            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            db_status = inconsistency.get('db_status')
            meta['document_status'] = db_status
            meta['is_effective'] = db_status != '全文废止'
            meta['label'] = '【废止】' if db_status == '全文废止' else ''
            meta['verify_time'] = datetime.now().isoformat()

            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            return {
                'file_path': file_path,
                'success': True,
                'message': f"状态已更新为: {db_status}"
            }

        except Exception as e:
            return {
                'file_path': file_path,
                'success': False,
                'message': f'更新状态失败: {e}'
            }

    def generate_validation_report(self, output_path: str = None) -> str:
        """
        生成验证报告

        Args:
            output_path: 报告输出路径（可选）

        Returns:
            报告内容
        """
        if not self.inconsistencies:
            return "所有文件验证通过，无不一致问题。"

        report_lines = [
            "=" * 60,
            "文件状态验证报告",
            "=" * 60,
            f"生成时间: {datetime.now().isoformat()}",
            f"发现问题数: {len(self.inconsistencies)}",
            "",
            "详细问题列表:",
            "-" * 60
        ]

        for i, issue in enumerate(self.inconsistencies, 1):
            report_lines.extend([
                f"\n[{i}] 文件: {issue.get('file_path')}",
                f"    问题类型: {issue.get('issue')}",
                f"    描述: {issue.get('message')}"
            ])

        report_lines.append("\n" + "=" * 60)

        report = '\n'.join(report_lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='文件状态验证工具')
    parser.add_argument('--check', action='store_true', help='执行验证检查')
    parser.add_argument('--fix', action='store_true', help='自动修复不一致')
    parser.add_argument('--report', type=str, help='生成报告文件路径')
    parser.add_argument('--dir', type=str, default=KNOWLEDGE_BASE_DIR, help='知识库目录')

    args = parser.parse_args()

    validator = FileStatusValidator()

    if args.check or (not args.fix and not args.report):
        print("开始验证文件状态...")
        result = validator.validate_all_files(args.dir)

        print(f"\n验证完成:")
        print(f"  总文件数: {result['total_files']}")
        print(f"  有效文件: {result['valid_files']}")
        print(f"  无效元数据: {result['invalid_meta']}")
        print(f"  缺少元数据: {result['missing_meta']}")
        print(f"  状态不一致: {result['inconsistent_status']}")

        if result['inconsistencies']:
            print(f"\n发现 {len(result['inconsistencies'])} 个问题")

    if args.fix:
        print("\n开始修复不一致...")
        fixed = validator.fix_inconsistencies(auto_fix=True)
        print(f"修复完成，处理了 {len(fixed)} 个问题")

    if args.report:
        report = validator.generate_validation_report(args.report)
        print(f"\n报告已生成: {args.report}")


if __name__ == '__main__':
    main()
