#!/usr/bin/env python3
"""Audit and optionally archive duplicated/old course materials."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


UPPER_OCR = "教材/机械原理与机械设计  上册 (OCR).pdf"
LOWER_OCR = "机原机设题目/机械原理与机械设计  下册  第3版_14572614(OCR).pdf"
OLD_TEXTBOOK_PATTERNS = [
    "教材/机械原理与机械设计上册.pdf",
    "教材/机械原理与机械设计  下册  第3版_14572614.pdf",
    "机原机设题目/机械原理与机械设计  下册  第3版_14572614.pdf",
]
PROTECTED_TOKENS = ["机原往年题", "往年题及复习题", "作业题答案 老师手写版"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Course material root.")
    parser.add_argument("--output-dir", required=True, help="Audit output directory.")
    parser.add_argument("--archive-root", help="Archive directory. Defaults to ROOT/_archive/duplicates_20260602.")
    parser.add_argument("--apply", action="store_true", help="Move archive candidates.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def group_for(rel: str) -> str:
    if rel.startswith("教材/") or "机械原理与机械设计" in rel:
        return "教材"
    if "往年题" in rel:
        return "往年题"
    if "习题" in rel or "题库" in rel or "答案" in rel:
        return "复习题库"
    if "课堂笔记" in rel or "笔记" in rel or rel.endswith(".note"):
        return "教学笔记"
    if "手写" in rel:
        return "手写答案"
    if rel.startswith("复习/"):
        return "课程讲义"
    return "其他"


def role_for(rel: str) -> str:
    if rel == UPPER_OCR:
        return "canonical_textbook_upper_ocr"
    if rel == LOWER_OCR:
        return "canonical_textbook_lower_ocr"
    if rel in OLD_TEXTBOOK_PATTERNS:
        return "archive_old_non_ocr_textbook"
    if rel.endswith(".md5") or "/.DS_Store" in rel or rel == ".DS_Store":
        return "archive_sidecar"
    return "keep"


def is_protected_source(rel: str) -> bool:
    suffix = Path(rel).suffix.lower()
    return suffix in {".png", ".jpg", ".jpeg", ".pdf", ".note"} and any(token in rel for token in PROTECTED_TOKENS)


def build_records(root: Path, archive_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "_archive" not in p.parts):
        rel = path.relative_to(root).as_posix()
        file_hash = sha256_file(path)
        record = {
            "path": str(path),
            "relative_path": rel,
            "sha256": file_hash,
            "size": path.stat().st_size,
            "group": group_for(rel),
            "role": role_for(rel),
        }
        records.append(record)
        by_hash[file_hash].append(record)

    archive_plan: list[dict[str, Any]] = []
    for record in records:
        if is_protected_source(record["relative_path"]):
            continue
        reason = ""
        if record["role"].startswith("archive_"):
            reason = record["role"]
        elif len(by_hash[record["sha256"]]) > 1:
            siblings = sorted(by_hash[record["sha256"]], key=lambda item: (0 if item["role"].startswith("canonical") else 1, item["relative_path"]))
            if record is not siblings[0]:
                reason = f"duplicate_of:{siblings[0]['relative_path']}"
        if not reason:
            continue
        target = archive_root / record["relative_path"]
        archive_plan.append(
            {
                "action": "move_to_archive",
                "source": record["path"],
                "target": str(target),
                "relative_path": record["relative_path"],
                "sha256": record["sha256"],
                "reason": reason,
            }
        )
    return records, archive_plan


def write_outputs(output_dir: Path, records: list[dict[str, Any]], archive_plan: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir.joinpath("curated_materials_manifest.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    output_dir.joinpath("archive_plan.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in archive_plan),
        encoding="utf-8",
    )

    keep = [r for r in records if not r["role"].startswith("archive_")]
    lines = [
        "# 机原机设素材审计",
        "",
        "## Canonical 教材",
        "",
        f"- 上册 OCR：`{UPPER_OCR}`",
        f"- 下册 OCR：`{LOWER_OCR}`",
        "",
        "## 统计",
        "",
        f"- 文件总数：{len(records)}",
        f"- 保留/索引文件：{len(keep)}",
        f"- 计划归档文件：{len(archive_plan)}",
        "",
        "## 归档候选",
        "",
    ]
    if archive_plan:
        for item in archive_plan:
            lines.append(f"- `{item['relative_path']}` -> `_archive/duplicates_20260602/`；原因：{item['reason']}")
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 分组命名",
            "",
            "- 教材：只把 OCR 教材作为 canonical 检索源。",
            "- 往年题：不移动 holdout 原题，只建立题型索引。",
            "- 复习题库：作为非 holdout 答案/练习来源。",
            "- 教学笔记：用于总结授课思路和复习课件。",
            "- 手写答案：作为视觉答案风格参考，不参与 holdout 蒸馏。",
        ]
    )
    output_dir.joinpath("materials_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_archive(archive_plan: list[dict[str, Any]]) -> None:
    for item in archive_plan:
        source = Path(item["source"])
        target = Path(item["target"])
        if not source.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(f"Archive target already exists: {target}")
        before = sha256_file(source)
        shutil.move(str(source), str(target))
        after = sha256_file(target)
        if before != after or before != item["sha256"]:
            raise RuntimeError(f"Hash mismatch after archiving {source}")


def main() -> None:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    archive_root = Path(args.archive_root).expanduser().resolve() if args.archive_root else root / "_archive" / "duplicates_20260602"
    records, archive_plan = build_records(root, archive_root)
    write_outputs(output_dir, records, archive_plan)
    if args.apply:
        apply_archive(archive_plan)
    print(json.dumps({"records": len(records), "archive_candidates": len(archive_plan), "applied": args.apply}, ensure_ascii=False))


if __name__ == "__main__":
    main()
