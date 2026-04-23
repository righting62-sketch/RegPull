"""
重试装饰器
"""
import time
import random
from functools import wraps


def retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间
        backoff: 延迟时间倍数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        print(f"第 {attempt + 1} 次尝试失败: {e}")
                        print(f"等待 {current_delay:.1f} 秒后重试...")
                        time.sleep(current_delay + random.uniform(0, 1))
                        current_delay *= backoff
                    else:
                        print(f"已达到最大重试次数 {max_retries}，放弃执行")

            raise last_exception
        return wrapper
    return decorator
