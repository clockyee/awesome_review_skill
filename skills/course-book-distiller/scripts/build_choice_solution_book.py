#!/usr/bin/env python3
"""Build a compact XeLaTeX solution book for multiple-choice questions."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


CHAPTER_ORDER = {
    "第十三章": 13,
    "第十四章": 14,
    "第十五章": 15,
    "第十七章": 17,
    "第十八章": 18,
    "第十九章": 19,
    "第二十章": 20,
    "第二十一章": 21,
    "第二十二章": 22,
    "第二十三章": 23,
}


CHAPTER_SUMMARIES: dict[str, dict[str, list[str] | str]] = {
    "第十三章": {
        "title": "机械零件设计基础：强度准则",
        "formulas": [
            r"\sigma \le [\sigma]",
            r"S_\sigma=\frac{\sigma_{\lim}}{\sigma_{\max}},\qquad S_\sigma\ge [S_\sigma]",
            r"\tau \le [\tau],\qquad S_\tau\ge [S_\tau]",
        ],
        "method": [
            "先判断题干给的是应力表达还是安全系数表达。",
            "应力表达看“实际值不能超过许用值”；安全系数表达看“实际安全系数不能小于许用安全系数”。",
            "凡出现“最大应力、许用应力、实际安全系数、许用安全系数”，优先写两个等价强度条件。",
        ],
        "example": "B 卷第 1 题就是强度条件的等价表达题，核心不是计算，而是比较不等号方向。",
        "mistakes": ["把安全系数不等号方向写反。", "把许用应力当成实际应力。"],
    },
    "第十四章": {
        "title": "螺纹紧固件连接：载荷、旋入深度、疲劳措施",
        "formulas": [
            r"F_0=F+F''",
            r"\tau=\frac{4F}{\pi d_0^2}\le[\tau]",
            r"F_i=\frac{M r_i}{\sum r_i^2}",
            r"\Delta F_b=\frac{C_b}{C_b+C_m}F",
        ],
        "method": [
            "先判连接类型：普通螺栓、紧螺栓、铰制孔螺栓。",
            "轴向受载紧螺栓抓 F、F'、F''、F0 的关系，避免重复相加。",
            "材料题按承载能力判断旋入深度；疲劳题按“减小螺栓刚度、增大被连接件刚度”判断。",
        ],
        "example": "B 卷第 2-4 题覆盖了总拉力、螺孔深度、降低应力幅三类常考判断。",
        "mistakes": ["F'、F''、F0 概念混在一起。", "铸铁旋入深度按钢件取。"],
    },
    "第十五章": {
        "title": "轴毂连接：键连接布置与承载",
        "formulas": [
            r"\tau=\frac{2T}{d b l}\le[\tau]",
            r"\sigma_p=\frac{4T}{d h l}\le[\sigma_p]",
            r"\Delta\phi_{\mathrm{two\ keys}}=180^\circ",
        ],
        "method": [
            "平键主要靠侧面传力，校核挤压和剪切。",
            "两个平键要对称布置，避免偏载；强度计算不能简单按 2 个键满额叠加。",
            "题干出现“一个键强度不够”时，先找布置角度，再谈承载折减。",
        ],
        "example": "B 卷第 5 题考查两个平键的布置，答案落在结构原则而不是复杂计算。",
        "mistakes": ["把平键工作面说成上下表面。", "两个键随意布置导致偏载。"],
    },
    "第十七章": {
        "title": "带传动与链传动：滑动、布置和链节数",
        "formulas": [
            r"v=\frac{\pi d_1 n_1}{60\times1000}",
            r"F_e=\frac{1000P}{v}",
            r"P_{\mathrm{ca}}=K_A P",
            r"z_{\mathrm{belt}}=\frac{P_{\mathrm{ca}}}{(P_0+\Delta P_0)K_\alpha K_L}",
        ],
        "method": [
            "带传动先分清弹性滑动和打滑：前者不可避免，后者是摩擦不足或过载失效。",
            "多级传动布置通常带在高速级、链在低速级，齿轮居中。",
            "链传动题抓链节数取偶数、小链轮齿数、润滑和冲击磨损。",
        ],
        "example": "B 卷第 6、7、14、15 题分别对应弹性滑动、小带轮直径、链节数和传动布置。",
        "mistakes": ["把弹性滑动说成打滑。", "链节数取偶数只背结论，不说过渡链节。"],
    },
    "第十八章": {
        "title": "齿轮传动：失效、强度准则、参数影响",
        "formulas": [
            r"i=\frac{z_2}{z_1}",
            r"d=mz",
            r"a=\frac{m(z_1+z_2)}{2}",
            r"m_n=m_t\cos\beta",
            r"\sigma_F \le [\sigma_F],\qquad \sigma_H \le [\sigma_H]",
        ],
        "method": [
            "先判闭式/开式、软齿面/硬齿面，再判主要失效形式。",
            "齿形系数题看齿数；分度圆直径不变时，模数增大主要改善齿根弯曲强度。",
            "锥齿轮强度计算用齿宽中点处背锥展开的当量齿轮。",
            "齿宽系数题要联系支承形式：悬臂布置载荷分布差，齿宽不宜大。",
        ],
        "example": "B 卷第 8-12 题覆盖齿形系数、点蚀、模数影响、锥齿轮当量、齿宽系数。",
        "mistakes": ["闭式软齿面和硬齿面的主要危险混淆。", "把分度圆直径和模数的影响说反。"],
    },
    "第十九章": {
        "title": "蜗杆传动：传动比与几何参数",
        "formulas": [
            r"i=\frac{n_1}{n_2}=\frac{z_2}{z_1}",
            r"\tan\gamma=\frac{z_1 m}{d_1}",
            r"\eta\approx\frac{\tan\gamma}{\tan(\gamma+\varphi_v)}",
        ],
        "method": [
            "传动比优先看转速比和齿数/头数比。",
            "蜗杆传动不能用分度圆直径比直接表示传动比。",
            "效率、自锁和导程角相连，概念题要同时想到摩擦角。",
        ],
        "example": "B 卷第 13 题是典型反选题：找错误表达式，i=d2/d1 不成立。",
        "mistakes": ["把蜗杆传动当成普通齿轮传动，用直径比求 i。"],
    },
    "第二十章": {
        "title": "轴的设计计算：轴的分类",
        "formulas": [
            r"T=9550\frac{P}{n}",
            r"d\ge \sqrt[3]{\frac{16T}{\pi[\tau]}}",
            r"M\neq0,T=0;\quad M=0,T\neq0;\quad M\neq0,T\neq0",
        ],
        "method": [
            "心轴只承受弯矩，不传递转矩。",
            "传动轴只传递转矩；转轴同时承受弯矩和转矩。",
            "生活结构题先问：轴是否随轮转？是否传递转矩？主要受弯还是受扭？",
        ],
        "example": "B 卷第 16 题用自行车前轮轴判断心轴，关键是“不传递转矩”。",
        "mistakes": ["看到轮转就误判轴也传递转矩。"],
    },
    "第二十一章": {
        "title": "滚动轴承：类型选择与轴向力",
        "formulas": [
            r"P=f_p(XF_R+YF_A)",
            r"L_{10h}=\frac{10^6}{60n}\left(\frac{C}{P}\right)^\varepsilon",
            r"F_a\neq0\Rightarrow \text{select angular-contact or tapered bearing}",
        ],
        "method": [
            "先看载荷方向：径向、轴向、联合载荷。",
            "圆锥滚子轴承和角接触球轴承可承受轴向力，常成对使用。",
            "寿命计算题才进入 X、Y、P、C、L10h；选择题多考载荷能力和布置原则。",
        ],
        "example": "B 卷第 18 题考圆锥滚子轴承的轴向分力和成对布置。",
        "mistakes": ["只看滚子/球，不看载荷方向。"],
    },
    "第二十二章": {
        "title": "滑动轴承：p、v、pv 条件",
        "formulas": [
            r"p=\frac{F}{Bd}\le[p]",
            r"v=\frac{\pi d n}{60\times1000}\le[v]",
            r"pv\le[pv]",
        ],
        "method": [
            "p 控制压强，主要防压溃和过度磨损。",
            "v 控制相对滑动速度，pv 控制摩擦发热。",
            "题干问“过度发热”时，优先定位 pv 条件。",
        ],
        "example": "B 卷第 17 题考 pv 限制目的，对应轴承温升和发热。",
        "mistakes": ["把 p、v、pv 的物理意义混成一个。"],
    },
    "第二十三章": {
        "title": "联轴器、离合器和制动器：补偿偏移与凸缘连接",
        "formulas": [
            r"T=F r",
            r"\tau=\frac{F}{A_{\mathrm{shear}}},\qquad \sigma_p=\frac{F}{A_{\mathrm{bearing}}}",
            r"\Delta r,\Delta\alpha,\Delta x\Rightarrow \text{compensation capacity}",
        ],
        "method": [
            "联轴器选择先看是否需要补偿径向、角向、轴向或综合偏移。",
            "齿式联轴器可补偿综合偏移，刚性凸缘联轴器主要靠铰制孔螺栓传递横向载荷。",
            "铰制孔螺栓传力时，螺杆受剪，接触面受挤压。",
        ],
        "example": "B 卷第 19、20 题分别考齿式联轴器和铰制孔螺栓受力。",
        "mistakes": ["把铰制孔螺栓按普通螺栓受拉处理。", "只说联轴器名称，不说补偿哪类偏移。"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--choice-data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--title", default="B卷选择题习题解样张")
    parser.add_argument("--max-questions", type=int, default=0)
    return parser.parse_args()


def normalize_marker(text: str) -> str:
    return (
        text.replace("①", "(1)")
        .replace("②", "(2)")
        .replace("③", "(3)")
        .replace("④", "(4)")
        .replace("⑤", "(5)")
    )


def tex_escape(text: Any) -> str:
    value = normalize_marker(str(text))
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in value)


def chapter_key(chapter: str) -> str:
    match = re.search(r"第[一二三四五六七八九十百零]+章", chapter)
    return match.group(0) if match else "未分类"


def first_citation(question: dict[str, Any]) -> dict[str, Any]:
    citations = question.get("textbook_citations") or []
    return citations[0] if citations else {}


def copy_snippets(questions: list[dict[str, Any]], output_dir: Path, cwd: Path) -> None:
    asset_dir = output_dir / "assets" / "snippets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    for question in questions:
        citation = first_citation(question)
        snippet = citation.get("snippet_image")
        if not snippet:
            continue
        src = Path(snippet)
        if not src.is_absolute():
            src = cwd / src
        if not src.exists():
            continue
        dst = asset_dir / f"q{int(question['no']):02d}_textbook.png"
        shutil.copyfile(src, dst)
        citation["snippet_local"] = f"assets/snippets/{dst.name}"


def doc_preamble(title: str) -> str:
    return rf"""
