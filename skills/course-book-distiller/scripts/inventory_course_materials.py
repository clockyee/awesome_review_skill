#!/usr/bin/env python3
"""Inventory course materials for holdout-safe distillation."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import mimetypes
import os
import warnings
from collections import Counter
from pathlib import Path
from typing import Any
from zipfile import ZipFile, is_zipfile
from xml.etree import ElementTree as ET

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

logging.getLogger("pypdf").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", module="pypdf")


DEFAULT_HOLDOUT_TOKENS = ["机原往年题b", "机原往年题g", "作业题答案 老师手写版"]
DEFAULT_EXCLUDE_TOKENS = ["系统辨识", "机器人建模和控制"]
ANSWER_TOKENS = ["答案", "answer", "解析", "solution", "key"]
TOPIC_KEYWORDS = {
    "机械原理": ["机械原理", "机原", "机构", "平面机构"],
    "机械设计": ["机械设计", "机设"],
    "齿轮": ["齿轮", "渐开线", "啮合", "蜗轮", "蜗杆"],
    "轴系": ["轴承", "轴.", "轴/", "轴系", "联轴器", "键"],
    "连接": ["螺纹", "螺栓", "键联接", "连接"],
    "带链传动": ["带传动", "链传动", "V带", "链轮"],
    "凸轮": ["凸轮"],
    "连杆": ["连杆", "四杆", "曲柄", "摇杆"],
    "力分析": ["力分析", "受力", "摩擦", "摩擦圆"],
    "运动分析": ["运动分析", "速度", "加速度", "解析法"],
    "疲劳强度": ["疲劳", "强度", "极限应力"],
    "滑动轴承": ["滑动轴承", "pv", "p值"],
    "复习题": ["复习", "往年题", "题库", "习题"],
    "辅导笔记": ["笔记", "备注", ".note"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Course material root directory.")
    parser.add_argument("--output-dir", required=True, help="Directory for manifest outputs.")
    parser.add_argument(
        "--holdout-token",
        action="append",
        default=[],
        help="Path token to mark as holdout. Can be repeated.",
    )
    parser.add_argument(
        "--exclude-token",
        action="append",
        default=[],
        help="Path token to exclude from v1. Can be repeated.",
    )
    parser.add_argument("--sample-limit", type=int, default=0, help="Only process first N files.")
    parser.add_argument("--max-pdf-pages", type=int, default=0, help="Only inspect first N pages per PDF.")
    parser.add_argument("--no-default-holdouts", action="store_true", help="Disable default holdout tokens.")
    parser.add_argument("--no-default-excludes", action="store_true", help="Disable default exclude tokens.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(*parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def clean_text(text: str, limit: int = 240) -> str:
    return " ".join(text.split())[:limit]


def infer_tags(path: Path, text: str = "") -> list[str]:
    haystack = f"{path.as_posix()} {text}"
    tags = [tag for tag, keys in TOPIC_KEYWORDS.items() if any(key in haystack for key in keys)]
    return sorted(set(tags))


def infer_role(relative_path: str, holdout_tokens: list[str]) -> str:
    lower = relative_path.lower()
    if any(token in relative_path for token in holdout_tokens):
        return "holdout"
    if any(token in relative_path for token in ANSWER_TOKENS) or any(token in lower for token in ANSWER_TOKENS):
        return "answer_key"
    return "distill_source"


def should_exclude(relative_path: str, exclude_tokens: list[str]) -> bool:
    return any(token in relative_path for token in exclude_tokens)


def base_record(root: Path, path: Path, material_type: str, role: str, source_hash: str) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    stat = path.stat()
    return {
        "record_id": stable_id(rel, material_type, "source"),
        "path": str(path),
        "relative_path": rel,
        "material_type": material_type,
        "role": role,
        "topic_tags": infer_tags(Path(rel)),
        "source_sha256": source_hash,
        "file_size": stat.st_size,
        "mtime": int(stat.st_mtime),
    }


def count_page_images(page: Any) -> tuple[int, list[str]]:
    resources = page.get("/Resources", {}) or {}
    xobjects = resources.get("/XObject", {}) or {}
    count = 0
    dimensions: list[str] = []
    for obj in xobjects.values():
        try:
            resolved = obj.get_object()
            if resolved.get("/Subtype") == "/Image":
                count += 1
                dimensions.append(f"{resolved.get('/Width')}x{resolved.get('/Height')}")
        except Exception:
            continue
    return count, dimensions


def inventory_pdf(root: Path, path: Path, role: str, source_hash: str, max_pages: int) -> list[dict[str, Any]]:
    records = [base_record(root, path, "pdf_source", role, source_hash)]
    if PdfReader is None:
        records[0]["error"] = "pypdf unavailable"
        return records
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        records[0]["error"] = f"pdf_read_error: {type(exc).__name__}: {exc}"
        return records

    page_count = len(reader.pages)
    records[0]["page_count"] = page_count
    pages = reader.pages[: max_pages or page_count]
    page_text_counts: list[int] = []
    for index, page in enumerate(pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        image_count, image_dimensions = count_page_images(page)
        text_chars = len(text.strip())
        page_text_counts.append(text_chars)
        rel = path.relative_to(root).as_posix()
        page_kind = "text_pdf_page" if text_chars >= 80 else "visual_pdf_page"
        if text_chars >= 80 and image_count:
            page_kind = "mixed_pdf_page"
        records.append(
            {
                "record_id": stable_id(rel, "page", index),
                "path": str(path),
                "relative_path": rel,
                "material_type": "pdf_page",
                "page_kind": page_kind,
                "role": role,
                "topic_tags": infer_tags(Path(rel), text),
                "source_sha256": source_hash,
                "page": index,
                "page_count": page_count,
                "text_chars": text_chars,
                "text_sample": clean_text(text),
                "image_count": image_count,
                "image_dimensions": image_dimensions[:8],
            }
        )
    records[0]["first_pages_text_chars"] = page_text_counts[:5]
    records[0]["inspected_pages"] = len(pages)
    return records


def inventory_image(root: Path, path: Path, role: str, source_hash: str) -> list[dict[str, Any]]:
    record = base_record(root, path, "image", role, source_hash)
    if Image is not None:
        try:
            with Image.open(path) as image:
                record["width"], record["height"] = image.size
                record["mode"] = image.mode
        except Exception as exc:
            record["error"] = f"image_read_error: {type(exc).__name__}: {exc}"
    else:
        record["error"] = "Pillow unavailable"
    return [record]


def inventory_pptx(root: Path, path: Path, role: str, source_hash: str) -> list[dict[str, Any]]:
    records = [base_record(root, path, "pptx_source", role, source_hash)]
    try:
        with ZipFile(path) as archive:
            slide_names = sorted(
                [name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")],
                key=lambda name: int(name.rsplit("slide", 1)[1].split(".xml")[0]),
            )
            records[0]["slide_count"] = len(slide_names)
            for slide_index, name in enumerate(slide_names, start=1):
                xml = ET.fromstring(archive.read(name))
                texts = [
                    el.text.strip()
                    for el in xml.iter()
                    if el.tag.endswith("}t") and el.text and el.text.strip()
                ]
                text = " | ".join(texts)
                rel = path.relative_to(root).as_posix()
                records.append(
                    {
                        "record_id": stable_id(rel, "slide", slide_index),
                        "path": str(path),
                        "relative_path": rel,
                        "material_type": "pptx_slide",
                        "role": role,
                        "topic_tags": infer_tags(Path(rel), text),
                        "source_sha256": source_hash,
                        "slide": slide_index,
                        "slide_count": len(slide_names),
                        "text_chars": len(text),
                        "text_sample": clean_text(text),
                    }
                )
    except Exception as exc:
        records[0]["error"] = f"pptx_read_error: {type(exc).__name__}: {exc}"
    return records


def inventory_note(root: Path, path: Path, role: str, source_hash: str) -> list[dict[str, Any]]:
    records = [base_record(root, path, "note_source", role, source_hash)]
    try:
        with ZipFile(path) as archive:
            names = archive.namelist()
            records[0]["zip_member_count"] = len(names)
            for name in names:
                if name.endswith("/"):
                    continue
                lower = name.lower()
                if "/images/" in lower and lower.endswith((".jpg", ".jpeg", ".png")):
                    material_type = "note_image"
                elif "/recordings/" in lower and lower.endswith((".m4a", ".mp3", ".wav")):
                    material_type = "note_audio"
                elif lower.endswith((".plist", ".xml")):
                    material_type = "note_metadata"
                elif "thumb" in lower and lower.endswith(".png"):
                    material_type = "note_thumbnail"
                else:
                    continue
                rel = path.relative_to(root).as_posix()
                info = archive.getinfo(name)
                records.append(
                    {
                        "record_id": stable_id(rel, "note", name),
                        "path": str(path),
                        "relative_path": rel,
                        "material_type": material_type,
                        "role": role,
                        "topic_tags": infer_tags(Path(rel + "/" + name)),
                        "source_sha256": source_hash,
                        "internal_path": name,
                        "file_size": info.file_size,
                    }
                )
    except Exception as exc:
        records[0]["error"] = f"note_read_error: {type(exc).__name__}: {exc}"
    return records


def inventory_zip(root: Path, path: Path, role: str, source_hash: str) -> list[dict[str, Any]]:
    record = base_record(root, path, "zip_source", role, source_hash)
    try:
        with ZipFile(path) as archive:
            record["zip_member_count"] = len(archive.namelist())
    except Exception as exc:
        record["error"] = f"zip_read_error: {type(exc).__name__}: {exc}"
    return [record]


def inventory_generic(root: Path, path: Path, role: str, source_hash: str) -> list[dict[str, Any]]:
    record = base_record(root, path, "file", role, source_hash)
    record["mime_type"] = mimetypes.guess_type(path.name)[0]
    return [record]


def inventory_path(root: Path, path: Path, role: str, max_pdf_pages: int) -> list[dict[str, Any]]:
    source_hash = sha256_file(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return inventory_pdf(root, path, role, source_hash, max_pdf_pages)
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}:
        return inventory_image(root, path, role, source_hash)
    if suffix == ".pptx":
        return inventory_pptx(root, path, role, source_hash)
    if suffix == ".note" and is_zipfile(path):
        return inventory_note(root, path, role, source_hash)
    if suffix == ".zip" and is_zipfile(path):
        return inventory_zip(root, path, role, source_hash)
    return inventory_generic(root, path, role, source_hash)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_summary(
    output_dir: Path,
    root: Path,
    records: list[dict[str, Any]],
    excluded: list[str],
    holdout_tokens: list[str],
    exclude_tokens: list[str],
) -> None:
    by_type = Counter(record["material_type"] for record in records)
    by_role = Counter(record["role"] for record in records)
    holdout_paths = sorted({record["relative_path"] for record in records if record["role"] == "holdout"})
    visual_pages = [
        record
        for record in records
        if record.get("page_kind") == "visual_pdf_page" or record["material_type"] in {"image", "note_image"}
    ]
    lines = [
        "# Inventory Summary",
        "",
        f"- Root: `{root}`",
        f"- Records: {len(records)}",
        f"- Holdout tokens: {', '.join(holdout_tokens) or '(none)'}",
        f"- Exclude tokens: {', '.join(exclude_tokens) or '(none)'}",
        "",
        "## By Role",
        "",
    ]
    lines.extend(f"- {role}: {count}" for role, count in sorted(by_role.items()))
    lines.extend(["", "## By Material Type", ""])
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(by_type.items()))
    lines.extend(["", "## Holdout Sources", ""])
    lines.extend(f"- `{path}`" for path in holdout_paths[:200])
    if len(holdout_paths) > 200:
        lines.append(f"- ... {len(holdout_paths) - 200} more")
    lines.extend(["", "## Visual Sources Requiring OCR/Vision", ""])
    for record in visual_pages[:80]:
        page = f" p.{record['page']}" if "page" in record else ""
        internal = f" :: {record['internal_path']}" if "internal_path" in record else ""
        lines.append(f"- `{record['relative_path']}`{page}{internal}")
    if len(visual_pages) > 80:
        lines.append(f"- ... {len(visual_pages) - 80} more")
    lines.extend(["", "## Excluded V1 Sources", ""])
    lines.extend(f"- `{path}`" for path in excluded)
    output_dir.joinpath("inventory_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    holdout_tokens = ([] if args.no_default_holdouts else DEFAULT_HOLDOUT_TOKENS) + args.holdout_token
    exclude_tokens = ([] if args.no_default_excludes else DEFAULT_EXCLUDE_TOKENS) + args.exclude_token

    files = [path for path in root.rglob("*") if path.is_file() and path.name != ".DS_Store"]
    files.sort(key=lambda item: item.relative_to(root).as_posix())
    if args.sample_limit:
        files = files[: args.sample_limit]

    records: list[dict[str, Any]] = []
    excluded: list[str] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        if should_exclude(rel, exclude_tokens):
            excluded.append(rel)
            continue
        if path.suffix.lower() == ".md5":
            continue
        role = infer_role(rel, holdout_tokens)
        try:
            records.extend(inventory_path(root, path, role, args.max_pdf_pages))
        except Exception as exc:
            records.append(
                {
                    "record_id": stable_id(rel, "error"),
                    "path": str(path),
                    "relative_path": rel,
                    "material_type": "file",
                    "role": role,
                    "topic_tags": infer_tags(Path(rel)),
                    "error": f"inventory_error: {type(exc).__name__}: {exc}",
                }
            )

    write_jsonl(output_dir / "manifest.jsonl", records)
    write_summary(output_dir, root, records, excluded, holdout_tokens, exclude_tokens)
    print(
        json.dumps(
            {
                "root": str(root),
                "output_dir": str(output_dir),
                "records": len(records),
                "roles": Counter(record["role"] for record in records),
                "material_types": Counter(record["material_type"] for record in records),
                "excluded": len(excluded),
            },
            ensure_ascii=False,
            default=dict,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
