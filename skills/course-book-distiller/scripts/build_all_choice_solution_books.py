#!/usr/bin/env python3
"""Build split XeLaTeX solution books for all structured objective questions."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image

try:
    from pypdf import PdfReader, PdfWriter
except Exception:  # pragma: no cover - optional dependency path
    PdfReader = None  # type: ignore[assignment]
    PdfWriter = None  # type: ignore[assignment]


CHAPTER_ORDER = {
    "第一章": 1,
    "第二章": 2,
    "第三章": 3,
    "第四章": 4,
    "第五章": 5,
    "第六章": 6,
    "第七章": 7,
    "第八章": 8,
    "第九章": 9,
    "第十章": 10,
    "第十一章": 11,
    "第十二章": 12,
    "第十三章": 13,
    "第十四章": 14,
    "第十五章": 15,
    "第十六章": 16,
    "第十七章": 17,
    "第十八章": 18,
    "第十九章": 19,
    "第二十章": 20,
    "第二十一章": 21,
    "第二十二章": 22,
    "第二十三章": 23,
}


DEFAULT_UPPER_TEXTBOOK = Path("/Users/yizhang/paper/how2learn/学业辅导-机原机设/教材/机械原理与机械设计  上册 (OCR).pdf")
DEFAULT_LOWER_TEXTBOOK = Path("/Users/yizhang/paper/how2learn/学业辅导-机原机设/机原机设题目/机械原理与机械设计  下册  第3版_14572614(OCR).pdf")


SEARCH_TERMS: dict[str, list[str]] = {
    "belt_min_diameter": ["弯曲应力", "小带轮", "带轮直径"],
    "belt_elastic_slip": ["弹性滑动", "松边", "紧边"],
    "flat_key_two_sides": ["平键", "两侧面", "工作面"],
    "double_key_180": ["两个平键", "180", "布置"],
    "chain_even_links": ["链节数", "偶数", "过渡链节"],
    "chain_max_teeth": ["链轮齿数", "不宜过多", "脱链"],
    "double_nut_locking": ["双螺母", "松动", "防松"],
    "worm_ratio": ["蜗杆传动比", "z2", "z1"],
    "worm_direction": ["螺纹", "右旋", "左旋"],
    "sliding_bearing_p": ["p值", "过度磨损", "轴承材料"],
    "sliding_bearing_pv": ["限制", "pv", "过度发热"],
    "gear_soft_pitting": ["软齿面", "点蚀", "闭式"],
    "gear_hard_bending": ["硬齿面", "疲劳折断"],
    "gear_form_factor": ["齿形系数", "齿数"],
    "gear_modulus_bending": ["足够大的模数", "轮齿折断"],
    "bevel_equivalent": ["齿宽中点", "背锥", "当量"],
    "gear_width_cantilever": ["悬臂布置", "齿宽系数"],
    "helical_normal_params": ["法面", "标准值", "斜齿圆柱齿轮"],
    "gear_tip_diameter": ["齿顶圆直径", "分度圆直径", "齿顶高系数"],
    "gear_coupling_offset": ["齿式联轴器", "综合位移", "综合偏移"],
    "reamed_bolt_shear": ["铰制孔螺栓", "剪切", "挤压"],
    "tapered_roller_pair": ["圆锥滚子轴承", "成对", "轴向"],
    "shaft_mandrel": ["心轴", "传动轴", "转轴"],
    "strength_condition": ["许用应力", "许用安全因数", "强度"],
    "bolt_total_tension": ["总拉力", "剩余预紧力"],
    "bolt_engagement_cast_iron": ["铸铁", "1.25", "1.5d"],
    "bolt_fatigue_stiffness": ["减小螺栓系统刚度", "增大被连接件系统刚度"],
    "mechanism_definition": ["机构具有确定运动", "自由度", "原动件"],
    "efficiency_series_parallel": ["效率", "串联", "并联"],
    "cam_pressure_angle": ["压力角", "基圆半径", "凸轮"],
    "ratchet_motion": ["棘轮机构", "单向间歇"],
    "dynamic_static_balance": ["静平衡", "动平衡", "惯性力矩"],
    "geneva_slots": ["槽轮", "槽数", "外槽轮"],
    "geneva_motion": ["槽轮", "运动系数", "间歇"],
    "fourbar_rr_synthesis": ["R-R", "导引机构", "位移矩阵"],
    "V带轮槽角与带楔角的关系": ["槽角", "楔角", "V带"],
}


PAGE_WINDOWS: dict[tuple[str, str], tuple[int, int]] = {
    ("lower", "第十三章"): (14, 22),
    ("lower", "第十四章"): (43, 68),
    ("lower", "第十五章"): (69, 79),
    ("lower", "第十七章"): (96, 125),
    ("lower", "第十八章"): (130, 166),
    ("lower", "第十九章"): (168, 180),
    ("lower", "第二十章"): (186, 197),
    ("lower", "第二十一章"): (204, 222),
    ("lower", "第二十二章"): (252, 260),
    ("lower", "第二十三章"): (262, 270),
    ("upper", "第三章"): (50, 75),
    ("upper", "第五章"): (120, 130),
    ("upper", "第六章"): (130, 182),
    ("upper", "第七章"): (190, 210),
    ("upper", "第八章"): (210, 252),
    ("upper", "第十章"): (280, 296),
    ("upper", "第十一章"): (330, 338),
    ("upper", "第十二章"): (340, 350),
}


FORMULA_CARDS: dict[str, list[dict[str, str]]] = {
    "第三章": [
        {
            "formula": r"F=3n-2P_L-P_H",
            "variables": r"$F$：机构自由度；$n$：活动构件数；$P_L$：低副数；$P_H$：高副数。",
            "meaning": "计算平面机构独立运动数，判断是否需要补充原动件或是否存在多余约束。",
            "use": "自由度、确定运动条件、复合铰链/局部自由度/虚约束判断。",
        },
        {
            "formula": r"F=\text{原动件数}",
            "variables": r"$F$：机构自由度；原动件数：独立输入运动个数。",
            "meaning": "机构具有确定运动的必要条件。若原动件少于或多于自由度，都不能得到唯一确定运动。",
            "use": "机构、主动件、从动件、确定运动条件类填空/判断。",
        },
    ],
    "第五章": [
        {
            "formula": r"\eta=\frac{P_{\mathrm{out}}}{P_{\mathrm{in}}},\qquad \eta_{\mathrm{series}}=\prod_i\eta_i",
            "variables": r"$\eta$：效率；$P_{\mathrm{out}}$：有效输出功率；$P_{\mathrm{in}}$：输入功率；$\eta_i$：第 $i$ 个串联系统效率。",
            "meaning": "效率是有用功率占输入功率的比例；串联系统每经过一级都会再乘一次效率。",
            "use": "串联机器越多总效率越低；并联系统需按功率分配看加权效率。",
        },
        {
            "formula": r"\eta\le 0 \Rightarrow \text{自锁}",
            "variables": r"$\eta$：机构效率。",
            "meaning": "从效率角度看，自锁表示反行程不能靠外载驱动机构运动。",
            "use": "自锁条件、摩擦角、总反力方向判断。",
        },
    ],
    "第六章": [
        {
            "formula": r"l_{\min}+l_{\max}\le l'+l''",
            "variables": r"$l_{\min}$：最短杆；$l_{\max}$：最长杆；$l',l''$：其余两杆长度。",
            "meaning": "铰链四杆机构存在整转副的杆长条件，是判断曲柄存在性的入口。",
            "use": "曲柄摇杆、双曲柄、双摇杆类型判断。",
        },
        {
            "formula": r"K=\frac{180^\circ+\theta}{180^\circ-\theta},\qquad \alpha+\gamma=90^\circ",
            "variables": r"$K$：行程速比系数；$\theta$：极位夹角；$\alpha$：压力角；$\gamma$：传动角。",
            "meaning": "极位夹角决定急回程度；压力角与传动角互余，传动角越大传力越好。",
            "use": "急回、死点、压力角、传动角、极位夹角类选择/作图题。",
        },
    ],
    "第七章": [
        {
            "formula": r"\alpha\le[\alpha]",
            "variables": r"$\alpha$：凸轮压力角；$[\alpha]$：许用压力角。",
            "meaning": "压力角过大时有效推力变差、导路反力增大，凸轮机构易卡滞或磨损。",
            "use": "基圆半径、偏置方向、从动件类型与压力角大小判断。",
        },
        {
            "formula": r"r_b\uparrow\Rightarrow \alpha\downarrow",
            "variables": r"$r_b$：基圆半径；$\alpha$：压力角。",
            "meaning": "在相同运动规律下，增大基圆通常可降低压力角，但会增大机构尺寸。",
            "use": "平底/滚子/尖顶从动件、推程压力角优化题。",
        },
    ],
    "第八章": [
        {
            "formula": r"d=mz,\qquad d_a=m(z+2h_a^*)",
            "variables": r"$d$：分度圆直径；$d_a$：齿顶圆直径；$m$：模数；$z$：齿数；$h_a^*$：齿顶高系数。",
            "meaning": "标准直齿圆柱齿轮的基本尺寸关系，选择题常由齿顶圆倒推分度圆。",
            "use": "标准齿轮尺寸、齿顶圆直径、分度圆直径、中心距判断。",
        },
        {
            "formula": r"m_n=m_t\cos\beta,\qquad z_v=\frac{z}{\cos^3\beta}",
            "variables": r"$m_n$：法面模数；$m_t$：端面模数；$\beta$：螺旋角；$z_v$：当量齿数。",
            "meaning": "斜齿轮以法面参数为标准参数，强度和齿形常转化到法面或当量齿轮分析。",
            "use": "斜齿轮标准参数、当量齿数、法面/端面概念题。",
        },
    ],
    "第十章": [
        {
            "formula": r"\tau_{\mathrm{Geneva}}=\frac{z-2}{2z}",
            "variables": r"$\tau$：槽轮运动系数；$z$：槽轮槽数。",
            "meaning": "单销外槽轮中从动槽轮的运动时间占一个周期的比例。",
            "use": "槽轮槽数、运动/停歇时间、间歇运动特征判断。",
        },
        {
            "formula": r"z\ge3",
            "variables": r"$z$：外槽轮槽数。",
            "meaning": "外槽轮槽数过少会导致几何上无法形成合理间歇运动。",
            "use": "单销外槽轮槽数下限类选择题。",
        },
    ],
    "第十一章": [
        {
            "formula": r"\delta=\frac{\omega_{\max}-\omega_{\min}}{\omega_m},\qquad J_F=\frac{\Delta W_{\max}}{\delta\omega_m^2}",
            "variables": r"$\delta$：速度不均匀系数；$\omega_{\max},\omega_{\min},\omega_m$：最大、最小、平均角速度；$J_F$：飞轮转动惯量；$\Delta W_{\max}$：最大盈亏功。",
            "meaning": "飞轮通过储放能量减小周期性速度波动，但不能完全消除波动。",
            "use": "飞轮作用、速度波动、等效力矩与飞轮惯量判断。",
        },
    ],
    "第十二章": [
        {
            "formula": r"\sum m_i r_i=0,\qquad \sum m_i r_i l_i=0",
            "variables": r"$m_i$：第 $i$ 个偏心质量；$r_i$：质径；$l_i$：到选定平衡基面的轴向距离。",
            "meaning": "静平衡要求惯性力合力为零；动平衡还要求惯性力矩为零。",
            "use": "静平衡/动平衡、单面/双面平衡、刚性转子宽径比判断。",
        },
    ],
    "第十三章": [
        {
            "formula": r"\sigma\le[\sigma],\qquad S_\sigma=\frac{\sigma_{\lim}}{\sigma_{\max}}\ge[S_\sigma]",
            "variables": r"$\sigma$：危险截面实际应力；$[\sigma]$：许用应力；$S_\sigma$：实际安全系数；$[S_\sigma]$：许用安全系数；$\sigma_{\lim}$：极限应力。",
            "meaning": "同一个强度条件可写成应力不超过许用值，也可写成安全系数不小于许用安全系数。",
            "use": "强度条件、不等号方向、安全系数概念题。",
        },
    ],
    "第十四章": [
        {
            "formula": r"F_0=F+F''",
            "variables": r"$F_0$：螺栓总拉力；$F$：轴向工作拉力；$F''$：剩余预紧力。",
            "meaning": "受轴向工作载荷后，初始预紧力的一部分转化为剩余预紧力，不能把 $F'$ 再重复相加。",
            "use": "紧螺栓轴向受载、总拉力、预紧力与剩余预紧力判断。",
        },
        {
            "formula": r"\Delta F_b=\frac{C_b}{C_b+C_m}F",
            "variables": r"$\Delta F_b$：螺栓拉力增量；$C_b$：螺栓刚度；$C_m$：被连接件刚度；$F$：工作载荷。",
            "meaning": "降低螺栓刚度、提高被连接件刚度，可减小螺栓承受的载荷增量和应力幅。",
            "use": "变载荷螺栓疲劳强度措施。",
        },
    ],
    "第十五章": [
        {
            "formula": r"\tau=\frac{2T}{dbl},\qquad \sigma_p=\frac{4T}{dhl}",
            "variables": r"$\tau$：键剪切应力；$\sigma_p$：挤压应力；$T$：转矩；$d$：轴径；$b,h,l$：键宽、高、工作长度。",
            "meaning": "平键主要靠两侧面传递转矩，通常校核剪切和挤压。",
            "use": "平键工作面、双键布置、承载能力判断。",
        },
        {
            "formula": r"\Delta\phi=180^\circ",
            "variables": r"$\Delta\phi$：两平键周向夹角。",
            "meaning": "两个平键对称布置可减轻偏载，是承载不足时的常规结构措施。",
            "use": "两个平键如何布置类选择题。",
        },
    ],
    "第十七章": [
        {
            "formula": r"v=\frac{\pi d_1n_1}{60\times1000},\qquad F_e=\frac{1000P}{v}",
            "variables": r"$v$：带速；$d_1$：小带轮直径；$n_1$：小带轮转速；$F_e$：有效圆周力；$P$：传递功率。",
            "meaning": "带速和有效拉力共同决定带传动受力水平，小带轮直径过小会增大弯曲应力。",
            "use": "小带轮最小直径、弯曲应力、带速与圆周力判断。",
        },
        {
            "formula": r"i=\frac{n_1}{n_2}=\frac{z_2}{z_1},\qquad L_p\ \text{通常取偶数}",
            "variables": r"$i$：链传动传动比；$n_1,n_2$：主动/从动链轮转速；$z_1,z_2$：链轮齿数；$L_p$：链节数。",
            "meaning": "链传动按链轮齿数比确定传动比；链节数取偶数可避免强度较弱的过渡链节。",
            "use": "链传动比、链节数、链轮齿数限制。",
        },
    ],
    "第十八章": [
        {
            "formula": r"d=mz,\qquad a=\frac{m(z_1+z_2)}{2},\qquad m_n=m_t\cos\beta",
            "variables": r"$d$：分度圆直径；$a$：中心距；$m$：模数；$z_1,z_2$：齿数；$m_n,m_t$：法面/端面模数；$\beta$：螺旋角。",
            "meaning": "齿轮几何尺寸与模数、齿数直接相关；斜齿轮标准参数在法面。",
            "use": "齿轮尺寸、斜齿轮标准参数、模数影响。",
        },
        {
            "formula": r"\sigma_F\le[\sigma_F],\qquad \sigma_H\le[\sigma_H]",
            "variables": r"$\sigma_F$：齿根弯曲应力；$\sigma_H$：齿面接触应力；$[\sigma_F],[\sigma_H]$：对应许用应力。",
            "meaning": "软齿面闭式齿轮常以接触疲劳点蚀为主要失效；硬齿面常更重视齿根弯曲疲劳。",
            "use": "点蚀、磨损、胶合、疲劳折断等失效形式判断。",
        },
    ],
    "第十九章": [
        {
            "formula": r"i=\frac{n_1}{n_2}=\frac{z_2}{z_1}\ne\frac{d_2}{d_1}",
            "variables": r"$i$：蜗杆传动比；$n_1,n_2$：蜗杆/蜗轮转速；$z_1$：蜗杆头数；$z_2$：蜗轮齿数；$d_1,d_2$：分度圆直径。",
            "meaning": "蜗杆传动比由头数和蜗轮齿数决定，不按分度圆直径比计算。",
            "use": "蜗杆传动比反选题。",
        },
        {
            "formula": r"\tan\gamma=\frac{z_1m}{d_1}",
            "variables": r"$\gamma$：导程角；$z_1$：蜗杆头数；$m$：模数；$d_1$：蜗杆分度圆直径。",
            "meaning": "导程角影响效率与自锁能力。",
            "use": "蜗杆头数、效率、自锁概念题。",
        },
    ],
    "第二十章": [
        {
            "formula": r"T=9550\frac{P}{n}",
            "variables": r"$T$：转矩；$P$：功率；$n$：转速。",
            "meaning": "轴的扭转载荷常由功率和转速换算得到。",
            "use": "轴径估算、转轴/传动轴受扭判断。",
        },
        {
            "formula": r"M\ne0,T=0:\text{心轴};\quad M=0,T\ne0:\text{传动轴};\quad M\ne0,T\ne0:\text{转轴}",
            "variables": r"$M$：弯矩；$T$：转矩。",
            "meaning": "按轴所受载荷分类，不按零件是否转动机械记忆。",
            "use": "自行车前轮轴等生活结构分类题。",
        },
    ],
    "第二十一章": [
        {
            "formula": r"P=f_p(XF_R+YF_A)",
            "variables": r"$P$：当量动载荷；$f_p$：载荷系数；$F_R$：径向载荷；$F_A$：轴向载荷；$X,Y$：径向/轴向载荷系数。",
            "meaning": "滚动轴承选型和寿命计算先把联合载荷折算为当量动载荷。",
            "use": "径向/轴向联合载荷、圆锥滚子轴承成对使用。",
        },
        {
            "formula": r"L_{10h}=\frac{10^6}{60n}\left(\frac{C}{P}\right)^\varepsilon",
            "variables": r"$L_{10h}$：基本额定寿命；$n$：转速；$C$：基本额定动载荷；$P$：当量动载荷；$\varepsilon$：寿命指数。",
            "meaning": "载荷增大会显著降低轴承寿命。",
            "use": "寿命、额定动载荷、轴承类型选择题。",
        },
    ],
    "第二十二章": [
        {
            "formula": r"p=\frac{F}{Bd},\qquad v=\frac{\pi dn}{60\times1000},\qquad pv\le[pv]",
            "variables": r"$p$：平均压强；$F$：径向载荷；$B$：轴承宽度；$d$：轴颈直径；$v$：滑动速度；$n$：转速；$pv$：压强速度积。",
            "meaning": "$p$ 主要限制磨损/压溃，$v$ 限制速度条件，$pv$ 反映发热强度。",
            "use": "不充分润滑滑动轴承的 p、v、pv 目的判断。",
        },
    ],
    "第二十三章": [
        {
            "formula": r"T=Fr",
            "variables": r"$T$：传递转矩；$F$：螺栓或接触处圆周力；$r$：受力半径。",
            "meaning": "凸缘联轴器通过螺栓或摩擦把转矩转化为圆周力传递。",
            "use": "铰制孔螺栓受剪切与挤压判断。",
        },
        {
            "formula": r"\Delta r,\Delta x,\Delta\alpha\Rightarrow\text{补偿径向、轴向、角向偏移}",
            "variables": r"$\Delta r$：径向偏移；$\Delta x$：轴向偏移；$\Delta\alpha$：角向偏移。",
            "meaning": "联轴器选型要先看是否需要补偿综合偏移。",
            "use": "齿式联轴器、弹性联轴器、刚性联轴器区别。",
        },
    ],
}


METHOD_LINES: dict[str, list[str]] = {
    "第三章": ["先数活动构件，再找低副/高副；复合铰链按同时相连构件数修正；最后用 F=原动件数判断确定运动。"],
    "第五章": ["效率题先判断串联还是并联；串联直接相乘，并联看各支路功率分配；自锁题从反行程是否能运动判断。"],
    "第六章": ["四杆机构先排杆长条件，再看固定哪一杆；压力角/传动角题先写互余关系。"],
    "第七章": ["凸轮题先圈从动件类型、导路位置、基圆半径；问压力角就看有效推力方向与速度方向夹角。"],
    "第八章": ["齿轮机构题先分标准直齿、变位、斜齿；尺寸题从 d=mz 和 da=m(z+2ha*) 入手。"],
    "第十章": ["间歇机构题先分棘轮、槽轮、不完全齿轮；槽轮题抓槽数、运动系数和冲击类型。"],
    "第十一章": ["飞轮题只解决周期性速度波动，不能改变非周期性波动；计算题再进盈亏功。"],
    "第十二章": ["平衡题先分静平衡和动平衡；动平衡同时满足力和力矩平衡，通常需要两个平衡基面。"],
    "第十三章": ["强度题只看两个不等号方向：应力不超过许用值，安全系数不小于许用值。"],
    "第十四章": ["螺栓题先判普通/紧/铰制孔，再判轴向拉、横向剪或防松；疲劳题看刚度分配。"],
    "第十五章": ["键连接题先找工作面；平键靠两侧面，两个键相隔 180°，强度不能简单翻倍。"],
    "第十七章": ["带链题先区分弹性滑动、打滑和弯曲应力；链传动题抓偶数链节、齿数和低速级布置。"],
    "第十八章": ["齿轮设计题先判开式/闭式、软齿面/硬齿面，再选主要失效和强度准则。"],
    "第十九章": ["蜗杆题优先写 i=n1/n2=z2/z1；看到 d2/d1 直接警惕，这是常见陷阱。"],
    "第二十章": ["轴分类题不要看是否有轮子在转，先判断轴是否传递转矩、是否主要承受弯矩。"],
    "第二十一章": ["轴承选择题先看载荷方向；能承受轴向力的轴承常需要成对布置或定位。"],
    "第二十二章": ["滑动轴承题把 p、v、pv 三个物理意义分开：压强、速度、发热。"],
    "第二十三章": ["联轴器题先看是否补偿偏移；铰制孔螺栓按剪切和挤压，不按普通螺栓拉伸。"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--objective-index", required=True)
    parser.add_argument("--b-choice-data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--upper-textbook", default=str(DEFAULT_UPPER_TEXTBOOK))
    parser.add_argument("--lower-textbook", default=str(DEFAULT_LOWER_TEXTBOOK))
    parser.add_argument("--skip-textbook-snippets", action="store_true")
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
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)
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


def split_papers(paper: str) -> list[str]:
    letters = re.findall(r"[A-G]", paper.upper())
    if letters:
        return [f"{letter}卷" for letter in letters]
    return [paper or "未知来源"]


def compact(text: str) -> str:
    return re.sub(r"\s+", "", normalize_marker(text))


def normalize_search(text: str) -> str:
    return re.sub(r"\s+", "", normalize_marker(str(text)).lower())


def infer_course(item: dict[str, Any]) -> str:
    chapter = item.get("chapter", "")
    source = item.get("source", "")
    paper = item.get("paper", "")
    ck = chapter_key(chapter)
    if "上册" in chapter and ("机械原理" in source or any(token in paper for token in ("A", "D", "E", "F", "G"))):
        return "principles"
    if "下册" in chapter or CHAPTER_ORDER.get(ck, 0) >= 13:
        return "design"
    if "上册" in chapter or "机械原理" in source or paper in {"A卷", "D卷", "E卷", "F卷", "G卷", "A/D卷", "E/F/G卷", "F/G卷"}:
        return "principles"
    return "design" if CHAPTER_ORDER.get(ck, 0) >= 13 else "principles"


def topic_key(item: dict[str, Any]) -> str:
    text = compact(" ".join(str(item.get(k, "")) for k in ("stem", "test_point", "answer_hint", "answer")))
    rules = [
        ("belt_min_diameter", ["带", "直径", "弯曲"]),
        ("belt_elastic_slip", ["弹性滑动"]),
        ("flat_key_two_sides", ["平键", "工作面"]),
        ("double_key_180", ["平键", "180"]),
        ("chain_even_links", ["链节", "偶数"]),
        ("chain_max_teeth", ["链轮", "脱链"]),
        ("worm_ratio", ["蜗杆", "直径比"]),
        ("sliding_bearing_p", ["滑动轴承", "p值"]),
        ("sliding_bearing_pv", ["滑动轴承", "pv"]),
        ("double_nut_locking", ["双螺母"]),
        ("gear_soft_pitting", ["软齿面", "点蚀"]),
        ("gear_hard_bending", ["硬齿面", "折断"]),
        ("gear_form_factor", ["齿形系数"]),
        ("gear_modulus_bending", ["模数", "弯曲强度"]),
        ("worm_direction", ["螺纹", "旋向"]),
        ("flywheel_speed", ["飞轮", "速度波动"]),
        ("dynamic_static_balance", ["静平衡", "动平衡"]),
        ("geneva_slots", ["槽轮", "槽数"]),
        ("geneva_motion", ["槽轮", "运动时间"]),
        ("gear_tip_diameter", ["齿顶圆", "分度圆"]),
        ("helical_normal_params", ["斜齿", "法面"]),
        ("efficiency_series_parallel", ["串联", "并联", "效率"]),
        ("cam_pressure_angle", ["凸轮", "压力角"]),
        ("ratchet_motion", ["棘轮"]),
        ("fourbar_rr_synthesis", ["R-R", "导引"]),
        ("mechanism_definition", ["机构", "主动件", "从动件"]),
        ("strength_condition", ["安全系数", "许用应力"]),
        ("bolt_total_tension", ["总拉力", "剩余预紧力"]),
        ("bolt_engagement_cast_iron", ["铸铁", "螺纹孔深度"]),
        ("bolt_fatigue_stiffness", ["应力幅", "螺栓刚度"]),
        ("bevel_equivalent", ["锥齿轮", "当量"]),
        ("gear_width_cantilever", ["齿宽系数", "悬臂"]),
        ("shaft_mandrel", ["自行车前轮轴"]),
        ("tapered_roller_pair", ["圆锥滚子轴承"]),
        ("gear_coupling_offset", ["齿轮联轴器", "综合偏移"]),
        ("reamed_bolt_shear", ["铰制孔螺栓"]),
    ]
    for key, needles in rules:
        if all(needle in text for needle in needles):
            return key
    return compact(item.get("test_point") or item.get("stem") or item.get("answer_hint"))[:72]


def merge_topic(item: dict[str, Any]) -> str:
    return str(item.get("merge_key", "")).split("::")[-1] or topic_key(item)


def first_citation(question: dict[str, Any]) -> dict[str, Any]:
    citations = question.get("textbook_citations") or []
    return citations[0] if citations else {}


def load_b_choice(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = []
    for question in raw.get("questions", []):
        citation = first_citation(question)
        review = (question.get("related_review_questions") or [{}])[0]
        items.append(
            {
                "course": "design",
                "kind": "选择",
                "paper": "B卷",
                "source": "机原往年题b/b-1.png",
                "stem": question.get("stem", ""),
                "options": question.get("options", {}),
                "answer": question.get("answer", ""),
                "answer_hint": question.get("analysis", ""),
                "analysis": question.get("analysis", ""),
                "test_point": question.get("analysis", ""),
                "chapter": citation.get("chapter", ""),
                "pdf_page": citation.get("pdf_page", ""),
                "print_page": citation.get("print_page", ""),
                "quote_anchor": citation.get("quote_anchor", ""),
                "snippet_image": citation.get("snippet_image", ""),
                "review_prompt": review,
            }
        )
    return items


def load_objective_index(path: Path) -> list[dict[str, Any]]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        if raw.get("paper") == "B卷":
            continue
        raw.setdefault("options", {})
        raw.setdefault("answer", "")
        raw.setdefault("analysis", raw.get("answer_hint", ""))
        raw["course"] = infer_course(raw)
        items.append(raw)
    return items


def manual_supplements() -> list[dict[str, Any]]:
    return [
        {
            "course": "principles",
            "kind": "填空式选择",
            "paper": "A/D卷",
            "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
            "stem": "在步式棘轮机构中，从动棘轮作____，它适用于____状态的工作机构。",
            "answer": "单向间歇转动；低速",
            "answer_hint": "棘轮机构输出单向间歇运动，常用于低速轻载的间歇进给、计数或防逆转。",
            "analysis": "关键词是“棘轮”和“从动棘轮”。棘爪每摆动一次推动棘轮转过一定角度，所以不是连续转动。",
            "test_point": "棘轮机构的间歇运动特征与适用场景",
            "chapter": "上册 第十章 其他常用机构 / 棘轮机构",
            "review_prompt": {"prompt": "比较棘轮、槽轮、不完全齿轮三种间歇机构。", "answer": "棘轮可单向间歇，槽轮间歇较规则，不完全齿轮适合按齿数控制间歇。"},
        },
        {
            "course": "principles",
            "kind": "填空式选择",
            "paper": "A/D卷",
            "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
            "stem": "平底垂直导路平底直动从动件盘形凸轮机构，压力角等于____；基圆半径相同时，正确配置可____推程压力角。",
            "answer": "常值；减小",
            "answer_hint": "平底从动件接触法线与平底方向有关，合理偏置或配置可改善推程压力角。",
            "analysis": "这题不是求数值，而是判断平底从动件压力角特征和基圆半径不变时的配置效果。",
            "test_point": "平底从动件压力角、基圆半径与推程压力角",
            "chapter": "上册 第七章 凸轮机构",
            "review_prompt": {"prompt": "比较尖顶、滚子、平底从动件在压力角上的差异。", "answer": "尖顶/滚子按理论轮廓法线判断，平底从动件常具有压力角小的优点。"},
        },
        {
            "course": "principles",
            "kind": "填空式选择",
            "paper": "A/D卷",
            "source": "机原往年题a/a-1.png; 机原往年题d/d-1.png",
            "stem": "正变位渐开线直齿圆柱齿轮的分度圆半径____，其分度圆齿厚____。",
            "answer": "不变；加大",
            "answer_hint": "变位不改变模数和齿数，因此分度圆不变；正变位使分度圆齿厚增大。",
            "analysis": "判断信号是“正变位”和“分度圆”。分度圆尺寸由 m 和 z 决定，正变位改变齿厚、齿根厚和齿顶厚。",
            "test_point": "变位齿轮分度圆不变、齿厚变化",
            "chapter": "上册 第八章 齿轮机构",
            "review_prompt": {"prompt": "列出正变位对齿根强度、齿厚、中心距的影响。", "answer": "分度圆不变，分度圆齿厚增加，齿根强度改善。"},
        },
        {
            "course": "design",
            "kind": "填空式选择",
            "paper": "C卷",
            "source": "机原往年题c/c-1.jpg",
            "stem": "V 带轮槽角小于带的楔角，主要原因是____。",
            "answer": "带弯曲变形后楔角会减小",
            "answer_hint": "V 带绕过带轮时发生弯曲变形，为保证两侧面良好接触，轮槽角通常小于带楔角。",
            "analysis": "不要选“增加摩擦力”作为直接原因；楔形增压是 V 带传动效果，轮槽角取小的直接原因是弯曲后截面角变化。",
            "test_point": "V带轮槽角与带楔角的关系",
            "chapter": "下册 第十七章 带传动和链传动",
            "review_prompt": {"prompt": "解释 V 带为什么靠两侧面工作。", "answer": "楔形作用增大法向力，从而提高摩擦传力能力。"},
        },
        {
            "course": "design",
            "kind": "图形判读",
            "paper": "C卷",
            "source": "机原往年题c/c-1.jpg",
            "stem": "图示螺纹的旋向应按____判断。",
            "answer": "按右手螺旋法或教材图例判断；该题需要结合原图复核旋向。",
            "answer_hint": "旋向题属于图形判读题，不能只背“左/右旋”，应看螺旋线在轴线方向上的倾斜关系。",
            "analysis": "后续若加入图上作答，应把原图局部裁出并在螺旋线上画右手判定箭头。",
            "test_point": "螺纹旋向图形判读",
            "chapter": "下册 第十四章 螺纹紧固件连接",
            "review_prompt": {"prompt": "画一条外螺纹简图，用右手法判断旋向。", "answer": "拇指指向轴向前进方向，四指弯曲方向对应旋转方向。"},
        },
        {
            "course": "principles",
            "kind": "选择",
            "paper": "G卷",
            "source": "机原往年题g/g-1.png",
            "stem": "安装飞轮后，机械系统的周期性速度波动将____。",
            "options": {"A": "减小", "B": "消除", "C": "增大"},
            "answer": "A 减小",
            "answer_hint": "飞轮通过储放能量减小周期性速度波动，但不能完全消除。",
            "analysis": "飞轮增加转动惯量，使同样盈亏功引起的角速度变化减小。",
            "test_point": "飞轮减小周期性速度波动",
            "chapter": "上册 第十一章机械系统动力学",
            "review_prompt": {"prompt": "飞轮能否消除非周期性速度波动？", "answer": "不能，飞轮主要调节周期性速度波动。"},
        },
        {
            "course": "principles",
            "kind": "选择",
            "paper": "G卷",
            "source": "机原往年题g/g-1.png",
            "stem": "经动平衡设计的刚性转子____是静平衡的，经静平衡设计的刚性转子____是动平衡的。",
            "options": {"A": "必定，必定", "B": "必定，未必", "C": "未必，必定", "D": "未必，未必"},
            "answer": "B 必定，未必",
            "answer_hint": "动平衡同时满足惯性力和惯性力矩平衡，因此包含静平衡；静平衡不一定满足力矩平衡。",
            "analysis": "动平衡条件比静平衡多一个力矩平衡条件，所以是充分但非必要关系。",
            "test_point": "动平衡与静平衡的包含关系",
            "chapter": "上册 第十二章 机械的平衡",
            "review_prompt": {"prompt": "为什么动平衡又叫双面平衡？", "answer": "需要在两个平衡基面上同时平衡力和力矩。"},
        },
        {
            "course": "principles",
            "kind": "选择",
            "paper": "G卷",
            "source": "机原往年题g/g-1.png",
            "stem": "单销外槽轮机构中，槽轮上径向槽的数目应____。",
            "options": {"A": "小于3", "B": "大于3", "C": "大于等于2", "D": "大于等于3"},
            "answer": "D 大于等于3",
            "answer_hint": "外槽轮槽数通常不少于 3。",
            "analysis": "槽数过少不能形成合理的外槽轮间歇运动几何关系。",
            "test_point": "单销外槽轮槽数下限",
            "chapter": "上册 第十章 其他常用机构 / 槽轮机构",
            "review_prompt": {"prompt": "槽轮机构槽数增大时运动系数如何变化？", "answer": "按 τ=(z-2)/(2z) 增大并趋近 1/2。"},
        },
        {
            "course": "principles",
            "kind": "选择",
            "paper": "G卷",
            "source": "机原往年题g/g-1.png",
            "stem": "标准直齿圆柱齿轮齿顶圆直径为 120 mm，齿数 22，则分度圆直径为____。",
            "options": {"A": "112 mm", "B": "108 mm", "C": "110 mm", "D": "115 mm"},
            "answer": "C 110 mm",
            "answer_hint": "标准齿轮 da=m(z+2)，由 120=m(22+2) 得 m=5，故 d=mz=110 mm。",
            "analysis": "先由齿顶圆公式倒推模数，再由 d=mz 求分度圆直径。",
            "test_point": "齿顶圆公式、标准中心距啮合角等于压力角",
            "chapter": "上册 第八章 齿轮机构",
            "review_prompt": {"prompt": "若 z=30,m=4, 求 d 与 da。", "answer": "d=120 mm，da=128 mm。"},
        },
    ]


def merge_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in items:
        item["course"] = item.get("course") or infer_course(item)
        key = f"{item['course']}::{chapter_key(item.get('chapter', ''))}::{topic_key(item)}"
        papers = split_papers(str(item.get("paper", "")))
        occurrence = {
            "paper": item.get("paper", ""),
            "source": item.get("source", ""),
        }
        if key not in merged:
            item = dict(item)
            item["occurrences"] = [occurrence]
            item["paper_set"] = sorted(set(papers))
            item["merge_key"] = key
            merged[key] = item
            continue
        target = merged[key]
        target["occurrences"].append(occurrence)
        target["paper_set"] = sorted(set(target.get("paper_set", [])) | set(papers))
        for field in ("options", "answer", "answer_hint", "analysis", "pdf_page", "print_page", "quote_anchor", "snippet_image"):
            if not target.get(field) and item.get(field):
                target[field] = item[field]
        if len(str(item.get("stem", ""))) > len(str(target.get("stem", ""))) and item.get("options"):
            target["stem"] = item["stem"]
            target["options"] = item.get("options", {})
    return sorted(
        merged.values(),
        key=lambda item: (
            item.get("course", ""),
            CHAPTER_ORDER.get(chapter_key(item.get("chapter", "")), 999),
            compact(item.get("stem", "")),
        ),
    )


def copy_snippets(items: list[dict[str, Any]], out_dir: Path, cwd: Path) -> None:
    asset_dir = out_dir / "assets" / "snippets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    for idx, item in enumerate(items, start=1):
        local = item.get("snippet_local")
        if local and (out_dir / str(local)).exists():
            item["snippet_image"] = local
            continue
        snippet = item.get("snippet_image")
        if not snippet:
            continue
        src = Path(snippet)
        if not src.is_absolute():
            src = cwd / src
        if not src.exists():
            continue
        dst = asset_dir / f"snippet_{idx:03d}.png"
        shutil.copyfile(src, dst)
        local_path = f"assets/snippets/{dst.name}"
        item["snippet_source"] = snippet
        item["snippet_image"] = local_path
        item["snippet_local"] = local_path


class TextbookIndex:
    def __init__(self, pdf_path: Path, tag: str) -> None:
        if PdfReader is None:
            raise RuntimeError("pypdf is required to locate textbook snippets")
        self.pdf_path = pdf_path
        self.tag = tag
        self.reader = PdfReader(str(pdf_path))
        self.pages: list[dict[str, Any]] = []
        for idx, page in enumerate(self.reader.pages):
            chunks: list[dict[str, Any]] = []

            def visitor(text: str, cm: Any, tm: Any, font_dict: Any, font_size: float) -> None:
                clean = text.strip()
                if clean:
                    chunks.append({"text": clean, "x": float(tm[4]), "y": float(tm[5]), "font_size": float(font_size)})

            try:
                text = page.extract_text(visitor_text=visitor) or ""
            except Exception:
                text = page.extract_text() or ""
            if not text and chunks:
                text = "\n".join(chunk["text"] for chunk in chunks)
            self.pages.append(
                {
                    "page_num": idx + 1,
                    "text": text,
                    "norm": normalize_search(text),
                    "chunks": chunks,
                    "width": float(page.mediabox.width),
                    "height": float(page.mediabox.height),
                }
            )

    def search(self, terms: list[str], page_window: tuple[int, int] | None = None) -> tuple[dict[str, Any] | None, list[str]]:
        norm_terms = [normalize_search(term) for term in terms if normalize_search(term)]
        best: tuple[int, dict[str, Any] | None, list[str]] = (0, None, [])
        for page in self.pages:
            page_num = int(page["page_num"])
            if page_window and not (page_window[0] <= page_num <= page_window[1]):
                continue
            if page_num <= 12 and ("目录" in page["text"] or "……" in page["text"] or "..." in page["text"]):
                continue
            hits = [term for term in norm_terms if term and term in page["norm"]]
            if not hits:
                continue
            score = sum(len(term) for term in hits) + 3 * len(hits)
            if score > best[0]:
                best = (score, page, hits)
        return best[1], best[2]

    def render_crop(self, page_info: dict[str, Any], hits: list[str], out_path: Path) -> str:
        page_num = int(page_info["page_num"])
        temp_pdf = out_path.with_suffix(".pdf")
        rendered_png = out_path.with_name(out_path.stem + "_page.png")
        writer = PdfWriter()
        writer.add_page(self.reader.pages[page_num - 1])
        with temp_pdf.open("wb") as fh:
            writer.write(fh)
        subprocess.run(["sips", "-s", "format", "png", str(temp_pdf), "--out", str(rendered_png)], check=True, stdout=subprocess.DEVNULL)
        image = Image.open(rendered_png).convert("RGBA")
        white = Image.new("RGBA", image.size, (255, 255, 255, 255))
        white.alpha_composite(image)
        image = white.convert("RGB")

        matching_chunks: list[dict[str, Any]] = []
        for chunk in page_info.get("chunks", []):
            ctext = normalize_search(chunk["text"])
            if any(hit in ctext or ctext in hit for hit in hits):
                matching_chunks.append(chunk)
        if not matching_chunks and hits:
            split_hits = [token for hit in hits for token in re.split(r"[,，;；/、]", hit) if len(token) >= 2]
            for chunk in page_info.get("chunks", []):
                ctext = normalize_search(chunk["text"])
                if any(token in ctext for token in split_hits):
                    matching_chunks.append(chunk)

        width, height = image.size
        x0 = int(width * 0.05)
        x1 = int(width * 0.95)
        if matching_chunks:
            ys = [
                (float(page_info["height"]) - float(chunk["y"])) * height / float(page_info["height"])
                for chunk in matching_chunks
            ]
            center = int(sum(ys) / len(ys))
            y0 = max(0, center - int(height * 0.18))
            y1 = min(height, center + int(height * 0.12))
        else:
            y0 = int(height * 0.22)
            y1 = int(height * 0.58)
        if y1 - y0 < int(height * 0.18):
            pad = int(height * 0.09)
            y0 = max(0, y0 - pad)
            y1 = min(height, y1 + pad)
        crop = image.crop((x0, y0, x1, y1))
        crop.save(out_path)
        try:
            temp_pdf.unlink()
            rendered_png.unlink()
        except OSError:
            pass
        anchor = ""
        if matching_chunks:
            anchor = matching_chunks[0]["text"]
        else:
            text_lines = [line.strip() for line in str(page_info.get("text", "")).splitlines() if line.strip()]
            anchor = text_lines[0] if text_lines else ""
        return anchor[:86]


def fallback_terms(item: dict[str, Any]) -> list[str]:
    source = " ".join(
        str(item.get(field, "")) for field in ("quote_anchor", "test_point", "answer_hint", "stem", "analysis")
    )
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9α-ωΑ-Ωβγδσπ_]+", source)
    useful = [token for token in tokens if len(token) >= 3]
    return useful[:8]


def textbook_for_item(item: dict[str, Any], upper: Path, lower: Path) -> tuple[str, Path]:
    chapter = str(item.get("chapter", ""))
    if "上册" in chapter:
        return "upper", upper
    if "下册" in chapter:
        return "lower", lower
    return ("upper", upper) if item.get("course") == "principles" else ("lower", lower)


def page_window_for_item(tag: str, item: dict[str, Any]) -> tuple[int, int] | None:
    return PAGE_WINDOWS.get((tag, chapter_key(str(item.get("chapter", "")))))


def enrich_textbook_snippets(items: list[dict[str, Any]], out_dir: Path, upper: Path, lower: Path) -> None:
    if PdfReader is None:
        return
    indexes: dict[str, TextbookIndex] = {}
    snippet_dir = out_dir / "assets" / "snippets"
    snippet_dir.mkdir(parents=True, exist_ok=True)
    for idx, item in enumerate(items, start=1):
        if item.get("snippet_image") or item.get("snippet_local"):
            continue
        tag, pdf_path = textbook_for_item(item, upper, lower)
        if not pdf_path.exists():
            continue
        if tag not in indexes:
            indexes[tag] = TextbookIndex(pdf_path, tag)
        topic = merge_topic(item)
        terms = SEARCH_TERMS.get(topic, [])
        if item.get("quote_anchor"):
            terms = [str(item["quote_anchor"])] + terms
        terms = terms + fallback_terms(item)
        page, hits = indexes[tag].search(terms, page_window_for_item(tag, item))
        if not page:
            page, hits = indexes[tag].search(terms)
        if not page:
            continue
        out_path = snippet_dir / f"auto_{tag}_{idx:03d}_p{int(page['page_num']):03d}.png"
        anchor = indexes[tag].render_crop(page, hits, out_path)
        local_path = f"assets/snippets/{out_path.name}"
        item["pdf_page"] = item.get("pdf_page") or int(page["page_num"])
        item["quote_anchor"] = item.get("quote_anchor") or anchor
        item["snippet_image"] = local_path
        item["snippet_local"] = local_path
        item["textbook_pdf"] = str(pdf_path)


def doc_preamble(title: str) -> str:
    return rf"""
