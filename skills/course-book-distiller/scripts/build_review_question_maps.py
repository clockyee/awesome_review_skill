#!/usr/bin/env python3
"""Build chapter-grouped review maps for objective, big, and textbook exercises."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from pypdf import PdfReader


UPPER_TEXTBOOK = "/Users/yizhang/paper/how2learn/学业辅导-机原机设/教材/机械原理与机械设计  上册 (OCR).pdf"
LOWER_TEXTBOOK = "/Users/yizhang/paper/how2learn/学业辅导-机原机设/机原机设题目/机械原理与机械设计  下册  第3版_14572614(OCR).pdf"


OBSERVED_OBJECTIVE_ITEMS: list[dict[str, Any]] = [
    {
        "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
        "paper": "A/D卷",
        "kind": "填空",
        "stem": "在步式棘轮机构中，从动棘轮作何种运动，适用于何种工况。",
        "chapter": "上册 第十章 其他常用机构 / 棘轮机构",
        "test_point": "棘轮机构的间歇运动特征与适用场景",
        "answer_hint": "从动棘轮作单向间歇转动；常用于间歇进给、计数、防逆转等场合。",
        "review_prompt": "给出棘轮、槽轮、不完全齿轮三种机构，比较其运动连续性和适用场景。",
    },
    {
        "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
        "paper": "A/D卷",
        "kind": "填空",
        "stem": "平底直动从动件盘形凸轮机构中，压力角与推程压力角变化。",
        "chapter": "上册 第七章 凸轮机构",
        "test_point": "平底从动件压力角、基圆半径与推程压力角",
        "answer_hint": "平底垂直导路的平底从动件凸轮压力角通常为常值；基圆半径相同时，合理配置可减小推程压力角。",
        "review_prompt": "比较尖顶、滚子、平底从动件在压力角和轮廓设计上的差异。",
    },
    {
        "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
        "paper": "A/D卷",
        "kind": "填空",
        "stem": "斜齿圆柱齿轮的模数和压力角标准值规定在何处。",
        "chapter": "上册 第八章 齿轮机构 / 下册 第十八章 齿轮传动",
        "test_point": "斜齿轮法面参数为标准参数",
        "answer_hint": "斜齿圆柱齿轮以法面模数、法面压力角为标准值。",
        "review_prompt": "说明法面模数、端面模数、螺旋角在斜齿轮几何计算中的关系。",
    },
    {
        "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
        "paper": "A/D卷",
        "kind": "填空",
        "stem": "效率相同机器并联/串联时机组效率变化。",
        "chapter": "上册 第五章 平面机构的力分析 / 机械效率",
        "test_point": "串联效率相乘、并联效率按功率分配加权",
        "answer_hint": "串联环节越多总效率越低；并联机组效率与各支路效率和功率分配有关，相同效率并联时不因并联数量改变。",
        "review_prompt": "给两级串联传动和两支路并联传动，分别写总效率公式。",
    },
    {
        "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
        "paper": "A/D卷",
        "kind": "填空",
        "stem": "刚性转子径宽比达到某条件时需要动平衡及平衡基面数。",
        "chapter": "上册 第十二章 机械的平衡",
        "test_point": "静平衡、动平衡和单/双面平衡",
        "answer_hint": "宽径比较大的刚性转子通常需动平衡，至少在两个平衡基面上配置平衡质量。",
        "review_prompt": "解释为什么动平衡又称双面平衡，静平衡又称单面平衡。",
    },
    {
        "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
        "paper": "A/D卷",
        "kind": "填空",
        "stem": "正变位渐开线直齿圆柱齿轮的分度圆半径和分度圆齿厚变化。",
        "chapter": "上册 第八章 齿轮机构",
        "test_point": "变位齿轮分度圆不变、齿厚变化",
        "answer_hint": "同一模数和齿数下分度圆半径不变；正变位使分度圆齿厚增大。",
        "review_prompt": "列出正变位对齿根强度、齿顶厚、啮合角和中心距的影响。",
    },
    {
        "source": "机原往年题c/c-1.jpg",
        "paper": "C卷",
        "kind": "填空/选择",
        "stem": "带传动设计中，小带轮最小基准直径的限制原因。",
        "chapter": "下册 第十七章 带传动和链传动",
        "test_point": "限制带的弯曲应力",
        "answer_hint": "小带轮直径过小会使带弯曲应力过大，降低疲劳寿命。",
        "review_prompt": "V带设计中哪些参数需要圆整后复核。",
    },
    {
        "source": "机原往年题c/c-1.jpg",
        "paper": "C卷",
        "kind": "填空/选择",
        "stem": "平键的工作面、两个平键的布置角度。",
        "chapter": "下册 第十五章 轴毂连接",
        "test_point": "平键侧面工作、双键相隔180度",
        "answer_hint": "平键以两个侧面为工作面；承载能力不足用两个平键时常相隔180度。",
        "review_prompt": "比较平键、楔键、半圆键、花键的工作面与失效形式。",
    },
    {
        "source": "机原往年题c/c-1.jpg",
        "paper": "C卷",
        "kind": "填空/选择",
        "stem": "链传动最大齿数、V带楔角、链传动比关系。",
        "chapter": "下册 第十七章 带传动和链传动",
        "test_point": "链磨损脱链限制、V带楔形增压、链传动比",
        "answer_hint": "链轮齿数过多会加剧磨损后脱链风险；V带槽角小于带楔角；链传动比按链轮齿数比确定。",
        "review_prompt": "解释链传动为什么通常链节数取偶数。",
    },
    {
        "source": "机原往年题c/c-1.jpg",
        "paper": "C卷",
        "kind": "填空/选择",
        "stem": "闭式硬齿面齿轮传动主要失效形式。",
        "chapter": "下册 第十八章 齿轮传动",
        "test_point": "硬齿面齿根弯曲疲劳常为主要失效约束",
        "answer_hint": "闭式硬齿面齿轮常以轮齿疲劳折断为主要危险，仍需按题意区分点蚀、磨损和胶合。",
        "review_prompt": "比较闭式软齿面、闭式硬齿面、开式齿轮的设计准则。",
    },
    {
        "source": "机原往年题c/c-1.jpg",
        "paper": "C卷",
        "kind": "填空/选择",
        "stem": "蜗杆传动中不成立的传动比关系。",
        "chapter": "下册 第十九章 蜗杆传动",
        "test_point": "蜗杆传动比由转速比和齿数/头数比确定，不由直径比确定",
        "answer_hint": "蜗杆传动中 i=n1/n2=z2/z1；直径比 d2/d1 不是传动比。",
        "review_prompt": "说明蜗杆头数、蜗轮齿数、导程角与效率之间的关系。",
    },
    {
        "source": "机原往年题c/c-1.jpg",
        "paper": "C卷",
        "kind": "填空/选择",
        "stem": "不充分润滑滑动轴承中限制 p 值的目的。",
        "chapter": "下册 第二十二章 滑动轴承",
        "test_point": "限制压强防止过度磨损",
        "answer_hint": "限制 p 主要防止轴承材料过度磨损或塑性变形；限制 pv 主要防止过热。",
        "review_prompt": "分别说明 p、v、pv 三个条件性计算指标的物理意义。",
    },
    {
        "source": "机原往年题c/c-1.jpg",
        "paper": "C卷",
        "kind": "填空/选择",
        "stem": "螺栓连接中采用双螺母的目的。",
        "chapter": "下册 第十四章 螺纹紧固件连接",
        "test_point": "防松",
        "answer_hint": "双螺母通过附加摩擦和互锁防止螺纹连接松动，不是提高强度或刚度。",
        "review_prompt": "按摩擦防松、机械防松、破坏螺纹副关系防松列举典型方法。",
    },
    {
        "source": "机原往年题e/e-1.png",
        "paper": "E卷",
        "kind": "填空",
        "stem": "机构、主动件、从动件和确定运动条件。",
        "chapter": "上册 第三章 机构的组成和结构分析",
        "test_point": "机构定义和 F=原动件数",
        "answer_hint": "机构是具有确定相对运动的构件系统；从动件按主动件规律运动；运动数等于从动件独立运动数。",
        "review_prompt": "给一机构自由度计算结果，判断需要几个原动件。",
    },
    {
        "source": "机原往年题e/e-1.png; 机原往年题f/f-1.png; 机原往年题g/g-1.png",
        "paper": "E/F/G卷",
        "kind": "填空/判断",
        "stem": "机械平衡、静平衡、动平衡、飞轮速度波动。",
        "chapter": "上册 第十一章机械系统动力学 / 第十二章机械的平衡",
        "test_point": "飞轮、周期性速度波动、静/动平衡条件",
        "answer_hint": "飞轮减小周期性速度波动；动平衡需满足惯性力和惯性力矩平衡，静平衡只需惯性力合力为零。",
        "review_prompt": "判断不论平衡质量如何分布，只在任意平面加一个平衡质量能否达到动平衡。",
    },
    {
        "source": "机原往年题f/f-1.png; 机原往年题g/g-1.png",
        "paper": "F/G卷",
        "kind": "填空/选择",
        "stem": "单销外槽轮槽数、运动/静止时间、冲击类型。",
        "chapter": "上册 第十章 其他常用机构 / 槽轮机构",
        "test_point": "槽轮机构几何约束、间歇运动时间和冲击",
        "answer_hint": "外槽轮槽数通常不少于3；槽轮机构由加速度突变引起柔性冲击，若存在速度突变则为刚性冲击。",
        "review_prompt": "说明槽轮机构与棘轮机构的间歇运动差异。",
    },
    {
        "source": "机原往年题g/g-1.png",
        "paper": "G卷",
        "kind": "选择/判断",
        "stem": "标准直齿圆柱齿轮齿顶圆直径和标准中心距啮合条件。",
        "chapter": "上册 第八章 齿轮机构",
        "test_point": "齿顶圆公式、标准中心距啮合角等于压力角",
        "answer_hint": "标准齿轮 da=m(z+2ha*)；标准中心距安装时啮合角等于分度圆压力角。",
        "review_prompt": "给 m、z、ha*，计算 d、db、da、df 并判断中心距变化后的 α'。",
    },
    {
        "source": "机原往年题g/g-1.png",
        "paper": "G卷",
        "kind": "判断",
        "stem": "用位移矩阵法综合 R-R 型导引机构时约束方程写法。",
        "chapter": "上册 第六章 连杆机构",
        "test_point": "刚体导引机构综合与位移矩阵",
        "answer_hint": "R-R 型导引机构综合需要根据给定位置列定长约束方程。",
        "review_prompt": "说明位移矩阵和相对位移矩阵分别用于哪类综合问题。",
    },
]


BIG_EXTRA_EXAMPLES = {
    "free_degree_structure": ["机原往年题e/e-1.png", "机原往年题f/f-1.png", "机原往年题g/g-1.png", "机原往年题1/1-1.png"],
    "cam_profile": ["机原往年题a/a-1.png", "机原往年题1/0-0.png"],
    "gear_parameter_design": ["机原往年题1/0-1.png"],
    "shafting_diagnosis": ["机原往年题1/0-0.png"],
    "gear_train": ["机原往年题e/e-1.png", "机原往年题f/f-1.png", "机原往年题1/0-0.png"],
}


TYPE_TO_CHAPTER = {
    "free_degree_structure": "上册 第三章 机构的组成和结构分析",
    "planar_motion_analysis": "上册 第四章 平面机构的运动分析",
    "force_friction_self_lock": "上册 第五章 平面机构的力分析",
    "cam_profile": "上册 第七章 凸轮机构",
    "involute_gear_drawing": "上册 第八章 齿轮机构",
    "worm_gear_force_direction": "下册 第十八章齿轮传动 / 第十九章蜗杆传动",
    "bolt_group": "下册 第十四章 螺纹紧固件连接",
    "belt_chain_drive": "下册 第十七章 带传动和链传动",
    "bearing_life": "下册 第二十一章 滚动轴承",
    "gear_parameter_design": "下册 第十八章 齿轮传动",
    "shafting_diagnosis": "下册 第二十六章 轴系及轮类零件的结构设计",
    "structure_correction": "下册 第十四/十五/二十六章 结构设计",
    "gear_train": "上册 第九章 轮系",
}


CHAPTER_METHODS = {
    "第一章": "概念题按定义-组成-功能作答，重点区分机器、机构、构件、零件。",
    "第三章": "先数构件和运动副，再检查复合铰链、局部自由度、虚约束，最后判断 F 是否等于原动件数。",
    "第四章": "速度题可用瞬心法，位移/速度/加速度完整题用矢量方程和求导。",
    "第五章": "先画分离体图和摩擦方向，再写平衡方程；自锁题必须给摩擦角或效率判据。",
    "第六章": "四杆机构先判类型、急回、压力角和传动角；综合题写约束方程或作图构造。",
    "第七章": "凸轮题先画位移线图，再用反转法生成理论轮廓和实际轮廓。",
    "第八章": "齿轮机构题先列 d、db、da、df、a、alpha'，作图题必须在图上标啮合线和节点。",
    "第九章": "轮系题先分定轴/周转/复合轮系，固定行星架或用转化机构法求传动比。",
    "第十章": "间歇机构题按运动特征、锁止、槽数/齿数约束和冲击类型作答。",
    "第十一章": "动力学题抓等效转动惯量、等效力矩、盈亏功和飞轮速度波动。",
    "第十二章": "平衡题分别写惯性力合力和惯性力矩合力条件，单面/双面不要混用。",
    "第十三章": "强度准则题先判断静/疲劳、塑性/脆性、应力状态，再选安全系数或强度理论。",
    "第十四章": "螺栓题先判受拉、受剪、预紧或偏心螺栓组，再选拉伸、剪切、挤压或疲劳校核。",
    "第十五章": "键连接题抓工作面、定位、失效形式、双键布置和强度校核。",
    "第十六章": "螺旋传动题写升角、当量摩擦角、自锁、效率和强度/耐磨校核。",
    "第十七章": "带链题按计算功率、标准参数、包角、速度、根数/链节数和失效准则作答。",
    "第十八章": "齿轮传动题先判失效形式和设计准则，再进行几何参数和强度校核。",
    "第十九章": "蜗杆题抓 z1、z2、导程角、效率、热平衡和传动比不是直径比。",
    "第二十章": "轴设计题先按扭矩估径，再按结构、强度、刚度、临界转速校核。",
    "第二十一章": "滚动轴承题先求支反力和轴向力分配，再选 X/Y、P、寿命。",
    "第二十二章": "滑动轴承题区分 p、v、pv，流体动压润滑题画楔形油膜和相对速度。",
    "第二十三章": "联轴器题按两轴偏移补偿能力、载荷、转速、刚柔性选择。",
    "第二十六章": "轴系诊断题必须编号，写固定/游动端、轴向力路线、装拆与密封。",
    "第二十八章": "方案设计题先功能分解，再列可选机构、运动循环和评价指标。",
    "第二十九章": "传动系统设计题按功率流、传动比分配、效率、布置和执行时序作答。",
}

OFFICIAL_CHAPTER_NAMES = {
    "第一章": "第一章 机械的组成、分类与发展",
    "第二章": "第二章 本课程在产品全生命周期中的地位和作用",
    "第三章": "第三章 机构的组成和结构分析",
    "第四章": "第四章 平面机构的运动分析",
    "第五章": "第五章 平面机构的力分析",
    "第六章": "第六章 连杆机构",
    "第七章": "第七章 凸轮机构",
    "第八章": "第八章 齿轮机构",
    "第九章": "第九章 轮系",
    "第十章": "第十章 其他常用机构",
    "第十一章": "第十一章 机械系统动力学",
    "第十二章": "第十二章 机械的平衡",
    "第十三章": "第十三章 机械零件设计基础",
    "第十四章": "第十四章 螺纹紧固件连接",
    "第十五章": "第十五章 轴毂连接",
    "第十六章": "第十六章 螺旋传动",
    "第十七章": "第十七章 带传动和链传动",
    "第十八章": "第十八章 齿轮传动",
    "第十九章": "第十九章 蜗杆传动",
    "第二十章": "第二十章 轴的设计计算",
    "第二十一章": "第二十一章 滚动轴承",
    "第二十二章": "第二十二章 滑动轴承",
    "第二十三章": "第二十三章 联轴器、离合器和制动器",
    "第二十四章": "第二十四章 弹簧",
    "第二十五章": "第二十五章 机械结构设计的方法和准则",
    "第二十六章": "第二十六章 轴系及轮类零件的结构设计",
    "第二十七章": "第二十七章 机架、箱体和导轨的结构设计",
    "第二十八章": "第二十八章 机械执行系统的方案设计",
    "第二十九章": "第二十九章 机械传动系统的方案设计",
    "第三十章": "第三十章 创新设计的基本原理与常用技法",
    "第三十一章": "第三十一章 机械创新设计方法",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--choice-data", required=True)
    parser.add_argument("--big-index", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def chapter_key(chapter: str) -> str:
    match = re.search(r"(第[一二三四五六七八九十百二十]+章[^/，, ]*)", chapter)
    return match.group(1) if match else chapter.split("/")[0].strip()


def clean_chapter(chapter: str) -> str:
    for key, name in OFFICIAL_CHAPTER_NAMES.items():
        if key in chapter:
            return name
    return chapter.strip()


def format_cell(value: Any) -> str:
    if isinstance(value, dict):
        prompt = value.get("prompt", "")
        answer = value.get("answer", "")
        return f"{prompt} 答：{answer}".strip()
    if isinstance(value, list):
        return "；".join(format_cell(item) for item in value)
    text = str(value)
    return text.replace("|", "/").replace("\n", " ")


def load_b_choice_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for q in data["questions"]:
        citation = q["textbook_citations"][0]
        rows.append(
            {
                "source": "机原往年题b/b-1.png",
                "paper": "B卷",
                "kind": "选择",
                "stem": q["stem"],
                "answer": q["answer"],
            "chapter": clean_chapter(citation["chapter"]),
                "pdf_page": citation["pdf_page"],
                "test_point": q["analysis"].split("。")[0],
                "answer_hint": q["analysis"],
                "review_prompt": (q.get("related_review_questions") or [""])[0],
            }
        )
    return rows


def render_choice_doc(rows: list[dict[str, Any]], out: Path) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[chapter_key(clean_chapter(row["chapter"]))].append(row)
    lines = [
        "# 往年题选择/填空/判断考点章节分类复习文档",
        "",
        "说明：B 卷选择题来自已精修题卡；A/C/D/E/F/G 卷当前按试卷图像视觉读取归纳为考点条目。学生复习时先按章节刷概念，再回到原卷做题。",
        "",
        "## 总览",
        "",
        "| 章节 | 题量/考点数 | 高频考法 |",
        "|---|---:|---|",
    ]
    for chapter, items in sorted(grouped.items()):
        hot = "；".join(dict.fromkeys(format_cell(item["test_point"]) for item in items[:3]))
        lines.append(f"| {chapter} | {len(items)} | {hot} |")

    for chapter, items in sorted(grouped.items()):
        lines.extend(["", f"## {chapter}", ""])
        method = next((v for k, v in CHAPTER_METHODS.items() if k in chapter), "按定义、公式入口、易错辨析三步复习。")
        lines.extend([f"复习方法：{method}", "", "| 来源 | 题型 | 考点 | 答题锚点 | 迁移复习题 |", "|---|---|---|---|---|"])
        for item in items:
            answer = format_cell(item.get("answer") or item.get("answer_hint", ""))
            if len(answer) > 120:
                answer = answer[:118] + "..."
            lines.append(
                f"| {item['source']} | {item['kind']} | {format_cell(item['test_point'])} | {answer} | {format_cell(item.get('review_prompt',''))} |"
            )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_big_doc(index_rows: list[dict[str, Any]], out: Path) -> None:
    lines = [
        "# 所有试卷大题分类解析文档",
        "",
        "说明：本文件把 a-g、机原往年题1、B/G示范题中的大题按题型存储。每类题保留来源、章节、公式入口、解题步骤、评分点和易错诊断，便于之后逐题生成图上作答。",
        "",
    ]
    for row in index_rows:
        type_id = row["type_id"]
        examples = list(dict.fromkeys(row.get("source_examples", []) + BIG_EXTRA_EXAMPLES.get(type_id, [])))
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- 章节定位：{TYPE_TO_CHAPTER.get(type_id, '待定位')}",
                f"- 来源样例：{'; '.join(examples)}",
                f"- 答题产物：{row.get('student_output', '')}",
                "",
                "公式入口：",
                "",
            ]
        )
        for formula in row.get("formula_entry", []):
            lines.append(f"- `{formula}`")
        lines.extend(["", "标准解题步骤：", ""])
        steps = [
            "题型判断：先说明为什么选用该方法。",
            "已知与目标：把图中尺寸、力、转速、齿数、方向约定写清。",
            "核心关系：写公式或作图构造关系。",
            "代入求解：保留单位和方向。",
            "结果检查：做标准值、方向、强度或运动确定性校核。",
        ]
        for idx, step in enumerate(steps, 1):
            lines.append(f"{idx}. {step}")
        lines.extend(["", "评分点："])
        for item in row.get("rubric", []):
            lines.append(f"- {item}")
        lines.extend(["", "易错诊断："])
        for item in row.get("common_mistakes", []):
            lines.append(f"- {item}")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def extract_exercise_pages(pdf_path: str, book: str) -> list[dict[str, Any]]:
    reader = PdfReader(pdf_path)
    rows: list[dict[str, Any]] = []
    current_chapter = ""
    exercise_mode = False
    for page_no, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        compact = " ".join(text.split())
        chapter_match = re.search(r"(第[一二三四五六七八九十百二十]+章\s*[^-\n·…]{2,28})", compact)
        if chapter_match:
            next_chapter = chapter_match.group(1).strip()
            if next_chapter != current_chapter and not re.search(r"习\s*题", compact):
                exercise_mode = False
            current_chapter = clean_chapter(next_chapter)
        if page_no > 20 and re.search(r"习\s*题", compact) and "目录" not in compact[:80]:
            exercise_mode = True
        ids = sorted(set(re.findall(r"\b(\d{1,2}-\d{1,2})\b", compact)))
        if exercise_mode and (ids or re.search(r"习\s*题", compact)):
            if ids:
                rows.append(
                    {
                        "book": book,
                        "pdf_path": pdf_path,
                        "pdf_page": page_no,
                        "chapter": clean_chapter(current_chapter),
                        "exercise_ids": ids,
                        "text_sample": compact[:500],
                    }
                )
    return rows


def method_for_chapter(chapter: str) -> str:
    for key, method in CHAPTER_METHODS.items():
        if key in chapter:
            return method
    return "先定位知识点，再按题型写公式入口、作图/计算步骤、评分点和易错诊断。"


def render_textbook_doc(rows: list[dict[str, Any]], out: Path) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("chapter") or row["book"]].append(row)

    lines = [
        "# 教材课后题蒸馏式作答索引",
        "",
        "说明：本文件从上册 OCR 与下册 OCR 中抽取课后题页和题号，按章节给出作答入口。由于大量题目依赖教材图，本版先建立全量索引和解题模板；需要精修时可按题号生成单题答案卡或图上作答。",
        "",
        "## 全量章节索引",
        "",
        "| 章节 | 页码 | 题号 | 作答方法 |",
        "|---|---|---|---|",
    ]
    for chapter, items in sorted(grouped.items()):
        for item in items:
            ids = ", ".join(item["exercise_ids"][:14])
            if len(item["exercise_ids"]) > 14:
                ids += ", ..."
            lines.append(f"| {chapter} | {item['book']} PDF p.{item['pdf_page']} | {ids} | {method_for_chapter(chapter)} |")

    lines.extend(["", "## 单题作答卡模板", ""])
    lines.extend(
        [
            "```markdown",
            "### 题号",
            "",
            "**教材定位：** 上/下册，第X章，PDF p.X。",
            "",
            "**题型判断：** 概念 / 计算 / 作图 / 诊断 / 方案设计。",
            "",
            "**已知与目标：** 从题干和图中摘出变量、单位、方向。",
            "",
            "**公式入口/构造关系：** 写核心公式或图上构造实体。",
            "",
            "**解答：** 分步代入、作图或编号诊断。",
            "",
            "**结论：** 给最终值、方向、结构修改或方案。",
            "",
            "**得分点：** 列评分点。",
            "",
            "**易错诊断：** 列最常见错误。",
            "```",
            "",
            "## 代表题示范",
            "",
            "### 3-1 机构组成要素",
            "",
            "**题型判断：** 概念题。按“构件-运动副-运动链-机架-原动件/从动件”链条作答。",
            "",
            "**答案框架：** 机构由若干构件通过运动副连接组成；具有确定相对运动时才能完成预期运动。复习时把零件和构件分清：零件是制造单元，构件是运动单元。",
            "",
            "**易错诊断：** 把多个固连零件误数成多个构件；把运动副的具体形状当成决定运动的唯一因素。",
            "",
            "### 8-7 齿轮啮合作图",
            "",
            "**题型判断：** 渐开线齿轮啮合作图。必须在图上标啮合线、节点、实际啮合线起止点和啮合角。",
            "",
            "**公式入口：** `db=d cos alpha`，中心距变化时 `cos alpha'=a cos alpha / a'`。",
            "",
            "**作答：** 画两基圆公切线为理论啮合线；与中心线交点为节点；齿顶圆截得实际啮合线起止点；再标 `N1,N2,B1,B2,P,alpha'`。",
            "",
            "**易错诊断：** 把分度圆当基圆；中心距变化后仍写标准压力角。",
            "",
            "### 14-2 受轴向外载荷的螺栓连接",
            "",
            "**题型判断：** 紧螺栓连接受轴向工作载荷。先画螺栓和被连接件的载荷-变形关系。",
            "",
            "**公式入口：** `F0=F''+F`，螺栓总拉力由剩余预紧力和工作载荷份额合成；若给刚度比，则按相对刚度分配工作载荷。",
            "",
            "**易错诊断：** 把工作载荷全部加到螺栓上；漏写剩余预紧力必须大于零。",
            "",
            "### 21-3 圆锥滚子轴承当量动载荷",
            "",
            "**题型判断：** 成对圆锥滚子轴承受径向力、轴向力。先求支反力和派生轴向力，再判哪只轴承受轴向载荷。",
            "",
            "**公式入口：** `P=f_p(XF_R+YF_A)`。",
            "",
            "**易错诊断：** 只按径向力求寿命；忽略圆锥滚子轴承需要成对处理轴向力。",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    choice_rows = load_b_choice_rows(Path(args.choice_data)) + OBSERVED_OBJECTIVE_ITEMS
    write_jsonl(output_dir / "objective_question_chapter_index.jsonl", choice_rows)
    render_choice_doc(choice_rows, output_dir / "objective_question_chapter_review.md")

    big_rows = [json.loads(line) for line in Path(args.big_index).read_text(encoding="utf-8").splitlines() if line.strip()]
    render_big_doc(big_rows, output_dir / "big_question_classified_solutions.md")

    exercise_rows = extract_exercise_pages(UPPER_TEXTBOOK, "上册") + extract_exercise_pages(LOWER_TEXTBOOK, "下册")
    write_jsonl(output_dir / "textbook_afterclass_exercise_index.jsonl", exercise_rows)
    render_textbook_doc(exercise_rows, output_dir / "textbook_afterclass_exercise_playbook.md")

    summary = {
        "objective_items": len(choice_rows),
        "big_problem_types": len(big_rows),
        "textbook_exercise_pages": len(exercise_rows),
        "outputs": [
            "objective_question_chapter_review.md",
            "objective_question_chapter_index.jsonl",
            "big_question_classified_solutions.md",
            "textbook_afterclass_exercise_playbook.md",
            "textbook_afterclass_exercise_index.jsonl",
        ],
    }
    (output_dir / "review_question_maps_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
