"""
使用Scrapling分析页面结构 - 正确版
"""
import time
from scrapling import StealthyFetcher

CATEGORIES = {
    "guowuyuan": {
        "name": "国务院文件",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102440/listflfg.html"
    },
    "caishui": {
        "name": "财税文件",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102416/listflfg.html"
    },
    "guizhang": {
        "name": "税务部门规章",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100011/list_guizhang.html"
    }
}

def analyze_page_structure():
    """分析页面结构"""
    print("=" * 60)
    print("使用Scrapling分析页面结构")
    print("=" * 60)

    fetcher = StealthyFetcher()

    for cat_key, cat_info in CATEGORIES.items():
        print(f"\n{'='*60}")
        print(f"分类: {cat_info['name']}")
        print(f"URL: {cat_info['url']}")
        print(f"{'='*60}")

        try:
            print("\n正在加载页面...")
            page = fetcher.fetch(cat_info['url'])

            print(f"\n状态码: {page.status}")
            print(f"URL: {page.url}")

            print("\n查找列表元素...")

            selectors = [
                ('ul li', 'ul li 元素'),
                ('.list li', '.list li 元素'),
                ('.item', '.item 元素'),
                ('[class*="list"]', '包含list的class'),
                ('[class*="item"]', '包含item的class'),
                ('table tr', '表格行'),
            ]

            for selector, desc in selectors:
                elements = page.css(selector)
                if elements:
                    print(f"\n找到 {len(elements)} 个 {desc}")
                    print("前3个元素:")
                    for i, elem in enumerate(elements[:3], 1):
                        text = elem.get_all_text()[:100]
                        print(f"  {i}. {text}")

            print("\n查找详情链接...")
            links = page.css('a')
            print(f"总共找到 {len(links)} 个链接")

            detail_links = []
            for link in links:
                href = link.attrib.get('href', '')
                if 'detail' in href or 'content' in href or '/zcfgk/' in href:
                    detail_links.append({
                        'href': href,
                        'text': link.get_all_text()[:50]
                    })

            print(f"找到 {len(detail_links)} 个可能的详情链接")
            if detail_links:
                print("前5个链接:")
                for i, link in enumerate(detail_links[:5], 1):
                    print(f"  {i}. {link['text']}")
                    print(f"     URL: {link['href']}")

            print("\n页面HTML片段 (前2000字符):")
            print(page.html_content[:2000])

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "-" * 60)
        time.sleep(3)


if __name__ == "__main__":
    analyze_page_structure()
