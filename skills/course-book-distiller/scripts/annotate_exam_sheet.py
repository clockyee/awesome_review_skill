#!/usr/bin/env python3
"""Annotate exam-sheet images with visual answer panels and callouts."""

from __future__ import annotations

import argparse
import json
import math
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin, PdfImagePlugin  # noqa: F401


DEFAULT_FONTS = [
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]
FONT_CJK = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
FONT_LATIN_BOLD = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
FONT_MATH = "/System/Library/Fonts/Supplemental/STIXTwoMath.otf"

PALETTE = {
    "blue": (31, 78, 121),
    "red": (199, 62, 58),
    "orange": (234, 126, 56),
    "green": (45, 128, 91),
    "ink": (17, 24, 39),
    "muted": (100, 116, 139),
    "paper": (248, 250, 252),
    "yellow": (255, 236, 153),
    "white": (255, 255, 255),
}

FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="JSON annotation spec.")
    parser.add_argument("--output-dir", required=True, help="Output image directory.")
    parser.add_argument("--pdf-out", help="Optional multi-page PDF output.")
    parser.add_argument("--font", help="Optional TrueType/OpenType font path.")
    return parser.parse_args()


def color(value: str | list[int] | tuple[int, ...], alpha: int | None = None) -> tuple[int, ...]:
    if isinstance(value, str):
        rgb = PALETTE.get(value, PALETTE["ink"])
    else:
        rgb = tuple(value[:3])  # type: ignore[assignment]
    if alpha is None:
        return rgb
    return (*rgb, alpha)


def find_font(preferred: str | None = None) -> str | None:
    candidates = [preferred] if preferred else []
    candidates.extend(DEFAULT_FONTS)
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def load_font(font_path: str | None, size: int) -> ImageFont.ImageFont:
    if font_path:
        return ImageFont.truetype(font_path, size=size)
    return ImageFont.load_default()


def role_font(size: int, role: str = "cjk", bold: bool = False) -> ImageFont.FreeTypeFont:
    if role == "math" and Path(FONT_MATH).exists():
        path = FONT_MATH
    elif role == "latin" and Path(FONT_LATIN).exists():
        path = FONT_LATIN_BOLD if bold and Path(FONT_LATIN_BOLD).exists() else FONT_LATIN
    else:
        path = FONT_CJK if Path(FONT_CJK).exists() else find_font()
    if not path:
        raise RuntimeError("No usable font found.")
    key = (path, size)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = ImageFont.truetype(path, size=size)
    return FONT_CACHE[key]


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


def mixed_font(ch: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if is_cjk(ch):
        return role_font(size, "cjk", bold)
    if is_math(ch):
        return role_font(size, "math", bold)
    return role_font(size, "latin", bold)


def mixed_text_width(draw: ImageDraw.ImageDraw, text: str, size: int, bold: bool = False) -> int:
    total = 0
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=mixed_font(ch, size, bold))
        total += bbox[2] - bbox[0]
    return total


def wrap_mixed_text(draw: ImageDraw.ImageDraw, text: str, size: int, max_width: int, bold: bool = False) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for ch in paragraph:
            candidate = current + ch
            if current and mixed_text_width(draw, candidate, size, bold) > max_width:
                lines.append(current)
                current = ch
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def draw_mixed_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    fill: tuple[int, ...],
    max_width: int | None = None,
    line_spacing: int = 8,
    bold: bool = False,
) -> int:
    x, y = xy
    lines = wrap_mixed_text(draw, text, size, max_width, bold) if max_width else text.splitlines()
    line_h = int(size * 1.35)
    for line in lines:
        cx = x
        for ch in line:
            font = mixed_font(ch, size, bold)
            draw.text((cx, y), ch, font=font, fill=fill)
            bbox = draw.textbbox((0, 0), ch, font=font)
            cx += bbox[2] - bbox[0]
        y += line_h + line_spacing
    return y


def pt(value: list[float] | tuple[float, float], origin: tuple[int, int], size: tuple[int, int]) -> tuple[int, int]:
    x, y = value
    ox, oy = origin
    width, height = size
    if abs(x) <= 1 and abs(y) <= 1:
        return int(ox + x * width), int(oy + y * height)
    return int(ox + x), int(oy + y)


