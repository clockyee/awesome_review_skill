#!/usr/bin/env python3
"""Generate XeLaTeX review-note PDFs for the TJU mechanical course pilot."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


CHAPTER_FORMULAS: dict[str, list[str]] = {
    "第三章": [
        r"F=3n-2P_L-P_H",
        r"F=3n-(2P_L+P_H)-F'_{\mathrm{local}}+F_{\mathrm{virtual}}",
        r"F=N_{\mathrm{driver}}",
    ],
    "第五章": [
        r"\eta_{\mathrm{series}}=\eta_1\eta_2\cdots\eta_k",
        r"\eta_{\mathrm{parallel}}=\frac{\sum P_{\mathrm{out},i}}{\sum P_{\mathrm{in},i}}",
        r"\tan\varphi=f",
    ],
    "第六章": [
        r"\theta=180^\circ\frac{K-1}{K+1}",
        r"K=\frac{180^\circ+\theta}{180^\circ-\theta}",
        r"\gamma_{\min}=\min(\gamma_1,\gamma_2,\ldots)",
    ],
    "第七章": [
        r"v=\omega\frac{ds}{d\varphi},\qquad a=\omega^2\frac{d^2s}{d\varphi^2}",
        r"\alpha=\angle(\vec F_{\mathrm{follower}},\vec n_v)",
        r"\varphi_{\mathrm{inverse}}=-\varphi",
    ],
    "第八章": [
        r"d=mz,\qquad d_b=d\cos\alpha,\qquad d_a=m(z+2h_a^*)",
        r"a=\frac{m(z_1+z_2)}{2},\qquad \cos\alpha'=\frac{a\cos\alpha}{a'}",
        r"m_t=\frac{m_n}{\cos\beta},\qquad d=\frac{m_n z}{\cos\beta}",
    ],
    "第十章": [
        r"z_{\mathrm{Geneva}}\ge 3",
        r"\Delta v\neq 0\Rightarrow \mathrm{rigid\ impact}",
        r"\Delta a\neq 0\Rightarrow \mathrm{flexible\ impact}",
    ],
    "第十一章": [
        r"\delta=\frac{\omega_{\max}-\omega_{\min}}{\omega_m}",
        r"J_F\ge \frac{W_{\max}}{\delta\omega_m^2}",
        r"M_{\mathrm{eq}}=\frac{P}{\omega}",
    ],
    "第十二章": [
        r"\sum \vec F_i=\sum m_i r_i\omega^2\,\vec e_i=0",
        r"\sum \vec M_i=\sum m_i r_i l_i\omega^2\,\vec e_i=0",
        r"\mathrm{static}:\sum \vec F=0,\qquad \mathrm{dynamic}:\sum \vec F=\sum \vec M=0",
    ],
    "第十三章": [
        r"\sigma\le [\sigma]",
        r"S_\sigma\ge [S_\sigma]",
        r"\sigma_{\mathrm{ca}}=\sqrt{\sigma^2+4\tau^2}",
    ],
    "第十四章": [
        r"F_0=F''+F",
        r"\tau=\frac{4F}{\pi d_0^2}\le[\tau]",
        r"F_i=\frac{M r_i}{\sum r_i^2},\qquad F_d=\frac{F}{z}",
    ],
    "第十五章": [
        r"\sigma_p=\frac{4T}{dhl}\le[\sigma_p]",
        r"\tau=\frac{2T}{dbl}\le[\tau]",
        r"\Delta\phi_{\mathrm{two\ keys}}=180^\circ",
    ],
    "第十七章": [
        r"v=\frac{\pi d_1 n_1}{60\times1000}",
        r"F_e=\frac{1000P}{v}",
        r"z=\frac{P_{\mathrm{ca}}}{(P_0+\Delta P_0)K_\alpha K_L}",
    ],
    "第十八章": [
        r"i=\frac{z_2}{z_1}",
        r"a=\frac{m_n(z_1+z_2)}{2\cos\beta}",
        r"d_1=\frac{m_n z_1}{\cos\beta},\qquad d_2=\frac{m_n z_2}{\cos\beta}",
    ],
    "第十九章": [
        r"i=\frac{n_1}{n_2}=\frac{z_2}{z_1}",
        r"\tan\gamma=\frac{z_1 m}{d_1}",
        r"\eta\approx\frac{\tan\gamma}{\tan(\gamma+\varphi_v)}",
    ],
    "第二十章": [
        r"T=9550\frac{P}{n}\quad(\mathrm{N\cdot m})",
        r"d\ge \sqrt[3]{\frac{16T}{\pi[\tau]}}",
        r"M\neq0,\ T=0;\qquad M=0,\ T\neq0;\qquad M\neq0,\ T\neq0",
    ],
    "第二十一章": [
        r"P=f_p(XF_R+YF_A)",
        r"L_{10h}=\frac{10^6}{60n}\left(\frac{C}{P}\right)^\varepsilon",
        r"\varepsilon=3\ (\text{球轴承}),\qquad \varepsilon=\frac{10}{3}\ (\text{滚子轴承})",
    ],
    "第二十二章": [
        r"p=\frac{F}{Bd}\le[p]",
        r"v=\frac{\pi d n}{60\times1000}\le[v]",
        r"pv\le[pv]",
    ],
    "第二十三章": [
        r"\text{凸缘联轴器：刚性；齿式联轴器：补偿综合偏移}",
        r"\text{铰制孔螺栓传递转矩：剪切 + 挤压}",
        r"\text{弹性联轴器：缓冲吸振，允许少量偏移}",
    ],
}


CHAPTER_METHODS: dict[str, list[str]] = {
    "第三章": ["先数活动构件，再数低副/高副。", "逐项排查复合铰链、局部自由度、虚约束。", "最后检查自由度是否等于原动件数。"],
    "第五章": ["先画分离体图。", "摩擦力方向必须按相对运动趋势判定。", "自锁题必须写摩擦角或效率判据。"],
    "第六章": ["先用杆长条件判机构类型。", "涉及急回先求极位夹角。", "设计题先定固定铰链，再用圆弧交点确定活动铰链。"],
    "第七章": ["先画位移线图。", "用反转法作理论轮廓。", "滚子从动件再由理论轮廓偏置得到实际轮廓。"],
    "第八章": ["先分清分度圆、基圆、齿顶圆、节圆。", "中心距变化时必须改用实际啮合角。", "作图题答案必须落在图上。"],
    "第十章": ["先识别间歇机构类型。", "再判断锁止、冲击和槽数/齿数约束。", "最后说适用工况。"],
    "第十一章": ["先判速度波动类型。", "飞轮只调周期性速度波动。", "盈亏功和转速波动系数一起进入飞轮转动惯量。"],
    "第十二章": ["先写惯性力合力条件。", "再写惯性力矩条件。", "只满足前者是静平衡，同时满足才是动平衡。"],
    "第十三章": ["先判断静强度还是疲劳强度。", "再判断材料塑性/脆性。", "最后选应力表达或安全系数表达。"],
    "第十四章": ["先判普通螺栓、紧螺栓、铰制孔螺栓。", "偏心螺栓组先把载荷移到形心。", "疲劳题抓螺栓刚度和被连接件刚度。"],
    "第十五章": ["先判断键型和工作面。", "强度不足时考虑键长、双键、花键或轴径。", "双键布置要避免偏载。"],
    "第十七章": ["先判断失效形式。", "设计题按计算功率、标准参数、包角、带速、根数校核。", "概念题区分弹性滑动和打滑。"],
    "第十八章": ["先判闭式/开式、软齿面/硬齿面。", "再选接触疲劳或弯曲疲劳准则。", "参数题必须检查传动比偏差和中心距。"],
    "第十九章": ["先抓蜗杆头数和蜗轮齿数。", "传动比不是直径比。", "设计题别忘热平衡和效率。"],
    "第二十章": ["先按功率和转速估算转矩。", "再按轴类型和受力做强度校核。", "结构题要考虑定位、装拆和密封。"],
    "第二十一章": ["先求径向支反力。", "成对轴承必须分配轴向力。", "由比例关系选 X,Y 后再算寿命。"],
    "第二十二章": ["先分非液体摩擦、边界润滑、流体动压润滑。", "条件计算 p、v、pv 各有物理含义。", "动压润滑题必须画楔形油膜。"],
    "第二十三章": ["先看偏移补偿能力。", "再看载荷冲击、转速、缓冲要求。", "凸缘联轴器若用铰制孔螺栓，螺栓受剪切和挤压。"],
}


BIG_GUIDES: list[dict[str, Any]] = [
    {
        "title": "机构自由度与结构分析",
        "signals": ["题干出现自由度、复合铰链、局部自由度、虚约束、确定运动。"],
        "steps": ["圈出机架和活动构件。", "数低副、高副；复合铰链按多个运动副计。", "把局部自由度删掉，把虚约束修正回来。", "代入自由度公式。", "判断自由度 F 是否等于原动件数。"],
        "formulas": [r"F=3n-2P_L-P_H", r"F=\text{原动件数}\Rightarrow\text{确定运动}"],
        "rubric": ["构件数", "运动副数", "特殊结构修正", "确定运动结论"],
        "mistakes": ["滚子局部转动未排除。", "复合铰链少计。", "只写公式不在图上圈特殊部位。"],
    },
    {
        "title": "四杆机构类型、急回与设计",
        "signals": ["题干出现曲柄摇杆、双曲柄、双摇杆、极位夹角、行程速度变化系数。"],
        "steps": ["按杆长排序，先检验 Grashof 条件。", "指定机架后判断曲柄/摇杆身份。", "急回题先由行程速度变化系数 K 求极位夹角 θ。", "作图设计时先确定固定铰链和极限位置。", "用圆弧交点确定活动铰链，最后校核传动角。"],
        "formulas": [r"l_{\min}+l_{\max}\le l'+l''", r"\theta=180^\circ\frac{K-1}{K+1}", r"K=\frac{180^\circ+\theta}{180^\circ-\theta}"],
        "rubric": ["杆长条件", "机架选择", "极位夹角", "作图构造", "传动角校核"],
        "mistakes": ["先背类型不看机架。", "K 和 θ 互算公式写反。", "作图后不检查最小传动角。"],
    },
    {
        "title": "平面机构速度分析",
        "signals": ["题干出现速度瞬心、角速度、杆件速度、图解法。"],
        "steps": ["先找直接瞬心。", "用三心定理补出间接瞬心。", "同一瞬心处两构件绝对速度相同。", "按速度等于角速度乘距离建立比例关系。", "速度方向不确定时先画方向线，交点决定大小。"],
        "formulas": [r"v=\omega l", r"\omega_i P_{ij}P_{ik}=\omega_k P_{ij}P_{ki}"],
        "rubric": ["瞬心位置", "三心定理", "速度方向", "比例计算"],
        "mistakes": ["用瞬心法求加速度。", "把速度方向画成沿杆。", "已知方向有限时没有画方向线找交点。"],
    },
    {
        "title": "凸轮廓线与压力角",
        "signals": ["题干出现位移线图、反转法、压力角、滚子半径、实际廓线。"],
        "steps": ["按推程、远休、回程、近休画位移图。", "从动件和导路按反转方向布置。", "得到理论轮廓。", "滚子从动件按滚子半径作包络得到实际轮廓。", "检查压力角和曲率半径。"],
        "formulas": [r"v=\omega\frac{ds}{d\varphi}", r"a=\omega^2\frac{d^2s}{d\varphi^2}"],
        "rubric": ["位移图", "反转方向", "理论/实际轮廓", "压力角"],
        "mistakes": ["反转方向画反。", "把理论轮廓当实际轮廓。", "漏压力角校核。"],
    },
    {
        "title": "齿轮啮合作图与参数设计",
        "signals": ["题干出现基圆、啮合线、节点、中心距、变位、斜齿轮参数。"],
        "steps": ["先列分度圆、基圆、齿顶圆和齿根圆。", "两基圆公切线为啮合线。", "啮合线与中心线交点为节点。", "中心距变化时计算实际啮合角 α'。", "参数设计题先选标准模数，再选齿数并校核传动比偏差。"],
        "formulas": [r"d=mz", r"d_b=d\cos\alpha", r"\cos\alpha'=\frac{a\cos\alpha}{a'}", r"a=\frac{m_n(z_1+z_2)}{2\cos\beta}"],
        "rubric": ["几何圆", "啮合线和节点", "实际啮合角", "标准值和偏差校核"],
        "mistakes": ["分度圆当基圆。", "中心距变了仍写 20°。", "只给齿数不校核中心距。"],
    },
    {
        "title": "轮系传动比",
        "signals": ["题干出现定轴轮系、周转轮系、行星架、转化机构。"],
        "steps": ["先拆分定轴和周转部分。", "定轴轮系按啮合级数确定正负号。", "周转轮系固定行星架，写转化机构传动比。", "把已知转速代回求未知转速。", "最后判断方向。"],
        "formulas": [r"i_{ab}=\frac{n_a}{n_b}", r"i_{ab}^{H}=\frac{n_a-n_H}{n_b-n_H}"],
        "rubric": ["轮系拆分", "转化公式", "方向", "转速大小"],
        "mistakes": ["把周转轮系当定轴轮系。", "漏行星架转速。", "正负号只靠直觉。"],
    },
    {
        "title": "螺栓组与连接强度",
        "signals": ["题干出现预紧力、剩余预紧力、铰制孔、偏心载荷、螺栓组形心。"],
        "steps": ["先判连接类型。", "轴向受拉题画载荷-变形线。", "横向铰制孔题按剪切和挤压。", "偏心螺栓组把载荷移到形心。", "找最危险螺栓后写强度条件。"],
        "formulas": [r"F_0=F''+F", r"F_i=\frac{M r_i}{\sum r_i^2}", r"\tau=\frac{4F}{\pi d_0^2}\le[\tau]"],
        "rubric": ["类型判断", "形心分解", "最危险螺栓", "强度条件"],
        "mistakes": ["铰制孔螺栓按普通螺栓处理。", "偏心载荷只平均分配。", "半径和直径混用。"],
    },
    {
        "title": "轴承寿命与轴系结构诊断",
        "signals": ["题干出现 X、Y、当量动载荷、寿命、固定端、游动端、轴向力路线。"],
        "steps": ["轴承题先求支反力。", "再分配轴向力并选择 X、Y。", "代入当量动载荷和寿命公式。", "结构诊断题先标固定端/游动端。", "每个错误按编号写位置、原因、修改。"],
        "formulas": [r"P=f_p(XF_R+YF_A)", r"L_{10h}=\frac{10^6}{60n}\left(\frac{C}{P}\right)^\varepsilon"],
        "rubric": ["支反力", "轴向力分配", "寿命公式", "固定/游动端", "编号诊断"],
        "mistakes": ["外载荷直接平均到轴承。", "漏载荷系数。", "结构题只写不合理但不编号。"],
    },
]


LECTURE_SECTIONS: list[dict[str, Any]] = [
    {
        "title": "第1-3章小题：机构组成与自由度",
        "source": "第1-3章小题.pdf；0322机械原理1-3章笔记.pdf",
        "points": ["空间运动副约束度范围：1 到 5；平面运动副约束度范围：1 到 2。", "构件是运动单元，零件是制造单元。", "机构有确定运动的条件是自由度等于原动件数。"],
        "formulas": [r"F=3n-2P_L-P_H", r"F=6n-\sum_{i=1}^{5} iP_i", r"F=\text{原动件数}"],
        "teaching": "这一组适合先让学生在图上圈机架、构件、运动副，再做公式代入。讲解时不要直接给公式，先让学生解释“为什么滚子转动不算机构整体自由度”。",
    },
    {
        "title": "第四、六章小题：瞬心、四杆、急回",
        "source": "第四周小题_.pdf；第四周大题_答案.pdf",
        "points": ["三个平面运动构件共有 3 个速度瞬心，三心共线。", "四杆机构类型必须先看最短杆、最长杆和机架。", "急回问题统一用 K 与极位夹角 θ 互算。"],
        "formulas": [r"N=\frac{n(n-1)}{2}", r"\theta=180^\circ\frac{K-1}{K+1}", r"K=\frac{180^\circ+\theta}{180^\circ-\theta}"],
        "teaching": "手写答案强调“测量、计算、代入、唯一”，这可以固化为作图题评分点：图上有极限位置，公式有 K 与 θ，最后有尺寸校核。",
    },
    {
        "title": "第五周：急回机构设计三件套",
        "source": "第五周笔记.pdf",
        "points": ["曲柄摇杆、曲柄滑块、摆动导杆都可以统一到 K、θ、极限位置。", "导杆机构常用 ψ=θ 作为作图入口。", "偏距 e 和导杆长度会改变极限位置与传动角。"],
        "formulas": [r"\theta=180^\circ\frac{K-1}{K+1}", r"AC_1=b-a,\qquad AC_2=b+a", r"a=d\sin\frac{\theta}{2}"],
        "teaching": "这页笔记最有价值的是把三类急回机构画在同一页比较。整理后应作为“同题型迁移”页：先问学生看到 K 应该想到什么，再让学生选择机构方案。",
    },
    {
        "title": "第七周：凸轮与导杆设计",
        "source": "第七周大题_.pdf",
        "points": ["凸轮题先明确行程、导路偏距、推程角。", "导杆机构设计先由 K 求 θ，再根据导杆长度和行程确定固定点。", "文字说明必须写清楚作图顺序。"],
        "formulas": [r"s=s(\varphi)", r"v=\omega\frac{ds}{d\varphi}", r"a=\omega^2\frac{d^2s}{d\varphi^2}"],
        "teaching": "这类题学生容易只画图不解释。规范答案应要求“作图步骤编号 + 图上标注 + 最终尺寸”。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objective-index", required=True)
    parser.add_argument("--big-index", required=True)
    parser.add_argument("--note-preview-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def tex_escape(text: Any) -> str:
    value = str(text)
    value = (
        value.replace("①", "(1)")
        .replace("②", "(2)")
        .replace("③", "(3)")
        .replace("④", "(4)")
        .replace("⑤", "(5)")
        .replace("⑥", "(6)")
        .replace("⑦", "(7)")
        .replace("⑧", "(8)")
    )
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def chapter_prefix(chapter: str) -> str:
    for key in CHAPTER_FORMULAS:
        if key in chapter:
            return key
    return chapter.split()[0]


def doc_preamble(title: str) -> str:
    return rf"""
