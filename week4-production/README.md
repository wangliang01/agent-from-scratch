# 第 4 周：上线能力

> 面试很现实：你能不能把 demo 变成 service？

## 清单

- [ ] FastAPI 接口 + SSE 流式输出（用 `client.messages.stream(...)`）
- [ ] 超时、重试、降级策略
- [ ] token 计费和成本日志（每次调用记录 input/output tokens）
- [ ] 30~50 条 eval set + LLM-as-judge + 回归测试
- [ ] 可观测性：Langfuse 或至少结构化日志
- [ ] Docker 打包，给一个能访问的 URL

## 文件

- `app.py` —— TODO：FastAPI 入口，POST 普通接口 + GET SSE 接口。
- `Dockerfile` —— TODO：镜像构建。
- `logging_utils.py` —— TODO：结构化日志 + token 统计。

## 验收标准

- `docker run` 起来，有 health check。
- eval 脚本一键跑回归，输出通过率。
- 日志里能看到每次调用的 token 数和耗时。

详细方法论见 `../docs/methodology.md` 第五节。