def rect(
    value: list[float],
    origin: tuple[int, int],
    size: tuple[int, int],
) -> tuple[int, int, int, int]:
    x, y, w, h = value
    ox, oy = origin
    width, height = size
    if all(abs(v) <= 1 for v in value):
        return int(ox + x * width), int(oy + y * height), int(ox + (x + w) * width), int(oy + (y + h) * height)
    return int(ox + x), int(oy + y), int(ox + x + w), int(oy + y + h)


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: tuple[int, ...], width: int = 4) -> None:
    draw.line([start, end], fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 18 + width
    spread = math.pi / 7
    points = [end]
    for sign in [1, -1]:
        theta = angle + math.pi + sign * spread
        points.append((int(end[0] + length * math.cos(theta)), int(end[1] + length * math.sin(theta))))
    draw.polygon(points, fill=fill)


def wrap_text(text: str, max_chars: int) -> str:
    def hard_wrap(chunk: str) -> list[str]:
        if len(chunk) <= max_chars:
            return [chunk]
        return [chunk[i : i + max_chars] for i in range(0, len(chunk), max_chars)]

    lines: list[str] = []
    for raw in text.splitlines():
        if not raw:
            lines.append("")
            continue
        if raw.startswith("- ") or raw.startswith("• "):
            prefix = raw[:2]
            body = raw[2:]
            chunks = textwrap.wrap(body, width=max_chars, break_long_words=False, replace_whitespace=False)
            if not chunks:
                lines.append(raw)
            else:
                first = True
                for chunk in chunks:
                    for part in hard_wrap(chunk):
                        lines.append((prefix if first else "  ") + part)
                        first = False
        else:
            chunks = textwrap.wrap(raw, width=max_chars, break_long_words=False, replace_whitespace=False) or [raw]
            for chunk in chunks:
                lines.extend(hard_wrap(chunk))
    return "\n".join(lines)


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, ...],
    line_spacing: int = 8,
) -> None:
    x1, y1, x2, _ = box
    if hasattr(font, "size"):
        draw_mixed_text(draw, (x1, y1), text, int(font.size), fill, max_width=x2 - x1, line_spacing=line_spacing)
        return
    avg_char = 18
    max_chars = max(8, (x2 - x1) // avg_char)
    wrapped = wrap_text(text, max_chars)
    draw.multiline_text((x1, y1), wrapped, font=font, fill=fill, spacing=line_spacing)


def draw_text_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    text: str,
    font_path: str | None,
    accent: str = "blue",
    fill_name: str = "white",
    title_size: int = 28,
    body_size: int = 23,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=16, fill=color(fill_name), outline=color(accent), width=3)
    if title:
        title_font = load_font(font_path, title_size)
        draw.rounded_rectangle((x1, y1, x2, y1 + 46), radius=16, fill=color(accent), outline=color(accent), width=0)
        draw.rectangle((x1, y1 + 25, x2, y1 + 46), fill=color(accent))
        draw_mixed_text(draw, (x1 + 18, y1 + 8), title, title_size, color("white"), max_width=x2 - x1 - 36, bold=True)
        content_top = y1 + 60
    else:
        content_top = y1 + 18
    body_font = load_font(font_path, body_size)
    draw_multiline(draw, (x1 + 18, content_top, x2 - 18, y2 - 12), text, body_font, color("ink"))


def draw_badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, font_path: str | None, fill_name: str = "red") -> None:
    font = load_font(font_path, 24)
    x, y = xy
    radius = 19
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color(fill_name), outline=color("white"), width=3)
    bbox = draw.textbbox((0, 0), label, font=font)
    draw.text((x - (bbox[2] - bbox[0]) / 2, y - (bbox[3] - bbox[1]) / 2 - 2), label, font=font, fill=color("white"))


