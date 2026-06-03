---
name: course-book-distiller
description: Distill textbooks, lecture notes, exams, answer keys, handwritten notes, PPTX decks, PDFs, and image-based course materials into course knowledge packs, tutoring answer workflows, teacher-prep materials, exam-generation rubrics, and holdout evaluations. Use when Codex needs to inventory course files, split non-leaking holdout tests, build a distilled study/teaching pack, solve or grade course problems, handle drawing/diagnosis questions, or compare baseline answers with distilled-course answers.
---

# Course Book Distiller

## Operating Rules

- Treat holdout tests as contamination-sensitive. Select and label holdout files before distilling, then never use holdout content to build the course pack.
- Prefer local-first extraction: use text layers, file metadata, and local scripts first; use vision/OCR only for scanned pages, handwritten notes, diagrams, and drawing/diagnosis questions that require visual understanding.
- Do not publicly upload copyrighted textbook pages or reproduce long textbook passages. Cite local source paths/pages and paraphrase.
- Separate student mode from teacher mode:
  - Student mode explains concepts, solves problems, diagnoses mistakes, and produces polished answers.
  - Teacher mode prepares lessons, variants, rubrics, quizzes, and review plans.
- For drawing and diagnosis questions, include the original figure reference, numbered annotations, construction or correction steps, final answer, grading points, and common mistakes.

## Quick Start

Run inventory first:

```bash
python3 <skill>/scripts/inventory_course_materials.py \
  --root /path/to/course_materials \
  --output-dir /path/to/output
```

Build the distilled pack from non-holdout materials:

```bash
python3 <skill>/scripts/build_course_pack.py \
  --manifest /path/to/output/manifest.jsonl \
  --output-dir /path/to/output
```

Create a holdout evaluation protocol:

```bash
python3 <skill>/scripts/evaluate_holdout.py \
  --question-bank /path/to/output/question_bank.jsonl \
  --output-dir /path/to/output/evaluation
```

Generate a simple editable PPTX review deck from the deck spec:

```bash
python3 <skill>/scripts/make_review_deck.py \
  --deck-spec /path/to/output/review_decks/deck_spec.json \
  --out /path/to/output/review_decks/course_review.pptx
```

Create on-paper visual answer annotations:

```bash
python3 <skill>/scripts/annotate_exam_sheet.py \
  --spec /path/to/visual_answer_spec.json \
  --output-dir /path/to/visual_answers \
  --pdf-out /path/to/visual_answers.pdf
```

Render per-question multiple-choice comparisons:

```bash
python3 <skill>/scripts/render_choice_comparison.py \
  --data /path/to/choice_comparison_data.json \
  --output-dir /path/to/choice_comparison \
  --pdf-out /path/to/choice_comparison.pdf \
  --questions-per-page 4
```

Render student-facing vertical answer cards for objective questions:

```bash
python3 <skill>/scripts/render_choice_cards.py \
  --data /path/to/choice_cards_data.json \
  --output-dir /path/to/choice_cards \
  --pdf-out /path/to/choice_cards.pdf \
  --resolved-data-out /path/to/choice_cards_resolved.json
```

Audit course materials and prepare a reversible archive plan:

```bash
python3 <skill>/scripts/audit_materials.py \
  --root /path/to/course_materials \
  --output-dir /path/to/output/materials_audit
```

Build chapter-grouped review maps for objective questions, big problems, and textbook after-class exercises:

```bash
python3 <skill>/scripts/build_review_question_maps.py \
  --choice-data /path/to/choice_cards_resolved.json \
  --big-index /path/to/big_problem_type_index.jsonl \
  --output-dir /path/to/output/review_question_maps
```

Generate XeLaTeX review-note sources from the chapter maps and note previews:

```bash
python3 <skill>/scripts/build_latex_review_notes.py \
  --objective-index /path/to/output/review_question_maps/objective_question_chapter_index.jsonl \
  --big-index /path/to/output/big_questions/big_problem_type_index.jsonl \
  --note-preview-dir /path/to/output/lecture_notes/previews_white \
  --output-dir /path/to/output/latex_review_notes
```

Build split objective-question solution books with de-duplication, formula explanations, textbook page search, and local textbook snippets:

```bash
python3 <skill>/scripts/build_all_choice_solution_books.py \
  --objective-index /path/to/output/review_question_maps/objective_question_chapter_index.jsonl \
  --b-choice-data /path/to/output/visual_answers/choice_cards/b_choice_cards_resolved.json \
  --output-dir /path/to/output/all_choice_solution_books
```

Before extending or regenerating these objective-question books, load `references/objective_solution_books.md`.

## Workflow

1. **Inventory sources**
   - Use `scripts/inventory_course_materials.py` to emit `manifest.jsonl`.
   - Mark each source/page/image as `distill_source`, `answer_key`, or `holdout`.
   - Keep image-only PDFs, `.note` images, handwritten notes, and past-paper PNG/JPG files as visual sources.

2. **Lock holdouts**
   - Choose 2-3 exam sets before distillation.
   - Use path tokens such as `机原往年题b`, `机原往年题g`, or teacher handwritten answer folders.
   - Verify `inventory_summary.md` lists holdout files and that `build_course_pack.py` excludes them.

