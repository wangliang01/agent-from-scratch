# AI Agent 开发：28 天方法论（完整版）

> 先手写，再上框架。先跑通，卡住了再补原理。

## 零、先搞清楚面试到底考什么

招聘 JD 上写「AI Agent 开发」，拆开看其实就四块能力，加一个贯穿始终的评测：

1. **调 LLM API**：流式、结构化输出、错误处理、控成本。
2. **工具调用**：定义工具、执行工具、把结果塞回对话、失败兜底。
3. **RAG**：切块、embedding、检索、rerank、评测。
4. **编排**：多步循环、状态管理、重试、人工确认。
5. **评测**：没有 eval set 的优化都是瞎调。

不需要训练模型，不需要推数学公式。你的角色是「接线工 + 质检员」。

---

## 一、第 0 天：工具链

- Python 3.12，用 [`uv`](https://docs.astral.sh/uv/) 管理环境和依赖。
- 官方 `anthropic` SDK（Python）。
- **不装 LangChain、LlamaIndex、AutoGPT 或任何 Agent 框架。**
- 环境变量里放 `ANTHROPIC_API_KEY`，不要写进代码。

验收标准：能跑通一次最简单的 `client.messages.create(...)`。

---

## 二、第 1 周：手写最小 Agent

### 核心循环

```
messages = [user]

while True:
    resp = llm(messages, tools=[...])
    if resp 没有 tool_call:
        break
    执行 tool → 把结果塞回 messages
```

别小看这 5 行。LangChain、LangGraph、AutoGPT 本质上都在包它。手写一遍之后，框架里那些"AgentExecutor"、"ReAct" 你一看就知道在干什么。

### 必须理解的几件事

- `tool_use` block 和 `tool_result` block 是怎么一回事。
- 为什么 tool result 要作为 **user** 消息发回去。
- 为什么要有 `max_tokens` 和最大循环次数（防失控）。
- 工具失败时，把错误当结果返回，让模型自己改参数重试。
- 流式输出用 `client.messages.stream(...)`，拿到 final message 用 `get_final_message()`。
- 结构化输出用 `client.messages.parse(...)` + Pydantic，不要靠字符串解析。
- 生产环境可以用 SDK 的 Tool Runner（`client.beta.messages.tool_runner`），但**学习阶段先手写**。

### 动手任务

实现一个 50~100 行的 agent，带 3 个工具：

1. 算数（用安全的表达式解析，不要用裸 `eval`）
2. 读本地文件（做路径白名单/规范化校验，防目录穿越）
3. 查天气（用 mock 数据，不需要外部 API key）

### 验收标准

- 能连续调用两次以上工具完成一个任务。
- 工具报错时 agent 能自我修正或至少给出清晰错误。
- CLI 输出能看到完整的消息历史（方便 debug）。

代码见 `week1-mini-agent/agent.py`。

---

## 三、第 2 周：RAG

### 顺序

1. **先切块**：从固定长度切块开始，再升级到按标题/段落的语义切块。
2. **建索引**：本地 Chroma 就够，不要一上来 Pinecone。
3. **先只做向量检索**，跑通后再加 BM25 做 hybrid search。
4. 加 rerank（哪怕用简单的 cross-encoder）。
5. 加 query 改写 / 多query 召回。
6. **最后才是评测**：命中率、MRR、带引用回答的正确率。

### 关键认知

- RAG 优化顺序应该是：**先优化检索，再优化 prompt**。召回不到，再花哨的 prompt 也救不回来。
- 强制模型基于检索片段回答，并给出引用来源。
- 检索不到时**要敢拒答**，而不是让模型瞎编。
- 记录每一步的指标："召回率从 62% 到 85%"这种话在面试里值钱，"我用了 rerank"不值钱。

### 验收标准

- 一个能回答私有文档问题的问答。
- 一份 30~50 条的 eval set。
- 至少两组对比数字（比如 hybrid vs 纯向量）。

骨架见 `week2-rag/`。

---

## 四、第 3 周：编排 + MCP

### 编排要手写一遍的东西

- 状态机 / 图结构（LangGraph 或自己写一个 `State` 类）。
- 失败重试（指数退避）。
- human-in-the-loop：敏感操作前停下来让人确认。
- 断点续跑：状态能序列化到文件/数据库，崩了能接着跑。

### MCP

自己写一个 MCP server：

- 暴露 2~3 个工具。
- 写清楚输入 schema、错误返回。
- 写一份 README 说明怎么接进 agent。

**小而完整 > 大而半吊子。** 有工具、有错误处理、有说明文档，这就是作品。

### 验收标准

- 一个多步任务 agent，展示重试、人工确认、断点续跑。
- 一个能连上的 MCP server。

骨架见 `week3-orchestration/` 和 `week3-orchestration/mcp_server/`。

---

## 五、第 4 周：上线能力

面试很现实：你能不能把 demo 变成 service？

- FastAPI 接口 + SSE 流式输出。
- 超时、重试、降级策略。
- token 计费和成本日志。
- 30~50 条 eval set + LLM-as-judge + 回归测试。
- 可观测性：Langfuse 或至少结构化日志。
- Docker 打包，给一个能访问的 URL。

### 验收标准

- `docker run` 起来，有 health check。
- eval 脚本一键跑回归，输出通过率。
- 日志里能看到每次调用的 token 数和耗时。

骨架见 `week4-production/` 和 `eval/`。

---

## 六、面试高频 6 问

### 1. 怎么防止 RAG 幻觉？

三层防御：
- **检索层**：top-k 限制、相似度阈值、hybrid search 提高召回质量。
- **生成层**：prompt 里明确"只基于给定片段回答，并标出引用"，检索为空时直接拒答。
- **校验层**：回答里引用的片段 ID 必须真实存在于检索结果中，否则判为幻觉并重试/拒答。

### 2. 长对话上下文怎么管理？

三种手段组合：
- **滑动窗口**：只保留最近 N 轮。
- **摘要压缩**： older turns 用一次 LLM 调用压成摘要，再和新消息一起送。
- **外部记忆**：把事实抽出来存到向量库/KV，按需检索。

### 3. 工具调用失败怎么办？

- 参数先在代码层校验（JSON schema / Pydantic）。
- 执行失败时，将错误作为 `tool_result`（`is_error: true`）返回给模型，让它自己改参数重试。
- 设置最大重试次数，超过则降级或交给人工确认。

### 4. 怎么评测 Agent？

- 先建 30~50 条真实任务的 eval set，有输入、期望输出、关键检查点。
- 按维度打分：任务完成率、工具调用正确率、幻觉率、延迟、成本。
- 可程序化检查的用断言，主观的用 LLM-as-judge（但要注意 judge 也有偏差）。
- 每次改动都跑回归，记录分数。

### 5. 成本怎么降？

- prompt 缓存（系统提示和长文档复用）。
- 分层：简单任务用 `claude-haiku-4-5`，复杂任务才用 `claude-opus-5`。
- 压缩检索片段，只送真正相关的 chunk。
- 限制 `max_tokens`，避免无意义长输出。

### 6. 为什么不用 LangChain？

别说"太重了"。说具体的：
- 抽象泄漏：出问题时你不知道循环里发生了什么。
- 版本变动快，API 不稳定。
- 团队能力足够时，手写 50 行循环更可控。

但也别说"永远不用"——第 3 周的编排可以上 LangGraph，关键是你知道它封装了什么。

---

## 七、避坑清单

1. **别一上来学 LangChain。** 先手写循环。
2. **别做通用聊天机器人当作品。** 垂直、有数据、有数字。
3. **别只看教程。** 跑起来 → 卡住 → 查文档 → 修好，这才叫学会。
4. **别背名词。** 面试官要听的是你踩过什么坑。
5. **别跳过评测。** 没有 eval set 的优化等于闭眼调遥控器。

---

## 八、时间账

每天 3 小时 × 28 天 ≈ 84 小时。按周验收，每周都要有一个能跑的东西。

| 周次 | 主题 | 产出 |
| --- | --- | --- |
| 第 1 周 | 手写 Agent 循环 | 50~100 行 agent |
| 第 2 周 | RAG | 有评测数字的问答 |
| 第 3 周 | 编排 + MCP | 多步 agent + MCP server |
| 第 4 周 | 上线能力 | FastAPI + SSE + eval + Docker |
