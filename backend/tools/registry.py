"""工具注册表。

简单工厂 + 单例，所有工具通过 name 注册和获取。
"""

from __future__ import annotations

from typing import Callable


class ToolRegistry:
    """工具注册表。

    用法：
        registry = ToolRegistry()
        registry.register("calculator", calculator_func, "数学计算")
        func = registry.get("calculator")
    """

    def __init__(self) -> None:
        self._tools: dict[str, "Tool"] = {}

    def register(self, name: str, func: Callable[[str], str], description: str) -> None:
        """注册一个工具。

        Args:
            name: 工具名（Agent 通过此名调用）
            func: 工具函数，接受字符串输入，返回字符串输出
            description: 工具描述（注入到 LLM prompt）
        """
        self._tools[name] = Tool(name=name, func=func, description=description)

    def get(self, name: str) -> "Tool | None":
        """获取工具对象。"""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有已注册工具名。"""
        return list(self._tools.keys())


class Tool:
    """工具对象（封装 name + func + description）。"""

    def __init__(self, name: str, func: Callable[[str], str], description: str) -> None:
        self.name = name
        self.func = func
        self.description = description

    def __call__(self, input_str: str) -> str:
        """让 Tool 对象像函数一样可调用。"""
        return self.func(input_str)


# 全局单例 + 默认注册
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表（懒加载）。"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        # 注册默认工具
        from .calculator import calculator, CALCULATOR_DESCRIPTION
        from .search import search, SEARCH_DESCRIPTION

        _registry.register("calculator", calculator, CALCULATOR_DESCRIPTION)
        _registry.register("search", search, SEARCH_DESCRIPTION)
    return _registry