\documentclass[UTF8,zihao=-4,fontset=none]{{ctexart}}
\usepackage[a4paper,margin=1.15cm,top=1.3cm,bottom=1.3cm]{{geometry}}
\usepackage{{amsmath,amssymb,mathtools}}
\usepackage{{fontspec}}
\usepackage{{unicode-math}}
\usepackage{{graphicx}}
\usepackage{{booktabs,tabularx,array,longtable}}
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
\definecolor{{linegray}}{{HTML}}{{D7D7D0}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{{tex_escape(title)}}}
\rhead{{\thepage}}
\setlength{{\headheight}}{{15pt}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{2.5pt}}
\setlength{{\emergencystretch}}{{4em}}
\setlist[itemize]{{leftmargin=1.1em,itemsep=1pt,topsep=2pt}}
\renewcommand{{\arraystretch}}{{1.12}}
\newcolumntype{{Y}}{{>{{\raggedright\arraybackslash}}X}}
\newcommand{{\tagpill}}[1]{{\tcbox[colback=softgray,colframe=black!20,arc=.7mm,boxrule=.25pt,on line,boxsep=.8pt,left=2pt,right=2pt]{{\scriptsize #1}}}}
\newtcolorbox{{chapterbox}}[1]{{enhanced,breakable,colback=softblue,colframe=deepblue,arc=1mm,boxrule=.6pt,left=5pt,right=5pt,top=4pt,bottom=4pt,title={{\bfseries #1}}}}
\newtcolorbox{{formulabox}}[1]{{enhanced,breakable,colback=white,colframe=deepblue!60,arc=.8mm,boxrule=.45pt,left=4pt,right=4pt,top=3pt,bottom=3pt,title={{\bfseries #1}}}}
\newtcolorbox{{qcard}}[1]{{enhanced,breakable,colback=white,colframe=black!35,arc=1mm,boxrule=.42pt,left=5pt,right=5pt,top=4pt,bottom=4pt,title={{\bfseries #1}},before upper=\raggedright}}
\begin{{document}}
\begin{{center}}
  {{\zihao{{2}}\bfseries {tex_escape(title)}}}\\[2pt]
  {{\small 按章节汇总公式、变量含义、做题方法线、去重客观小题与教材定位}}
\end{{center}}
\tableofcontents
\newpage
"""


def option_grid(options: dict[str, str]) -> str:
    if not options:
        return ""
    pairs = [(normalize_marker(k), v) for k, v in options.items()]
    rows: list[str] = []
    if max((len(v) for _, v in pairs), default=0) > 14:
        rows = [rf"\textbf{{{tex_escape(k)}}} & {tex_escape(v)} \\" for k, v in pairs]
        return "\n".join([r"\begin{tabularx}{\linewidth}{@{}p{.08\linewidth}Y@{}}", *rows, r"\end{tabularx}"])
    for idx in range(0, len(pairs), 2):
        left = pairs[idx]
        right = pairs[idx + 1] if idx + 1 < len(pairs) else ("", "")
        rows.append(rf"\textbf{{{tex_escape(left[0])}}} {tex_escape(left[1])} & \textbf{{{tex_escape(right[0])}}} {tex_escape(right[1])} \\")
    return "\n".join([r"\begin{tabularx}{\linewidth}{@{}Y Y@{}}", *rows, r"\end{tabularx}"])


def render_formula_cards(chapter: str) -> str:
    cards = FORMULA_CARDS.get(chapter, [])
    if not cards:
        return ""
    parts = [r"\begin{formulabox}{公式入口：变量、意义和使用场景}"]
    for card in cards:
        parts.append(r"\begin{tabularx}{\linewidth}{@{}p{.25\linewidth}Y@{}}")
        parts.append(rf"\textbf{{公式}} & $\displaystyle {card['formula']}$ \\")
        parts.append(rf"\textbf{{变量}} & {card['variables']} \\")
        parts.append(rf"\textbf{{意义}} & {tex_escape(card['meaning'])} \\")
        parts.append(rf"\textbf{{用在}} & {tex_escape(card['use'])} \\")
        parts.append(r"\end{tabularx}")
        parts.append(r"\vspace{2pt}\hrule\vspace{2pt}")
    parts.append(r"\end{formulabox}")
    return "\n".join(parts)


def render_method(chapter: str) -> str:
    methods = METHOD_LINES.get(chapter, ["先圈关键词，再定位公式和教材判据，最后排除相近选项。"])
    return "\n".join([r"\begin{chapterbox}{做题方法线}", *[tex_escape(m) for m in methods], r"\end{chapterbox}"])


def render_occurrences(item: dict[str, Any]) -> str:
    papers = item.get("paper_set") or split_papers(str(item.get("paper", "")))
    return f"出现 {len(papers)} 次：{', '.join(papers)}"


def render_question(item: dict[str, Any], idx: int) -> str:
    chapter = chapter_key(item.get("chapter", ""))
    title = f"{idx:02d}｜{chapter}｜{render_occurrences(item)}"
    answer = item.get("answer") or item.get("answer_hint") or "答案待补"
    source = item.get("source", "")
    pdf_page = item.get("pdf_page", "")
    print_page = item.get("print_page", "")
    anchor = item.get("quote_anchor", "")
    review = item.get("review_prompt", "")
    if isinstance(review, dict):
        review_text = f"{review.get('prompt', '')} 答：{review.get('answer', '')}".strip()
    else:
        review_text = str(review)
    parts = [rf"\begin{{qcard}}{{{tex_escape(title)}}}"]
    parts.append(rf"\textbf{{题目}}\quad {{\bfseries {tex_escape(item.get('stem', ''))}}}")
    opt = option_grid(item.get("options", {}) or {})
    if opt:
        parts.append(opt)
    parts.append(rf"\textbf{{答案/结论}}\quad {tex_escape(answer)}")
    parts.append(r"\begin{tabularx}{\linewidth}{@{}p{.14\linewidth}Y@{}}")
    parts.append(rf"\textbf{{信号}} & {tex_escape(item.get('test_point') or item.get('stem', ''))} \\")
    parts.append(rf"\textbf{{方法线}} & 先定位 {tex_escape(chapter)} 的公式/判据，再检查题干是否偷换对象、方向、载荷或失效形式。 \\")
    parts.append(rf"\textbf{{解析}} & {tex_escape(item.get('analysis') or item.get('answer_hint') or '')} \\")
    locator = tex_escape(item.get("chapter", "教材章节待补"))
    if pdf_page:
        locator += f"；PDF页 {tex_escape(pdf_page)}"
    if print_page:
        locator += f"；印刷页 {tex_escape(print_page)}"
    parts.append(rf"\textbf{{教材定位}} & {locator} \\")
    if anchor:
        parts.append(rf"\textbf{{原文锚点}} & {tex_escape(anchor)} \\")
    parts.append(rf"\textbf{{来源}} & {tex_escape(source)} \\")
    if review_text:
        parts.append(rf"\textbf{{迁移题}} & {tex_escape(review_text)} \\")
    parts.append(r"\end{tabularx}")
    snippet = item.get("snippet_local")
    if snippet:
        parts.append(r"\vspace{2pt}\begin{center}\includegraphics[width=.72\linewidth,height=.18\textheight,keepaspectratio]{" + snippet + r"}\\{\scriptsize 教材局部截图}\end{center}")
    parts.append(r"\end{qcard}")
    return "\n".join(parts)


def render_book(items: list[dict[str, Any]], out_dir: Path, filename: str, title: str, course: str) -> None:
    course_items = [item for item in items if item.get("course") == course]
    copy_snippets(course_items, out_dir, Path.cwd())
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in course_items:
        grouped[chapter_key(item.get("chapter", ""))].append(item)

    parts = [doc_preamble(title)]
    parts.append(r"\section*{使用说明}\addcontentsline{toc}{section}{使用说明}")
    parts.append(
        r"\begin{chapterbox}{收录口径}"
        "\n本册收录已结构化并可核验的往年卷客观小题，包括选择题、填空式选择题和判断题。"
        "同一考点的重复题不重复展开，而是在题卡标题中标注出现次数和来源卷。"
        "\n\\end{chapterbox}"
    )
    question_idx = 1
    for chapter in sorted(grouped, key=lambda key: CHAPTER_ORDER.get(key, 999)):
        parts.append(rf"\section{{{tex_escape(chapter)}}}")
        parts.append(render_formula_cards(chapter))
        parts.append(render_method(chapter))
        for item in grouped[chapter]:
            parts.append(render_question(item, question_idx))
            question_idx += 1
    parts.append(r"\end{document}")
    tex_path = out_dir / filename
    tex_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    items = load_b_choice(Path(args.b_choice_data))
    items.extend(load_objective_index(Path(args.objective_index)))
    items.extend(manual_supplements())
    merged = merge_items(items)
    if not args.skip_textbook_snippets:
        enrich_textbook_snippets(merged, out_dir, Path(args.upper_textbook), Path(args.lower_textbook))
    copy_snippets(merged, out_dir, Path.cwd())

    jsonl_path = out_dir / "deduped_objective_questions.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for item in merged:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    render_book(merged, out_dir, "mechanical_principles_choice_solution_book.tex", "机械原理选择小题题集", "principles")
    render_book(merged, out_dir, "mechanical_design_choice_solution_book.tex", "机械设计选择小题题集", "design")

    summary = {
        "total_deduped": len(merged),
        "principles": sum(1 for item in merged if item.get("course") == "principles"),
        "design": sum(1 for item in merged if item.get("course") == "design"),
        "jsonl": jsonl_path.name,
    }
    (out_dir / "all_choice_solution_books_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
