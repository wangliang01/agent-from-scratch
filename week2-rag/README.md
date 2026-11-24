# 第 2 周：RAG 骨架

> 目标：一个能回答私有文档问题、**且有评测数字**的问答系统。

## 优化顺序（别跳步）

1. 固定长度切块 → 按标题/段落的语义切块
2. 本地 Chroma 建索引
3. 纯向量检索（先跑通）
4. 加 BM25 → hybrid search
5. 加 rerank
6. query 改写 / 多 query 召回
7. **评测：命中率、MRR、带引用回答的正确率**

核心原则：**先优化检索，再优化 prompt**。召回不到，prompt 写得再花哨也救不回来。

## 目录

```
week2-rag/
├── README.md       ← 你在这里
├── pipeline.py     ← TODO：切块 → 索引 → 检索 → 生成
└── data/           ← TODO：放你的真实文档
```

## 验收标准

- [ ] 能回答私有文档里的问题，回答带引用片段 ID。
- [ ] 检索为空时能拒答。
- [ ] 有一份 30~50 条 eval set（`eval/rag_cases.jsonl`）。
- [ ] 至少两组对比数字（如 hybrid vs 纯向量）。

详细方法论见 `../docs/methodology.md` 第三节。
