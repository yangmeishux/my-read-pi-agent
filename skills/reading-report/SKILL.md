---
name: reading-report
description: 合并 summary + insights + external-reviews → report.md（确定性导出）
triggers:
  - reading-report
  - 生成报告
  - 合并输出
---

# reading-report

将 `summary.md`、`insights.md`、`external-reviews.md` 合并为最终读书报告 `report.md`。

## 重要

这是一个**确定性导出** Skill：
- 不改写论证
- 不添加新观点
- 只做结构化合并 + 格式统一

## 合并顺序

1. **书籍概览**（来自 summary.md 的一句话论点 + 三句话摘要）
2. **章节地图**（来自 summary.md）
3. **关键概念**（来自 summary.md）
4. **核心论证**（来自 summary.md 的论证链）
5. **深刻洞见**（来自 insights.md）
6. **启发清单**（来自 insights.md）
7. **外部评价**（来自 external-reviews.md）
8. **争议与局限**（来自 summary.md）
9. **延伸阅读**（来自 summary.md）
10. **引用索引**（汇总所有引用的章节/页码）

## 输出

写入 `workspace/<slug>/report.md`。

## 格式要求

- 使用统一的 Markdown 标题层级
- 引用格式统一为 `[章节名 / 页码]`
- 添加目录（TOC）
- 末尾附引用索引表

## 验证

- 10 个章节全部存在
- 引用数 ≥ 5
- 无禁用词
