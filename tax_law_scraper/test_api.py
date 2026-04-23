"""
API接口分析测试脚本 - 修复版
"""
import requests
import json
import time

BASE_URL = "https://fgk.chinatax.gov.cn/zcfgk"

CATEGORIES = {
    "guowuyuan": {
        "name": "国务院文件",
        "code": "c102440",
        "url": f"{BASE_URL}/c102440/listflfg.html"
    },
    "caishui": {
        "name": "财税文件",
        "code": "c102416",
        "url": f"{BASE_URL}/c102416/listflfg.html"
    },
    "guifanxing": {
        "name": "税务规范性文件",
        "code": "c100012",
        "url": f"{BASE_URL}/c100012/listflfg.html"
    },
    "falv": {
        "name": "法律",
        "code": "c100009",
        "url": f"{BASE_URL}/c100009/listflfg_fg.html"
    },
    "guizhang": {
        "name": "税务部门规章",
        "code": "c100011",
        "url": f"{BASE_URL}/c100011/list_guizhang.html"
    },
    "zhengcejiedu": {
        "name": "政策解读",
        "code": "c100015",
        "url": f"{BASE_URL}/c100015/list_zcjd.html"
    }
}

def test_api():
    """测试API接口"""
    print("=" * 60)
    print("开始测试API接口")
    print("=" * 60)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://fgk.chinatax.gov.cn/'
    }

    api_url = "https://www.chinatax.gov.cn/getFileListByCodeId"

    for cat_key, cat_info in CATEGORIES.items():
        print(f"\n{'='*60}")
        print(f"测试分类: {cat_info['name']}")
        print(f"Code: {cat_info['code']}")
        print(f"{'='*60}")

        param_combinations = [
            {"codeId": "", "channelId": cat_info['code'], "page": 1, "size": 10},
            {"codeId": cat_info['code'], "channelId": "", "page": 1, "size": 10},
            {"codeId": cat_info['code'], "channelId": cat_info['code'], "page": 1, "size": 10},
            {"channelId": cat_info['code'], "page": 1, "size": 10},
        ]

        for i, params in enumerate(param_combinations, 1):
            print(f"\n尝试参数组合 {i}: {params}")
            try:
                response = requests.post(api_url, data=params, headers=headers, timeout=30)
                print(f"状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', {}).get('data', {}).get('results', [])
                    total = data.get('results', {}).get('data', {}).get('total', 0)

                    print(f"总数: {total}, 当前页: {len(results)} 条")

                    if results:
                        print(f"成功! 前2条数据:")
                        for j, item in enumerate(results[:2], 1):
                            print(f"  {j}. 标题: {item.get('title', 'N/A')[:50]}")
                            print(f"     ID: {item.get('id', 'N/A')}")
                            print(f"     日期: {item.get('publishDate', item.get('publish_date', 'N/A'))}")
                        break
                else:
                    print(f"请求失败: {response.status_code}")

            except Exception as e:
                print(f"请求异常: {e}")

            time.sleep(1)


if __name__ == "__main__":
    test_api()
