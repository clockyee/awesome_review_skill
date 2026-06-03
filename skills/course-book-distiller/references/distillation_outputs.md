# Distillation Output Contracts

## `manifest.jsonl`

One JSON object per source, page, slide, image, or note-archive media item.

Required fields:

- `record_id`: stable id.
- `path`: absolute file path.
- `relative_path`: path relative to the material root.
- `material_type`: e.g. `pdf_source`, `pdf_page`, `image`, `pptx_slide`, `note_image`, `note_audio`.
- `role`: `distill_source`, `answer_key`, or `holdout`.
- `topic_tags`: short tags inferred from path/text.
- `source_sha256`: file hash when available.

Useful optional fields:

- `page`, `slide`, `internal_path`
- `text_chars`, `text_sample`
- `image_count`, `image_dimensions`, `width`, `height`
- `file_size`, `page_count`, `zip_member_count`

## `question_bank.jsonl`

One object per candidate question or question-bearing source.

Required fields:

- `question_id`
- `type`: `objective`, `calculation`, `drawing`, `diagnosis`, or `short_answer`
- `source_path`
- `source_page` or `source_image`
- `holdout`: boolean
- `topic_tags`
- `answer_key`: null or short key reference
- `rubric`: list of scoring criteria

## `distilled_course_pack/`

Minimum files:

- `course_map.md`: topic hierarchy, source coverage, prerequisites, and learning path.
- `exam_taxonomy.md`: exam question types, scoring patterns, and likely traps.
- `formula_cards.md`: formulas and when to use them.
- `answer_templates.md`: student and teacher answer templates.
- `teacher_prep.md`: lesson plans, exercise selection, and exam-generation workflow.

Review deck outputs:

- `review_decks/<course>_review_outline.md`
- `review_decks/deck_spec.json`
- Optional PPTX generated from the deck spec.

## Contamination Guard

- Distillation outputs must not include holdout text or images.
- Holdout records can appear in `question_bank.jsonl` and evaluation templates.
- Evaluation prompts must state whether the model has access to the distilled pack.
