#!/usr/bin/env python3
"""
文档解析 + 向量索引构建
用法：python ingest.py <book_path> [--slug <slug>]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# 项目根
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


def slugify(text: str) -> str:
    """生成 URL 友好的 slug"""
    text = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text.strip())
    return text.lower().strip('-')[:60]


def detect_format(path: Path) -> str:
    """根据扩展名检测文档格式"""
    ext = path.suffix.lower()
    if ext == '.pdf':
        return 'pdf'
    elif ext == '.epub':
        return 'epub'
    elif ext in ('.txt', '.md'):
        return 'text'
    else:
        raise ValueError(f"不支持的格式: {ext}")


def parse_pdf(path: Path, output_dir: Path) -> Path:
    """PDF → Markdown（使用 marker-pdf）"""
    try:
        from marker.scripts.convert_single import convert_single
        from marker.config.parser import ConfigParser
    except ImportError:
        print("[WARN] marker-pdf 未安装，回退到 pymupdf4llm")
        return parse_pdf_fallback(path, output_dir)

    output_md = output_dir / f"{path.stem}.md"
    try:
        config_parser = ConfigParser()
        convert_single(
            str(path),
            output_dir=str(output_dir),
            config=config_parser.generate_config_dict(),
        )
        # marker 输出可能与源文件同名
        candidates = list(output_dir.glob("*.md"))
        if candidates:
            return candidates[0]
    except Exception as e:
        print(f"[WARN] marker-pdf 失败: {e}，回退到 pymupdf4llm")
        return parse_pdf_fallback(path, output_dir)

    return output_md


def parse_pdf_fallback(path: Path, output_dir: Path) -> Path:
    """PDF → Markdown（pymupdf4llm 快速通道）"""
    import pymupdf4llm
    md_text = pymupdf4llm.to_markdown(str(path))
    output_md = output_dir / f"{path.stem}.md"
    output_md.write_text(md_text, encoding='utf-8')
    return output_md


def parse_epub(path: Path, output_dir: Path) -> Path:
    """EPUB → Markdown"""
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(str(path))
    chapters = []

    for item in book.get_items_of_type(9):  # ITEM_DOCUMENT = 9
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        text = soup.get_text(separator='\n')
        if text.strip():
            chapters.append(f"# {item.get_name()}\n\n{text.strip()}")

    md_text = '\n\n---\n\n'.join(chapters)
    output_md = output_dir / f"{path.stem}.md"
    output_md.write_text(md_text, encoding='utf-8')
    return output_md


def parse_text(path: Path, output_dir: Path) -> Path:
    """纯文本直接复制"""
    output_md = output_dir / f"{path.stem}.md"
    output_md.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    return output_md


def chunk_by_headings(md_text: str, max_chunk_chars: int = 2000) -> list[dict]:
    """
    按 Markdown 标题层级切块，保留章节锚点。
    如果单个章节超长，按 max_chunk_chars 二次切分。
    """
    chunks = []
    current_section = "前言"
    current_text = []
    current_chars = 0

    for line in md_text.split('\n'):
        heading_match = re.match(r'^(#{1,3})\s+(.+)', line)
        if heading_match:
            # 保存上一段
            if current_text:
                text = '\n'.join(current_text).strip()
                if text:
                    chunks.append({
                        'section': current_section,
                        'text': text,
                    })
            current_section = heading_match.group(2).strip()
            current_text = [line]
            current_chars = len(line)
        else:
            current_text.append(line)
            current_chars += len(line)
            # 超长切分
            if current_chars > max_chunk_chars:
                text = '\n'.join(current_text).strip()
                if text:
                    chunks.append({
                        'section': current_section,
                        'text': text,
                    })
                current_text = []
                current_chars = 0

    # 最后一段
    if current_text:
        text = '\n'.join(current_text).strip()
        if text:
            chunks.append({
                'section': current_section,
                'text': text,
            })

    # 给每个 chunk 编号
    for i, chunk in enumerate(chunks):
        chunk['id'] = f"chunk_{i:04d}"
    return chunks


def build_vector_index(chunks: list[dict], book_slug: str, index_dir: Path):
    """
    构建 Chroma 向量索引。
    使用 DashScope text-embedding-v3 作为 embedding 模型。
    """
    import chromadb
    from chromadb.utils import embedding_functions
    import dashscope

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY，请在 .env 中设置")

    # DashScope embedding 兼容 OpenAI 接口
    embed_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_name="text-embedding-v3",
    )

    client = chromadb.PersistentClient(path=str(index_dir))
    collection = client.get_or_create_collection(
        name=book_slug,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # 分批写入（Chroma 单次上限 ~4000）
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.add(
            ids=[c['id'] for c in batch],
            documents=[c['text'] for c in batch],
            metadatas=[{"section": c['section'], "index": j} for j, c in enumerate(batch, start=i)],
        )

    print(f"[OK] 向量索引已构建：{len(chunks)} chunks → {index_dir}")
    return collection


def save_book_metadata(book_slug: str, source_path: Path, parsed_path: Path,
                       chunk_count: int, workspace_dir: Path):
    """保存 book.yaml 元信息"""
    import yaml

    metadata = {
        'slug': book_slug,
        'source_file': str(source_path),
        'parsed_file': str(parsed_path),
        'format': detect_format(source_path),
        'chunk_count': chunk_count,
        'status': 'ingested',
    }

    workspace_dir.mkdir(parents=True, exist_ok=True)
    meta_path = workspace_dir / "book.yaml"
    with open(meta_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)

    print(f"[OK] book.yaml → {meta_path}")
    return meta_path


def main():
    parser = argparse.ArgumentParser(description="文档解析 + 向量索引")
    parser.add_argument("book_path", help="PDF/EPUB/TXT 文件路径")
    parser.add_argument("--slug", help="自定义 slug（默认从文件名生成）")
    args = parser.parse_args()

    book_path = Path(args.book_path).resolve()
    if not book_path.exists():
        print(f"[ERROR] 文件不存在: {book_path}")
        sys.exit(1)

    # 生成 slug
    book_slug = args.slug or slugify(book_path.stem)
    print(f"[INFO] 书名 slug: {book_slug}")

    # 目录
    parsed_dir = ROOT / "library" / "parsed"
    parsed_dir.mkdir(parents=True, exist_ok=True)

    index_dir = ROOT / "library" / "index" / book_slug
    index_dir.mkdir(parents=True, exist_ok=True)

    workspace_dir = ROOT / "workspace" / book_slug
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # 1. 解析
    fmt = detect_format(book_path)
    print(f"[INFO] 检测到格式: {fmt}")

    if fmt == 'pdf':
        parsed_path = parse_pdf(book_path, parsed_dir)
    elif fmt == 'epub':
        parsed_path = parse_epub(book_path, parsed_dir)
    elif fmt == 'text':
        parsed_path = parse_text(book_path, parsed_dir)
    else:
        raise ValueError(f"不支持的格式: {fmt}")

    print(f"[OK] 解析完成: {parsed_path}")

    # 2. 切块
    md_text = parsed_path.read_text(encoding='utf-8')
    chunks = chunk_by_headings(md_text)
    print(f"[OK] 切块完成: {len(chunks)} chunks")

    if len(chunks) < 10:
        print("[WARN] chunk 数量较少，可能解析质量不佳，请检查 parsed 输出")

    # 3. 向量索引
    build_vector_index(chunks, book_slug, index_dir)

    # 4. 保存元信息
    save_book_metadata(book_slug, book_path, parsed_path, len(chunks), workspace_dir)

    # 5. 输出 refs.json（空模板）
    refs_path = workspace_dir / "refs.json"
    refs_path.write_text(json.dumps({
        "book_slug": book_slug,
        "chunks": [{"id": c['id'], "section": c['section']} for c in chunks],
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"\n[SUCCESS] 文档已入库")
    print(f"  slug: {book_slug}")
    print(f"  chunks: {len(chunks)}")
    print(f"  workspace: {workspace_dir}")


if __name__ == "__main__":
    main()
