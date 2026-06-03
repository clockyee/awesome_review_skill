#!/usr/bin/env python3
"""Build the B-paper multiple-choice answer-card data with textbook citations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LOWER_OCR = "/Users/yizhang/paper/how2learn/学业辅导-机原机设/机原机设题目/机械原理与机械设计  下册  第3版_14572614(OCR).pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Existing B choice JSON.")
    parser.add_argument("--out", required=True, help="Output answer-card JSON.")
    return parser.parse_args()


def cite(
    chapter: str,
    pdf_page: int,
    print_page: str,
    quote_anchor: str,
    search_terms: list[str],
) -> dict[str, Any]:
    return {
        "book": "机械原理与机械设计 下册 第3版",
        "pdf_path": LOWER_OCR,
        "chapter": chapter,
        "pdf_page": pdf_page,
        "print_page": print_page,
        "quote_anchor": quote_anchor,
        "search_terms": search_terms,
    }


CITATIONS: dict[int, list[dict[str, Any]]] = {
    1: [cite("第十三章 机械零件设计基础 / 第一节 机械零件的设计计算准则", 15, "4", "应力小于许用应力；安全因数S大于许用安全因数[S]", ["许用应力", "安全因数"])],
    2: [cite("第十四章 螺纹紧固件连接 / 第三节 螺纹紧固件上的载荷", 54, "43", "螺栓所受总拉力为外载荷F与剩余预紧力之和", ["总拉力", "剩余预紧力"])],
    3: [cite("第十四章 螺纹紧固件连接 / 第二节 螺纹紧固件连接的类型", 49, "38", "铸铁H=(1.25~1.5)d", ["铸铁H=(1.25~1.5)d", "螺纹孔深度"])],
    4: [cite("第十四章 螺纹紧固件连接 / 第七节 提高紧固螺纹连接强度的措施", 64, "53", "减小螺栓系统刚度和增大被连接件系统刚度", ["减小螺栓系统刚度", "增大被连接件系统刚度"])],
    5: [cite("第十五章 轴毂连接 / 第一节 键连接", 73, "62", "两个平键，两键应相隔180°布置", ["两个平键", "相隔180"])],
    6: [cite("第十七章 带传动和链传动 / 第二节 带传动", 103, "92", "松、紧边受力不同时伸长量不等", ["弹性滑动", "松、紧边受力"])],
    7: [cite("第十七章 带传动和链传动 / 第二节 带传动", 103, "92", "带绕经小带轮时产生的弯曲应力", ["弯曲应力", "小带轮"])],
    8: [cite("第十八章 齿轮传动 / 第六节 直齿圆柱齿轮传动的齿根弯曲疲劳强度计算", 149, "138", "引入齿形系数YF", ["齿形系数", "YF"])],
    9: [cite("第十八章 齿轮传动 / 第二节 轮齿的失效形式与计算准则", 132, "121", "这种现象称为齿面点蚀", ["齿面点蚀", "闭式齿轮传动"])],
    10: [cite("第十八章 齿轮传动 / 第二节 轮齿的失效形式与计算准则", 132, "121", "为防止轮齿折断，齿轮必须具有足够大的模数", ["足够大的模数", "轮齿折断"])],
    11: [cite("第十八章 齿轮传动 / 第九节 直齿锥齿轮传动的受力分析和强度计算", 164, "153", "过齿宽中点处的背锥展开", ["齿宽中点处的背锥", "当量直齿圆柱"])],
    12: [cite("第十八章 齿轮传动 / 第五节 直齿圆柱齿轮传动的齿面接触疲劳强度计算", 148, "137", "悬臂布置 0.3~0.4 / 0.2~0.25", ["悬臂布置", "齿宽系数"])],
    13: [cite("第十九章 蜗杆传动 / 第二节 蜗杆传动的主要参数与几何尺寸", 172, "161", "蜗杆头数z1、蜗轮齿数z2", ["蜗杆头数", "蜗轮齿数"])],
    14: [cite("第十七章 带传动和链传动 / 第三节 链传动", 117, "106", "设计传动时链节数以偶数为宜", ["链节数以偶数为宜", "过渡链节"])],
    15: [cite("第十七章 带传动和链传动 / 概述与参数选择", 123, "112", "推荐i=2~3.5；链轮齿数不宜过多或过少", ["传动比", "链轮齿数"])],
    16: [cite("第二十章 轴的设计计算 / 第一节 概述", 190, "179", "工作中只承受弯矩而不传递转矩的轴称为心轴", ["只承受弯矩", "称为心轴"])],
    17: [cite("第二十二章 滑动轴承 / 第五节 滑动轴承的设计计算", 256, "245", "仅增大轴颈直径d不会使pv值减小", ["pv值", "发热"])],
    18: [cite("第二十一章 滚动轴承 / 第二节 滚动轴承的类型和选择", 213, "202", "受径向和轴向联合载荷时，常选用角接触球轴承或圆锥滚子轴承", ["圆锥滚子轴承", "联合载荷"])],
    19: [cite("第二十三章 联轴器、离合器和制动器 / 第一节 联轴器", 265, "254", "齿式联轴器对综合偏移有良好的补偿性", ["齿式联轴器", "综合偏移"])],
    20: [cite("第二十三章 联轴器、离合器和制动器 / 第一节 联轴器", 264, "253", "用铰制孔螺栓对中", ["铰制孔螺栓", "凸缘联轴器"])],
}


RELATED: dict[int, list[dict[str, str]]] = {
    1: [{"source": "教材思考题化", "prompt": "写出强度校核的两种等价表达：应力表达和安全因数表达。", "answer": "σ≤[σ]，S≥[S]。"}],
    2: [{"source": "下册习题14-2同类", "prompt": "已知轴向外载荷F和剩余预紧力，求螺栓总拉力。", "answer": "F0=F+F''。"}],
    3: [{"source": "教材表格同类", "prompt": "螺钉连接中钢/铸铁材料的旋入深度如何取？", "answer": "钢约d，铸铁约(1.25~1.5)d。"}],
    4: [{"source": "教材结构措施同类", "prompt": "受循环载荷螺栓如何降低应力幅？", "answer": "减小螺栓刚度，增大被连接件刚度。"}],
    5: [{"source": "思考题15-2", "prompt": "一个键强度不够，两个平键如何布置？", "answer": "相隔180°，校核时按约1.5个键考虑。"}],
    6: [{"source": "思考题17-2", "prompt": "弹性滑动和打滑的区别是什么？", "answer": "弹性滑动不可避免；打滑是过载或摩擦不足导致的失效。"}],
    7: [{"source": "带传动设计同类", "prompt": "为什么小带轮直径不能过小？", "answer": "小带轮使弯曲应力增大，降低疲劳寿命。"}],
    8: [{"source": "齿根弯曲强度同类", "prompt": "标准直齿圆柱齿轮齿形系数按什么查？", "answer": "按齿数查取。"}],
    9: [{"source": "思考题18-失效形式", "prompt": "闭式软齿面齿轮常见主要失效是什么？", "answer": "齿面疲劳点蚀。"}],
    10: [{"source": "齿根强度同类", "prompt": "分度圆直径不变时，增大模数对弯曲强度有什么影响？", "answer": "增大齿根承载能力，提高弯曲强度。"}],
    11: [{"source": "锥齿轮强度同类", "prompt": "直齿锥齿轮强度计算用哪个当量齿轮？", "answer": "齿宽中点背锥展开得到的当量直齿圆柱齿轮。"}],
    12: [{"source": "齿宽系数表18-12", "prompt": "齿轮悬臂布置时齿宽系数如何取？", "answer": "取小，表中软齿面0.3~0.4，硬齿面0.2~0.25。"}],
    13: [{"source": "蜗杆传动参数同类", "prompt": "蜗杆传动比由哪些量决定？", "answer": "i=n1/n2=z2/z1，不是d2/d1。"}],
    14: [{"source": "链传动接头同类", "prompt": "链节数为什么取偶数？", "answer": "避免采用强度较弱的过渡链节。"}],
    15: [{"source": "传动布置同类", "prompt": "带、齿轮、链组合时如何按速度级布置？", "answer": "带放高速级，链放低速级，齿轮居中。"}],
    16: [{"source": "轴分类同类", "prompt": "自行车前轮轴为什么是心轴？", "answer": "主要承受弯矩，不传递转矩。"}],
    17: [{"source": "滑动轴承条件计算同类", "prompt": "p、v、pv分别控制什么？", "answer": "p防压溃/过磨，v防速度过高，pv控制摩擦发热。"}],
    18: [{"source": "滚动轴承类型选择同类", "prompt": "径向和轴向联合载荷常选什么轴承？", "answer": "角接触球轴承或圆锥滚子轴承。"}],
    19: [{"source": "思考题23-3", "prompt": "说明齿式联轴器为什么允许综合偏移。", "answer": "内外齿啮合结构可补偿径向、角向等综合偏移。"}],
    20: [{"source": "凸缘联轴器同类", "prompt": "铰制孔螺栓连接传递转矩时螺栓受什么？", "answer": "受剪切和挤压。"}],
}


def convert_question(q: dict[str, Any]) -> dict[str, Any]:
    no = int(q["no"])
    distilled = q.get("distilled") or {}
    answer = q.get("correct", "")
    analysis = distilled.get("analysis") or ""
    return {
        "no": no,
        "stem": q["stem"],
        "options": q["options"],
        "answer": answer,
        "analysis": analysis,
        "textbook_citations": CITATIONS[no],
        "related_review_questions": RELATED[no],
    }


def main() -> None:
    args = parse_args()
    source = json.loads(Path(args.source).read_text(encoding="utf-8"))
    data = {
        "title": "B卷选择题：大字号答案解析卡",
        "subtitle": "学生版：不展示非蒸馏答案；每题给答案、解析、教材页码、教材局部截图和关联复习题。",
        "questions": [convert_question(q) for q in source["questions"]],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "questions": len(data["questions"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
