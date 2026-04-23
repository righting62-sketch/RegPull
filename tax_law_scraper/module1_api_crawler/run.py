"""
模块一运行入口
"""
import argparse
from .task_generator import TaskGenerator
from config.category_mapping import CATEGORY_MAPPING, CATEGORY_NAMES


def run_module1(category: str = None, max_pages: int = None, show_stats: bool = False):
    """
    运行模块一

    Args:
        category: 分类键
        max_pages: 最大页数
        show_stats: 是否显示统计
    """
    generator = TaskGenerator()

    if show_stats:
        stats = generator.get_statistics()
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
    print("模块一：任务生成器")
    print("=" * 60)

    if category:
        print(f"分类: {CATEGORY_NAMES[category]}")
    else:
        print("分类: 全部")

    if max_pages:
        print(f"最大页数: {max_pages}")

    print("=" * 60)

    generator.generate_tasks(
        category_key=category,
        max_pages=max_pages
    )

    stats = generator.get_statistics()
    print("\n任务生成完成!")
    print(f"数据库总记录数: {stats['total']}")


def main():
    """独立运行时的主函数"""
    parser = argparse.ArgumentParser(description="模块一：任务生成器")

    parser.add_argument(
        "-c", "--category",
        choices=list(CATEGORY_MAPPING.keys()),
        help=f"指定分类，可选: {list(CATEGORY_MAPPING.keys())}"
    )

    parser.add_argument(
        "-p", "--max-pages",
        type=int,
        help="最大抓取页数"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )

    args = parser.parse_args()
    run_module1(args.category, args.max_pages, args.stats)


if __name__ == "__main__":
    main()
