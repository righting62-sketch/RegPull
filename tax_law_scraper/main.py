"""
国家税务总局法律法规抓取系统 - 主程序入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from module1_api_crawler.run import run_module1
from module2_detail_downloader.run import run_module2
from database.db_manager import TaxDocumentDB
from config.settings import DB_PATH
from config.category_mapping import CATEGORY_MAPPING, CATEGORY_NAMES


def show_stats():
    """显示统计信息"""
    db = TaxDocumentDB(DB_PATH)
    stats = db.get_statistics()

    print("\n" + "=" * 60)
    print("数据库统计")
    print("=" * 60)
    print(f"总记录数: {stats['total']}")
    print(f"已下载: {stats['downloaded']}")
    print(f"待处理: {stats['pending']}")

    print("\n按分类统计:")
    for cat, count in stats['by_category'].items():
        cat_name = CATEGORY_NAMES.get(cat, cat)
        print(f"  {cat_name}: {count}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="国家税务总局法律法规抓取系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --module 1                    # 运行模块一（任务生成器）
  python main.py --module 2                    # 运行模块二（详情页下载器）
  python main.py --module 1 -c guizhang        # 只抓取税务部门规章
  python main.py --module 1 -c caishui -p 5    # 只抓取财税文件前5页
  python main.py --module 2 -l 10              # 只处理10个文档
  python main.py --stats                       # 显示统计信息
        """
    )

    parser.add_argument(
        "--module",
        type=int,
        choices=[1, 2],
        help="选择模块: 1=任务生成器, 2=详情页下载器"
    )

    parser.add_argument(
        "-c", "--category",
        choices=list(CATEGORY_MAPPING.keys()),
        help=f"指定分类 (模块一)"
    )

    parser.add_argument(
        "-p", "--max-pages",
        type=int,
        help="最大抓取页数 (模块一)"
    )

    parser.add_argument(
        "-l", "--limit",
        type=int,
        help="处理数量限制 (模块二)"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    if not args.module:
        parser.print_help()
        return

    print("\n" + "#" * 60)
    print("# 国家税务总局法律法规抓取系统")
    print("#" * 60)

    if args.module == 1:
        print("\n运行模块一：任务生成器")
        run_module1(args.category, args.max_pages)
    elif args.module == 2:
        print("\n运行模块二：详情页下载器")
        run_module2(args.limit)


if __name__ == "__main__":
    main()
