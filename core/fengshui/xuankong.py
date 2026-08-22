"""
core/fengshui/xuankong.py
=========================
玄空飞星 (Xuan Kong Flying Stars) 专业版

实现《沈氏玄空学》《地理辨正》《玄空秘旨》核心理论：

1. **三元九运**（Three Yuan Nine Cycles）
   每运 20 年：
     - 上元一运（1864-1883）、二运（1884-1903）、三运（1904-1923）
     - 中元四运（1924-1943）、五运（1944-1963）、六运（1964-1983）
     - 下元七运（1984-2003）、八运（2004-2023）、九运（2024-2043）

2. **运盘** — 当运中宫飞星，顺飞至九宫

3. **山盘 + 向盘**（坐山+朝向各自起飞星）
   - 山星管丁口（人）
   - 向星管财帛（财）
   - 按坐山/朝向地支阴阳决定顺飞 / 逆飞（挨星诀）

4. **二十四山** — 360° 分 24 山，每山 15°
   每山有阴阳属性，决定起飞顺逆

5. **令星到位** — 当令山向星到坐 / 到向的格局判定：
   - 旺山旺向（上吉）：山星到坐 + 向星到向
   - 上山下水（大凶）：山星到向 + 向星到坐
   - 双星到向：山向二星皆到向（财旺丁退）
   - 双星到坐：山向二星皆到坐（丁旺财退）

6. **特殊格局**：
   - 七星打劫
   - 合十（运星 + 山星 / 向星 = 10）
   - 连珠三般卦（123、234、345...）
   - 父母三般卦（147、258、369）

7. **二十四山水法**
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional


# ─────────────────────────────────────────────────────────────
# 1. 三元九运
# ─────────────────────────────────────────────────────────────

YUAN_YUN_PERIODS: List[Tuple[int, int, int, str]] = [
    # (运数, 起始年, 终止年, 三元)
    (1, 1864, 1883, "上元"),
    (2, 1884, 1903, "上元"),
    (3, 1904, 1923, "上元"),
    (4, 1924, 1943, "中元"),
    (5, 1944, 1963, "中元"),
    (6, 1964, 1983, "中元"),
    (7, 1984, 2003, "下元"),
    (8, 2004, 2023, "下元"),
    (9, 2024, 2043, "下元"),
]


def get_yun(year: int) -> Dict[str, Any]:
    """根据年份返回所在运。"""
    for yun, start, end, sanyuan in YUAN_YUN_PERIODS:
        if start <= year <= end:
            return {
                "yun": yun,
                "yun_name": ["一白", "二黑", "三碧", "四绿", "五黄", "六白", "七赤", "八白", "九紫"][yun-1],
                "start": start, "end": end,
                "sanyuan": sanyuan,
                "is_current": True if yun == 9 else False,  # 九运为当令
            }
    # 推算未来运
    if year > 2043:
        offset = (year - 1864) // 20
        yun = (offset % 9) + 1
        start = 1864 + offset * 20
        return {"yun": yun, "yun_name": "推算", "start": start, "end": start + 19, "sanyuan": "推算", "is_current": False}
    return {"yun": 0, "yun_name": "", "start": 0, "end": 0, "sanyuan": "", "is_current": False}


# ─────────────────────────────────────────────────────────────
# 2. 二十四山方位（360° 分 24 等份）
# ─────────────────────────────────────────────────────────────
# 顺序：壬子癸 丑艮寅 甲卯乙 辰巽巳 丙午丁 未坤申 庚酉辛 戌乾亥
# 三个一组对应八卦：坎艮震巽离坤兑乾
# 每山 15°，每卦 45°
# 山有阴阳：阴山逆飞，阳山顺飞
#
# 阳山（顺飞）：壬寅甲辰丙申庚戌 — 各卦地支三山中的第1、3山多为阳
# 阴山（逆飞）：子癸丑卯乙巳午丁未酉辛亥
#
# 严格按《沈氏玄空学·挨星诀》：
TWENTY_FOUR_MOUNTAINS: List[Dict[str, Any]] = [
    # (山名, 起始度数, 结束度数, 阴阳, 所属卦, 卦内序号 1/2/3)
    {"name": "壬", "start": 337.5, "end": 352.5, "yin_yang": "阳", "gua": "坎", "idx": 1},
    {"name": "子", "start": 352.5, "end": 7.5,   "yin_yang": "阴", "gua": "坎", "idx": 2},  # cross 0
    {"name": "癸", "start": 7.5,   "end": 22.5,  "yin_yang": "阴", "gua": "坎", "idx": 3},
    {"name": "丑", "start": 22.5,  "end": 37.5,  "yin_yang": "阴", "gua": "艮", "idx": 1},
    {"name": "艮", "start": 37.5,  "end": 52.5,  "yin_yang": "阳", "gua": "艮", "idx": 2},
    {"name": "寅", "start": 52.5,  "end": 67.5,  "yin_yang": "阳", "gua": "艮", "idx": 3},
    {"name": "甲", "start": 67.5,  "end": 82.5,  "yin_yang": "阳", "gua": "震", "idx": 1},
    {"name": "卯", "start": 82.5,  "end": 97.5,  "yin_yang": "阴", "gua": "震", "idx": 2},
    {"name": "乙", "start": 97.5,  "end": 112.5, "yin_yang": "阴", "gua": "震", "idx": 3},
    {"name": "辰", "start": 112.5, "end": 127.5, "yin_yang": "阴", "gua": "巽", "idx": 1},
    {"name": "巽", "start": 127.5, "end": 142.5, "yin_yang": "阳", "gua": "巽", "idx": 2},
    {"name": "巳", "start": 142.5, "end": 157.5, "yin_yang": "阳", "gua": "巽", "idx": 3},
    {"name": "丙", "start": 157.5, "end": 172.5, "yin_yang": "阳", "gua": "离", "idx": 1},
    {"name": "午", "start": 172.5, "end": 187.5, "yin_yang": "阴", "gua": "离", "idx": 2},
    {"name": "丁", "start": 187.5, "end": 202.5, "yin_yang": "阴", "gua": "离", "idx": 3},
    {"name": "未", "start": 202.5, "end": 217.5, "yin_yang": "阴", "gua": "坤", "idx": 1},
    {"name": "坤", "start": 217.5, "end": 232.5, "yin_yang": "阳", "gua": "坤", "idx": 2},
    {"name": "申", "start": 232.5, "end": 247.5, "yin_yang": "阳", "gua": "坤", "idx": 3},
    {"name": "庚", "start": 247.5, "end": 262.5, "yin_yang": "阳", "gua": "兑", "idx": 1},
    {"name": "酉", "start": 262.5, "end": 277.5, "yin_yang": "阴", "gua": "兑", "idx": 2},
    {"name": "辛", "start": 277.5, "end": 292.5, "yin_yang": "阴", "gua": "兑", "idx": 3},
    {"name": "戌", "start": 292.5, "end": 307.5, "yin_yang": "阴", "gua": "乾", "idx": 1},
    {"name": "乾", "start": 307.5, "end": 322.5, "yin_yang": "阳", "gua": "乾", "idx": 2},
    {"name": "亥", "start": 322.5, "end": 337.5, "yin_yang": "阳", "gua": "乾", "idx": 3},
]


def get_mountain_by_degree(degree: float) -> Dict[str, Any]:
    """根据精确度数（0-360）返回所在的山。"""
    deg = degree % 360
    for m in TWENTY_FOUR_MOUNTAINS:
        if m["start"] <= m["end"]:
            if m["start"] <= deg < m["end"]:
                return m
        else:  # 跨 0 度
            if deg >= m["start"] or deg < m["end"]:
                return m
    return TWENTY_FOUR_MOUNTAINS[0]


def get_mountain_by_name(name: str) -> Optional[Dict[str, Any]]:
    for m in TWENTY_FOUR_MOUNTAINS:
        if m["name"] == name:
            return m
    return None


# 坐山 → 朝向（180° 对应）
MOUNTAIN_OPPOSITE = {
    "壬": "丙", "子": "午", "癸": "丁",
    "丑": "未", "艮": "坤", "寅": "申",
    "甲": "庚", "卯": "酉", "乙": "辛",
    "辰": "戌", "巽": "乾", "巳": "亥",
    "丙": "壬", "午": "子", "丁": "癸",
    "未": "丑", "坤": "艮", "申": "寅",
    "庚": "甲", "酉": "卯", "辛": "乙",
    "戌": "辰", "乾": "巽", "亥": "巳",
}


# ─────────────────────────────────────────────────────────────
# 3. 九宫飞星核心算法
# ─────────────────────────────────────────────────────────────
# 洛书九宫位置（中宫为 5）：
#   4  9  2     东南 南  西南
#   3  5  7     东   中  西
#   8  1  6     东北 北  西北
# 阳顺飞：5→6→7→8→9→1→2→3→4（按洛书自然序）
# 阴逆飞：5→4→3→2→1→9→8→7→6
#
# 飞行的九宫位次（按数字 1-9 在洛书中的固定位置）：
LUOSHU_POS: Dict[int, Tuple[int, int]] = {
    # 数字 → (row, col)，row 0=上 1=中 2=下，col 0=左 1=中 2=右
    1: (2, 1),  # 北
    2: (0, 2),  # 西南（南方位中的右边）—— 但洛书 2 在西南
    3: (1, 0),  # 东
    4: (0, 0),  # 东南
    5: (1, 1),  # 中
    6: (2, 2),  # 西北
    7: (1, 2),  # 西
    8: (2, 0),  # 东北
    9: (0, 1),  # 南
}

LUOSHU_DIRECTION: Dict[int, str] = {
    1: "北", 2: "西南", 3: "东", 4: "东南", 5: "中",
    6: "西北", 7: "西", 8: "东北", 9: "南",
}

# 阳顺：中宫→西北→西→东北→南→北→西南→东→东南
YANG_FLY_SEQ = [5, 6, 7, 8, 9, 1, 2, 3, 4]
# 阴逆：相反
YIN_FLY_SEQ = [5, 4, 3, 2, 1, 9, 8, 7, 6]


def fly_stars(center_star: int, direction: str) -> Dict[int, int]:
    """
    从中宫起飞九宫飞星。
    
    Args:
        center_star: 入中宫的星数
        direction:   'yang' 顺飞 / 'yin' 逆飞
    
    Returns:
        {luoshu_position: star_number} (1-9 -> 1-9)
    """
    palace_seq = YANG_FLY_SEQ if direction == "yang" else YIN_FLY_SEQ
    palace_to_star: Dict[int, int] = {}
    for i, palace in enumerate(palace_seq):
        # 第 i 步飞入第 palace 宫
        star = ((center_star - 1 + i) % 9) + 1
        palace_to_star[palace] = star
    return palace_to_star


# ─────────────────────────────────────────────────────────────
# 4. 玄空飞星完整排盘
# ─────────────────────────────────────────────────────────────

def calculate_xuankong_chart(
    year: int,
    sitting_mountain: str = None,
    sitting_degree: float = None,
    analysis_year: int = None,
) -> Dict[str, Any]:
    """
    计算玄空飞星完整三盘（运/山/向）。
    
    Args:
        year:              建宅或入伙年份（决定运 —— 本盘静态，定终身不变）
        sitting_mountain:  坐山名（壬/子/癸/丑/艮/寅/...）— 二选一
        sitting_degree:    精确坐山度数 0-360 — 二选一（精确度数会自动判定下卦/起星）
        analysis_year:     分析流年（流年紫白叠加用 —— 动态辅参，宅静时动）。
                           缺省取当前年。建宅年定运为「体」，流年为「用」，二者须分。
    
    Returns:
        含 32+ 个字段，参见之前的文档字符串。
        若精确度数则额外含 chart_type 字段说明下卦/起星/兼线过度。
    """
    from datetime import datetime as _dt_now
    if analysis_year is None:
        analysis_year = _dt_now.now().year
    chart_type_info = None
    
    # 如果只提供度数，自动反查坐山名
    if sitting_mountain is None and sitting_degree is not None:
        mtn_info = get_mountain_by_degree(sitting_degree)
        sitting_mountain = mtn_info["name"]
    
    # 如果提供了度数，判定下卦/起星
    if sitting_degree is not None:
        from core.fengshui.xuankong_advanced import calculate_chart_type
        chart_type_info = calculate_chart_type(sitting_degree, sitting_mountain)
    
    if sitting_mountain is None:
        raise ValueError("须提供 sitting_mountain 或 sitting_degree 之一")
    
    yun_info = get_yun(year)
    yun = yun_info["yun"]
    
    # === 运盘 ===
    # 运数入中宫顺飞
    yun_chart = fly_stars(yun, "yang")
    
    # === 山盘 ===
    mtn = get_mountain_by_name(sitting_mountain)
    if not mtn:
        raise ValueError(f"未知坐山：{sitting_mountain}")
    
    sitting_gua = mtn["gua"]
    # 坐山对应卦的洛书数 = 山盘入中之星
    GUA_TO_LUOSHU = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "乾": 6, "兑": 7, "艮": 8, "离": 9}
    sitting_luoshu = GUA_TO_LUOSHU[sitting_gua]
    
    # 找坐山所在宫位的运星，作为山盘中宫星
    sitting_palace_yun_star = yun_chart[sitting_luoshu]
    # 山盘入中星 = 坐山所在宫位的运星
    # 飞行方向：阳山顺飞 / 阴山逆飞
    mtn_direction = "yang" if mtn["yin_yang"] == "阳" else "yin"
    mountain_chart = fly_stars(sitting_palace_yun_star, mtn_direction)
    
    # === 向盘 ===
    facing_mtn_name = MOUNTAIN_OPPOSITE[sitting_mountain]
    facing_mtn = get_mountain_by_name(facing_mtn_name)
    facing_gua = facing_mtn["gua"]
    facing_luoshu = GUA_TO_LUOSHU[facing_gua]
    facing_palace_yun_star = yun_chart[facing_luoshu]
    facing_direction = "yang" if facing_mtn["yin_yang"] == "阳" else "yin"
    direction_chart = fly_stars(facing_palace_yun_star, facing_direction)
    
    # === 合参 ===
    combined: Dict[int, Dict[str, int]] = {}
    for pos in range(1, 10):
        combined[pos] = {
            "yun": yun_chart[pos],
            "mountain": mountain_chart[pos],
            "facing": direction_chart[pos],
            "direction": LUOSHU_DIRECTION[pos],
        }
    
    # === 令星到位判定 ===
    # 当令山星到坐位 = 旺山，当令向星到向位 = 旺向
    current_yun = yun  # 当令星数 = 运数
    
    sitting_mtn_star = combined[sitting_luoshu]["mountain"]
    sitting_dir_star = combined[sitting_luoshu]["facing"]
    facing_mtn_star = combined[facing_luoshu]["mountain"]
    facing_dir_star = combined[facing_luoshu]["facing"]
    
    is_wangshan = (sitting_mtn_star == current_yun)  # 山星到坐
    is_wangxiang = (facing_dir_star == current_yun)  # 向星到向
    is_shangshan = (facing_mtn_star == current_yun)  # 山星到向（错位）
    is_xiashui = (sitting_dir_star == current_yun)   # 向星到坐（错位）
    
    if is_wangshan and is_wangxiang:
        verdict = "旺山旺向"
        verdict_level = "auspicious_great"
        verdict_desc = "山星到坐丁旺，向星到向财旺，乃上吉之局，丁财两旺"
    elif is_shangshan and is_xiashui:
        verdict = "上山下水"
        verdict_level = "inauspicious_great"
        verdict_desc = "山星到向、向星到坐，错位之凶局，损丁破财"
    elif is_wangshan and is_xiashui:
        verdict = "双星到坐"
        verdict_level = "mixed"
        verdict_desc = "山星与向星皆到坐方，丁旺财不利，宜坐方见山"
    elif is_shangshan and is_wangxiang:
        verdict = "双星到向"
        verdict_level = "mixed"
        verdict_desc = "山星与向星皆到向方，财旺丁不利，宜向方见水"
    else:
        verdict = "一般格局"
        verdict_level = "neutral"
        verdict_desc = "令星分布平均，需配合山水形势综合判断"
    
    # === 特殊格局检测 ===
    patterns = detect_special_patterns(combined, yun)
    
    # === 高级理论集成 ===
    from core.fengshui.xuankong_advanced import (
        analyze_zheng_ling_layout, detect_fan_fu_yin,
        overlay_annual_on_base, detect_annual_warnings,
        detect_qixing_dajie_precise, analyze_shoushan_chusha,
        detect_taisui_conflict,
    )
    from core.fengshui.double_star_judgments import (
        get_double_star_judgment, get_wuxing_interaction,
    )
    
    # 1. 零正神分析
    zheng_ling = analyze_zheng_ling_layout(yun, sitting_gua, facing_gua)
    
    # 2. 反伏吟检测
    fan_fu_yin = detect_fan_fu_yin(yun, sitting_palace_yun_star, facing_palace_yun_star)
    
    # 3. 流年紫白叠加（动态辅参：用分析流年，非建宅年——宅静时动）
    overlaid = overlay_annual_on_base(combined, analysis_year)
    annual_warnings = detect_annual_warnings(overlaid, analysis_year)
    
    # 4. 精确七星打劫
    qixing = detect_qixing_dajie_precise(combined, facing_gua)
    
    # 5. 收山出煞
    shoushan_chusha = analyze_shoushan_chusha(combined, sitting_luoshu, facing_luoshu, yun)
    
    # 6. 太岁刑冲（流年现象：太岁随年迁，用分析流年而非建宅年）
    taisui = detect_taisui_conflict(analysis_year, sitting_mountain)
    
    # 6b. 金龙四诀（蒋大鸿真传）
    from core.fengshui.xuankong_advanced import analyze_jinlong_juejue
    jinlong = analyze_jinlong_juejue(
        combined, sitting_luoshu, facing_luoshu, yun,
        mtn["yin_yang"], facing_mtn["yin_yang"],
        sitting_gua, facing_gua,
    )
    
    # 7. 每宫双星断（81 种组合）
    palace_judgments = {}
    for pos, stars in combined.items():
        m, f = stars["mountain"], stars["facing"]
        judgment = get_double_star_judgment(m, f, current_yun=yun)
        wuxing = get_wuxing_interaction(m, f)
        palace_judgments[pos] = {
            **judgment,
            "mountain_star": m,
            "facing_star": f,
            "direction": stars["direction"],
            "wuxing_interaction": wuxing,
        }
    
    # === 综合 verdict —— 多维度合参（最高专业等级核心）===
    overall = _calculate_overall_verdict(
        wangshan=is_wangshan, wangxiang=is_wangxiang,
        shangshan=is_shangshan, xiashui=is_xiashui,
        zheng_ling=zheng_ling, fan_fu_yin=fan_fu_yin,
        qixing=qixing, taisui=taisui,
        special_patterns=patterns,
    )
    
    return {
        "year": year,                            # 建宅/入伙年（定运·本盘静态）
        "analysis_year": analysis_year,          # 分析流年（流年紫白/太岁叠加·动态辅参）
        "yun": yun_info,
        "sitting_mountain": sitting_mountain,
        "sitting_degree": sitting_degree,
        "chart_type": chart_type_info,   # 下卦/起星/兼线过度（仅当提供度数时）
        "sitting_gua": sitting_gua,
        "sitting_yin_yang": mtn["yin_yang"],
        "facing_mountain": facing_mtn_name,
        "facing_gua": facing_gua,
        "facing_yin_yang": facing_mtn["yin_yang"],
        "yun_chart": yun_chart,
        "mountain_chart": mountain_chart,
        "direction_chart": direction_chart,
        "combined": combined,
        "overlaid_with_annual": overlaid,
        "current_yun_star": current_yun,
        "wangshan": is_wangshan,
        "wangxiang": is_wangxiang,
        "shangshan": is_shangshan,
        "xiashui": is_xiashui,
        "verdict": verdict,
        "verdict_level": verdict_level,
        "verdict_desc": verdict_desc,
        "special_patterns": patterns,
        "remedies": _get_remedies(combined, yun),
        # ─── 高级专业内容 ───
        "zheng_ling_shen": zheng_ling,            # 零正神
        "fan_fu_yin": fan_fu_yin,                  # 反伏吟
        "annual_warnings": annual_warnings,        # 流年警示
        "qixing_dajie_precise": qixing,            # 精确七星打劫
        "shoushan_chusha": shoushan_chusha,        # 收山出煞
        "taisui": taisui,                          # 太岁刑冲
        "jinlong_juejue": jinlong,                  # 金龙四诀（《青囊奥语》）
        "palace_judgments": palace_judgments,      # 9 宫 81 组合断语
        "overall": overall,                        # 综合多维评级（合参 5 维）
    }


def _calculate_overall_verdict(wangshan, wangxiang, shangshan, xiashui,
                                  zheng_ling, fan_fu_yin, qixing, taisui,
                                  special_patterns):
    """
    综合 5 维评级（玄空最高专业水平的核心判断）：
      维度 1：令星到位（旺山旺向 +2 / 上山下水 -2 / 双星到一边 0）
      维度 2：零正神（perfect +2 / good +1 / bad -1 / very_bad -2）
      维度 3：反伏吟（-2 / -3）
      维度 4：精确七星打劫（真打劫 +3 / 假打劫 +1）
      维度 5：太岁冲坐（-2 / -1）
      额外：父母三般卦/合十 +1，五黄到山到向 -1
    
    总分范围约 -8 ~ +8，归一化为五级：
      ≥ 5：上吉局（极品）
      3-4：吉局
      0-2：平局
      -2 ~ -1：凶局
      ≤ -3：大凶局
    """
    score = 0
    factors = []
    
    # 维度 1：令星到位
    if wangshan and wangxiang:
        score += 2; factors.append(("令星到位", 2, "旺山旺向（上吉）"))
    elif shangshan and xiashui:
        score -= 2; factors.append(("令星到位", -2, "上山下水（大凶）"))
    elif wangshan and xiashui:
        score += 0; factors.append(("令星到位", 0, "双星到坐（丁旺财不利）"))
    elif shangshan and wangxiang:
        score += 0; factors.append(("令星到位", 0, "双星到向（财旺丁不利）"))
    else:
        score -= 1; factors.append(("令星到位", -1, "令星散乱"))
    
    # 维度 2：零正神（《天玉经》核心）
    if zheng_ling:
        verdict = zheng_ling.get("verdict", "neutral")
        zl_score = {"perfect": 2, "good": 1, "neutral": 0, "bad": -1, "very_bad": -2}.get(verdict, 0)
        score += zl_score
        factors.append(("零正神", zl_score, f"{zheng_ling.get('desc', '')[:30]}…"))
    
    # 维度 3：反伏吟
    if fan_fu_yin and fan_fu_yin.get("has_fan_fu_yin"):
        ffy_count = len(fan_fu_yin.get("patterns", []))
        ffy_score = -2 * ffy_count
        # 反吟比伏吟更凶
        if any("反吟" in p.get("type","") for p in fan_fu_yin.get("patterns", [])):
            ffy_score -= 1
        score += ffy_score
        factors.append(("反伏吟", ffy_score, f"犯 {ffy_count} 处反伏吟"))
    
    # 维度 4：七星打劫
    if qixing and qixing.get("type", "无") != "无":
        if qixing.get("is_real"):
            score += 3; factors.append(("七星打劫", 3, "真打劫（玄空至贵）"))
        else:
            score += 1; factors.append(("七星打劫", 1, qixing.get("type", "假打劫")))
    
    # 维度 5：太岁刑冲
    if taisui and taisui.get("has_conflict"):
        if taisui.get("type") == "冲太岁":
            score -= 2; factors.append(("太岁", -2, "冲太岁（岁破）"))
        else:
            score -= 1; factors.append(("太岁", -1, taisui.get("type", "")))
    
    # 额外特殊格局加减
    for p in special_patterns or []:
        if "父母三般卦" in p.get("name", ""):
            score += 1; factors.append(("特殊格局", 1, "父母三般卦"))
        elif "合十" in p.get("name", "") and "全盘" in p.get("name", ""):
            score += 1; factors.append(("特殊格局", 1, "全盘合十"))
        elif "五黄入" in p.get("name", ""):
            score -= 0.5; factors.append(("特殊格局", -0.5, p["name"]))
    
    # 归一化等级
    if score >= 5:
        grade = "上吉局"; grade_level = "auspicious_great"
        desc = "极品玄空局，丁财两旺、富贵绵长，三元不败之贵格"
    elif score >= 3:
        grade = "吉局"; grade_level = "auspicious"
        desc = "上等玄空局，财运亨通、家口平安"
    elif score >= 0:
        grade = "平局"; grade_level = "mixed"
        desc = "玄空局有得有失，须配合形理及人事综合判断"
    elif score >= -2:
        grade = "凶局"; grade_level = "inauspicious"
        desc = "玄空局凶象明显，须及时化解或改门换向"
    else:
        grade = "大凶局"; grade_level = "inauspicious_great"
        desc = "玄空大凶局，不利居住，宜尽早搬迁或彻底改局"
    
    return {
        "score": round(score, 1),
        "grade": grade,
        "grade_level": grade_level,
        "desc": desc,
        "factors": [{"dim": d, "score": s, "note": n} for d, s, n in factors],
    }


# ─────────────────────────────────────────────────────────────
# 5. 特殊格局检测
# ─────────────────────────────────────────────────────────────

def detect_special_patterns(combined: Dict, current_yun: int) -> List[Dict[str, Any]]:
    """检测特殊格局：合十、连珠、父母三般卦、七星打劫"""
    patterns = []
    
    # === 合十（运星+山星=10 或 运星+向星=10）===
    he_shi_mountain = []
    he_shi_facing = []
    for pos, stars in combined.items():
        if stars["yun"] + stars["mountain"] == 10:
            he_shi_mountain.append(LUOSHU_DIRECTION[pos])
        if stars["yun"] + stars["facing"] == 10:
            he_shi_facing.append(LUOSHU_DIRECTION[pos])
    
    if len(he_shi_mountain) == 9:
        patterns.append({
            "name": "全盘合十（山盘）",
            "level": "auspicious_great",
            "desc": "九宫运星与山星处处合十，主旺丁，家口平安，乃大吉之局",
            "source": "《沈氏玄空学·合十吉格》",
        })
    elif len(he_shi_mountain) >= 3:
        patterns.append({
            "name": f"部分合十（山盘，{len(he_shi_mountain)}宫）",
            "level": "auspicious",
            "desc": f"{', '.join(he_shi_mountain)}方运山合十，主该方旺人丁",
            "source": "《沈氏玄空学》",
        })
    
    if len(he_shi_facing) == 9:
        patterns.append({
            "name": "全盘合十（向盘）",
            "level": "auspicious_great",
            "desc": "九宫运星与向星处处合十，主旺财，财源广进",
            "source": "《沈氏玄空学·合十吉格》",
        })
    elif len(he_shi_facing) >= 3:
        patterns.append({
            "name": f"部分合十（向盘，{len(he_shi_facing)}宫）",
            "level": "auspicious",
            "desc": f"{', '.join(he_shi_facing)}方运向合十，主该方旺财",
            "source": "《沈氏玄空学》",
        })
    
    # === 父母三般卦（147/258/369）===
    # 检查山向运三盘星组成 147/258/369 之一
    sanban_count = 0
    for pos, stars in combined.items():
        s = {stars["yun"], stars["mountain"], stars["facing"]}
        if s == {1, 4, 7} or s == {2, 5, 8} or s == {3, 6, 9}:
            sanban_count += 1
    
    if sanban_count >= 6:
        patterns.append({
            "name": "父母三般卦",
            "level": "auspicious_great",
            "desc": f"九宫多见 147/258/369 组合（{sanban_count}/9 宫），最贵之局，主三元不败",
            "source": "《地理辨正·天玉经》「父母三般卦，时师未曾话」",
        })
    
    # === 连珠三般卦（123/234/345/456/567/678/789/891/912）===
    lianzhu_count = 0
    for pos, stars in combined.items():
        s = sorted([stars["yun"], stars["mountain"], stars["facing"]])
        # 连续三数
        if s[1] - s[0] == 1 and s[2] - s[1] == 1:
            lianzhu_count += 1
        # 跨越9-1的特殊连珠
        if s == [1, 8, 9] or s == [1, 2, 9]:
            lianzhu_count += 1
    
    if lianzhu_count >= 6:
        patterns.append({
            "name": "连珠三般卦",
            "level": "auspicious",
            "desc": f"九宫多见三星连珠（{lianzhu_count}/9 宫），主一气流通，吉利之局",
            "source": "《地理辨正·青囊奥语》",
        })
    
    # === 七星打劫（一四七 / 二五八 / 三六九） ===
    # 检查向盘是否构成"打劫局"（一定方位上有特殊星组合）
    facing_stars_by_dir = {LUOSHU_DIRECTION[pos]: stars["facing"] for pos, stars in combined.items()}
    # 北中南 / 东中西 / 东南中西北 / 东北中西南 四组之一构成 147 / 258 / 369
    qixing_groups = [
        ["北", "中", "南"], ["东", "中", "西"],
        ["东南", "中", "西北"], ["东北", "中", "西南"],
    ]
    for group in qixing_groups:
        stars_in_group = sorted([facing_stars_by_dir[d] for d in group])
        if stars_in_group == [1, 4, 7] or stars_in_group == [2, 5, 8] or stars_in_group == [3, 6, 9]:
            patterns.append({
                "name": "七星打劫",
                "level": "auspicious",
                "desc": f"{' - '.join(group)}三宫向星成 {''.join(map(str, stars_in_group))} 之局，主一气贯通，劫财得宝",
                "source": "《玄空秘旨》「七星打劫，离宫要相合」",
            })
            break
    
    # === 五黄到坐/到向（凶象警示）===
    sitting_palace_facing_star = None
    facing_palace_facing_star = None
    # 找出坐位/向位的星
    for pos, stars in combined.items():
        if stars["mountain"] == 5:
            patterns.append({
                "name": "五黄入山",
                "level": "inauspicious",
                "desc": f"五黄飞临{LUOSHU_DIRECTION[pos]}方山盘，此方位忌动土修造，主疾病灾祸",
                "source": "《沈氏玄空学·五黄忌》",
            })
        if stars["facing"] == 5:
            patterns.append({
                "name": "五黄入向",
                "level": "inauspicious",
                "desc": f"五黄飞临{LUOSHU_DIRECTION[pos]}方向盘，此方位忌见水路或大门，主破财灾难",
                "source": "《沈氏玄空学》",
            })
    
    return patterns


def _get_remedies(combined: Dict, current_yun: int) -> List[Dict[str, Any]]:
    """生成化解建议"""
    remedies = []
    for pos, stars in combined.items():
        direction = LUOSHU_DIRECTION[pos]
        m, f = stars["mountain"], stars["facing"]
        
        # 五黄
        if m == 5 or f == 5:
            remedies.append({
                "direction": direction,
                "issue": f"五黄星临{direction}方",
                "remedy": "放铜质风铃、六帝钱、葫芦化煞；忌动土",
                "color_suggestion": "白色、金色（金泄土）",
            })
        # 二黑病符
        if m == 2 or f == 2:
            remedies.append({
                "direction": direction,
                "issue": f"二黑病符临{direction}方",
                "remedy": "放铜葫芦、铜钟化病气；老人小孩避免久居",
                "color_suggestion": "白色（金泄土）",
            })
        # 三碧蚩尤（口舌）
        if m == 3 or f == 3:
            remedies.append({
                "direction": direction,
                "issue": f"三碧蚩尤临{direction}方",
                "remedy": "放红色物品、红地毯化解（火克木）",
                "color_suggestion": "红色、紫色",
            })
        # 七赤破军（血光口舌）
        if m == 7 or f == 7:
            remedies.append({
                "direction": direction,
                "issue": f"七赤破军临{direction}方",
                "remedy": "放蓝色水晶、水种植物化解（水泄金）",
                "color_suggestion": "蓝色、黑色",
            })
    
    # 当运吉星
    for pos, stars in combined.items():
        direction = LUOSHU_DIRECTION[pos]
        # 当令星到向
        if stars["facing"] == current_yun:
            remedies.append({
                "direction": direction,
                "issue": f"{['','一白','二黑','三碧','四绿','五黄','六白','七赤','八白','九紫'][current_yun]}当令向星到{direction}方",
                "remedy": "此方位宜见水（鱼缸、流水）、放大门、开窗；旺财之地",
                "color_suggestion": "招财色（金黄、紫色）",
                "is_auspicious": True,
            })
        # 当令星到坐
        if stars["mountain"] == current_yun:
            remedies.append({
                "direction": direction,
                "issue": f"{['','一白','二黑','三碧','四绿','五黄','六白','七赤','八白','九紫'][current_yun]}当令山星到{direction}方",
                "remedy": "此方位宜见山（实体建筑、靠山）、放主卧床头；旺人丁之地",
                "color_suggestion": "稳重色（土黄、深棕）",
                "is_auspicious": True,
            })
        # 八白财星（九运辅佐财星）
        if (stars["mountain"] == 8 or stars["facing"] == 8) and current_yun == 9:
            remedies.append({
                "direction": direction,
                "issue": f"八白财星临{direction}方",
                "remedy": "此方位宜放招财物品（貔貅、聚宝盆、水晶）",
                "color_suggestion": "金黄、土黄",
                "is_auspicious": True,
            })
    
    return remedies


# ─────────────────────────────────────────────────────────────
# 6. 城门诀（特殊水法）
# ─────────────────────────────────────────────────────────────

def get_chengmen_jue(sitting_mountain: str) -> Dict[str, Any]:
    """
    城门诀（《沈氏玄空学》）：坐山左右两个山为"城门"，可放水开门得吉。
    
    Args:
        sitting_mountain: 坐山名
    
    Returns:
        {'left_chengmen': ..., 'right_chengmen': ..., 'desc': ...}
    """
    mtn = get_mountain_by_name(sitting_mountain)
    if not mtn:
        return {}
    
    # 找到当前山在 24 山中的索引
    idx = next((i for i, m in enumerate(TWENTY_FOUR_MOUNTAINS) if m["name"] == sitting_mountain), 0)
    # 朝向对面 + 左右各一山
    facing_idx = (idx + 12) % 24
    left_idx = (facing_idx - 1) % 24
    right_idx = (facing_idx + 1) % 24
    
    return {
        "sitting": sitting_mountain,
        "facing": TWENTY_FOUR_MOUNTAINS[facing_idx]["name"],
        "left_chengmen": TWENTY_FOUR_MOUNTAINS[left_idx]["name"],
        "right_chengmen": TWENTY_FOUR_MOUNTAINS[right_idx]["name"],
        "desc": (
            f"坐{sitting_mountain}朝{TWENTY_FOUR_MOUNTAINS[facing_idx]['name']}，"
            f"左城门{TWENTY_FOUR_MOUNTAINS[left_idx]['name']}，"
            f"右城门{TWENTY_FOUR_MOUNTAINS[right_idx]['name']}。"
            f"城门方位宜见水或开门，可催财气，乃《玄空秘旨》「城门一诀最为良」之妙。"
        ),
    }
