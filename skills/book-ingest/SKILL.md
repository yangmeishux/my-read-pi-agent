---
name: book-ingest
description: 文档解析 + 向量索引构建（PDF/EPUB → Markdown → Chroma）
triggers:
  - book-ingest
  - 解析文档
  - 导入书籍
---

# book-ingest

将 PDF/EPUB/TXT 文件解析为 Markdown，按章节切块，构建 Chroma 向量索引。

## 输入

- `--file <path>`: 文档文件路径
- `--slug <slug>`: 自定义 slug（可选，默认从文件名生成）

## 执行

```bash
python scripts/ingest.py <file_path> [--slug <slug>]
```

## 输出

- `library/parsed/<slug>.md` — 解析后的 Markdown
- `library/index/<slug>/` — Chroma 向量索引
- `workspace/<slug>/book.yaml` — 书籍元信息
- `workspace/<slug>/refs.json` — chunk 索引（用于引用溯源）

## 解析策略

| 格式 | 主力 | 回退 |
|------|------|------|
| PDF | marker-pdf（保留章节/公式/表格） | pymupdf4llm（快速但结构弱） |
| EPUB | ebooklib + beautifulsoup4 | — |
| TXT | 直接复制 | — |

## 切块策略

- 按 Markdown 标题层级（# ## ###）切分
- 单 chunk 超过 2000 字符二次切分
- 每个 chunk 保留 section 名称（用于引用定位）

## 验证

```bash
# 检查输出
cat workspace/<slug>/book.yaml
# 测试检索
python scripts/query.py <slug> "这本书讲了什么"
```

## 常见陷阱

- marker-pdf 首次运行会下载模型，需要网络
- EPUB 解析质量取决于原始排版
- chunk 数 < 10 说明解析可能失败，检查 parsed 输出
