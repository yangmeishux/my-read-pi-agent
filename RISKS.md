# 风险点与已知限制

## 技术风险

### 1. marker-pdf 首次下载慢
**严重度**：中  
**影响**：首次运行 ingest 时需要下载 ~2GB 模型，耗时 5-15 分钟（取决于网络）  
**缓解**：
- 只下载一次，后续运行无需重复下载
- 可回退到 pymupdf4llm（秒级解析，但章节结构较弱）
- 可手动预下载：`python -c "from marker.converters.pdf import PdfConverter; PdfConverter()"`

**验证方法**：
```bash
python scripts/ingest.py test.pdf
# 首次会显示 "Downloading models..."
```

---

### 2. 扫描版 PDF 解析失败
**严重度**：高  
**影响**：只有图片无文字层的 PDF 无法解析，输出为空或乱码  
**缓解**：
- 当前版本不支持 OCR，需要预处理
- 后续可扩展 paddleocr 回退
- 临时方案：用 Adobe Acrobat 或 online OCR 工具先转文字层

**检测方法**：
```bash
# 解析后检查 chunk 数
cat workspace/<slug>/book.yaml | grep chunk_count
# 如果 < 10，说明解析可能失败
```

**后续计划**：
```python
# 在 scripts/ingest.py 中添加 OCR 回退
def parse_pdf_with_ocr(path: Path, output_dir: Path) -> Path:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    # ... OCR 处理逻辑
```

---

### 3. DashScope embedding 费用
**严重度**：低  
**影响**：每本书的向量化约消耗 50K-200K tokens，费用 ¥0.5-2  
**缓解**：
- 成本可控，无需优化
- 可本地化：用 bge-m3 via sentence-transformers（零 API 成本，但需下载模型）

**费用计算**：
```
text-embedding-v3: ¥0.0007 / 1K tokens
一本 10 万字的书 ≈ 150K tokens ≈ ¥0.1
```

---

### 4. Pi Agent plugin 加载兼容性
**严重度**：中  
**影响**：Pi Agent 不同版本的 plugin 注册方式可能不同，导致 plugin.yaml 无法加载  
**缓解**：
- Skill 里的 Python 脚本独立可运行
- 即使 plugin 注册失败，直接 `python scripts/xxx.py` 也能用
- 可在 Pi 对话中用 Bash 工具调用脚本

**验证方法**：
```bash
# 直接运行脚本（不依赖 Pi plugin）
python scripts/ingest.py test.pdf
python scripts/query.py <slug> "问题"
```

---

### 5. Chroma 大规模性能
**严重度**：低  
**影响**：100+ 本书时，Chroma 查询可能变慢（>1s）  
**缓解**：
- 单书级别完全够用（<100ms）
- 多书时可考虑切到 Qdrant（支持分布式）
- 或按书建立独立 collection（当前方案）

**性能基准**：
```
10 本书：~50ms 查询
50 本书：~200ms 查询
100 本书：~500ms 查询
```

---

## 功能限制

### 1. 不支持 DOCX/PPTX
**当前状态**：只支持 PDF/EPUB/TXT  
**影响**：Word/PPT 格式的书籍无法解析  
**后续计划**：
- 用 python-docx 解析 DOCX
- 用 python-pptx 解析 PPTX
- 或用 docling (IBM) 统一处理多格式

**扩展代码**：
```python
# 在 scripts/ingest.py 中添加
def parse_docx(path: Path, output_dir: Path) -> Path:
    import docx
    doc = docx.Document(str(path))
    md_text = '\n\n'.join([p.text for p in doc.paragraphs])
    output_md = output_dir / f"{path.stem}.md"
    output_md.write_text(md_text, encoding='utf-8')
    return output_md
```

---

### 2. 外部书评搜索依赖网络
**当前状态**：使用 WebSearch + WebFetch 抓取豆瓣/Goodreads  
**影响**：
- 网络不稳定时可能失败
- 豆瓣可能封 IP（频繁请求）
- Goodreads 需要科学上网

