# Holdout Evaluation Protocol

## Setup

1. Select holdout sets before distillation.
2. Run inventory and confirm holdout paths are labeled `holdout`.
3. Build the course pack only from non-holdout records.
4. Create a question bank and evaluation template.

## Baseline Vs Distilled

Baseline:

- Answer holdout questions using only the raw question text/image and general model knowledge.
- Do not load `distilled_course_pack/`.

Distilled:

- Answer the same holdout questions with access to `distilled_course_pack/`.
- Permit local source citations only from non-holdout distillation sources.

## Scoring

Objective questions:

- Exact answer accuracy.
- Short reason correctness.

Calculation questions:

- Correct method selection.
- Correct formula.
- Correct substitution and units.
- Numeric result.
- Result check or physical interpretation.

Drawing/diagnosis questions:

- Required visual entities identified.
- Correct directions/sign conventions.
- Correct numbered error labels or construction steps.
- Correct final corrected structure or diagram.
- Good grading rubric and common mistake diagnosis.

## Reporting

Report:

- Accuracy/score table by question type.
- Qualitative delta: what improved after distillation.
- Failure cases and missing source coverage.
- Contamination check: no holdout source path used in distilled pack.
