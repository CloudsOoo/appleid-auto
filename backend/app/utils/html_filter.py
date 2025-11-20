"""
HTML 安全过滤器
用于过滤用户自定义 HTML，防止 XSS 攻击
"""
import bleach
from typing import List, Dict
from app.core.config import settings


class HTMLFilter:
    """HTML 白名单过滤器"""

    def __init__(self):
        # 允许的标签
        self.allowed_tags = settings.allowed_html_tags_list

        # 允许的属性
        self.allowed_attributes = {
            "*": settings.allowed_html_attributes_list,
            "a": ["href", "title", "target", "rel"],
            "img": ["src", "alt", "title", "width", "height"],
        }

        # 允许的协议
        self.allowed_protocols = ["http", "https", "mailto"]

    def clean(self, html: str) -> str:
        """
        清理 HTML，移除危险标签和属性

        Args:
            html: 原始 HTML

        Returns:
            清理后的安全 HTML
        """
        if not html:
            return ""

        # 使用 bleach 清理 HTML
        cleaned = bleach.clean(
            html,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            protocols=self.allowed_protocols,
            strip=True,  # 移除不允许的标签
        )

        # 额外的安全检查
        cleaned = self._remove_event_handlers(cleaned)
        cleaned = self._remove_javascript_protocol(cleaned)

        return cleaned

    def _remove_event_handlers(self, html: str) -> str:
        """移除事件处理器（on* 属性）"""
        import re

        # 匹配所有 on* 事件属性
        pattern = r'\s+on\w+\s*=\s*["\'][^"\']*["\']'
        cleaned = re.sub(pattern, "", html, flags=re.IGNORECASE)

        return cleaned

    def _remove_javascript_protocol(self, html: str) -> str:
        """移除 javascript: 协议"""
        import re

        # 匹配 javascript: 协议
        pattern = r'javascript\s*:'
        cleaned = re.sub(pattern, "", html, flags=re.IGNORECASE)

        return cleaned

    def validate_size(self, html: str) -> bool:
        """
        验证 HTML 大小是否超过限制

        Args:
            html: HTML 内容

        Returns:
            是否通过验证
        """
        if not html:
            return True

        size = len(html.encode("utf-8"))
        return size <= settings.SHARE_PAGE_MAX_CUSTOM_HTML_SIZE

    def clean_custom_html(
        self, header: str = None, body: str = None, footer: str = None
    ) -> Dict[str, str]:
        """
        清理自定义 HTML（分享页使用）

        Args:
            header: <head> 中的 HTML
            body: <body> 顶部的 HTML
            footer: <body> 底部的 HTML

        Returns:
            清理后的 HTML 字典
        """
        result = {}

        if header:
            # header 只允许 style 标签和 meta 标签
            header_cleaned = bleach.clean(
                header,
                tags=["style", "meta", "link"],
                attributes={"meta": ["name", "content"], "link": ["rel", "href"]},
                strip=True,
            )
            result["header"] = header_cleaned

        if body:
            result["body"] = self.clean(body)

        if footer:
            result["footer"] = self.clean(footer)

        return result


# 创建全局实例
html_filter = HTMLFilter()


def clean_html(html: str) -> str:
    """快捷函数：清理 HTML"""
    return html_filter.clean(html)


def validate_custom_html(header: str = None, body: str = None, footer: str = None) -> tuple[bool, str]:
    """
    验证自定义 HTML

    Returns:
        (是否通过, 错误信息)
    """
    # 检查大小
    total_size = 0
    if header:
        total_size += len(header.encode("utf-8"))
    if body:
        total_size += len(body.encode("utf-8"))
    if footer:
        total_size += len(footer.encode("utf-8"))

    if total_size > settings.SHARE_PAGE_MAX_CUSTOM_HTML_SIZE:
        max_kb = settings.SHARE_PAGE_MAX_CUSTOM_HTML_SIZE / 1024
        return False, f"自定义 HTML 总大小超过限制（最大 {max_kb:.0f}KB）"

    # 检查危险内容
    dangerous_patterns = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "onclick=",
        "<iframe",
        "<embed",
        "<object",
    ]

    for content in [header, body, footer]:
        if content:
            content_lower = content.lower()
            for pattern in dangerous_patterns:
                if pattern in content_lower:
                    return False, f"HTML 包含危险内容：{pattern}"

    return True, ""
