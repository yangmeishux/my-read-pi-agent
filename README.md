# my-read-pi-agent

基于 Pi Agent 的读书学习智能体。支持 PDF/EPUB 文档解析、RAG 检索、全书总结、深刻洞见挖掘、外部书评聚合，最终输出结构化读书报告。

## 核心能力

| 能力 | 实现 |
|------|------|
| PDF 解析 | marker-pdf（主力，保留章节/公式/表格）+ pymupdf4llm（快速通道） |
| EPUB 解析 | ebooklib + beautifulsoup4 |
| 向量检索 | Chroma + DashScope text-embedding-v3 |
| 混合检索 | 向量 + BM25 关键词 + 章节锚点 |
| 联网书评 | WebSearch + 豆瓣/Goodreads 抓取 |
| 结构化总结 | Skill harness（10 个必含章节） |
| 门禁评分 | 生成/评判分离，≥9 分才输出 |

## 安装

### Node / Pi Agent

```bash
npm install
npx pi install -l . --approve
```

### Python 依赖

```bash
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 填入 DashScope API Key
```

## 使用

### 方式 1：交互式（推荐）

```bash
npm run pi

# 在 Pi 对话中
/skill:book-ingest
/skill:book-summary
/skill:book-insights
/skill:book-review-search
/skill:reading-report
```

### 方式 2：一键读书（开发中）

```bash
npm run read -- "书名" --file ~/Downloads/book.pdf
```

## 工作流

```
book-ingest → [并行] book-summary / book-insights / book-review-search
           → reading-report（合并）
           → quality-reviewer（门禁 ≥9）
           → 输出 workspace/<book-slug>/report.md
```

## 目录结构

```
library/          # 书库（raw/parsed/index/metadata）
workspace/        # 每次读书的输出
skills/           # 7 个 Skill（思维脚手架）
plugins/          # 3 个底层插件（解析/向量/搜索）
workflows/        # 主工作流定义
config/           # 门禁/评分/模型路由
```

## 约束

- 每段引用必须带章节/页码
- 禁用泛泛套话（"让我们"、"综上所述"等）
- 启发必须可落地到具体行动
- 不许虚构作者经历/数据
