# 评测集（eval set）

从第 1 周就要开始攒。没有评测集，所有优化都是瞎调。

## 目录

- `README.md` —— 你在这里
- `agent_cases.jsonl` —— TODO：Agent 任务评测（每行一条）
- `rag_cases.jsonl` —— TODO：RAG 问答评测
- `run_eval.py` —— TODO：一键跑回归，输出通过率

## 每条 case 的格式

```json
{"id": "calc_01", "input": "算一下 (12+3)*2", "expect": {"tool": "calculate", "answer": "30"}}
```

RAG case：

```json
{"id": "rag_01", "question": "...", "answer": "...", "source_ids": ["chunk_03"]}
```

## 评测维度

- 任务完成率
- 工具调用正确率
- 幻觉率（引用不存在）
- 平均延迟
- 单次成本（token）
