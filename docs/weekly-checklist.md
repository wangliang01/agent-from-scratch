# 第 1 周：手写循环

- 目标：一个能调工具的 agent，不用框架。
- 完成标准：一次提问能连续触发两次以上工具；`AGENT_VERBOSE=1` 能看懂消息结构。
- 状态：见 `week1-mini-agent/`。

# 第 2 周：RAG

- 目标：真实数据 + 强制引用 + 评测数字。
- 完成标准：有 30~50 条 eval set，至少两组对比数字。
- 状态：待实现，见 `week2-rag/README.md`。

# 第 3 周：编排 + MCP

- 目标：多步任务 agent（重试、人工确认、断点续跑）+ 一个 MCP server。
- 状态：待实现，见 `week3-orchestration/README.md`。

# 第 4 周：上线

- 目标：FastAPI + SSE + 日志 + eval 回归 + Docker。
- 状态：待实现，见 `week4-production/README.md`。
