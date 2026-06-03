#!/usr/bin/env python3
"""Build a distilled course-pack scaffold from a course-material manifest."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


QUESTION_TYPES = ["objective", "calculation", "drawing", "diagnosis", "short_answer"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to manifest.jsonl.")
    parser.add_argument("--output-dir", required=True, help="Course-pack output directory.")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def unique_sources(records: list[dict[str, Any]], roles: set[str] | None = None) -> list[str]:
    values = sorted(
        {
            record["relative_path"]
            for record in records
            if roles is None or record.get("role") in roles
        }
    )
    return values


def tags_for(records: list[dict[str, Any]], roles: set[str] | None = None) -> Counter:
    counter: Counter = Counter()
    for record in records:
        if roles is not None and record.get("role") not in roles:
            continue
        counter.update(record.get("topic_tags") or [])
    return counter


def source_examples(records: list[dict[str, Any]], tag: str, limit: int = 4) -> list[str]:
    seen: list[str] = []
    for record in records:
        if record.get("role") == "holdout":
            continue
        if tag not in (record.get("topic_tags") or []):
            continue
        rel = record["relative_path"]
        page = f" p.{record['page']}" if record.get("page") else ""
        item = f"`{rel}`{page}"
        if item not in seen:
            seen.append(item)
        if len(seen) >= limit:
            break
    return seen


def infer_question_type(record: dict[str, Any]) -> str:
    rel = record.get("relative_path", "")
    sample = record.get("text_sample", "")
    haystack = f"{rel} {sample}"
    if record.get("material_type") == "image" and record.get("role") == "holdout":
        name = Path(rel).stem.lower()
        if "b-1" in name:
            return "objective"
        if "b-4" in name:
            return "diagnosis"
        if any(token in name for token in ["b-2", "g-4"]) or "摩擦圆" in rel:
            return "drawing"
        if any(token in name for token in ["b-3", "g-1", "g-2", "g-3"]) or any(
            token in rel for token in ["解析法", "加速度", "章"]
        ):
            return "calculation"
    if any(token in haystack for token in ["结构错误", "错误", "诊断", "改正", "正确结构图"]):
        return "diagnosis"
    if any(token in haystack for token in ["画", "绘制", "作图", "标出", "受力方向", "结构图", "啮合线"]):
        return "drawing"
    if any(token in haystack for token in ["计算", "校核", "求", "设计", "MPa", "mm", "rad/s"]):
        return "calculation"
    if any(token in haystack for token in ["选择题", "单项选择", "填空题", "A", "B", "C", "D"]):
        return "objective"
    return "short_answer"


def rubric_for(question_type: str) -> list[str]:
    return {
        "objective": ["答案正确", "理由能对应概念或公式", "不误用相近概念"],
        "calculation": ["方法选择正确", "公式正确", "代入与单位正确", "结果与校核合理"],
        "drawing": ["关键构造实体完整", "方向/点名/半径标注正确", "图文结论一致", "说明常见扣分点"],
        "diagnosis": ["错误编号清晰", "原因解释正确", "修改建议可执行", "必要时给出正确结构图"],
        "short_answer": ["概念表述准确", "覆盖关键条件", "语言简洁有层次"],
    }[question_type]


def build_question_bank(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bank: list[dict[str, Any]] = []
    for record in records:
        if record["material_type"] not in {"pdf_page", "image"}:
            continue
        rel = record["relative_path"]
        sample = record.get("text_sample", "")
        is_questionish = record["role"] == "holdout" or any(
            token in f"{rel} {sample}" for token in ["题", "考试", "习题", "选择", "填空", "计算", "结构", "画", "绘制"]
        )
        if not is_questionish:
            continue
        question_type = infer_question_type(record)
        bank.append(
            {
                "question_id": f"q_{len(bank) + 1:04d}",
                "type": question_type,
                "source_path": record["path"],
                "source_relative_path": rel,
                "source_page": record.get("page"),
                "source_image": None if record["material_type"] == "pdf_page" else record["path"],
                "holdout": record["role"] == "holdout",
                "topic_tags": record.get("topic_tags") or [],
                "answer_key": None if record["role"] != "answer_key" else "source is labeled answer_key",
                "rubric": rubric_for(question_type),
                "text_sample": sample,
            }
        )
    return bank


def write_course_map(pack_dir: Path, records: list[dict[str, Any]]) -> None:
    tag_counts = tags_for(records, {"distill_source", "answer_key"})
    source_count = len(unique_sources(records, {"distill_source", "answer_key"}))
    holdout_count = len(unique_sources(records, {"holdout"}))
    lines = [
        "# 机原机设课程图谱",
        "",
        "本课程包由非 holdout 材料生成，用于学生答疑、教师备课、出题和复习组织。holdout 往年题只用于评测。",
        "",
        f"- 可用于蒸馏的来源文件数：{source_count}",
        f"- 保留评测来源文件数：{holdout_count}",
        "",
        "## 主线结构",
        "",
        "- 机械原理：机构组成、运动分析、力分析、凸轮、齿轮啮合与轮系。",
        "- 机械设计：强度与疲劳、连接、轴系、齿轮/蜗杆/带链传动、轴承、结构诊断。",
        "- 复习方法：先建知识框架，再按题型训练，最后用往年题做闭卷诊断。",
        "",
        "## 主题覆盖",
        "",
    ]
    for tag, count in tag_counts.most_common():
        examples = "；".join(source_examples(records, tag))
        lines.append(f"- **{tag}**：{count} 条记录。来源示例：{examples or '待补充'}")
    lines.extend(
        [
            "",
            "## 使用建议",
            "",
            "- 学生模式先问题型，再走公式/构造/诊断模板。",
            "- 教师模式先抽考点，再生成例题、变式题和评分细则。",
            "- 对扫描页、手写笔记、结构图题，优先保留图片引用并使用局部视觉理解。",
        ]
    )
    pack_dir.joinpath("course_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_exam_taxonomy(pack_dir: Path, question_bank: list[dict[str, Any]]) -> None:
    by_type = Counter(item["type"] for item in question_bank)
    lines = [
        "# 考试题型与评分框架",
        "",
        "## 题型分布候选",
        "",
    ]
    for kind in QUESTION_TYPES:
        lines.append(f"- `{kind}`：{by_type.get(kind, 0)} 个候选记录")
    lines.extend(
        [
            "",
            "## 题型处理策略",
            "",
            "- 客观题：答案 + 关键概念 + 易混点。",
            "- 计算题：已知量、公式、代入、单位、结果校核。",
            "- 作图题：图源引用、构造对象、标注、结论、得分点。",
            "- 结构诊断题：编号圈错、错误原因、修改建议、正确结构图或文字构造。",
            "- 简答题：定义、适用条件、失效形式、设计准则或对比表。",
            "",
            "## 高频扣分点",
            "",
            "- 公式会背但没有写适用条件。",
            "- 把节圆、基圆、分度圆或实际中心距混用。",
            "- 结构诊断只写结论不解释原因。",
            "- 运动分析中速度/加速度方向和符号约定不清。",
            "- 机械设计题漏掉单位、许用条件或安全系数判断。",
        ]
    )
    pack_dir.joinpath("exam_taxonomy.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_formula_cards(pack_dir: Path) -> None:
    lines = [
        "# 公式卡片",
        "",
        "## 机械原理",
        "",
        "- 平面机构自由度：$F = 3n - 2p_l - p_h$，先判断复合铰链、局部自由度和虚约束。",
        "- 位移解析法：建立闭环矢量方程，分解为 $x/y$ 两个标量方程。",
        "- 速度分析：对位移方程求导，注意转动项方向相差 $90^\\circ$。",
        "- 加速度分析：继续求导，区分切向加速度和法向加速度。",
        "- 渐开线齿轮：$d=mz$，基圆 $d_b=d\\cos\\alpha$，中心距变化会改变啮合角。",
        "- 轮系传动比：先判定定轴、周转或复合轮系，再写方向关系。",
        "",
        "## 机械设计",
        "",
        "- 疲劳应力：$\\sigma_m=(\\sigma_{max}+\\sigma_{min})/2$，$\\sigma_a=(\\sigma_{max}-\\sigma_{min})/2$。",
        "- 螺纹自锁：比较螺旋升角与当量摩擦角，注意牙型角影响当量摩擦系数。",
        "- 键连接强度：静连接重在挤压/剪切，动连接重在磨损压强。",
        "- 齿轮接触强度：按较弱齿轮许用接触应力校核。",
        "- 带传动：检查包角、张紧、弹性滑动与打滑区别。",
        "- 滑动轴承：校核 $p$ 防磨损，校核 $pv$ 防温升胶合。",
        "",
        "## 使用方式",
        "",
        "先判断题型和失效/运动机理，再选公式；不要从公式倒推题型。",
    ]
    pack_dir.joinpath("formula_cards.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_answer_templates(pack_dir: Path) -> None:
    lines = [
        "# 答案模板",
        "",
        "## 学生答题模板",
        "",
        "1. 题型判断：本题属于哪类题，为什么。",
        "2. 已知与目标：列变量、单位、求解对象。",
        "3. 方法与公式：写核心关系和适用条件。",
        "4. 代入求解：保留关键步骤。",
        "5. 结论检查：单位、方向、安全或合理性。",
        "6. 易错诊断：指出本题最容易错在哪里。",
        "",
        "## 教师答案模板",
        "",
        "1. 标准答案。",
        "2. 分步评分点。",
        "3. 常见错误与对应补救讲法。",
        "4. 变式题参数或图形改造方式。",
        "5. 课堂讲解顺序：概念、例题、诊断、练习。",
        "",
        "## 作图/诊断题模板",
        "",
        "- 图源：本地路径 + 页码/图片名。",
        "- 标注：①②③ 对应实体、错误或构造线。",
        "- 原理：一句话说明判断依据。",
        "- 修改：文字说明或简图。",
        "- 得分：按编号列评分点。",
    ]
    pack_dir.joinpath("answer_templates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_teacher_prep(pack_dir: Path) -> None:
    lines = [
        "# 教师备课与出题包",
        "",
        "## 一课一策",
        "",
        "- 课前：根据本章考点选择 3 类题型：概念判断、计算校核、图形诊断。",
        "- 课中：先讲题型识别，再讲公式来源，最后讲评分与易错诊断。",
        "- 课后：用 5-8 道题形成闭环，客观题查概念，计算题查流程，作图题查表达。",
        "",
        "## 一生一策",
        "",
        "- 基础薄弱：先公式卡片 + 简答题，降低题图复杂度。",
        "- 会算但丢分：强化单位、方向、标注和评分点。",
        "- 冲高分：加入结构诊断、变式参数和跨章节综合题。",
        "",
        "## 出题流程",
        "",
        "1. 选考点和题型。",
        "2. 选源题或教材例题作为结构参考。",
        "3. 改参数或图形，不改变核心能力点。",
        "4. 写标准答案和评分点。",
        "5. 写 2-3 个常见错误作为讲评材料。",
    ]
    pack_dir.joinpath("teacher_prep.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review_outline(output_dir: Path) -> None:
    review_dir = output_dir / "review_decks"
    review_dir.mkdir(parents=True, exist_ok=True)
    slides = [
        {
            "title": "机原机设期末复习总览",
            "bullets": ["一课一策：先知识框架，再题型训练", "一生一策：按错误类型安排复习路径", "保留往年题作为最后诊断"],
        },
        {
            "title": "课程知识框架",
            "bullets": ["机械原理：机构、运动、力、凸轮、齿轮、轮系", "机械设计：强度、连接、传动、轴系、轴承", "两门课共同考察工程判断"],
        },
        {
            "title": "机械原理答题主线",
            "bullets": ["先判机构和自由度", "再列位移/速度/加速度关系", "作图题必须标点、线、方向和结论"],
        },
        {
            "title": "机械设计答题主线",
            "bullets": ["先判失效形式", "再选强度/刚度/寿命校核公式", "结构诊断要编号、原因、修改建议"],
        },
        {
            "title": "高频题型",
            "bullets": ["客观题：概念和适用条件", "计算题：公式、单位、校核", "图形题：标注和构造过程"],
        },
        {
            "title": "画图题处理",
            "bullets": ["保留原图引用", "用①②③标注构造或错误", "给出得分点和易错诊断"],
        },
        {
            "title": "教师备课",
            "bullets": ["每章准备例题、变式题、诊断题", "用评分点指导学生表达", "用错题反推薄弱概念"],
        },
        {
            "title": "Holdout评测",
            "bullets": ["蒸馏前后同题对比", "客观题看准确率", "计算/图题看评分点覆盖"],
        },
    ]
    outline_lines = ["# 机原机设复习课件大纲", ""]
    for index, slide in enumerate(slides, start=1):
        outline_lines.append(f"## {index}. {slide['title']}")
        outline_lines.extend(f"- {bullet}" for bullet in slide["bullets"])
        outline_lines.append("")
    review_dir.joinpath("tju_mech_review_outline.md").write_text("\n".join(outline_lines), encoding="utf-8")
    review_dir.joinpath("deck_spec.json").write_text(
        json.dumps({"title": "机原机设期末复习", "slides": slides}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_summary(output_dir: Path, records: list[dict[str, Any]], question_bank: list[dict[str, Any]]) -> None:
    by_role = Counter(record["role"] for record in records)
    by_qtype = Counter(item["type"] for item in question_bank)
    lines = [
        "# Course Pack Build Summary",
        "",
        f"- Manifest records: {len(records)}",
        f"- Question-bank candidates: {len(question_bank)}",
        "",
        "## Roles",
        "",
    ]
    lines.extend(f"- {role}: {count}" for role, count in sorted(by_role.items()))
    lines.extend(["", "## Question Types", ""])
    lines.extend(f"- {kind}: {by_qtype.get(kind, 0)}" for kind in QUESTION_TYPES)
    lines.extend(
        [
            "",
            "## Contamination Guard",
            "",
            "- `distilled_course_pack/` is generated from non-holdout records only.",
            "- Holdout records are retained only in `question_bank.jsonl` and evaluation templates.",
        ]
    )
    output_dir.joinpath("build_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    manifest = Path(args.manifest).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    pack_dir = output_dir / "distilled_course_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)

    records = read_jsonl(manifest)
    non_holdout = [record for record in records if record.get("role") != "holdout"]
    question_bank = build_question_bank(records)
    write_jsonl(output_dir / "question_bank.jsonl", question_bank)

    write_course_map(pack_dir, non_holdout)
    write_exam_taxonomy(pack_dir, question_bank)
    write_formula_cards(pack_dir)
    write_answer_templates(pack_dir)
    write_teacher_prep(pack_dir)
    write_review_outline(output_dir)
    write_summary(output_dir, records, question_bank)

    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "pack_dir": str(pack_dir),
                "question_bank": str(output_dir / "question_bank.jsonl"),
                "questions": len(question_bank),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