3. **Distill non-holdout material**
   - Build `distilled_course_pack/course_map.md`, `exam_taxonomy.md`, `formula_cards.md`, `answer_templates.md`, and `teacher_prep.md`.
   - Use source tags and samples as scaffolding, then refine with course-specific reasoning.
   - For large or scanned sources, summarize by topic and citation instead of copying source text.

4. **Answer problems**
   - Load `references/answer_style.md` before solving or formatting answers.
   - For objective questions from scanned papers, split each question out and render a large vertical card: question/options, answer, analysis, textbook chapter/page, local textbook snippet, and a related review question.
   - Student-facing objective answers should not show a baseline/non-distilled answer. Keep baseline comparisons only in evaluation files.
   - Distilled objective-answer analysis should cite a textbook chapter, PDF page, printed page when known, and a short original-phrase anchor from the course materials. Keep copied source wording short.
   - For calculation questions, show knowns, governing formulas, substitutions, result, units, and checks.
   - For drawing/diagnosis questions, mark errors or construction entities by number and include a correction/rubric.
   - For scanned exams, prefer on-paper visual answers: write inside the answer region when space allows; if not, crop or preserve the question image and place correct, baseline, and distilled answers below or beside it.
   - For drawing questions, answer directly on the original figure with construction lines, dots, labels, arrows, and numbered callouts, then add a concise side or bottom panel for calculations and scoring points.
   - For large problems, maintain a reusable `big_questions/` library with:
     - `b_paper_full_solutions.md` for complete holdout-paper讲评.
     - `big_problem_type_library.md` for topic-by-topic methods, formulas, scoring points, and mistake diagnosis.
     - `big_problem_type_index.jsonl` for scriptable retrieval and deck generation.
   - For review handouts, maintain `review_question_maps/`:
     - `objective_question_chapter_review.md` groups all observed objective/fill/judgment exam points by textbook chapter.
     - `big_question_classified_solutions.md` stores all large-problem types with templates and examples.
     - `textbook_afterclass_exercise_playbook.md` indexes textbook after-class exercises and gives the distilled answer-card method.
   - For polished PDF review notes, maintain `latex_review_notes/`:
     - `choice_review_notes.tex/.pdf` groups objective questions by chapter with formulas, topic signals, answer anchors, migration review questions, and mistake diagnosis.
     - `big_question_guidance.tex/.pdf` gives question-type-specific solving actions, formula entrances, scoring points, and common mistakes.
     - `lecture_formula_pack.tex/.pdf` integrates handwritten prep notes into normalized formulas and lesson scripts, with local note snapshots as evidence.
   - For split objective-question solution books, maintain `all_choice_solution_books/`:
     - `mechanical_principles_choice_solution_book.tex/.pdf` covers upper-book objective questions.
     - `mechanical_design_choice_solution_book.tex/.pdf` covers lower-book objective questions.
     - `deduped_objective_questions.jsonl` records merged appearances, textbook PDF pages, quote anchors, and snippet paths.
     - Every formula card should include the formula, variable meanings, conceptual meaning, and the question types where it is used.

5. **Evaluate**
   - Use `scripts/evaluate_holdout.py` to create scoring templates.
   - Compare baseline answers produced without the distilled pack against answers produced with the distilled pack.
   - Report objective accuracy, calculation rubric score, drawing/diagnosis rubric coverage, citation quality, and contamination checks.

## References

- `references/answer_style.md`: polished Chinese answer format, LaTeX, diagrams, scoring points, and mistake diagnosis.
- `references/distillation_outputs.md`: artifact contracts for manifest, question bank, and course pack files.
- `references/evaluation.md`: baseline vs distilled evaluation protocol.
- `references/github_landscape.md`: related open-source project categories and how to use them as design references.
- `references/objective_solution_books.md`: chapter-grouped objective-question solution book method, including de-duplication, formula cards, textbook snippets, typography, and QA.
- `references/tju_mech_pilot.md`: defaults for the Tianjin University mechanical principles/design pilot.

## Script Notes

- Scripts use the Python standard library plus optional `pypdf` and `Pillow` when available.
- Visual scripts prefer Songti for Chinese, Times New Roman for Latin text, and STIX-style math fonts when available.
- `build_latex_review_notes.py` emits XeLaTeX sources. Compile with XeLaTeX; use Songti SC for Chinese, Times New Roman for Latin text, and STIX Two Math for formulas.
- `build_all_choice_solution_books.py` emits split XeLaTeX solution books for objective questions. Run it with the bundled Python environment when `pypdf` is not available in system Python.
- `render_choice_cards.py` uses OCR text positions to crop local textbook snippets; it prefers embedded PDF page images and falls back to `sips` rendering when needed.
- `make_review_deck.py` uses the bundled Presentations artifact-tool builder when available; if it is unavailable, keep the Markdown deck outline as the source of truth.
- If Poppler or OCR tools are unavailable, do not silently drop scanned pages. Mark them as visual/image-only sources in the manifest.
