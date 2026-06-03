# Objective Solution Books

Use this reference when generating chapter-grouped multiple-choice, fill-in, or judgment-question solution books from course exams and textbook citations.

## Output Goal

Produce two compact XeLaTeX solution books by textbook volume:

- `mechanical_principles_choice_solution_book.tex/.pdf` for upper-book mechanical principles topics.
- `mechanical_design_choice_solution_book.tex/.pdf` for lower-book mechanical design topics.

Each book should be a review handout, not an evaluation report. Do not show baseline or non-distilled answers in student-facing pages.

## Question Processing

1. Collect all observed objective questions from past papers and resolved card data.
2. Normalize duplicate or near-duplicate questions into one record when they test the same concept and answer. Track all appearances, such as paper name, question number, and source page.
3. Classify each record by course part, textbook chapter, and exam point. Use the cited textbook chapter as the primary grouping key; use the exam point only as a secondary heading.
4. Preserve the original question stem and options. Render the stem in bold.
5. For repeated questions, show `出现次数` and list source appearances instead of duplicating the full solution.

## Solution Card Contract

Each question card must include:

- **题干与选项**: original stem and options, with the stem bolded.
- **答案**: one clear answer key.
- **考点定位**: course part, chapter, PDF page, printed page when known, and a short quote anchor.
- **公式与意义**: formulas used by this question type. For every formula, explain variables, conceptual meaning, and when to use it.
- **解析**: concise reasoning tied to the textbook anchor. Keep copied source wording short.
- **教材截图**: a local crop around the cited phrase or figure, never a whole textbook page.
- **关联复习题**: one migration question testing the same concept with enough context to practice.
- **易错诊断**: one or more common traps, such as confusing related definitions, using the wrong parameter plane, or ignoring applicability conditions.

## Textbook Citation And Snippets

- Use the canonical OCR textbooks for search:
  - Upper book: `/Users/yizhang/paper/how2learn/学业辅导-机原机设/教材/机械原理与机械设计  上册 (OCR).pdf`
  - Lower book: `/Users/yizhang/paper/how2learn/学业辅导-机原机设/机原机设题目/机械原理与机械设计  下册  第3版_14572614(OCR).pdf`
- Search inside chapter page windows before falling back to whole-book search. Avoid table-of-contents, bibliography, and exercise-answer pages unless the question explicitly asks about them.
- Record `textbook_volume`, `chapter`, `pdf_page`, `printed_page` when available, `quote_anchor`, and `snippet_image`.
- Crop snippets around the matched phrase or figure. If text coordinates are unavailable, crop the most relevant local region after rendering the page image.
- If a citation cannot be found, mark the record for review instead of fabricating a page number.

## LaTeX And Visual Style

- Compile with XeLaTeX.
- Use Songti SC or an equivalent Song typeface for Chinese text, Times New Roman for Latin text, and STIX Two Math or a similar LaTeX-style math font.
- Keep layout compact but readable: 1-2 questions per page for dense sections, enough whitespace around snippets, and no three-column answer comparisons.
- Use chapter headers, small formula cards, shaded answer boxes, and consistent page footers.
- Avoid overlong quotes. Prefer short anchors plus page citations and snippets.

## QA Checklist

- Skill validation passes with `quick_validate.py`.
- Both `.tex` files compile to PDF without fatal errors.
- Every retained question has a chapter and PDF page.
- Every retained question has a snippet image that exists and opens.
- Render and inspect sample pages from the beginning, middle, and end of each PDF.
- Check staged files before committing; do not include `.aux`, `.log`, `.out`, `.toc`, `.xdv`, `.fls`, `.fdb_latexmk`, `.synctex.gz`, `qa_render*/`, or `__pycache__/`.
