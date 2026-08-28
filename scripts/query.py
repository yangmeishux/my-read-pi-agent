#!/usr/bin/env python3
"""
RAG 混合检索：向量 + BM25 + 章节锚点
用法：python query.py <book_slug> <question> [--top_k 10]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


def load_chunks(parsed_path: Path) -> list[dict]:
    """从 parsed MD 重新加载 chunks（与 ingest 逻辑一致）"""
    from scripts.ingest import chunk_by_headings
    md_text = parsed_path.read_text(encoding='utf-8')
    return chunk_by_headings(md_text)


def vector_search(query: str, book_slug: str, top_k: int = 10) -> list[dict]:
    """Chroma 向量检索"""
    import chromadb

    from scripts.ingest import chroma_collection_name, make_embed_fn

    embed_fn = make_embed_fn()

    index_dir = ROOT / "library" / "index" / book_slug
    client = chromadb.PersistentClient(path=str(index_dir))
    collection = client.get_collection(
        name=chroma_collection_name(book_slug),
        embedding_function=embed_fn,
    )

    results = collection.query(query_texts=[query], n_results=top_k)
    hits = []
    for i, doc in enumerate(results['documents'][0]):
        hits.append({
            'id': results['ids'][0][i],
            'text': doc,
            'section': results['metadatas'][0][i].get('section', ''),
            'score': 1.0 - (results['distances'][0][i] if results.get('distances') else 0),
            'source': 'vector',
        })
    return hits


def bm25_search(query: str, chunks: list[dict], top_k: int = 10) -> list[dict]:
    """BM25 关键词检索"""
    from rank_bm25 import BM25Okapi

    corpus = [c['text'] for c in chunks]
    tokenized = [list(re.sub(r'[^\w\u4e00-\u9fff]', ' ', doc).lower().split()) for doc in corpus]
    bm25 = BM25Okapi(tokenized)

    tokens = list(re.sub(r'[^\w\u4e00-\u9fff]', ' ', query).lower().split())
    scores = bm25.get_scores(tokens)

    # top_k
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    hits = []
    for idx, score in ranked:
        if score > 0:
            hits.append({
                'id': chunks[idx]['id'],
                'text': chunks[idx]['text'],
                'section': chunks[idx]['section'],
                'score': score,
                'source': 'bm25',
            })
    return hits


def merge_and_rerank(vector_hits: list[dict], bm25_hits: list[dict],
                     top_k: int = 10) -> list[dict]:
    """
    RRF (Reciprocal Rank Fusion) 合并两路检索结果
    """
    score_map = {}
    k = 60  # RRF 常数

    for rank, hit in enumerate(vector_hits):
        doc_id = hit['id']
        if doc_id not in score_map:
            score_map[doc_id] = {'hit': hit, 'rrf': 0}
        score_map[doc_id]['rrf'] += 1.0 / (k + rank + 1)

    for rank, hit in enumerate(bm25_hits):
        doc_id = hit['id']
        if doc_id not in score_map:
            score_map[doc_id] = {'hit': hit, 'rrf': 0}
        score_map[doc_id]['rrf'] += 1.0 / (k + rank + 1)

    # 按 RRF 排序
    ranked = sorted(score_map.values(), key=lambda x: x['rrf'], reverse=True)[:top_k]
    results = []
    for item in ranked:
        hit = item['hit']
        hit['rrf_score'] = item['rrf']
        results.append(hit)

    return results


def query(book_slug: str, question: str, top_k: int = 10) -> list[dict]:
    """主检索入口"""
    # 向量检索
    vector_hits = vector_search(question, book_slug, top_k=top_k * 2)

    # BM25 检索（从 parsed MD 重建 chunks）
    import yaml
    workspace_dir = ROOT / "workspace" / book_slug
    book_yaml = workspace_dir / "book.yaml"
    if not book_yaml.exists():
        raise RuntimeError(f"未找到 book.yaml: {book_yaml}，请先执行 ingest")

    with open(book_yaml, 'r', encoding='utf-8') as f:
        meta = yaml.safe_load(f)

    parsed_path = Path(meta['parsed_file'])
    if not parsed_path.exists():
        raise RuntimeError(f"parsed 文件不存在: {parsed_path}")

    chunks = load_chunks(parsed_path)
    bm25_hits = bm25_search(question, chunks, top_k=top_k * 2)

    # 合并
    merged = merge_and_rerank(vector_hits, bm25_hits, top_k=top_k)

    return merged


def main():
    parser = argparse.ArgumentParser(description="RAG 混合检索")
    parser.add_argument("book_slug", help="书籍 slug")
    parser.add_argument("question", help="检索问题")
    parser.add_argument("--top_k", type=int, default=10, help="返回结果数")
    args = parser.parse_args()

    results = query(args.book_slug, args.question, top_k=args.top_k)

    # 格式化输出
    print(f"## 检索结果：{args.question}\n")
    print(f"共 {len(results)} 条命中\n")

    for i, hit in enumerate(results, 1):
        print(f"### [{i}] {hit['section']}")
        print(f"- ID: {hit['id']}")
        print(f"- RRF Score: {hit.get('rrf_score', 0):.4f}")
        print(f"- 来源: {hit['source']}")
        print(f"\n{hit['text'][:500]}...")
        print()


if __name__ == "__main__":
    main()
