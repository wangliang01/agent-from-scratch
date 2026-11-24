# 面试题库

> 不是抄来的通用八股。每道题都锚定本仓库的一个文件，追问链一路打到「只有真做过才答得上来」的地方。

## 为什么自建，而不是爬题库

网上题库能搜到目录，正文多在付费墙后；更关键的是，通用题库问的是「ReAct 是什么」，而 2026 年真实面试的区分点已经不是知道不知道，而是**追问深度**。

一项对 1493 条 JD、715 条面经的分析显示，**L3 及以上的追问占 57%**。而且面试官默认「简历上的项目可能是 AI 生成的」，会沿着项目往下打，一直打到归属层。

| 层级 | 问什么 | 例子 |
| --- | --- | --- |
| L1 概念 | 是什么 | 「tool_use 和 tool_result 是什么关系？」 |
| L2 机制 | 为什么这样设计 | 「为什么 tool_result 要作为 user 消息发回？」 |
| L3 选型 | 为什么用这个不用那个 | 「chunk 策略换过几种，怎么比较的？」 |
| L4 排障 | 出问题怎么定位 | 「Agent 死循环了怎么定位？」 |
| L5 架构 | 完整系统怎么设计 | 「设计一个企业客服 Agent，怎么分层？」 |
| L6 归属 | 哪块是你做的 | 「这个评测集是你构建的吗？」 |

L6 没法用题库准备，它靠你真的动过手。前五层可以——这个目录管前五层。

## 结构

```
interview/
├── README.md            ← 你在这里
├── quiz.py              ← CLI：抽题、看答案、标记掌握度、统计进度
├── progress.json        ← 答题记录（quiz.py 自动生成）
└── questions/
    ├── llm-api.jsonl        ← 第 0 周：调 LLM API
    ├── tools.jsonl          ← 第 1 周：工具调用
    ├── rag.jsonl            ← 第 2 周：RAG
    ├── orchestration.jsonl  ← 第 3 周：编排 + MCP
    └── production.jsonl     ← 第 4 周：上线能力 + 系统设计
```

## 用法

> 本机 `python` 是 Windows 应用商店占位程序，直接跑没输出。统一用 `uv run python`。

```bash
# 列出第 1 周的题
uv run python interview/quiz.py list --week 1

# 随机抽 3 道没做过的题
uv run python interview/quiz.py draw -n 3 --unseen

# 看某道题（题面 + 面试官会怎么追问，不含答案）
uv run python interview/quiz.py show tools-003

# 答完再看答案要点和反面教材
uv run python interview/quiz.py reveal tools-003

# 标记掌握度：solid / shaky / miss
uv run python interview/quiz.py mark tools-003 shaky

# 按周统计掌握度
uv run python interview/quiz.py stats

# 列出需要复习的题
uv run python interview/quiz.py review
```

抽题支持按周、标签、层级过滤：

```bash
uv run python interview/quiz.py draw --week 2 --tag retrieval -n 5
uv run python interview/quiz.py draw --level L4 -n 5      # 只抽排障题
uv run python interview/quiz.py draw --weak -n 5          # 只抽含糊/不会的
```

## 题库规模

| 文件 | 题数 |
| --- | --- |
| llm-api.jsonl | 12 |
| tools.jsonl | 12 |
| rag.jsonl | 16 |
| orchestration.jsonl | 15 |
| production.jsonl | 20 |
| **合计** | **75** |

## 题目格式

每行一个 JSON：

```json
{
  "id": "rag-002",
  "week": 2,
  "level": "L4",
  "tags": ["retrieval", "debugging"],
  "q": "向量检索召回率低，你怎么判断是数据问题还是索引问题？",
  "probe": [
    "你怎么验证这个判断？",
    "如果精确检索也召不到呢？",
    "这个指标的阈值谁定的？"
  ],
  "strong": [
    "先人工核查：拿失败 query 到全量文档库搜，确认文档存在且完整——几分钟排除一半方向",
    "对照实验：同一批向量和度量下，用暴力精确检索做「检索上限」，隔离出索引变量",
    "分层指标：解析/切分/入库/索引参数/过滤/重排逐层定位，最后用回归用例确认"
  ],
  "weak": [
    "直接换 embedding 模型（最常见的错误动作）",
    "列一堆可能原因，但说不出第一步查什么"
  ],
  "anchor": "week2-rag/pipeline.py"
}
```

- `probe` 是追问链，面试官不会只问一句，会顺着往下打。
- `strong` 是强答案的要点，不是背的话术——你要用自己的话讲出来。
- `weak` 是常见弱答案，用来对照自己是不是踩了。
- `anchor` 指向本仓库里对应的代码或文档，做到那一步时回来做这道题。

## 和项目周次的映射

| 周次 | 题库文件 | 什么时候解锁 |
| --- | --- | --- |
| 第 0 周 | llm-api.jsonl | 调通第一个 API 调用 |
| 第 1 周 | tools.jsonl | 手写 Agent 循环跑通 |
| 第 2 周 | rag.jsonl | RAG 有评测数字 |
| 第 3 周 | orchestration.jsonl | 多步 Agent + MCP server |
| 第 4 周 | production.jsonl | FastAPI + eval 回归上线 |

**别提前刷后面的题。** 没做过就答，只能背，背出来的答案在 L3 追问下就穿了。做完一周，回来抽这一周的题。

## 怎么用才对

1. **先自己答，别急着 reveal。** 对着 `show` 的题面口述一遍，或者写下来。
2. **让追问继续。** 每题都有 probe 链，答完第一问，试着回答后面几问。卡住的地方就是你的薄弱项。
3. **标记要诚实。** 能说清「为什么」才算 solid，只记得结论标 shaky。
4. **对话里深挖。** 抽到题后，把题面发给我，我按 probe 链往下追问、挑漏洞。CLI 负责记录，对话负责压测。

## 掌握度统计口径

- ✅ solid：能讲清机制和取舍，经得住追问。
- ⚠️ shaky：记得结论，但说不出为什么。
- ❌ miss：答不上来，或者答错了。
- 未做：还没抽到过。

`stats` 只统计 solid 为「掌握」。shaky 算没掌握——面试里含糊等于不会。