def draw_annotation(
    draw: ImageDraw.ImageDraw,
    annotation: dict[str, Any],
    font_path: str | None,
    source_size: tuple[int, int],
    margin_origin: tuple[int, int],
    margin_size: tuple[int, int],
) -> None:
    target = annotation.get("target", "source")
    origin = margin_origin if target == "margin" else (0, 0)
    size = margin_size if target == "margin" else source_size
    kind = annotation["type"]
    if kind == "highlight":
        box = rect(annotation["box"], origin, size)
        draw.rounded_rectangle(box, radius=10, outline=color(annotation.get("outline", "red")), width=5)
    elif kind == "box":
        draw.rounded_rectangle(rect(annotation["box"], origin, size), radius=12, outline=color(annotation.get("outline", "red")), width=5)
    elif kind == "badge":
        draw_badge(draw, pt(annotation["xy"], origin, size), annotation["label"], font_path, annotation.get("fill", "red"))
    elif kind == "arrow":
        start_target = annotation.get("start_target", target)
        end_target = annotation.get("end_target", "source")
        start_origin = margin_origin if start_target == "margin" else (0, 0)
        start_size = margin_size if start_target == "margin" else source_size
        end_origin = margin_origin if end_target == "margin" else (0, 0)
        end_size = margin_size if end_target == "margin" else source_size
        draw_arrow(
            draw,
            pt(annotation["start"], start_origin, start_size),
            pt(annotation["end"], end_origin, end_size),
            color(annotation.get("color", "red")),
            int(annotation.get("width", 4)),
        )
    elif kind == "line":
        start_target = annotation.get("start_target", target)
        end_target = annotation.get("end_target", target)
        start_origin = margin_origin if start_target == "margin" else (0, 0)
        start_size = margin_size if start_target == "margin" else source_size
        end_origin = margin_origin if end_target == "margin" else (0, 0)
        end_size = margin_size if end_target == "margin" else source_size
        draw.line(
            [
                pt(annotation["start"], start_origin, start_size),
                pt(annotation["end"], end_origin, end_size),
            ],
            fill=color(annotation.get("color", "red")),
            width=int(annotation.get("width", 4)),
        )
    elif kind == "dot":
        xy = pt(annotation["xy"], origin, size)
        radius = int(annotation.get("radius", 10))
        draw.ellipse(
            (xy[0] - radius, xy[1] - radius, xy[0] + radius, xy[1] + radius),
            fill=color(annotation.get("fill", "red")),
            outline=color(annotation.get("outline", "white")),
            width=int(annotation.get("width", 3)),
        )
    elif kind == "text":
        text_size = int(annotation.get("size", 26))
        text_font = load_font(font_path, text_size)
        xy = pt(annotation["xy"], origin, size)
        if annotation.get("box", False):
            bbox = draw.textbbox((0, 0), annotation.get("text", ""), font=text_font)
            pad = int(annotation.get("pad", 8))
            draw.rounded_rectangle(
                (xy[0] - pad, xy[1] - pad, xy[0] + bbox[2] - bbox[0] + pad, xy[1] + bbox[3] - bbox[1] + pad),
                radius=8,
                fill=color(annotation.get("box_fill", "white"), int(annotation.get("box_alpha", 235))),
                outline=color(annotation.get("outline", "red")),
                width=int(annotation.get("width", 2)),
            )
        draw_mixed_text(draw, xy, annotation.get("text", ""), text_size, color(annotation.get("fill", "red")))
    elif kind == "text_box":
        draw_text_box(
            draw,
            rect(annotation["box"], origin, size),
            annotation.get("title", ""),
            annotation.get("text", ""),
            font_path,
            annotation.get("accent", "blue"),
            annotation.get("fill", "white"),
            int(annotation.get("title_size", 28)),
            int(annotation.get("body_size", 23)),
        )
    else:
        raise ValueError(f"Unknown annotation type: {kind}")


def render_page(page: dict[str, Any], output_dir: Path, font_path: str | None) -> Path:
    source = Path(page["source"]).expanduser().resolve()
    image = Image.open(source).convert("RGBA")
    source_w, source_h = image.size
    margin_right = int(page.get("margin_right", 560))
    pad = int(page.get("pad", 24))
    canvas = Image.new("RGBA", (source_w + margin_right, source_h), color("paper"))
    canvas.alpha_composite(image, (0, 0))
    draw = ImageDraw.Draw(canvas)
    margin_origin = (source_w + pad, pad)
    margin_size = (margin_right - pad * 2, source_h - pad * 2)
    draw.rounded_rectangle(
        (source_w + 10, 10, source_w + margin_right - 10, source_h - 10),
        radius=18,
        fill=(255, 255, 255, 245),
        outline=color("blue"),
        width=3,
    )
    title = page.get("title", source.name)
    draw.text((source_w + pad, 28), title, font=load_font(font_path, 34), fill=color("blue"))
    draw.line((source_w + pad, 76, source_w + margin_right - pad, 76), fill=color("red"), width=5)
    for annotation in page.get("annotations", []):
        draw_annotation(draw, annotation, font_path, (source_w, source_h), margin_origin, margin_size)
    output_name = page.get("output") or f"{source.stem}_annotated.png"
    output_path = output_dir / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=95)
    return output_path


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    font_path = find_font(args.font or spec.get("font"))
    output_paths = [render_page(page, output_dir, font_path) for page in spec["pages"]]
    if args.pdf_out:
        pdf_path = Path(args.pdf_out).expanduser().resolve()
        images = [Image.open(path).convert("RGB") for path in output_paths]
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
    print(json.dumps({"outputs": [str(path) for path in output_paths], "pdf": args.pdf_out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
