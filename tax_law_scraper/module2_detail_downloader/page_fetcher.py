"""
页面抓取（使用Scrapling）
"""
import time
import random
import re
import tempfile
import os
from typing import Dict, List, Optional, Tuple
from scrapling import StealthyFetcher, DynamicFetcher
from config.settings import REQUEST_CONFIG, SCRAPLING_CONFIG


class PageFetcher:
    """页面抓取类"""

    def __init__(self):
        self.stealthy_fetcher = StealthyFetcher()
        self.dynamic_fetcher = DynamicFetcher()
        self._download_result = None
        self._content_result = None

    def fetch_page(self, url: str, use_dynamic: bool = False) -> Optional[object]:
        """
        抓取页面

        Args:
            url: 页面URL
            use_dynamic: 是否使用动态渲染

        Returns:
            Scrapling Response对象
        """
        try:
            if use_dynamic:
                response = self.dynamic_fetcher.fetch(
                    url,
                    headless=SCRAPLING_CONFIG.get('headless', True),
                    network_idle=True
                )
            else:
                response = self.stealthy_fetcher.fetch(
                    url,
                    headless=SCRAPLING_CONFIG.get('headless', True)
                )

            delay = random.uniform(
                REQUEST_CONFIG['delay_min'],
                REQUEST_CONFIG['delay_max']
            )
            time.sleep(delay)

            return response

        except Exception as e:
            print(f"页面抓取失败: {e}")
            return None

    def fetch_and_process_page(self, url: str) -> Tuple[str, Optional[str]]:
        """
        抓取页面并处理：提取正文和获取下载链接

        Args:
            url: 页面URL

        Returns:
            (正文内容, 下载链接URL)
        """
        content = ""
        download_url = None

        try:
            page = self.dynamic_fetcher.fetch(
                url,
                headless=SCRAPLING_CONFIG.get('headless', True),
                network_idle=True
            )

            if not page:
                print("  页面抓取失败")
                return content, download_url

            content = self.extract_content(page)
            print(f"  提取正文: {len(content)} 字符")

            download_url = self.get_download_url(page)

            delay = random.uniform(
                REQUEST_CONFIG['delay_min'],
                REQUEST_CONFIG['delay_max']
            )
            time.sleep(delay)

            return content, download_url

        except Exception as e:
            print(f"  页面处理失败: {e}")
            return content, download_url

    def fetch_click_and_download(self, url: str) -> Tuple[str, Optional[str]]:
        """
        抓取页面，提取正文，并点击下载按钮获取文件

        Args:
            url: 页面URL

        Returns:
            (正文内容, 下载文件临时路径)
        """
        self._download_result = None
        self._content_result = ""

        try:
            self.dynamic_fetcher.fetch(
                url,
                headless=SCRAPLING_CONFIG.get('headless', True),
                network_idle=True,
                page_action=self._click_download_action
            )

            return self._content_result, self._download_result

        except Exception as e:
            print(f"  页面处理失败: {e}")
            return self._content_result, self._download_result

    def _click_download_action(self, page) -> None:
        """
        page_action 回调函数：提取正文并点击下载按钮

        Args:
            page: Playwright Page 对象
        """
        try:
            self._content_result = self._extract_content_from_page(page)
            print(f"  提取正文: {len(self._content_result)} 字符")

            download_btn = page.query_selector('#zwxz')
            if not download_btn:
                download_btn = page.query_selector('.xxgk-download-btn')

            if download_btn:
                print("  找到下载按钮，尝试点击下载...")
                try:
                    with page.expect_download(timeout=30000) as download_info:
                        download_btn.click()

                    download = download_info.value
                    suggested_filename = download.suggested_filename
                    if not suggested_filename:
                        suggested_filename = "downloaded_file.pdf"

                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, suggested_filename)
                    download.save_as(temp_path)

                    self._download_result = temp_path
                    print(f"  下载成功: {suggested_filename}")

                except Exception as e:
                    print(f"  点击下载失败: {e}")
            else:
                print("  未找到下载按钮")

        except Exception as e:
            print(f"  页面处理失败: {e}")

    def _extract_content_from_page(self, page) -> str:
        """
        从 Playwright Page 对象提取正文

        Args:
            page: Playwright Page 对象

        Returns:
            正文内容
        """
        content_selectors = [
            '#zoom',
            '.zoom',
            '.content',
            '.article-content',
            '.TRS_Editor',
            '.view-content',
            '.text-content',
            'article',
            '.xxgk-content'
        ]

        for selector in content_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    content = elements[0].inner_text()
                    if content and len(content) > 50:
                        return self._clean_content(content)
            except Exception:
                continue

        try:
            body = page.query_selector('body')
            if body:
                return self._clean_content(body.inner_text())
        except Exception:
            pass

        return ""

    def extract_content(self, page) -> str:
        """
        提取正文内容

        Args:
            page: Scrapling页面对象

        Returns:
            正文内容
        """
        content_selectors = [
            '#zoom',
            '.zoom',
            '.content',
            '.article-content',
            '.TRS_Editor',
            '.view-content',
            '.text-content',
            'article',
            '.xxgk-content'
        ]

        for selector in content_selectors:
            elements = page.css(selector)
            if elements:
                content = elements[0].get_all_text()
                if content and len(content) > 50:
                    return self._clean_content(content)

        body = page.css('body')
        if body:
            return self._clean_content(body[0].get_all_text())

        return ""

    def _clean_content(self, content: str) -> str:
        """
        清理内容

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        content = re.sub(r'\n\s*\n+', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        lines = content.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(lines)

    def get_download_url(self, page) -> Optional[str]:
        """
        获取下载链接（通过点击下载按钮）

        Args:
            page: Scrapling页面对象

        Returns:
            下载链接URL
        """
        try:
            download_btn = page.css('#zwxz')
            if not download_btn:
                download_btn = page.css('.xxgk-download-btn')

            if download_btn:
                btn = download_btn[0]
                href = btn.attrib.get('href', '')

                if href and href != '#' and href != '':
                    if href.startswith('/'):
                        href = f"https://fgk.chinatax.gov.cn{href}"
                    elif not href.startswith('http'):
                        href = f"https://fgk.chinatax.gov.cn/{href}"
                    print(f"  找到下载链接: {href[:80]}...")
                    return href

            download_links = self._find_download_links(page)
            if download_links:
                print(f"  找到下载链接: {download_links[0][:80]}...")
                return download_links[0]

            print("  未找到下载链接")
            return None

        except Exception as e:
            print(f"  获取下载链接失败: {e}")
            return None

    def _find_download_links(self, page) -> List[str]:
        """
        查找页面中的下载链接

        Args:
            page: Scrapling页面对象

        Returns:
            下载链接列表
        """
        download_links = []

        selectors = [
            'a[href$=".pdf"]',
            'a[href$=".doc"]',
            'a[href$=".docx"]',
            'a[href$=".xls"]',
            'a[href$=".xlsx"]',
            'a[href*="download"]',
            'a[href*="attachment"]'
        ]

        for selector in selectors:
            links = page.css(selector)
            for link in links:
                href = link.attrib.get('href', '')
                text = link.get_all_text().strip()

                if href:
                    if href.startswith('/'):
                        href = f"https://fgk.chinatax.gov.cn{href}"
                    elif not href.startswith('http'):
                        href = f"https://fgk.chinatax.gov.cn/{href}"

                    if href not in download_links:
                        download_links.append(href)

        return download_links

    def extract_attachments(self, page) -> List[Dict]:
        """
        提取附件链接

        Args:
            page: Scrapling页面对象

        Returns:
            附件列表
        """
        attachments = []

        selectors = [
            'a[href$=".pdf"]',
            'a[href$=".doc"]',
            'a[href$=".docx"]',
            'a[href$=".xls"]',
            'a[href$=".xlsx"]',
            'a[href*="download"]',
            'a[href*="attachment"]'
        ]

        for selector in selectors:
            links = page.css(selector)
            for link in links:
                href = link.attrib.get('href', '')
                text = link.get_all_text().strip()

                if href and href not in [a['url'] for a in attachments]:
                    if href.startswith('/'):
                        href = f"https://fgk.chinatax.gov.cn{href}"
                    elif not href.startswith('http'):
                        href = f"https://fgk.chinatax.gov.cn/{href}"

                    attachments.append({
                        'url': href,
                        'name': text or '附件'
                    })

        return attachments
