#!/usr/bin/env python3
"""Create or score holdout evaluation templates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question-bank", required=True, help="Path to question_bank.jsonl.")
    parser.add_argument("--output-dir", required=True, help="Evaluation output directory.")
    parser.add_argument("--baseline", help="Optional baseline answer JSONL.")
    parser.add_argument("--distilled", help="Optional distilled answer JSONL.")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def criteria_for(question_type: str) -> list[dict[str, Any]]:
    tables = {
        "objective": [
            ("answer_exact", 2, "答案选项或填空结果正确"),
            ("reason", 1, "理由对应概念/公式"),
        ],
        "calculation": [
            ("method", 2, "方法选择正确"),
            ("formula", 2, "公式和适用条件正确"),
            ("substitution_units", 2, "代入、单位和方向正确"),
            ("result_check", 2, "结果、校核或物理意义正确"),
        ],
        "drawing": [
            ("visual_entities", 2, "关键点/线/圆/方向标注完整"),
            ("construction", 2, "构造或作图步骤正确"),
            ("calculation_link", 1, "图与计算结论一致"),
            ("rubric_mistakes", 1, "给出得分点和易错诊断"),
        ],
        "diagnosis": [
            ("numbered_errors", 2, "错误编号清晰"),
            ("causes", 2, "原因解释正确"),
            ("fixes", 2, "修改建议或正确结构可执行"),
            ("grading", 1, "评分点覆盖关键错误"),
        ],
        "short_answer": [
            ("concept", 2, "概念准确"),
            ("conditions", 1, "适用条件完整"),
            ("expression", 1, "表达清楚简洁"),
        ],
    }
    return [
        {"criterion": name, "points": points, "description": description}
        for name, points, description in tables.get(question_type, tables["short_answer"])
    ]


def create_template(holdouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    template: list[dict[str, Any]] = []
    for item in holdouts:
        template.append(
            {
                "question_id": item["question_id"],
                "type": item["type"],
                "source_relative_path": item.get("source_relative_path"),
                "source_page": item.get("source_page"),
                "source_image": item.get("source_image"),
                "topic_tags": item.get("topic_tags") or [],
                "criteria": criteria_for(item["type"]),
                "baseline_score": None,
                "distilled_score": None,
                "baseline_notes": "",
                "distilled_notes": "",
                "contamination_notes": "",
            }
        )
    return template


def answers_by_id(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    return {record["question_id"]: record for record in read_jsonl(Path(path).expanduser().resolve())}


def score_if_available(
    template: list[dict[str, Any]],
    baseline_answers: dict[str, dict[str, Any]],
    distilled_answers: dict[str, dict[str, Any]],
) -> None:
    for row in template:
        qid = row["question_id"]
        for label, answers in [("baseline", baseline_answers), ("distilled", distilled_answers)]:
            answer = answers.get(qid)
            if not answer:
                continue
            row[f"{label}_answer_path"] = answer.get("answer_path")
            row[f"{label}_score"] = answer.get("score")
            row[f"{label}_notes"] = answer.get("notes", "")


def write_protocol(output_dir: Path, holdouts: list[dict[str, Any]], template: list[dict[str, Any]]) -> None:
    by_type = Counter(item["type"] for item in holdouts)
    max_points = sum(sum(criteria["points"] for criteria in row["criteria"]) for row in template)
    lines = [
        "# Holdout Evaluation Protocol",
        "",
        "## Purpose",
        "",
        "Compare answers produced before loading the distilled course pack with answers produced after loading it.",
        "",
        "## Holdout Set",
        "",
        f"- Questions/sources: {len(holdouts)}",
        f"- Max rubric points: {max_points}",
        "",
        "## By Type",
        "",
    ]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(by_type.items()))
    lines.extend(
        [
            "",
            "## Baseline Prompt",
            "",
            "Answer the holdout question using only the question text/image and general knowledge. Do not read the distilled course pack.",
            "",
            "## Distilled Prompt",
            "",
            "Answer the same holdout question after reading `distilled_course_pack/`. Cite only non-holdout local sources.",
            "",
            "## Contamination Check",
            "",
            "- Search distilled answers for holdout file paths.",
            "- Reject any answer that quotes or cites holdout material beyond the prompt question itself.",
        ]
    )
    output_dir.joinpath("evaluation_protocol.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_comparison(output_dir: Path, template: list[dict[str, Any]]) -> None:
    rows_with_scores = [row for row in template if row.get("baseline_score") is not None or row.get("distilled_score") is not None]
    baseline_total = sum(row.get("baseline_score") or 0 for row in rows_with_scores)
    distilled_total = sum(row.get("distilled_score") or 0 for row in rows_with_scores)
    lines = [
        "# Baseline Vs Distilled Comparison",
        "",
        f"- Scored rows: {len(rows_with_scores)}",
        f"- Baseline total: {baseline_total}",
        f"- Distilled total: {distilled_total}",
        f"- Delta: {distilled_total - baseline_total}",
        "",
        "## Notes",
        "",
        "Populate `baseline_score` and `distilled_score` in `holdout_score_template.jsonl`, or pass answer JSONL files with scores.",
    ]
    output_dir.joinpath("comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    question_bank = read_jsonl(Path(args.question_bank).expanduser().resolve())
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    holdouts = [item for item in question_bank if item.get("holdout")]
    template = create_template(holdouts)
    score_if_available(template, answers_by_id(args.baseline), answers_by_id(args.distilled))
    write_jsonl(output_dir / "holdout_score_template.jsonl", template)
    write_protocol(output_dir, holdouts, template)
    write_comparison(output_dir, template)

    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "holdout_items": len(holdouts),
                "template": str(output_dir / "holdout_score_template.jsonl"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
