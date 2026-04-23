"""
测试API返回的数据结构
"""
import requests
import json

api_url = "https://www.chinatax.gov.cn/getFileListByCodeId"
channel_id = "0ac34e96afbb4be28844f18eef412421"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://fgk.chinatax.gov.cn/'
}

params = {
    "codeId": "",
    "channelId": channel_id,
    "page": 1,
    "size": 3
}

response = requests.post(api_url, data=params, headers=headers, timeout=30)
data = response.json()

print("完整响应:")
print(json.dumps(data, ensure_ascii=False, indent=2))

results = data.get('results', {}).get('data', {}).get('results', [])
print("\n\n解析后的数据:")
for i, item in enumerate(results, 1):
    print(f"\n第 {i} 条:")
    print(f"  所有字段: {list(item.keys())}")
    for key, value in item.items():
        print(f"  {key}: {value}")
