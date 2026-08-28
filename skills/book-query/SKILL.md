---
name: book-query
description: RAG 混合检索（向量 + BM25 + RRF 融合）
triggers:
  - book-query
  - 检索
  - 搜索书中内容
---

# book-query

对已索引的书籍执行混合检索，返回带章节锚点的引用结果。

## 输入

- `book_slug`: 书籍 slug
- `question`: 检索问题
- `--top_k`: 返回结果数（默认 10）

## 执行

```bash
python scripts/query.py <book_slug> "<question>" [--top_k 10]
```

## 检索策略

1. **向量检索**：DashScope text-embedding-v3 + Chroma（语义匹配）
2. **BM25 检索**：关键词精确匹配（术语/人名/书名）
3. **RRF 融合**：Reciprocal Rank Fusion 合并两路结果

## 输出格式

每条结果包含：
- `id`: chunk 编号
- `section`: 所在章节
- `text`: 原文片段
- `rrf_score`: 融合得分
- `source`: 命中来源（vector/bm25/both）

## 使用场景

- `book-summary`、`book-insights`、`book-reading-guide` 调用此 Skill 获取原文与目录
- 用户直接提问时，先检索再生成回答
- 验证引用准确性时，用此 Skill 回溯原文

## 引用格式

输出引用时使用 `[章节名]` 格式，例如：
> "系统1的运行是无意识的，系统2则需要注意力。" — [第1章：两个系统]
