#!/usr/bin/env python3
"""Generate an editable PPTX review deck through the bundled artifact-tool builder."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_BUILDER = Path(
    "/Users/yizhang/.codex/plugins/cache/openai-primary-runtime/presentations/26.601.10930/"
    "skills/presentations/scripts/build_artifact_deck.mjs"
)
DEFAULT_NODE = Path("/Users/yizhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck-spec", required=True, help="Path to deck_spec.json.")
    parser.add_argument("--out", required=True, help="Output PPTX path.")
    parser.add_argument("--workspace", help="Workspace for generated slide modules/previews.")
    parser.add_argument("--builder", default=str(DEFAULT_BUILDER), help="Path to build_artifact_deck.mjs.")
    parser.add_argument("--node", default=str(DEFAULT_NODE), help="Node executable.")
    return parser.parse_args()


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def slide_module(index: int, title: str, bullets: list[str], deck_title: str) -> str:
    bullet_text = "\n".join(f"• {bullet}" for bullet in bullets)
    return f"""export async function slide{index:02d}(presentation, ctx) {{
  const slide = presentation.slides.add();
  ctx.addShape(slide, {{ x: 0, y: 0, w: 1280, h: 720, fill: "#F8FAFC", line: ctx.line("#F8FAFC", 0) }});
  ctx.addShape(slide, {{ x: 0, y: 0, w: 1280, h: 74, fill: "#1F4E79", line: ctx.line("#1F4E79", 0) }});
  ctx.addText(slide, {{ x: 54, y: 24, w: 520, h: 28, text: {js_string(deck_title)}, fontSize: 18, color: "#FFFFFF", bold: true }});
  ctx.addText(slide, {{ x: 54, y: 116, w: 940, h: 72, text: {js_string(title)}, fontSize: 42, color: "#111827", bold: true, face: ctx.fonts.title }});
  ctx.addShape(slide, {{ x: 54, y: 205, w: 92, h: 5, fill: "#C73E3A", line: ctx.line("#C73E3A", 0) }});
  ctx.addText(slide, {{ x: 90, y: 258, w: 1020, h: 330, text: {js_string(bullet_text)}, fontSize: 28, color: "#1F2937", insets: {{ left: 0, right: 0, top: 0, bottom: 0 }} }});
  ctx.addText(slide, {{ x: 1120, y: 642, w: 116, h: 30, text: {js_string(str(index).zfill(2))}, fontSize: 18, color: "#64748B", align: "right" }});
  return slide;
}}
"""


def write_slide_modules(spec: dict[str, Any], slides_dir: Path) -> None:
    slides_dir.mkdir(parents=True, exist_ok=True)
    deck_title = spec.get("title") or "Course Review"
    for index, slide in enumerate(spec.get("slides") or [], start=1):
        title = str(slide.get("title") or f"Slide {index}")
        bullets = [str(item) for item in (slide.get("bullets") or [])]
        slides_dir.joinpath(f"slide-{index:02d}.mjs").write_text(
            slide_module(index, title, bullets, deck_title),
            encoding="utf-8",
        )


def main() -> None:
    args = parse_args()
    deck_spec = Path(args.deck_spec).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    builder = Path(args.builder).expanduser().resolve()
    node = Path(args.node).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else out.parent / "artifact_workspace"

    spec = json.loads(deck_spec.read_text(encoding="utf-8"))
    slides = spec.get("slides") or []
    if not slides:
        raise SystemExit(f"No slides in deck spec: {deck_spec}")
    if not builder.exists():
        raise SystemExit(f"Artifact-tool builder not found: {builder}")
    if not node.exists() and shutil.which(str(node)) is None:
        raise SystemExit(f"Node executable not found: {node}")

    slides_dir = workspace / "slides"
    preview_dir = workspace / "preview"
    layout_dir = workspace / "layout"
    write_slide_modules(spec, slides_dir)

    command = [
        str(node),
        str(builder),
        "--slides-dir",
        str(slides_dir),
        "--out",
        str(out),
        "--preview-dir",
        str(preview_dir),
        "--workspace",
        str(workspace),
        "--layout-dir",
        str(layout_dir),
        "--manifest",
        str(workspace / "artifact-build-manifest.json"),
        "--slide-count",
        str(len(slides)),
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit("\n".join(part for part in [result.stdout, result.stderr] if part))
    print(result.stdout)


if __name__ == "__main__":
    main()
