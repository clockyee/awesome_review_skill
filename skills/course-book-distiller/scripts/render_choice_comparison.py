#!/usr/bin/env python3
"""Render per-question multiple-choice answer comparisons."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin, PdfImagePlugin  # noqa: F401


FONT_CJK = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_LATIN_BOLD = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
FONT_MATH = "/System/Library/Fonts/Supplemental/STIXTwoMath.otf"

COLORS = {
    "ink": (20, 24, 33),
    "muted": (91, 104, 124),
    "blue": (30, 76, 120),
    "red": (190, 55, 49),
    "green": (36, 125, 84),
    "orange": (230, 126, 50),
    "paper": (248, 250, 252),
    "line": (209, 217, 226),
    "white": (255, 255, 255),
    "pale_blue": (236, 244, 252),
    "pale_green": (235, 248, 239),
    "pale_red": (253, 240, 240),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Choice comparison data JSON.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--pdf-out", help="Optional PDF output.")
    parser.add_argument("--questions-per-page", type=int, default=5)
    return parser.parse_args()


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def is_cjk(ch: str) -> bool:
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x3000 <= code <= 0x303F
        or 0xFF00 <= code <= 0xFFEF
        or 0x2460 <= code <= 0x24FF
    )


def is_math(ch: str) -> bool:
    return ch in "σπβατψφθωε≤≥≈±×÷√∑∞°′″_{}[]()/=+-<>0123456789"


class FontSet:
    def __init__(self) -> None:
        self.cjk: dict[int, ImageFont.FreeTypeFont] = {}
        self.latin: dict[int, ImageFont.FreeTypeFont] = {}
        self.latin_bold: dict[int, ImageFont.FreeTypeFont] = {}
        self.math: dict[int, ImageFont.FreeTypeFont] = {}

    def get(self, size: int, role: str = "auto", bold: bool = False) -> ImageFont.FreeTypeFont:
        if role == "math":
            return self.math.setdefault(size, font(FONT_MATH, size))
        if role == "latin":
            store = self.latin_bold if bold else self.latin
            return store.setdefault(size, font(FONT_LATIN_BOLD if bold else FONT_LATIN, size))
        return self.cjk.setdefault(size, font(FONT_CJK, size))


def char_font(fonts: FontSet, ch: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if is_cjk(ch):
        return fonts.get(size, "cjk", bold)
    if is_math(ch):
        return fonts.get(size, "math", bold)
    return fonts.get(size, "latin", bold)


def text_width(draw: ImageDraw.ImageDraw, text: str, fonts: FontSet, size: int, bold: bool = False) -> int:
    width = 0
    for ch in text:
        fnt = char_font(fonts, ch, size, bold)
        box = draw.textbbox((0, 0), ch, font=fnt)
        width += box[2] - box[0]
    return width


def wrap_mixed(draw: ImageDraw.ImageDraw, text: str, fonts: FontSet, size: int, width: int) -> list[str]:
    lines: list[str] = []
    for para in text.splitlines():
        if not para:
            lines.append("")
            continue
        current = ""
        for ch in para:
            candidate = current + ch
            if current and text_width(draw, candidate, fonts, size) > width:
                lines.append(current)
                current = ch
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def draw_mixed(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fonts: FontSet,
    size: int,
    fill: tuple[int, int, int] = COLORS["ink"],
    bold: bool = False,
    max_width: int | None = None,
    line_gap: int = 8,
) -> int:
    x, y = xy
    lines = wrap_mixed(draw, text, fonts, size, max_width) if max_width else text.splitlines()
    line_h = int(size * 1.35)
    for line in lines:
        cx = x
        for ch in line:
            fnt = char_font(fonts, ch, size, bold)
            draw.text((cx, y), ch, font=fnt, fill=fill)
            box = draw.textbbox((0, 0), ch, font=fnt)
            cx += box[2] - box[0]
        y += line_h + line_gap
    return y


def rounded_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, color: tuple[int, int, int], fill: tuple[int, int, int], fonts: FontSet) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=color, width=3)
    draw.rounded_rectangle((x1, y1, x2, y1 + 46), radius=18, fill=color, outline=color)
    draw.rectangle((x1, y1 + 24, x2, y1 + 46), fill=color)
    draw_mixed(draw, (x1 + 18, y1 + 8), title, fonts, 23, COLORS["white"], bold=True)


def render_question(draw: ImageDraw.ImageDraw, q: dict[str, Any], box: tuple[int, int, int, int], fonts: FontSet) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=18, fill=COLORS["white"], outline=COLORS["line"], width=2)
    qno = q["no"]
    draw.rounded_rectangle((x1 + 18, y1 + 18, x1 + 78, y1 + 58), radius=12, fill=COLORS["blue"])
    draw_mixed(draw, (x1 + 31, y1 + 23), f"{qno:02d}", fonts, 22, COLORS["white"], bold=True)
    stem = q["stem"]
    opts = "  ".join(f"{key}.{value}" for key, value in q["options"].items())
    draw_mixed(draw, (x1 + 94, y1 + 19), stem, fonts, 24, COLORS["ink"], max_width=x2 - x1 - 120)
    draw_mixed(draw, (x1 + 94, y1 + 78), opts, fonts, 21, COLORS["muted"], max_width=x2 - x1 - 120)

    panel_y = y1 + 138
    gutter = 18
    col_w = (x2 - x1 - 36 - gutter * 2) // 3
    panels = [
        ("正确答案", q["correct"], COLORS["blue"], COLORS["pale_blue"]),
        ("非蒸馏答案", q["baseline"], COLORS["red"], COLORS["pale_red"]),
        ("蒸馏答案+解析", q["distilled"], COLORS["green"], COLORS["pale_green"]),
    ]
    for idx, (title, value, accent, fill) in enumerate(panels):
        px1 = x1 + 18 + idx * (col_w + gutter)
        px2 = px1 + col_w
        rounded_panel(draw, (px1, panel_y, px2, y2 - 18), title, accent, fill, fonts)
        if isinstance(value, dict):
            body = "\n".join(
                part
                for part in [
                    f"选择：{value.get('choice', '')}",
                    value.get("analysis", ""),
                    f"教材：{value.get('chapter', '')}",
                    f"原话锚点：{value.get('quote_anchor', '')}",
                    value.get("quote_note", ""),
                ]
                if part
            )
        else:
            body = str(value)
        draw_mixed(draw, (px1 + 18, panel_y + 62), body, fonts, 19, COLORS["ink"], max_width=col_w - 36, line_gap=5)


def render_page(page_questions: list[dict[str, Any]], page_no: int, spec: dict[str, Any], output_dir: Path, fonts: FontSet) -> Path:
    width, height = 2400, 3200
    image = Image.new("RGB", (width, height), COLORS["paper"])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 118), fill=COLORS["blue"])
    draw_mixed(draw, (72, 32), spec.get("title", "选择题逐题对比"), fonts, 36, COLORS["white"], bold=True)
    draw_mixed(draw, (width - 250, 40), f"Page {page_no}", fonts, 28, COLORS["white"], bold=True)
    subtitle = spec.get("subtitle", "")
    if subtitle:
        draw_mixed(draw, (72, 145), subtitle, fonts, 24, COLORS["muted"], max_width=width - 144)
    start_y = 210
    gap = 26
    qh = (height - start_y - 80 - gap * (len(page_questions) - 1)) // max(1, len(page_questions))
    for idx, question in enumerate(page_questions):
        y = start_y + idx * (qh + gap)
        render_question(draw, question, (72, y, width - 72, y + qh), fonts)
    out = output_dir / f"choice_comparison_p{page_no:02d}.png"
    image.save(out, quality=95)
    return out


def main() -> None:
    args = parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fonts = FontSet()
    questions = data["questions"]
    outputs: list[Path] = []
    for page_no, start in enumerate(range(0, len(questions), args.questions_per_page), start=1):
        outputs.append(render_page(questions[start : start + args.questions_per_page], page_no, data, output_dir, fonts))
    if args.pdf_out:
        images = [Image.open(path).convert("RGB") for path in outputs]
        images[0].save(args.pdf_out, save_all=True, append_images=images[1:])
    print(json.dumps({"outputs": [str(path) for path in outputs], "pdf": args.pdf_out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
