"""
检查Scrapling Response对象结构
"""
from scrapling import StealthyFetcher

url = "https://fgk.chinatax.gov.cn/zcfgk/c102440/listflfg.html"

fetcher = StealthyFetcher()
response = fetcher.fetch(url)

print("Response对象类型:", type(response))
print("\nResponse对象属性和方法:")
for attr in dir(response):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\n尝试获取页面内容:")
try:
    if hasattr(response, 'text'):
        print("text属性存在")
        print("内容前500字符:", response.text[:500])
except Exception as e:
    print(f"text属性错误: {e}")

try:
    if hasattr(response, 'content'):
        print("content属性存在")
except Exception as e:
    print(f"content属性错误: {e}")

try:
    if hasattr(response, 'soup'):
        print("soup属性存在")
        soup = response.soup
        print("soup类型:", type(soup))
        if soup.title:
            print("页面标题:", soup.title.string)
except Exception as e:
    print(f"soup属性错误: {e}")

try:
    if hasattr(response, 'html'):
        print("html属性存在")
        print("HTML前500字符:", response.html[:500])
except Exception as e:
    print(f"html属性错误: {e}")
