# Awesome Review Skill

**Awesome Review Skill** is a public-safe Codex skill for turning course books, lecture notes, exams, handwritten materials, and answer keys into structured review workflows.

It is designed for course review distillation, tutoring answers, teacher preparation, exam-question organization, and holdout-style evaluation. The repository contains the reusable skill, scripts, and workflow references only. It does **not** include copyrighted textbooks, exam scans, answer-key scans, or generated textbook screenshots.

## What It Does

- Inventories PDFs, PPTX files, images, handwritten notes, and `.note`-style containers.
- Labels materials as distillation sources, answer keys, or holdout test sets.
- Builds course maps, formula cards, answer templates, teacher-prep notes, and review packs.
- Produces polished student-facing solutions with LaTeX-style formulas, citations, rubrics, and mistake diagnosis.
- Supports objective-question solution books grouped by chapter and test point.
- Supports visual answer workflows for scanned exams, drawing problems, and diagnosis problems.
- Compares baseline answers with distilled-course answers for holdout evaluation.

## Repository Layout

```text
skills/course-book-distiller/
├── SKILL.md
├── agents/openai.yaml
├── references/
└── scripts/
```

Key references:

- `references/answer_style.md`: answer formatting, LaTeX, scoring points, and mistake diagnosis.
- `references/objective_solution_books.md`: chapter-based objective-question solution book workflow.
- `references/distillation_outputs.md`: manifest, question bank, and course-pack artifact contracts.
- `references/evaluation.md`: baseline vs distilled evaluation workflow.

## Quick Start

Copy or keep `skills/course-book-distiller` under your Codex skills directory, then invoke the skill as:

```text
$course-book-distiller
```

Typical workflow:

```bash
python3 skills/course-book-distiller/scripts/inventory_course_materials.py \
  --root /path/to/course_materials \
  --output-dir /path/to/output

python3 skills/course-book-distiller/scripts/build_course_pack.py \
  --manifest /path/to/output/manifest.jsonl \
  --output-dir /path/to/output

python3 skills/course-book-distiller/scripts/evaluate_holdout.py \
  --question-bank /path/to/output/question_bank.jsonl \
  --output-dir /path/to/output/evaluation
```

For chapter-grouped objective-question solution books, see:

```text
skills/course-book-distiller/references/objective_solution_books.md
```

## Public-Safe Policy

This public repository is meant to share methods, scripts, and reusable skill instructions. Do not commit:

- textbook PDFs or OCR copies;
- scanned exams or answer keys;
- generated textbook snippets or screenshots;
- private tutoring notes that should not be redistributed;
- student-identifying records.

For real course pilots, keep source materials and generated citation screenshots in a private local workspace or private repository.

## License

This project is released under the Apache License 2.0. See `LICENSE`.

---

# Awesome Review Skill 中文说明

**Awesome Review Skill** 是一个公开安全版本的 Codex skill，用来把课程教材、讲义、试卷、手写笔记和答案资料整理成结构化复习流程。

它适合做课程知识蒸馏、学生答题辅导、教师备课、试题分类、复习题集生成和留出卷评测。本仓库只包含可复用的 skill、脚本和方法文档，不包含受版权保护的教材、试卷扫描件、答案扫描件或教材截图。

## 能做什么

- 盘点 PDF、PPTX、图片、手写笔记和 `.note` 类资料包。
- 将资料标记为蒸馏来源、答案来源或留出测试集。
- 生成课程地图、公式卡片、答题模板、教师备课材料和复习包。
- 生成更美观的学生版答案：包含 LaTeX 风格公式、教材定位、评分点和易错诊断。
- 支持按章节和考点整理选择题、填空式选择题、判断题。
- 支持扫描试卷、绘图题和结构诊断题的图上作答流程。
- 支持用留出试卷对比“蒸馏前”和“蒸馏后”的答题效果。

## 目录结构

```text
skills/course-book-distiller/
├── SKILL.md
├── agents/openai.yaml
├── references/
└── scripts/
```

重要参考文件：

- `references/answer_style.md`：答案排版、公式、评分点、易错诊断。
- `references/objective_solution_books.md`：按章节整理小题题集的方法。
- `references/distillation_outputs.md`：manifest、题库和课程包的产物约定。
- `references/evaluation.md`：蒸馏前后留出评测流程。

## 快速开始

将 `skills/course-book-distiller` 放在 Codex skills 目录下，然后调用：

```text
$course-book-distiller
```

典型流程：

```bash
python3 skills/course-book-distiller/scripts/inventory_course_materials.py \
  --root /path/to/course_materials \
  --output-dir /path/to/output

python3 skills/course-book-distiller/scripts/build_course_pack.py \
  --manifest /path/to/output/manifest.jsonl \
  --output-dir /path/to/output

python3 skills/course-book-distiller/scripts/evaluate_holdout.py \
  --question-bank /path/to/output/question_bank.jsonl \
  --output-dir /path/to/output/evaluation
```

如果要生成按章节归类的小题题集，请先阅读：

```text
skills/course-book-distiller/references/objective_solution_books.md
```

## 公开仓库注意事项

这个仓库用于公开方法、脚本和 skill 说明。不要提交：

- 教材 PDF 或 OCR 副本；
- 扫描试卷或答案；
- 生成的教材局部截图；
- 不适合公开的辅导笔记；
- 学生身份相关记录。

真实课程试点中的原始资料和带教材截图的产物，建议保存在本地私有目录或私有仓库中。

## License

本项目使用 Apache License 2.0，见 `LICENSE`。
