"""搜索工具（Mock 实现）。

生产环境可替换为 Tavily / SerpAPI / DuckDuckGo。
"""

from __future__ import annotations

import urllib.parse

SEARCH_DESCRIPTION = """搜索工具（Mock）。输入查询关键词，返回模拟搜索结果。
当前是 Mock 实现，返回固定模板字符串。
生产环境可替换为 Tavily / SerpAPI 等真实搜索 API。
"""


def search(query: str) -> str:
    """Mock 搜索函数。

    Args:
        query: 搜索关键词

    Returns:
        模拟搜索结果
    """
    # 简单 URL 编码演示
    encoded = urllib.parse.quote(query)
    return (
        f"[Mock Search Results for: {query}]\n"
        f"1. https://example.com/search?q={encoded} - 搜索结果占位\n"
        f"2. https://docs.python.org - Python 官方文档\n"
        f"3. （更多结果请接入真实搜索 API）"
    )