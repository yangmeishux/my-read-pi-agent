# 读书智能体 - 领域术语表

## 核心概念

### RAG (Retrieval-Augmented Generation)
检索增强生成。先从文档库检索相关内容，再用检索结果辅助 LLM 生成回答。避免 LLM 凭记忆瞎说。

### Chroma
开源向量数据库。嵌入式部署（无需起服务），Python 原生 API，适合本地书籍索引。

### Embedding
将文本转换为向量表示。本项目使用 DashScope text-embedding-v3，中文效果好。

### BM25
经典关键词检索算法。与向量检索互补：向量擅长语义匹配，BM25 擅长术语/人名精确匹配。

### RRF (Reciprocal Rank Fusion)
多路检索结果融合算法。公式：`score = Σ 1/(k + rank)`，k 通常取 60。

### Harness
思维脚手架。限制 LLM 输出结构的框架，避免泛泛而谈。本项目用 summary 的 10 个必含章节、独立的阅读标注（reading-guide.md）、以及逐章详述（digest.md）作为 harness。

### 门禁 (Quality Gate)
硬检查点。未通过门禁的输出不允许进入下一阶段。本项目门禁：引用 ≥5、无禁用词、评分 ≥9。

## 项目特定术语

### slug
书籍的 URL 友好标识符。从书名生成，例如"思考快与慢" → `思考快与慢`。

### chunk
文档切块。按章节标题切分，每个 chunk ≤ 2000 字符，保留 section 名称用于引用定位。

### book.yaml
书籍元信息文件。包含 slug、source_file、parsed_file、chunk_count、status。

### workspace
每本书的独立工作目录。包含 book.yaml、summary.md、insights.md、external-reviews.md、reading-guide.md、digest.md、report.md。

### reading-guide.md
阅读标注。按章打标签：精读 / 带着问题读 / 略读 / 当附录查 / 可跳过。精读章限制 1–4 个。

### digest.md
逐章详述 + 全书总述。覆盖目录每一章，回答「这本书具体讲了什么」。与 summary.md（骨架）分工。

### library
书库目录。包含 raw（原始文件）、parsed（解析后的 MD）、index（Chroma 索引）、metadata。

## 禁用词列表

以下词汇出现在输出中会触发门禁失败：

- "让我们"
- "综上所述"
- "值得注意的是"
- "随着技术的发展"
- "毫无疑问"
- "不可否认"
- "众所周知"

## 引用格式

所有原文引用必须标注来源：

```markdown
> "引用内容" — [章节名]
```

示例：
> "系统1的运行是无意识的，系统2则需要注意力。" — [第1章：两个系统]

## 评分标准

0-10 分，≥9 分通过门禁。评分维度：

| 维度 | 权重 | 标准 |
|------|------|------|
| 结构完整性 | 20% | 报告 12 个必含章节全部存在（含阅读标注与逐章详述） |
| 引用质量 | 25% | ≥5 条引用，每条带章节来源 |
| 深度 | 20% | 深刻洞见有反常识点，启发可落地 |
| 语言 | 15% | 无禁用词，无 AI 套话 |
| 完整性 | 20% | 外部评价已聚合，争议与局限已提及 |