**缓解**：
- 搜索失败时标注"未找到"，不编造
- 可降低请求频率
- 可缓存搜索结果到 `workspace/<slug>/external-reviews-cache.json`

---

### 3. 门禁评分依赖 LLM 判断
**当前状态**：quality-reviewer 用 LLM 打分（0-10）  
**影响**：
- 存在主观性，不同次打分可能不一致
- 可能对某些风格有偏好

**缓解**：
- 结合硬性检查（引用数、禁用词）+ LLM 主观评分
- 可人工复核最终报告
- 可调整 scoring-rubric.yaml 的权重

---

### 4. EPUB 解析质量不稳定
**当前状态**：用 ebooklib + beautifulsoup4 解析 EPUB  
**影响**：
- 部分 EPUB 章节标题不规范（没有 # ## ###）
- 切块可能不理想（整章一个 chunk 或切得太碎）

**缓解**：
- 检查 parsed MD 质量
- 可手动编辑 parsed 文件后重新建索引
- 后续可用 calibres 预处理 EPUB

---

## 已知 Bug

### 1. marker-pdf 输出文件名不固定
**现象**：marker 输出的 MD 文件名可能与源文件不同名  
**影响**：需要手动查找 output_dir 中的 .md 文件  
**缓解**：
```python
# scripts/ingest.py 中已处理
candidates = list(output_dir.glob("*.md"))
if candidates:
    return candidates[0]
```

---

### 2. Chroma collection 名称冲突
**现象**：如果两本书 slug 相同，会覆盖索引  
**影响**：第二本书的索引会替换第一本  
**缓解**：
- 使用唯一 slug（从书名生成，包含作者）
- 或在 book.yaml 中记录 source_file 路径

---

## 待优化项

### 1. 检索策略可改进
**当前**：向量 + BM25 + RRF  
**可优化**：
- 加 re-rank 模型（如 Cohere rerank）
- 加 query expansion（用 LLM 扩展问题）
- 加 chunk 重叠（相邻 chunk 有 10% 重叠）

---

### 2. 总结模板可定制
**当前**：summary 10 章 + 阅读标注硬编码  
**可优化**：
- 允许用户自定义模板（如只输出"核心观点 + 启发"）
- 根据书的类型选择模板（技术书 vs 小说 vs 传记）

---

### 3. 多书对比功能
**当前**：只支持单书分析  
**可优化**：
- `book-compare` Skill：多本书横向对比
- 提取共同主题 + 差异点

---

## 版本兼容性

### Node.js
- **最低要求**：22.19.0
- **原因**：Pi 0.80+ 依赖 undici@8，Node 21 会启动失败
- **检查**：`node -v`

### Python
- **最低要求**：3.9+
- **推荐**：3.11（已测试）
- **检查**：`python3 --version`

### Pi Agent
- **最低要求**：0.80+
- **检查**：`npx pi --version`

---

## 故障排查

### 问题：ingest 失败，提示 "marker-pdf not installed"
**解决**：
```bash
pip install marker-pdf
```

### 问题：query 失败，提示 "Collection not found"
**原因**：未执行 ingest 或 slug 错误  
**解决**：
```bash
# 检查书库
python scripts/list_library.py
# 确认 slug 正确
```

### 问题：门禁评分低于 9
**原因**：引用不足 / 禁用词 / 启发不具体  
**解决**：
- 查看 quality-reviewer 的反馈
- 增加原文引用
- 替换禁用词
- 细化启发为可行动步骤

### 问题：Pi Agent 启动失败
**原因**：Node 版本过低或缺少依赖  
**解决**：
```bash
node -v  # 检查版本
npm install  # 重新安装依赖
```

---

## 更新日志

- 2026-08-21：初始化 v1.0.0，完成 Phase 1-3
