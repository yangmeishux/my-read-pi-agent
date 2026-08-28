#!/usr/bin/env python3
"""
新建一本书的工作区
用法：python new_book.py <book_name> [--file <path>]
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def slugify(text: str) -> str:
    text = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text.strip())
    return text.lower().strip('-')[:60]


def main():
    parser = argparse.ArgumentParser(description="新建书籍工作区")
    parser.add_argument("book_name", help="书名")
    parser.add_argument("--file", help="PDF/EPUB 文件路径（可选，稍后 ingest）")
    parser.add_argument("--author", help="作者（可选）")
    args = parser.parse_args()

    book_slug = slugify(args.book_name)
    workspace_dir = ROOT / "workspace" / book_slug

    if workspace_dir.exists():
        print(f"[WARN] 工作区已存在: {workspace_dir}")
        sys.exit(1)

    workspace_dir.mkdir(parents=True)

    metadata = {
        'slug': book_slug,
        'title': args.book_name,
        'author': args.author or '[待补充]',
        'source_file': str(Path(args.file).resolve()) if args.file else None,
        'status': 'created',
    }

    meta_path = workspace_dir / "book.yaml"
    with open(meta_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)

    print(f"[OK] 工作区已创建: {workspace_dir}")
    print(f"  slug: {book_slug}")
    if args.file:
        print(f"  下一步: npm run ingest -- {args.file}")
    else:
        print(f"  下一步: 将 PDF/EPUB 文件放入 library/raw/ 并执行 ingest")


if __name__ == "__main__":
    main()
