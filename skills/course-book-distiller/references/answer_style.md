# Answer Style Reference

Use this reference when producing student-facing solutions, teacher keys, review handouts, or drawing/diagnosis answers.

## Core Shape

For every answer, use this order:

1. **题型判断**: name the method and why it applies.
2. **已知与目标**: list variables, units, target quantity, and constraints.
3. **核心公式/构造关系**: write formulas in LaTeX or a clean text equation.
4. **代入与求解**: show substitution and only necessary arithmetic.
5. **结果与检查**: include final value, units, direction, safety condition, or pass/fail.
6. **得分点**: list what a grader should award.
7. **易错诊断**: list common wrong assumptions, sign errors, unit errors, missing annotations, or diagram mistakes.

## Objective Questions

Use a compact answer:

```markdown
**答案：C**

**理由：** ...

**易错点：** ...
```

For scanned multiple-choice papers, use a per-question vertical card layout:

- Extract each question stem and options.
- Show only the student-facing answer and explanation. Do not show baseline/non-distilled answers unless the file is explicitly an evaluation report.
- The explanation must include the textbook chapter, PDF page, printed page if known, and a short original-phrase anchor when available, e.g. `教材：下册第十八章 齿轮传动，PDF p.149；原话锚点："齿形系数"`。
- Add a local textbook snippet image when possible. The snippet should be a small crop around the cited phrase, not a whole textbook page.
- Add one related review question below the explanation so the student can immediately practice the same concept.
- Keep source quotes short; cite local page/source ids instead of reproducing textbook paragraphs.
- If the original answer area is too small, crop or preserve the question region and place the answer card below it.
- Preferred typography for rendered visual answers: Chinese in Songti, Latin in Times New Roman, formulas/math symbols in STIX or a LaTeX-like math font.

## Calculation Questions

Use a readable engineering solution:

```markdown
**方法：** 疲劳强度校核，先求平均应力和应力幅，再映射到极限应力线图。

**已知：** $\sigma_{\max}=...$，$\sigma_{\min}=...$。

**计算：**
$$
\sigma_m = \frac{\sigma_{\max}+\sigma_{\min}}{2}, \quad
\sigma_a = \frac{\sigma_{\max}-\sigma_{\min}}{2}
$$

**结论：** ...

**得分点：** ...

**易错诊断：** ...
```

## Drawing And Diagnosis Questions

Always preserve the visual reasoning chain:

- Cite the source page/image path and page or image id.
- If answering from an existing figure, identify features as `① ② ③` and explain each.
- If drawing a corrected structure, provide either a clean SVG/Matplotlib/Mermaid sketch or a precise construction list.
- For force-direction or velocity/acceleration diagrams, name the coordinate convention and sign convention.
- For mechanism geometry, state the construction entities: centers, pitch circles, base circles, pressure angle, tangent/common normal, instant centers, or velocity poles.
- When the source is a scanned exam page, produce an on-paper visual answer if possible: add translucent highlights over the original figure, numbered badges beside errors or construction entities, arrows for force/velocity directions, and a side-panel solution with formulas and grading points.
- If the problem asks for drawing, do the drawing on the original figure when possible: add construction lines, force arrows, velocity directions, corrected joints, labels, and key points directly over the source image. Use a side or bottom panel only for formulas, conclusions, and rubric.

Template:

```markdown
**图源：** `.../g-4.png`

**题型判断：** 渐开线齿轮啮合作图 + 几何计算。

**标注/构造：**
① ...
② ...
③ ...

**计算：**
...

**结论：** ...

**得分点：**
- 标出实际啮合线和节点。
- 写出关键半径/中心距关系。
- 说明变位或传动类型。

**易错诊断：**
- 把节圆和基圆混用。
- 漏掉实际中心距导致压力角变化。
- 图上没有标注方向或点名。
```

## Teacher-Facing Keys

Add:

- Score allocation by step.
- Optional alternative methods.
- Minimal answer expected from students.
- Variant-generation knobs: changed dimensions, changed load direction, changed support type, or changed gear parameters.
- Which mistakes reveal conceptual gaps suitable for remedial teaching.
