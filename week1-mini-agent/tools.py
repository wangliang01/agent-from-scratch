"""第 1 周：示例工具。

重点不在工具多复杂，而在它们如何接入 agent 循环。
"""

from __future__ import annotations

import ast
import operator
from pathlib import Path
from typing import Callable

# ---- 算数工具：用 AST 安全解析，不用裸 eval ----

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class UnsafeExpression(ValueError):
    """表达式包含不允许的语法。"""


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise UnsafeExpression("division by zero")
        return _ALLOWED_BINOPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_node(node.operand))
    raise UnsafeExpression(f"unsupported syntax: {type(node).__name__}")


def calculate(expression: str) -> str:
    """计算一个只包含数字和 + - * / ( ) 的算术表达式。"""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree)
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except (SyntaxError, UnsafeExpression) as exc:
        raise ValueError(f"unsafe or invalid expression: {exc}") from exc


# ---- 读文件工具：限制在 allowed/ 目录内 ----

_ALLOWED_DIR = Path(__file__).parent / "allowed"
_ALLOWED_DIR.mkdir(exist_ok=True)


def read_file(path: str) -> str:
    """读取 allowed/ 目录内的文本文件。path 是相对该目录的路径。"""
    requested = (_ALLOWED_DIR / path).resolve()
    if not requested.is_relative_to(_ALLOWED_DIR.resolve()):
        raise ValueError("path escapes the allowed directory")
    if not requested.is_file():
        raise FileNotFoundError(f"file not found: {path}")
    return requested.read_text(encoding="utf-8")


# ---- 天气工具：mock 数据，不依赖外部 API ----

_MOCK_WEATHER = {
    "北京": "22°C, 晴",
    "上海": "26°C, 多云",
    "深圳": "30°C, 阵雨",
}


def get_weather(city: str) -> str:
    """查询指定城市的天气（演示用 mock 数据）。"""
    return _MOCK_WEATHER.get(city, f"暂无 {city} 的天气数据（演示数据仅包含北京、上海、深圳）")


# ---- 工具定义：传给 Claude API 的 JSON schema ----

TOOL_DEFINITIONS = [
    {
        "name": "calculate",
        "description": "计算算术表达式。用户问数学计算时调用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "合法的 Python 风格算术表达式，例如 '(12 + 3) * 2'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "读取 allowed/ 目录内的文本文件。"
            "用户问文件内容时调用，path 是相对 allowed/ 的路径。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "相对 allowed/ 的文件路径，例如 'notes.txt'",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "get_weather",
        "description": "查询城市天气（演示 mock 数据，支持北京、上海、深圳）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名，例如 '北京'"}
            },
            "required": ["city"],
        },
    },
]

TOOL_IMPLEMENTATIONS: dict[str, Callable[..., str]] = {
    "calculate": calculate,
    "read_file": read_file,
    "get_weather": get_weather,
}
