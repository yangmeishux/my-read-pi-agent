# 项目变更记录

## [1.1.0] - 2026-08-28

### 新增

- Skill `book-reading-guide`：独立产出 `reading-guide.md`（精读 / 带着问题读 / 略读 / 当附录查 / 可跳过）
- 终稿 `report.md` 新增第 3 章「阅读标注与拆解」，报告由 10 章扩为 11 章
- Agent `reading-guide-writer`；工作流与 summary/insights/书评并行
- 门禁：精读章 1–4 个，必须覆盖目录每一章，且至少有一个非精读标签

## [1.0.0] - 2026-08-21

### 新增

#### 项目初始化
- 建立完整仓库骨架（27 个文件，124K）
- 定义 6 个 Agent：reader-coordinator、ingest-worker、query-worker、summary-writer、insight-writer、quality-reviewer
- 实现 6 个核心 Skill：book-ingest、book-query、book-summary、book-insights、book-review-search、reading-report
- 定义主工作流 book-reading.yaml（解析 → 并行分析 → 合并 → 门禁）

#### 文档解析能力
- PDF 解析：marker-pdf（主力）+ pymupdf4llm（快速回退）
- EPUB 解析：ebooklib + beautifulsoup4
- TXT 解析：直接复制
- 按 Markdown 标题层级切块（每 chunk ≤ 2000 字符）

#### 向量检索能力
- Chroma 向量数据库（本地嵌入式）
- DashScope text-embedding-v3 作为 embedding 模型
- BM25 关键词检索（与向量检索互补）
- RRF（Reciprocal Rank Fusion）融合两路结果

#### 质量控制
- 10 个必含章节的 harness（一句话论点、三句话摘要、章节地图、关键概念、论证链、深刻洞见、启发清单、争议与局限、延伸阅读、原文引用）
- 门禁规则：引用 ≥5、无禁用词、评分 ≥9
- 生成/评判分离（quality-reviewer 独立打分）
- 重试机制：最多 3 次回退，超限走 best_effort

#### 文档与工具
- 完整使用指南：docs/guides/使用指南.md
- 领域术语表：docs/CONTEXT.md
- 安装脚本：setup.sh（一键检查依赖 + 安装）
- 4 个 Python 脚本：ingest.py、query.py、new_book.py、list_library.py

### 技术选型

| 能力 | 选型 | 理由 |
|------|------|------|
| PDF 解析 | marker-pdf | 保留章节/公式/表格最好 |
| EPUB 解析 | ebooklib | 标准库，零依赖 |
| 向量库 | Chroma | 嵌入式、零配置、Python 原生 |
| Embedding | DashScope text-embedding-v3 | 复用已有 API Key，中文效果好 |
| 检索策略 | Hybrid（向量 + BM25 + RRF） | 纯向量对术语检索弱 |

### 风险点与缓解

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| **marker-pdf 首次下载慢**（~2GB 模型） | 中 | 等一次就好；可回退到 pymupdf4llm（秒级，但结构弱） |
| **扫描版 PDF 解析差**（只有图片无文字层） | 高 | 当前不支持 OCR；后续可加 paddleocr 回退 |
| **DashScope embedding 有 token 费用** | 低 | 一本书约 ¥0.5-2，成本可控 |
| **Pi Agent plugin 加载方式可能不匹配** | 中 | Skill 里的 Python 脚本独立可运行（`python scripts/xxx.py`），即使 plugin 注册有问题也能用 |
| **Chroma 在大量书籍时性能** | 低 | 单书级别完全够用；100+ 本书时考虑切到 Qdrant |
| **EPUB 解析质量取决于原始排版** | 中 | 部分 EPUB 章节标题不规范，切块可能不理想 |
| **禁用词列表可能不够全面** | 低 | 根据实际输出迭代补充 constraints.yaml |

### 已知限制

1. **不支持扫描件 PDF**：需要 OCR 预处理（后续可扩展 paddleocr）
2. **不支持 DOCX/PPTX**：当前只支持 PDF/EPUB/TXT
3. **外部书评搜索依赖网络**：豆瓣/Goodreads 可能被封 IP
4. **门禁评分依赖 LLM 判断**：存在主观性，可能需要人工复核
5. **Pi Agent 版本兼容性**：需要 Node.js >= 22.19.0

### 后续可扩展

- `book-compare` Skill：多本书横向对比
- `reading-notes` Skill：按章节做细粒度读书笔记
- OCR 回退：扫描件 PDF → paddleocr → 文本
- 导出格式：HTML 版 / 微信版 / Obsidian 版
- 多语言支持：英文书籍的 summary/insights 模板

### 文件清单

```
my-read-pi-agent/
├── AGENTS.md                      # 总纲
├── agents.yaml                    # 6 个 Agent 定义
├── constraints.yaml               # 全局约束（禁用词、必含章节、预算）
├── package.json                   # Node 依赖
├── requirements.txt               # Python 依赖
├── .env.example                   # API Key 模板
├── .gitignore                     # Git 忽略规则
├── setup.sh                       # 一键安装脚本
├── README.md                      # 项目说明
│
├── config/
│   ├── llm-routing.yaml           # 模型路由（embedding/summary/insights/review）
│   ├── quality-gates.yaml         # 门禁规则
│   └── scoring-rubric.yaml        # 评分 rubric（5 维度 0-10 分）
│
├── scripts/
│   ├── ingest.py                  # 文档解析 + 向量索引
│   ├── query.py                   # RAG 混合检索
│   ├── new_book.py                # 新建书籍工作区
│   └── list_library.py            # 列出书库
│
├── plugins/
│   ├── doc-parser/plugin.yaml     # 文档解析插件声明
│   ├── vector-store/plugin.yaml   # 向量检索插件声明
│   └── web-research/plugin.yaml   # 联网搜索插件声明
│
├── skills/
│   ├── book-ingest/SKILL.md       # 文档解析 + 索引
│   ├── book-query/SKILL.md        # RAG 检索
│   ├── book-summary/SKILL.md      # 全书总结（10 章节 harness）
│   ├── book-insights/SKILL.md     # 深刻洞见 + 启发
│   ├── book-review-search/SKILL.md # 外部书评
│   └── reading-report/SKILL.md    # 合并终稿
│
├── workflows/
│   └── book-reading.yaml          # 主工作流
│
├── docs/
│   ├── CONTEXT.md                 # 领域术语表
│   └── guides/使用指南.md          # 完整使用流程
│
└── library/                       # 书库（不入 git）
    ├── raw/                       # 原始文件
    ├── parsed/                    # 解析后的 MD
    ├── index/                     # Chroma 索引
    └── metadata/                  # 书籍元信息

workspace/                         # 每本书的输出（不入 git）
```

### 快速开始

```bash
cd ~/Documents/my-2026/my-read-pi-agent

# 1. 安装依赖
./setup.sh

# 2. 配置 API Key
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 3. 起一本新书
python scripts/ingest.py ~/Downloads/你的书.pdf

# 4. 启动 Pi Agent
npm run pi

# 5. 在 Pi 对话中
/skill:book-summary
/skill:book-insights
/skill:book-review-search
/skill:reading-report
```

### 参考文档

- [使用指南](docs/guides/使用指南.md)
- [领域术语表](docs/CONTEXT.md)
- [Pi Agent 官方文档](https://pi.dev/docs)
