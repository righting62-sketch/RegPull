"""
API请求封装 - 增强版反爬虫策略
"""
try:
    from curl_cffi import requests as curl_requests
    USE_CURL_CFFI = True
except ImportError:
    import requests as curl_requests
    USE_CURL_CFFI = False
    print("⚠️  警告: curl_cffi 未安装，将使用普通 requests 库，反爬虫能力较弱")
    print("   建议运行: pip install curl_cffi")

import random
import time
from typing import Dict, Optional, List
from config.settings import REQUEST_CONFIG


class APIFetcher:
    """API请求封装类 - 增强版"""

    API_URL = "https://www.chinatax.gov.cn/getFileListByCodeId"

    def __init__(self):
        self.session = curl_requests.Session()
        self.request_count = 0
        self.last_request_time = 0
        self.consecutive_failures = 0
        self.current_delay_multiplier = 1.0
        
        self._setup_headers()

    def _setup_headers(self):
        """设置请求头"""
        self.base_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://fgk.chinatax.gov.cn',
            'Referer': 'https://fgk.chinatax.gov.cn/',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': random.choice(REQUEST_CONFIG['user_agents'])
        }

    def _check_firewall_blocked(self, response) -> bool:
        """检查是否被防火墙拦截"""
        if response.status_code == 403:
            return True
        
        try:
            text = response.text.lower()
            for indicator in REQUEST_CONFIG['firewall_indicators']:
                if indicator.lower() in text:
                    return True
        except:
            pass
        
        return False

    def _calculate_adaptive_delay(self) -> float:
        """计算自适应延迟时间"""
        base_delay = random.uniform(
            REQUEST_CONFIG['delay_min'],
            REQUEST_CONFIG['delay_max']
        )
        
        if self.consecutive_failures > 0:
            multiplier = min(self.current_delay_multiplier * 1.5, 5.0)
            self.current_delay_multiplier = multiplier
        else:
            self.current_delay_multiplier = max(1.0, self.current_delay_multiplier * 0.9)
        
        adaptive_delay = base_delay * self.current_delay_multiplier
        
        return min(adaptive_delay, 30.0)

    def _exponential_backoff(self, retry_count: int) -> float:
        """指数退避算法"""
        base_delay = REQUEST_CONFIG['retry_delay_base']
        max_delay = REQUEST_CONFIG['retry_delay_max']
        
        delay = base_delay * (2 ** retry_count)
        delay = min(delay, max_delay)
        
        jitter = random.uniform(0, delay * 0.3)
        
        return delay + jitter

    def _smart_sleep(self, delay: float, reason: str = ""):
        """智能休眠"""
        if reason:
            print(f"💤 休眠 {delay:.2f} 秒 ({reason})...")
        time.sleep(delay)

    def fetch_list(self, channel_id: str, page: int = 1, size: int = 10) -> Optional[Dict]:
        """
        获取列表数据 - 增强版

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

        max_retries = REQUEST_CONFIG['max_retries']
        
        for retry_count in range(max_retries):
            try:
                headers = self.base_headers.copy()
                headers['User-Agent'] = random.choice(REQUEST_CONFIG['user_agents'])
                
                request_kwargs = {
                    'url': self.API_URL,
                    'data': params,
                    'headers': headers,
                    'timeout': REQUEST_CONFIG['timeout']
                }
                
                if USE_CURL_CFFI:
                    request_kwargs['impersonate'] = REQUEST_CONFIG['impersonate_browser']
                
                response = self.session.post(**request_kwargs)
                
                if self._check_firewall_blocked(response):
                    print("❌ 警告：检测到防火墙拦截！")
                    self.consecutive_failures += 1
                    
                    if retry_count < max_retries - 1:
                        backoff_delay = self._exponential_backoff(retry_count)
                        print(f"🔄 将在 {backoff_delay:.2f} 秒后重试 (第 {retry_count + 2}/{max_retries} 次)...")
                        self._smart_sleep(backoff_delay, "防火墙拦截退避")
                        continue
                    else:
                        print("❌ 已达到最大重试次数，放弃本次请求")
                        return None
                
                response.raise_for_status()
                
                data = response.json()
                
                self.consecutive_failures = 0
                self.request_count += 1
                
                delay = self._calculate_adaptive_delay()
                self._smart_sleep(delay, "请求间隔")
                
                return data

            except Exception as e:
                self.consecutive_failures += 1
                print(f"⚠️  API请求失败 (第 {retry_count + 1}/{max_retries} 次): {e}")
                
                if retry_count < max_retries - 1:
                    backoff_delay = self._exponential_backoff(retry_count)
                    print(f"🔄 将在 {backoff_delay:.2f} 秒后重试...")
                    self._smart_sleep(backoff_delay, "异常重试退避")
                else:
                    print(f"❌ 已达到最大重试次数，放弃本次请求")
                    return None

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

    def get_stats(self) -> Dict:
        """获取请求统计信息"""
        return {
            'total_requests': self.request_count,
            'consecutive_failures': self.consecutive_failures,
            'current_delay_multiplier': self.current_delay_multiplier,
            'using_curl_cffi': USE_CURL_CFFI
        }
