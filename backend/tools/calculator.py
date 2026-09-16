"""计算器工具。

安全的数学表达式计算（基于 ast，禁止 eval 任意代码）。
"""

from __future__ import annotations

import ast
import math
import operator

# 允许的二元运算符
_BIN_OPS: dict[type, operator] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# 允许的一元运算符
_UNARY_OPS: dict[type, operator] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# 允许的数学函数
_ALLOWED_FUNCS = {
    name: getattr(math, name)
    for name in ["sqrt", "log", "log2", "log10", "sin", "cos", "tan", "asin", "acos", "atan", "ceil", "floor", "factorial"]
}

# 允许的常量
_ALLOWED_CONSTS = {"pi": math.pi, "e": math.e}


CALCULATOR_DESCRIPTION = """数学计算器。输入数学表达式字符串，返回计算结果。
示例输入: '2 + 3 * 4'、'sqrt(16)'、'pi * 2'
支持: + - * / // % **, sqrt/log/sin/cos/tan 等数学函数, 常量 pi 和 e
"""


def calculator(expression: str) -> str:
    """安全地计算数学表达式。

    Args:
        expression: 数学表达式，如 "2 + 3 * 4"

    Returns:
        字符串形式的计算结果，或错误信息
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except Exception as e:
        return f"[计算错误] {type(e).__name__}: {e}"


def _eval_node(node: ast.AST) -> float | int:
    """递归求值 AST 节点。"""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"不支持的常量: {node.value}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _BIN_OPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return _UNARY_OPS[op_type](operand)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("只支持简单的函数调用")
        func_name = node.func.id
        if func_name not in _ALLOWED_FUNCS:
            raise ValueError(f"不支持的函数: {func_name}")
        if len(node.args) != 1 or not isinstance(node.args[0], ast.AST):
            raise ValueError("函数调用必须恰好 1 个参数")
        arg = _eval_node(node.args[0])
        return _ALLOWED_FUNCS[func_name](arg)

    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_CONSTS:
            return _ALLOWED_CONSTS[node.id]
        raise ValueError(f"不支持的标识符: {node.id}")

    raise ValueError(f"不支持的语法节点: {type(node).__name__}")