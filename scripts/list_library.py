#!/usr/bin/env python3
"""
列出书库中所有已索引的书籍
用法：python list_library.py
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def main():
    workspace_dir = ROOT / "workspace"
    if not workspace_dir.exists():
        print("[INFO] 书库为空，还没有索引任何书籍")
        return

    books = []
    for book_dir in sorted(workspace_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        meta_path = book_dir / "book.yaml"
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f)
            books.append(meta)

    if not books:
        print("[INFO] 书库为空")
        return

    print(f"## 书库 ({len(books)} 本)\n")
    for b in books:
        status = b.get('status', 'unknown')
        chunks = b.get('chunk_count', '?')
        title = b.get('title', b.get('slug', '?'))
        author = b.get('author', '')
        print(f"- **{title}** {f'({author})' if author else ''}")
        print(f"  slug: `{b['slug']}` | 状态: {status} | chunks: {chunks}")
        print()


if __name__ == "__main__":
    main()