\documentclass[UTF8,zihao=-4,fontset=none]{{ctexart}}
\usepackage[a4paper,margin=1.25cm,top=1.35cm,bottom=1.35cm]{{geometry}}
\usepackage{{amsmath,amssymb,mathtools}}
\usepackage{{fontspec}}
\usepackage{{unicode-math}}
\usepackage{{graphicx}}
\usepackage{{booktabs,tabularx,array,multicol}}
\usepackage{{enumitem}}
\usepackage[most]{{tcolorbox}}
\usepackage{{xcolor}}
\usepackage{{fancyhdr}}
\usepackage{{hyperref}}
\setmainfont[
  Path=/System/Library/Fonts/Supplemental/,
  BoldFont={{Times New Roman Bold.ttf}},
  ItalicFont={{Times New Roman Italic.ttf}},
  BoldItalicFont={{Times New Roman Bold Italic.ttf}}
]{{Times New Roman.ttf}}
\setCJKmainfont{{Songti SC}}
\setCJKsansfont{{Songti SC}}
\setCJKmonofont{{Songti SC}}
\setmathfont[Path=/System/Library/Fonts/Supplemental/]{{STIXTwoMath.otf}}
\hypersetup{{colorlinks=true,linkcolor=blue!55!black,urlcolor=blue!55!black}}
\definecolor{{ink}}{{HTML}}{{222222}}
\definecolor{{deepblue}}{{HTML}}{{183A59}}
\definecolor{{softblue}}{{HTML}}{{EEF5FB}}
\definecolor{{deepgreen}}{{HTML}}{{235B2B}}
\definecolor{{softgreen}}{{HTML}}{{F0FAF2}}
\definecolor{{deepred}}{{HTML}}{{8A1F15}}
\definecolor{{softred}}{{HTML}}{{FFF3F1}}
\definecolor{{softgray}}{{HTML}}{{F7F7F4}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{{tex_escape(title)}}}
\rhead{{\thepage}}
\setlength{{\headheight}}{{15pt}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{3pt}}
\setlength{{\emergencystretch}}{{3em}}
\setlist[itemize]{{leftmargin=1.1em,itemsep=1pt,topsep=2pt}}
\renewcommand{{\arraystretch}}{{1.13}}
\newcolumntype{{Y}}{{>{{\raggedright\arraybackslash}}X}}
\newcommand{{\pill}}[1]{{\tcbox[colback=softgray,colframe=black!25,arc=.8mm,boxrule=.25pt,on line,boxsep=1pt,left=2pt,right=2pt]{{\small #1}}}}
\newtcolorbox{{chapterbox}}[1]{{enhanced,breakable,colback=softblue,colframe=deepblue,arc=1mm,boxrule=.6pt,left=5pt,right=5pt,top=4pt,bottom=4pt,title=\bfseries #1}}
\newtcolorbox{{methodbox}}[1]{{enhanced,breakable,colback=softgreen,colframe=deepgreen,arc=1mm,boxrule=.55pt,left=5pt,right=5pt,top=4pt,bottom=4pt,title=\bfseries #1}}
\newtcolorbox{{warnbox}}[1]{{enhanced,breakable,colback=softred,colframe=deepred,arc=1mm,boxrule=.55pt,left=5pt,right=5pt,top=4pt,bottom=4pt,title=\bfseries #1}}
\newtcolorbox{{qcard}}[1]{{enhanced,breakable,colback=white,colframe=black!35,arc=1mm,boxrule=.45pt,left=5pt,right=5pt,top=4pt,bottom=4pt,title=\bfseries #1,before upper=\raggedright}}
\newcommand{{\answerline}}[1]{{\tcbox[colback=deepred!8,colframe=deepred!65,arc=.8mm,boxrule=.4pt,on line,boxsep=1.2pt,left=4pt,right=4pt]{{\bfseries #1}}}}
\begin{{document}}
\begin{{center}}
  {{\zihao{{2}}\bfseries {tex_escape(title)}}}\\[2pt]
  {{\large 机械原理与机械设计：选择题题解册样张}}\\[4pt]
  {{\small 版式：章首方法总结 + 逐题题解卡 + 教材定位局部截图}}
\end{{center}}
\tableofcontents
\newpage
"""


def itemize(items: list[str]) -> str:
    lines = [r"\begin{itemize}"]
    lines.extend(rf"\item {tex_escape(item)}" for item in items)
    lines.append(r"\end{itemize}")
    return "\n".join(lines)


def formula_block(formulas: list[str]) -> str:
    if not formulas:
        return ""
    lines = [r"\begin{methodbox}{公式与判据入口}"]
    for formula in formulas:
        lines.append(rf"\[{formula}\]")
    lines.append(r"\end{methodbox}")
    return "\n".join(lines)


def option_grid(options: dict[str, str]) -> str:
    pairs = [(normalize_marker(k), v) for k, v in options.items()]
    if max((len(value) for _, value in pairs), default=0) > 12:
        rows = [
            rf"\textbf{{{tex_escape(marker)}}} & {tex_escape(value)} \\"
            for marker, value in pairs
        ]
        return "\n".join([r"\begin{tabularx}{\linewidth}{@{}p{.07\linewidth}Y@{}}", *rows, r"\end{tabularx}"])
    rows: list[str] = []
    for idx in range(0, len(pairs), 2):
        left = pairs[idx]
        right = pairs[idx + 1] if idx + 1 < len(pairs) else ("", "")
        rows.append(
            rf"\textbf{{{tex_escape(left[0])}}} {tex_escape(left[1])} & "
            rf"\textbf{{{tex_escape(right[0])}}} {tex_escape(right[1])} \\"
        )
    return "\n".join([r"\begin{tabularx}{\linewidth}{@{}Y Y@{}}", *rows, r"\end{tabularx}"])


def related_question(question: dict[str, Any]) -> str:
    related = question.get("related_review_questions") or []
    if not related:
        return "同类复习：回到本章公式入口，自拟一题说明判断条件。"
    first = related[0]
    prompt = first.get("prompt", "")
    answer = first.get("answer", "")
    return f"同类复习：{prompt} 答：{answer}"


def compact_signal(question: dict[str, Any], citation: dict[str, Any]) -> str:
    terms = citation.get("search_terms") or []
    if terms:
        return "、".join(str(term) for term in terms[:3])
    return question.get("analysis", "")[:22]


def render_question_card(question: dict[str, Any]) -> str:
    citation = first_citation(question)
    no = int(question["no"])
    chapter = citation.get("chapter", "教材定位待补")
    pdf_page = citation.get("pdf_page", "")
    print_page = citation.get("print_page", "")
    anchor = citation.get("quote_anchor", "")
    snippet = citation.get("snippet_local", "")
    signal = compact_signal(question, citation)
    answer = normalize_marker(question.get("answer", ""))

    answer_marker = answer.split()[0] if answer else ""
    title = f"题 {no:02d}｜{chapter_key(chapter)}｜答案 {answer_marker}"
    lines = [rf"\begin{{qcard}}{{{tex_escape(title)}}}"]
    lines.append(rf"\textbf{{题干}}\quad {tex_escape(question.get('stem', ''))}")
    lines.append(option_grid(question.get("options", {})))
    lines.append(r"\vspace{2pt}")
    lines.append(
        r"\begin{tcolorbox}[enhanced,breakable,colback=deepred!8,colframe=deepred!65,"
        r"arc=.8mm,boxrule=.35pt,left=3pt,right=3pt,top=2pt,bottom=2pt]"
        + rf"\textbf{{答案：}}{tex_escape(answer)}"
        + r"\end{tcolorbox}"
    )
    lines.append(r"\vspace{3pt}")
    lines.append(r"\begin{tabularx}{\linewidth}{@{}p{.15\linewidth}Y@{}}")
    lines.append(rf"\textbf{{解题线}} & \pill{{1 信号}} {tex_escape(signal)} \\")
    lines.append(rf" & \pill{{2 判据}} {tex_escape(anchor)} \\")
    lines.append(rf" & \pill{{3 排除}} 看不等号、载荷、失效或结构关键词是否被偷换 \\")
    lines.append(rf" & \pill{{4 作答}} 选 {tex_escape(answer_marker)} \\")
    lines.append(r"\end{tabularx}")
    lines.append(r"\vspace{3pt}")
    lines.append(r"\begin{minipage}[t]{.64\linewidth}")
    lines.append(rf"\textbf{{解法}}\quad {tex_escape(question.get('analysis', ''))}")
    lines.append("")
    lines.append(
        rf"\textbf{{教材定位}}\quad {tex_escape(chapter)}；PDF 页 {tex_escape(pdf_page)}"
        + (rf"，印刷页 {tex_escape(print_page)}" if print_page else "")
        + "。"
    )
    if anchor:
        lines.append(rf"\textbf{{原文锚点}}\quad {tex_escape(anchor)}")
    lines.append(rf"\textbf{{迁移题}}\quad {tex_escape(related_question(question))}")
    lines.append(r"\end{minipage}\hfill")
    lines.append(r"\begin{minipage}[t]{.33\linewidth}")
    if snippet:
        lines.append(r"\vspace{0pt}\includegraphics[width=\linewidth,height=.19\textheight,keepaspectratio]{" + snippet + "}")
        lines.append(r"\scriptsize 教材局部截图")
    else:
        lines.append(r"\scriptsize 教材截图待补")
    lines.append(r"\end{minipage}")
    lines.append(r"\end{qcard}")
    return "\n".join(lines)


def render_chapter(chapter: str, questions: list[dict[str, Any]]) -> str:
    summary = CHAPTER_SUMMARIES.get(chapter, {})
    title = summary.get("title", chapter)
    parts = [rf"\section{{{tex_escape(chapter + '  ' + str(title).replace(chapter, '').strip())}}}"]
    parts.append(formula_block(list(summary.get("formulas", []))))
    parts.append(r"\begin{chapterbox}{做题方法线}")
    parts.append(itemize(list(summary.get("method", ["先圈关键词，再定位教材判据，最后排除相近选项。"]))))
    parts.append(r"\end{chapterbox}")
    parts.append(r"\begin{methodbox}{例题归纳}")
    parts.append(tex_escape(summary.get("example", f"本章样题来自 B 卷第 {questions[0]['no']} 题。")))
    parts.append(r"\end{methodbox}")
    if summary.get("mistakes"):
        parts.append(r"\begin{warnbox}{常见误区}")
        parts.append(itemize(list(summary.get("mistakes", []))))
        parts.append(r"\end{warnbox}")
    for question in questions:
        parts.append(render_question_card(question))
    return "\n".join(parts)


def render_document(data: dict[str, Any], output_dir: Path, title: str, max_questions: int) -> None:
    questions = list(data.get("questions", []))
    if max_questions > 0:
        questions = questions[:max_questions]

    copy_snippets(questions, output_dir, Path.cwd())

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for question in questions:
        grouped[chapter_key(first_citation(question).get("chapter", ""))].append(question)

    parts = [doc_preamble(title)]
    parts.append(r"\section*{使用说明}\addcontentsline{toc}{section}{使用说明}")
    parts.append(
        r"\begin{chapterbox}{这版和上一版的区别}"
        "\n这不是按考点泛泛罗列，而是把每章先压缩成“公式入口—判断流程—例题归纳”，"
        "再逐题给出题干、选项、答案、解题线、教材定位和教材局部截图。"
        "\n\\end{chapterbox}"
    )
    parts.append(
        r"\begin{methodbox}{阅读顺序}"
        "\n先读章首公式与做题方法，再做本章题卡；每题先遮住答案，只看“题干信号”能否推出教材判据。"
        "\n\\end{methodbox}"
    )
    for chapter in sorted(grouped, key=lambda key: CHAPTER_ORDER.get(key, 999)):
        parts.append(render_chapter(chapter, grouped[chapter]))
    parts.append("\n\\end{document}\n")

    tex_path = output_dir / "b_choice_solution_book.tex"
    tex_path.write_text("\n".join(parts), encoding="utf-8")
    summary = {
        "tex": tex_path.name,
        "questions": len(questions),
        "chapters": list(sorted(grouped, key=lambda key: CHAPTER_ORDER.get(key, 999))),
    }
    (output_dir / "choice_solution_book_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(Path(args.choice_data).read_text(encoding="utf-8"))
    render_document(data, output_dir, args.title, args.max_questions)


if __name__ == "__main__":
    main()