\documentclass[UTF8,zihao=-4,fontset=none]{{ctexart}}
\usepackage[a4paper,margin=1.55cm]{{geometry}}
\usepackage{{amsmath,amssymb,mathtools}}
\usepackage{{fontspec}}
\usepackage{{unicode-math}}
\usepackage{{graphicx}}
\usepackage{{booktabs,tabularx,longtable,array}}
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
\definecolor{{mainblue}}{{HTML}}{{1F4E79}}
\definecolor{{softblue}}{{HTML}}{{EEF6FD}}
\definecolor{{softgreen}}{{HTML}}{{EFFAF3}}
\definecolor{{softorange}}{{HTML}}{{FFF4E8}}
\definecolor{{softred}}{{HTML}}{{FFF1F0}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{{tex_escape(title)}}}
\rhead{{\thepage}}
\setlength{{\headheight}}{{15pt}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{5pt}}
\renewcommand{{\arraystretch}}{{1.22}}
\newtcolorbox{{chapterbox}}[1]{{enhanced,breakable,colback=softblue,colframe=mainblue,arc=1.5mm,boxrule=.7pt,title=\large\bfseries #1}}
\newtcolorbox{{methodbox}}[1]{{enhanced,breakable,colback=softgreen,colframe=green!45!black,arc=1.5mm,boxrule=.6pt,title=\bfseries #1}}
\newtcolorbox{{warnbox}}[1]{{enhanced,breakable,colback=softred,colframe=red!55!black,arc=1.5mm,boxrule=.6pt,title=\bfseries #1}}
\newcommand{{\tagpill}}[1]{{\tcbox[colback=softorange,colframe=orange!65!black,arc=1mm,boxrule=.4pt,on line,boxsep=1pt,left=3pt,right=3pt]{{\small #1}}}}
\begin{{document}}
\begin{{center}}
  {{\zihao{{2}}\bfseries {tex_escape(title)}}}\\[4pt]
  {{\large 机械原理与机械设计复习材料}}\\[6pt]
  {{\small 生成方式：本地教材 OCR、往年题整理与备课笔记蒸馏；公式使用 XeLaTeX 规范排版。}}
\end{{center}}
\tableofcontents
\newpage
"""


def doc_end() -> str:
    return "\n\\end{document}\n"


def itemize(items: list[str]) -> str:
    body = ["\\begin{itemize}[leftmargin=1.2em,itemsep=2pt]"]
    body.extend(f"\\item {tex_escape(item)}" for item in items)
    body.append("\\end{itemize}")
    return "\n".join(body)


def formula_box(formulas: list[str]) -> str:
    if not formulas:
        return ""
    lines = ["\\begin{methodbox}{规范公式入口}"]
    for formula in formulas:
        lines.append(rf"\[{formula}\]")
    lines.append("\\end{methodbox}")
    return "\n".join(lines)


def render_choice_notes(rows: list[dict[str, Any]], out: Path) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[chapter_prefix(row.get("chapter", ""))].append(row)

    parts = [doc_preamble("选择题考点章节分类可视化复习笔记")]
    parts.append("\\section*{使用方法}\n\\addcontentsline{toc}{section}{使用方法}")
    parts.append(
        "\\begin{chapterbox}{刷题顺序}\n"
        "先按章节背公式入口，再做题面信号识别，最后回到原卷限时作答。每个考点都按“题面信号、判断句、易错点、迁移题”复习。\n"
        "\\end{chapterbox}"
    )

    for chapter, items in sorted(grouped.items()):
        parts.append(f"\\section{{{tex_escape(chapter)}}}")
        parts.append(formula_box(CHAPTER_FORMULAS.get(chapter, [])))
        methods = CHAPTER_METHODS.get(chapter, ["先定位概念，再找公式入口，最后做相近概念辨析。"])
        parts.append("\\begin{methodbox}{答题方法}\n" + itemize(methods) + "\n\\end{methodbox}")
        parts.append("\\begin{longtable}{p{0.18\\linewidth}p{0.24\\linewidth}p{0.28\\linewidth}p{0.22\\linewidth}}")
        parts.append("\\toprule 来源 & 题面信号 & 判断锚点 & 迁移复习 \\\\ \\midrule")
        for row in items:
            prompt = row.get("review_prompt", "")
            if isinstance(prompt, dict):
                prompt = f"{prompt.get('prompt','')} 答：{prompt.get('answer','')}"
            parts.append(
                f"{tex_escape(row.get('source',''))} & "
                f"{tex_escape(row.get('test_point',''))} & "
                f"{tex_escape(row.get('answer') or row.get('answer_hint',''))} & "
                f"{tex_escape(prompt)} \\\\"
            )
        parts.append("\\bottomrule\\end{longtable}")
        parts.append("\\begin{warnbox}{本章易错诊断}\n")
        mistakes = {
            "第三章": ["把零件当构件数。", "局部自由度、虚约束、复合铰链不修正。"],
            "第八章": ["分度圆、基圆、节圆混用。", "斜齿轮把端面参数当标准参数。"],
            "第十四章": ["普通螺栓和铰制孔螺栓受力模型混用。", "预紧力、工作拉力、剩余预紧力重复相加。"],
            "第十七章": ["弹性滑动和打滑混为一谈。", "链节数取偶数的原因只背不理解。"],
            "第十八章": ["软齿面和硬齿面主要失效形式混淆。", "模数、齿数、分度圆直径的影响说反。"],
        }.get(chapter, ["概念题不能只背关键词，要写出判断条件。", "选择题解析要能定位到公式或结构特征。"])
        parts.append(itemize(mistakes))
        parts.append("\\end{warnbox}")

    parts.append("\\section*{考前收束卡}\n\\addcontentsline{toc}{section}{考前收束卡}")
    parts.append(
        "\\begin{chapterbox}{选择题审题顺序}\n"
        + itemize(
            [
                "先圈题干限定词：标准、闭式、软齿面、急回、有无确定运动、是否自锁。",
                "再写一句判断锚点：自由度公式、传动比公式、强度准则、失效形式或结构特征。",
                "最后排除相近概念：弹性滑动/打滑，节圆/分度圆，普通螺栓/铰制孔螺栓，心轴/转轴/传动轴。",
            ]
        )
        + "\n\\end{chapterbox}"
    )
    parts.append(
        "\\begin{methodbox}{考前 30 分钟只看这些}\n"
        + itemize(
            [
                "机构部分：自由度修正、急回系数、压力角与传动角、齿轮几何参数。",
                "机械设计部分：螺栓、键、带链、齿轮、蜗杆、轴承、轴的失效形式和校核入口。",
                "遇到陌生题时，不猜名词，先把题面信号翻译成教材章节的判断条件。",
            ]
        )
        + "\n\\end{methodbox}"
    )

    parts.append(doc_end())
    out.write_text("\n".join(parts), encoding="utf-8")


def render_big_guidance(out: Path) -> None:
    parts = [doc_preamble("大题分类答题思路与评分指导")]
    parts.append("\\section*{总原则}\n\\addcontentsline{toc}{section}{总原则}")
    parts.append(
        "\\begin{chapterbox}{大题不是背答案，而是固定作答动作}\n"
        "每道大题先写题型判断，再在图上标关键实体，随后写公式入口和代入。图上作答题必须把答案画回原图；诊断题必须编号。\n"
        "\\end{chapterbox}"
    )
    for guide in BIG_GUIDES:
        parts.append(f"\\section{{{tex_escape(guide['title'])}}}")
        parts.append("\\begin{chapterbox}{题面信号}\n" + itemize(guide["signals"]) + "\n\\end{chapterbox}")
        parts.append(formula_box(guide["formulas"]))
        parts.append("\\begin{methodbox}{拿到题后的固定动作}\n" + itemize(guide["steps"]) + "\n\\end{methodbox}")
        parts.append("\\begin{methodbox}{评分点}\n" + itemize(guide["rubric"]) + "\n\\end{methodbox}")
        parts.append("\\begin{warnbox}{易错诊断}\n" + itemize(guide["mistakes"]) + "\n\\end{warnbox}")
    parts.append(doc_end())
    out.write_text("\n".join(parts), encoding="utf-8")


def copy_assets(preview_dir: Path, asset_dir: Path) -> dict[str, str]:
    asset_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "small_1_3": "第1-3章小题_p01.png",
        "week4_small": "第四周小题__p01.png",
        "week4_answer": "第四周大题_答案_p01.png",
        "week5": "第五周笔记_p01.png",
    }
    copied: dict[str, str] = {}
    for key, name in mapping.items():
        src = preview_dir / name
        if src.exists():
            dst = asset_dir / f"{key}.png"
            shutil.copyfile(src, dst)
            copied[key] = f"assets/{dst.name}"
    return copied


def render_lecture_formula_pack(out: Path, assets: dict[str, str]) -> None:
    parts = [doc_preamble("备课笔记公式化整理")]
    parts.append("\\section*{来源说明}\n\\addcontentsline{toc}{section}{来源说明}")
    parts.append(
        "\\begin{chapterbox}{处理原则}\n"
        "手写 PDF 中可辨识的备课思路被整理为规范公式、作图步骤和课堂提示；无法稳定 OCR 的部分不逐字转写，只抽取题型结构和讲解方法。\n"
        "\\end{chapterbox}"
    )
    for section in LECTURE_SECTIONS:
        parts.append(f"\\section{{{tex_escape(section['title'])}}}")
        parts.append(f"\\tagpill{{来源：{tex_escape(section['source'])}}}")
        parts.append(formula_box(section["formulas"]))
        parts.append("\\begin{methodbox}{知识点整理}\n" + itemize(section["points"]) + "\n\\end{methodbox}")
        parts.append("\\begin{chapterbox}{课堂讲法}\n" + tex_escape(section["teaching"]) + "\n\\end{chapterbox}")
        if "第五周" in section["title"] and "week5" in assets:
            parts.append("\\begin{center}\\includegraphics[width=.82\\linewidth]{" + assets["week5"] + "}\\end{center}")
        if "第四、六章" in section["title"] and "week4_answer" in assets:
            parts.append("\\begin{center}\\includegraphics[width=.78\\linewidth]{" + assets["week4_answer"] + "}\\end{center}")
        if "第1-3章" in section["title"] and "small_1_3" in assets:
            parts.append("\\begin{center}\\includegraphics[width=.72\\linewidth]{" + assets["small_1_3"] + "}\\end{center}")
    parts.append(doc_end())
    out.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    objective_rows = read_jsonl(Path(args.objective_index))
    preview_dir = Path(args.note_preview_dir)
    assets = copy_assets(preview_dir, out_dir / "assets")

    render_choice_notes(objective_rows, out_dir / "choice_review_notes.tex")
    render_big_guidance(out_dir / "big_question_guidance.tex")
    render_lecture_formula_pack(out_dir / "lecture_formula_pack.tex", assets)

    summary = {
        "tex_outputs": ["choice_review_notes.tex", "big_question_guidance.tex", "lecture_formula_pack.tex"],
        "assets": assets,
    }
    (out_dir / "latex_notes_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
