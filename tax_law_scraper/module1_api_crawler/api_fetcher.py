"""
API请求封装
"""
import requests
import random
import time
from typing import Dict, Optional, List
from config.settings import REQUEST_CONFIG


class APIFetcher:
    """API请求封装类"""

    API_URL = "https://www.chinatax.gov.cn/getFileListByCodeId"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(REQUEST_CONFIG['user_agents']),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://fgk.chinatax.gov.cn/'
        })

    def fetch_list(self, channel_id: str, page: int = 1, size: int = 10) -> Optional[Dict]:
        """
        获取列表数据

        Args:
            channel_id: 频道ID
            page: 页码
            size: 每页条数

        Returns:
            API响应数据
        """
        params = {
            "codeId": "",
            "channelId": channel_id,
            "page": page,
            "size": size
        }

        try:
            response = self.session.post(
                self.API_URL,
                data=params,
                timeout=REQUEST_CONFIG['timeout']
            )
            response.raise_for_status()

            data = response.json()

            delay = random.uniform(
                REQUEST_CONFIG['delay_min'],
                REQUEST_CONFIG['delay_max']
            )
            time.sleep(delay)

            return data

        except Exception as e:
            print(f"API请求失败: {e}")
            return None

    def parse_list_response(self, response: Dict) -> List[Dict]:
        """
        解析列表响应

        Args:
            response: API响应数据

        Returns:
            文档列表
        """
        if not response:
            return []

        results = response.get('results', {})
        data = results.get('data', {})
        items = data.get('results', [])

        return items if items else []

    def get_total_count(self, response: Dict) -> int:
        """
        获取总数

        Args:
            response: API响应数据

        Returns:
            总数
        """
        if not response:
            return 0

        results = response.get('results', {})
        data = results.get('data', {})
        return data.get('total', 0)
