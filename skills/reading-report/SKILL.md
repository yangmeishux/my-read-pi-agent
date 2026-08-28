---
name: reading-report
description: 合并 summary + insights + external-reviews + reading-guide + digest → report.md
triggers:
  - reading-report
  - 生成报告
  - 合并输出
---

# reading-report

将 `summary.md`、`insights.md`、`external-reviews.md`、`reading-guide.md`、`digest.md` 合并为最终读书报告 `report.md`。

## 重要

这是一个**确定性导出** Skill：
- 不改写论证
- 不添加新观点
- 只做结构化合并 + 格式统一

## 合并顺序

1. **书籍概览**（来自 summary.md 的一句话论点 + 三句话摘要）
2. **章节地图**（来自 summary.md）
3. **阅读标注与拆解**（来自 reading-guide.md）
4. **逐章详述与全书总述**（来自 digest.md：各章「本章主旨」列表 + 全书总述全文；完整展开见 digest.md）
5. **关键概念**（来自 summary.md）
6. **核心论证**（来自 summary.md 的论证链）
7. **深刻洞见**（来自 insights.md）
8. **启发清单**（来自 insights.md）
9. **外部评价**（来自 external-reviews.md）
10. **争议与局限**（来自 summary.md）
11. **延伸阅读**（来自 summary.md）
12. **引用索引**（汇总所有引用的章节/页码）

## 输出

写入 `workspace/<slug>/report.md`。

## 格式要求

- 使用统一的 Markdown 标题层级
- 引用格式统一为 `[章节名 / 页码]`
- 添加目录（TOC）
- 末尾附引用索引表

## 验证

- 12 个章节全部存在（含「阅读标注与拆解」「逐章详述与全书总述」）
- 引用数 ≥ 5
- 无禁用词
