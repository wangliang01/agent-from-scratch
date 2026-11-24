# 第 1 周：手写最小 Agent

## 目标

不用任何 Agent 框架，手写一个能调用工具的对话循环。**理解 tool_use / tool_result 的回合结构比代码行数重要。**

## 运行

```bash
uv sync
cp .env.example .env  # 填入 ANTHROPIC_API_KEY
uv run python week1-mini-agent/agent.py "算一下 (12+3)*2，再告诉我北京的天气"
```

设置 `AGENT_VERBOSE=1` 可以看到每轮的完整消息历史。

## 代码结构

- `agent.py`：Agent 主循环 + CLI 入口。
- `tools.py`：三个示例工具（算数、读文件、查天气）。
- `README.md`：这个文件。

## 核心循环

```python
while True:
    response = client.messages.create(model=..., tools=tools, messages=messages)
    if response.stop_reason == "end_turn":
        break
    # 把 assistant 的 tool_use blocks 放进历史
    # 执行工具，把 tool_result blocks 作为 user 消息发回
```

## 三个工具的设计取舍

| 工具 | 实现 | 为什么 |
| --- | --- | --- |
| calculate | 用 `ast` 解析，只允许数字和 + - * / ( ) | 裸 `eval` 是安全漏洞；模型输出属于不可信输入 |
| read_file | 限制在 `week1-mini-agent/allowed/` 目录内 | 演示路径白名单，防目录穿越 |
| get_weather | 返回 mock 数据 | 不需要外部 API key，专注 Agent 循环本身 |

## 验收

- [ ] 一次提问能连续触发两个工具。
- [ ] 故意让工具失败（例如除零），看 agent 能否处理。
- [ ] `AGENT_VERBOSE=1` 能看懂每轮的消息结构。
