#!/usr/bin/env python3
"""Render vertical answer cards for multiple-choice course questions."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin, PdfImagePlugin  # noqa: F401
from pypdf import PdfReader, PdfWriter


FONT_CJK = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_LATIN_BOLD = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
FONT_MATH = "/System/Library/Fonts/Supplemental/STIXTwoMath.otf"

COLORS = {
    "paper": (248, 250, 252),
    "white": (255, 255, 255),
    "ink": (20, 24, 33),
    "muted": (83, 96, 116),
    "line": (209, 217, 226),
    "blue": (29, 78, 121),
    "green": (38, 127, 89),
    "orange": (220, 116, 43),
    "red": (190, 55, 49),
    "pale_blue": (238, 246, 253),
    "pale_green": (237, 249, 241),
    "pale_orange": (255, 247, 237),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Answer-card JSON.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--pdf-out", help="Optional PDF path.")
    parser.add_argument("--resolved-data-out", help="Write data with generated snippet paths.")
    parser.add_argument("--cards-per-page", type=int, default=1)
    return parser.parse_args()


class FontSet:
    def __init__(self) -> None:
        self.cjk: dict[int, ImageFont.FreeTypeFont] = {}
        self.latin: dict[int, ImageFont.FreeTypeFont] = {}
        self.latin_bold: dict[int, ImageFont.FreeTypeFont] = {}
        self.math: dict[int, ImageFont.FreeTypeFont] = {}

    def get(self, size: int, role: str = "cjk", bold: bool = False) -> ImageFont.FreeTypeFont:
        if role == "math":
            return self.math.setdefault(size, ImageFont.truetype(FONT_MATH, size=size))
        if role == "latin":
            store = self.latin_bold if bold else self.latin
            return store.setdefault(size, ImageFont.truetype(FONT_LATIN_BOLD if bold else FONT_LATIN, size=size))
        return self.cjk.setdefault(size, ImageFont.truetype(FONT_CJK, size=size))


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


def char_font(fonts: FontSet, ch: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if is_cjk(ch):
        return fonts.get(size, "cjk", bold)
    if is_math(ch):
        return fonts.get(size, "math", bold)
    return fonts.get(size, "latin", bold)


def text_width(draw: ImageDraw.ImageDraw, text: str, fonts: FontSet, size: int, bold: bool = False) -> int:
    width = 0
    for ch in text:
        box = draw.textbbox((0, 0), ch, font=char_font(fonts, ch, size, bold))
        width += box[2] - box[0]
    return width


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fonts: FontSet, size: int, max_width: int, bold: bool = False) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for ch in paragraph:
            candidate = current + ch
            if current and text_width(draw, candidate, fonts, size, bold) > max_width:
                lines.append(current)
                current = ch
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def draw_text(
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
    lines = wrap_text(draw, text, fonts, size, max_width, bold) if max_width else text.splitlines()
    line_h = int(size * 1.35)
    for line in lines:
        cx = x
        for ch in line:
            font = char_font(fonts, ch, size, bold)
            draw.text((cx, y), ch, font=font, fill=fill)
            box = draw.textbbox((0, 0), ch, font=font)
            cx += box[2] - box[0]
        y += line_h + line_gap
    return y


def find_citation_y(reader: PdfReader, page_index: int, search_terms: list[str]) -> float | None:
    hits: list[float] = []

    def visitor(text: str, cm: Any, tm: Any, font_dict: Any, font_size: float) -> None:
        if not text or not text.strip():
            return
        compact = " ".join(text.split())
        if any(term and term in compact for term in search_terms):
            hits.append(float(tm[5]))

    reader.pages[page_index].extract_text(visitor_text=visitor)
    return hits[0] if hits else None


def render_page_image(reader: PdfReader, page_index: int, tmp_dir: Path) -> Image.Image:
    page = reader.pages[page_index]
    try:
        if page.images:
            return page.images[0].image.convert("RGB")
    except Exception:
        pass

    single_pdf = tmp_dir / f"page_{page_index + 1}.pdf"
    out_png = tmp_dir / f"page_{page_index + 1}.png"
    writer = PdfWriter()
    writer.add_page(page)
    with single_pdf.open("wb") as handle:
        writer.write(handle)
    subprocess.run(["sips", "-s", "format", "png", str(single_pdf), "--out", str(out_png)], check=True, stdout=subprocess.DEVNULL)
    return Image.open(out_png).convert("RGB")


def make_snippet(citation: dict[str, Any], snippet_dir: Path, qno: int, citation_index: int) -> str:
    snippet_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = Path(citation["pdf_path"])
    page_no = int(citation["pdf_page"])
    reader = PdfReader(str(pdf_path))
    page_index = page_no - 1
    page = reader.pages[page_index]
    page_w = float(page.mediabox.width)
    page_h = float(page.mediabox.height)
    y = find_citation_y(reader, page_index, citation.get("search_terms") or [citation.get("quote_anchor", "")])

    with tempfile.TemporaryDirectory() as raw_tmp:
        page_image = render_page_image(reader, page_index, Path(raw_tmp))

    img_w, img_h = page_image.size
    scale_y = img_h / page_h
    y_px = int((page_h - (y if y is not None else page_h * 0.5)) * scale_y)
    crop_h = min(img_h, max(430, int(img_h * 0.17)))
    crop_top = max(0, min(img_h - crop_h, y_px - int(crop_h * 0.35)))
    crop_left = int(img_w * 0.06)
    crop_right = int(img_w * 0.94)
    snippet = page_image.crop((crop_left, crop_top, crop_right, crop_top + crop_h))
    target_w = 1450
    target_h = int(snippet.height * (target_w / snippet.width))
    snippet = snippet.resize((target_w, target_h), Image.Resampling.LANCZOS)

    out = snippet_dir / f"q{qno:02d}_citation_{citation_index:02d}_p{page_no}.png"
    snippet.save(out, quality=95)
    return str(out)


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, accent: tuple[int, int, int], fill: tuple[int, int, int], fonts: FontSet) -> int:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=20, fill=fill, outline=accent, width=3)
    draw.rounded_rectangle((x1, y1, x2, y1 + 58), radius=20, fill=accent, outline=accent)
    draw.rectangle((x1, y1 + 30, x2, y1 + 58), fill=accent)
    draw_text(draw, (x1 + 24, y1 + 10), title, fonts, 31, COLORS["white"], bold=True)
    return y1 + 84


def render_question_page(q: dict[str, Any], page_no: int, data: dict[str, Any], output_dir: Path, fonts: FontSet) -> Path:
    width, height = 1800, 2400
    image = Image.new("RGB", (width, height), COLORS["paper"])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 120), fill=COLORS["blue"])
    draw_text(draw, (70, 30), data.get("title", "选择题答案卡"), fonts, 42, COLORS["white"], bold=True)
    draw_text(draw, (width - 210, 38), f"Q{q['no']:02d}", fonts, 34, COLORS["white"], bold=True)

    margin = 70
    y = 158
    draw.rounded_rectangle((margin, y, width - margin, y + 320), radius=20, fill=COLORS["white"], outline=COLORS["line"], width=2)
    draw_text(draw, (margin + 28, y + 24), f"{q['no']:02d}. {q['stem']}", fonts, 36, COLORS["ink"], bold=True, max_width=width - margin * 2 - 56, line_gap=10)
    opt_y = y + 134
    for key, value in q["options"].items():
        opt_y = draw_text(draw, (margin + 42, opt_y), f"{key} {value}", fonts, 31, COLORS["muted"], max_width=width - margin * 2 - 84, line_gap=6)
    y += 348

    y0 = y
    content_y = panel(draw, (margin, y0, width - margin, y0 + 245), "答案", COLORS["green"], COLORS["pale_green"], fonts)
    draw_text(draw, (margin + 28, content_y), q["answer"], fonts, 42, COLORS["ink"], bold=True, max_width=width - margin * 2 - 56)
    y = y0 + 270

    y0 = y
    content_y = panel(draw, (margin, y0, width - margin, y0 + 330), "解析", COLORS["blue"], COLORS["pale_blue"], fonts)
    draw_text(draw, (margin + 28, content_y), q["analysis"], fonts, 31, COLORS["ink"], max_width=width - margin * 2 - 56, line_gap=8)
    y = y0 + 355

    citation = q["textbook_citations"][0]
    snippet_path = citation.get("snippet_image")
    y0 = y
    content_y = panel(draw, (margin, y0, width - margin, y0 + 520), "教材定位", COLORS["orange"], COLORS["pale_orange"], fonts)
    cite_line = (
        f"{citation['book']}，{citation['chapter']}，PDF p.{citation['pdf_page']}"
        f"（教材印刷页 {citation.get('print_page', '待核')}）"
    )
    content_y = draw_text(draw, (margin + 28, content_y), cite_line, fonts, 27, COLORS["ink"], bold=True, max_width=width - margin * 2 - 56)
    content_y = draw_text(draw, (margin + 28, content_y + 4), f"短原文锚点：{citation['quote_anchor']}", fonts, 26, COLORS["muted"], max_width=width - margin * 2 - 56)
    if snippet_path and Path(snippet_path).exists():
        snippet = Image.open(snippet_path).convert("RGB")
        max_w, max_h = width - margin * 2 - 56, 270
        ratio = min(max_w / snippet.width, max_h / snippet.height)
        snippet = snippet.resize((int(snippet.width * ratio), int(snippet.height * ratio)), Image.Resampling.LANCZOS)
        sx, sy = margin + 28, content_y + 14
        draw.rectangle((sx - 6, sy - 6, sx + snippet.width + 6, sy + snippet.height + 6), fill=COLORS["white"], outline=COLORS["line"], width=2)
        image.paste(snippet, (sx, sy))
    y = y0 + 545

    related = q.get("related_review_questions", [])
    y0 = y
    content_y = panel(draw, (margin, y0, width - margin, height - 100), "关联复习题", COLORS["red"], (255, 246, 246), fonts)
    for item in related[:2]:
        content_y = draw_text(draw, (margin + 28, content_y), f"题：{item['prompt']}", fonts, 28, COLORS["ink"], bold=True, max_width=width - margin * 2 - 56, line_gap=8)
        content_y = draw_text(draw, (margin + 28, content_y + 2), f"答：{item['answer']}（来源：{item['source']}）", fonts, 27, COLORS["muted"], max_width=width - margin * 2 - 56, line_gap=8)
        content_y += 10

    out = output_dir / f"choice_card_q{q['no']:02d}.png"
    image.save(out, quality=95)
    return out


def main() -> None:
    args = parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snippet_dir = output_dir / "textbook_snippets"

    for question in data["questions"]:
        for idx, citation in enumerate(question.get("textbook_citations", []), start=1):
            if not citation.get("snippet_image"):
                citation["snippet_image"] = make_snippet(citation, snippet_dir, int(question["no"]), idx)

    fonts = FontSet()
    outputs = [
        render_question_page(question, page_no, data, output_dir, fonts)
        for page_no, question in enumerate(data["questions"], start=1)
    ]

    if args.pdf_out:
        images = [Image.open(path).convert("RGB") for path in outputs]
        images[0].save(args.pdf_out, save_all=True, append_images=images[1:])
    if args.resolved_data_out:
        Path(args.resolved_data_out).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outputs": [str(path) for path in outputs], "pdf": args.pdf_out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
