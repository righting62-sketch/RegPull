"""
获取所有分类的channelId
"""
import re
import time
from scrapling import StealthyFetcher

CATEGORIES = {
    "guowuyuan": {
        "name": "国务院文件",
        "code": "c102440",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102440/listflfg.html"
    },
    "caishui": {
        "name": "财税文件",
        "code": "c102416",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102416/listflfg.html"
    },
    "guifanxing": {
        "name": "税务规范性文件",
        "code": "c100012",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100012/listflfg.html"
    },
    "qita": {
        "name": "其他文件",
        "code": "c100013",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100013/listflfg.html"
    },
    "gongzuo": {
        "name": "工作通知",
        "code": "c102424",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c102424/listflfg.html"
    },
    "falv": {
        "name": "法律",
        "code": "c100009",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100009/listflfg_fg.html"
    },
    "xingzhengfagui": {
        "name": "行政法规",
        "code": "c100010",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100010/listflfg_fg.html"
    },
    "guizhang": {
        "name": "税务部门规章",
        "code": "c100011",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100011/list_guizhang.html"
    },
    "zhengcejiedu": {
        "name": "政策解读",
        "code": "c100015",
        "url": "https://fgk.chinatax.gov.cn/zcfgk/c100015/list_zcjd.html"
    }
}

def get_channel_ids():
    """获取所有分类的channelId"""
    print("=" * 60)
    print("获取所有分类的channelId")
    print("=" * 60)

    fetcher = StealthyFetcher()
    channel_ids = {}

    for cat_key, cat_info in CATEGORIES.items():
        print(f"\n分类: {cat_info['name']}")
        print(f"URL: {cat_info['url']}")

        try:
            page = fetcher.fetch(cat_info['url'])
            html = page.html_content

            match = re.search(r'var channelId = "([^"]+)";', html)
            if match:
                channel_id = match.group(1)
                channel_ids[cat_key] = {
                    'name': cat_info['name'],
                    'code': cat_info['code'],
                    'channel_id': channel_id
                }
                print(f"channelId: {channel_id}")
            else:
                print("未找到channelId")
                channel_ids[cat_key] = {
                    'name': cat_info['name'],
                    'code': cat_info['code'],
                    'channel_id': ''
                }

        except Exception as e:
            print(f"错误: {e}")

        time.sleep(2)

    print("\n" + "=" * 60)
    print("所有分类的channelId:")
    print("=" * 60)
    for cat_key, info in channel_ids.items():
        print(f"{info['name']}: {info['channel_id']}")

    return channel_ids


if __name__ == "__main__":
    get_channel_ids()
