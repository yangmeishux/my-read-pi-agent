---
name: book-review-search
description: 联网搜索外部书评（豆瓣/Goodreads/维基百科）
triggers:
  - book-review-search
  - 搜索书评
  - 外部评价
---

# book-review-search

联网搜索书籍的外部评价与解读，输出聚合报告。

## 搜索源

| 来源 | 搜索词模板 | 提取内容 |
|------|-----------|---------|
| 豆瓣 | `<书名> 豆瓣 书评` | 评分、热门书评摘要 |
| Goodreads | `<book_title> goodreads review` | 评分、top reviews |
| 维基百科 | `<书名> 维基百科` | 背景介绍、评价 |
| 知乎 | `<书名> 知乎 评价` | 深度讨论 |
| 通用 | `<书名> 读后感 书评` | 综合 |

## 执行流程

1. 从 `book.yaml` 读取书名和作者
2. 依次搜索上述来源（使用 WebSearch + WebFetch）
3. 提取关键评价，去重合并
4. 标注来源 URL

## 输出结构

### 外部评价概览

- 豆瓣评分 / Goodreads 评分
- 读者画像（什么人觉得好/不好）

### 正面评价（3-5 条）

每条带来源链接。

### 负面评价（3-5 条）

每条带来源链接。

### 专业解读

来自维基百科、知名书评人的深度分析。

## 输出

写入 `workspace/<slug>/external-reviews.md`。

## 注意

- 每条引用必须给 URL
- 不确定的信息标 `[待核实]`
- 如果某来源搜不到，标注"未找到"，不要编造
