"""第 1 周：手写 Agent 主循环。

不依赖任何 Agent 框架。看懂这个文件，就看懂了 LangChain 的 AgentExecutor。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 让 `uv run python week1-mini-agent/agent.py` 能找到同目录的 tools.py
sys.path.insert(0, str(Path(__file__).parent))

import anthropic
from dotenv import load_dotenv

from tools import TOOL_DEFINITIONS, TOOL_IMPLEMENTATIONS

MODEL = "claude-opus-5"
MAX_TOKENS = 16000
MAX_TURNS = 10

load_dotenv(Path(__file__).parent.parent / ".env")
client = anthropic.Anthropic()


def run(user_input: str) -> str:
    """跑一次 agent 循环，返回最终文本。"""
    messages = [{"role": "user", "content": user_input}]
    verbose = os.getenv("AGENT_VERBOSE", "") == "1"

    for turn in range(1, MAX_TURNS + 1):
        if verbose:
            print(f"\n--- turn {turn} ---", file=sys.stderr)
            for m in messages:
                print(f"  {m['role']}: {m['content']}", file=sys.stderr)

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # 把 assistant 的整段响应（含 thinking / text / tool_use）放进历史
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if response.stop_reason == "end_turn" or not tool_uses:
            return "".join(b.text for b in response.content if b.type == "text")

        if response.stop_reason == "refusal":
            text = "".join(b.text for b in response.content if b.type == "text")
            return text or "模型拒绝了这次请求。"

        if response.stop_reason == "max_tokens":
            return "输出达到 max_tokens 上限，请简化问题或调大上限。"

        # 执行工具，结果作为 user 消息发回
        tool_results = []
        for block in tool_uses:
            name = block.name
            impl = TOOL_IMPLEMENTATIONS.get(name)
            if impl is None:
                result = f"unknown tool: {name}"
                is_error = True
            else:
                try:
                    result = str(impl(**block.input))
                    is_error = False
                except Exception as exc:
                    # 把错误当结果返回，让模型自己改参数重试
                    result = f"tool error: {exc}"
                    is_error = True

            if verbose:
                print(f"  tool {name} -> {result}", file=sys.stderr)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return f"达到最大轮数 {MAX_TURNS}，已停止。"


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: uv run python week1-mini-agent/agent.py '你的问题'")
        sys.exit(1)
    print(run(" ".join(sys.argv[1:])))


if __name__ == "__main__":
    main()
