"""
core/fengshui/flying_stars.py
===============================
玄空飞星风水 (Xuan Kong Flying Stars FengShui)

Implements:
  • Annual flying star calculation (年飞星) for any year
  • Nine star (九宫飞星) meanings and interactions
  • Auspicious / inauspicious sector identification
  • Room placement recommendations
  • Personal lucky direction (文昌/催财/桃花/健康位)
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional
from core.constants import JIUGONG_POSITIONS

# ─────────────────────────────────────────────────────────────
# 1. Nine Star (九星) Properties
# ─────────────────────────────────────────────────────────────

NINE_STARS: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "一白贪狼星", "element": "水", "nature": "吉",
        "color": "#3498db", "palace": "坎",
        "meaning": "主桃花、文学、学业、贵人、口才",
        "room_use": ["书房", "主卧（单身或学生）"],
        "career": "利文学、外交、贸易、演讲",
        "health": "注意肾脏、泌尿系统",
        "annual_2026": "流年运势中等，利文学求职",
    },
    2: {
        "name": "二黑巨门星", "element": "土", "nature": "大凶",
        "color": "#e74c3c", "palace": "坤",
        "meaning": "主疾病、孕产风险、官非口舌",
        "room_use": ["厕所", "储物室（避免卧室厨房）"],
        "career": "此宫位不利工作，防官非",
        "health": "脾胃、妇科（女性）、腹部疾病",
        "annual_2026": "二黑病符，此方位放铜葫芦化煞",
        "remedy": "铜葫芦、六帝钱、铜钟化煞",
    },
    3: {
        "name": "三碧禄存星", "element": "木", "nature": "凶",
        "color": "#e67e22", "palace": "震",
        "meaning": "主口舌是非、争吵、官司",
        "room_use": ["厕所", "厨房（火克木，化解口舌）"],
        "career": "防口舌纷争，合同纠纷",
        "health": "肝胆、神经系统、肢体受伤",
        "annual_2026": "三碧蚩尤，此方位易有口角官非",
        "remedy": "红色物品化解（火克木）",
    },
    4: {
        "name": "四绿文昌星", "element": "木", "nature": "吉",
        "color": "#27ae60", "palace": "巽",
        "meaning": "主文学、考试、桃花、聪明才智",
        "room_use": ["书房", "儿童房", "办公室"],
        "career": "利文职、学术、写作、教育",
        "health": "注意肝胆，整体较平稳",
        "annual_2026": "四绿文昌，此方位学习读书大吉",
    },
    5: {
        "name": "五黄廉贞星", "element": "土", "nature": "大凶",
        "color": "#c0392b", "palace": "中",
        "meaning": "主灾祸、疾病、死亡、破财，最凶之星",
        "room_use": ["避免一切活动，尤其忌动土"],
        "career": "此方位开工动土必出大事",
        "health": "五脏皆有风险，尤其重病",
        "annual_2026": "五黄飞入XX宫（见年飞星表），此方绝对不可动土",
        "remedy": "六帝钱、铜风铃、葫芦化煞（最重要）",
    },
    6: {
        "name": "六白武曲星", "element": "金", "nature": "吉",
        "color": "#f39c12", "palace": "乾",
        "meaning": "主武职、权力、偏财、贵人",
        "room_use": ["主卧（当家者）", "书房", "客厅主位"],
        "career": "利军警、管理、投资、武职",
        "health": "头部、肺部注意",
        "annual_2026": "六白武曲当旺，利偏财求财",
    },
    7: {
        "name": "七赤破军星", "element": "金", "nature": "凶",
        "color": "#9b59b6", "palace": "兑",
        "meaning": "主口舌、血光、盗贼、破财",
        "room_use": ["厕所", "储物室"],
        "career": "防被骗、合同纠纷、口舌",
        "health": "肺部、皮肤、手术",
        "annual_2026": "七赤入中，防口舌血光",
        "remedy": "蓝色水晶球、水种植物化解",
    },
    8: {
        "name": "八白左辅星", "element": "土", "nature": "大吉",
        "color": "#f1c40f", "palace": "艮",
        "meaning": "主财帛、房产、旺丁旺财，当运最吉之星",
        "room_use": ["主卧", "客厅", "财位（放招财物品）"],
        "career": "最利置业、投资、经营",
        "health": "脾胃平稳，整体健康",
        "annual_2026": "八白正当运，旺丁旺财，此方位为财位",
    },
    9: {
        "name": "九紫右弼星", "element": "火", "nature": "吉",
        "color": "#e74c3c", "palace": "离",
        "meaning": "主喜庆、婚姻、名声、贵人",
        "room_use": ["客厅", "主卧（夫妻）"],
        "career": "利名声、喜庆、升迁、婚事",
        "health": "心脑血管、眼睛注意",
        "annual_2026": "九紫入宅，主喜庆连连，婚嫁喜事",
    },
}

# ─────────────────────────────────────────────────────────────
# 2. Annual Flying Star Chart Calculation (年飞星布局)
#    The annual center star cycles: 1→9→8→7→6→5→4→3→2→1
#    Regression: 2024=三碧(3), 2025=二黑(2), 2026=一白(1), 2027=九紫(9)
# ─────────────────────────────────────────────────────────────

# 标准年飞星算法（《沈氏玄空学》三元紫白）：
#   下元甲子 1984 年中宫 = 七赤
#   每年中宫数 -1，1↔9 循环
#
# 验证：2024=三碧，2025=二黑，2026=一白，2027=九紫
# 民间俗称"逆推法"
def get_annual_center_star(year: int) -> int:
    """
    Return the center palace star for a year.
    1984 (甲子) = 七赤，每年减一，循环 1-9。
    """
    offset = year - 1984
    # (7 - offset) 取模到 [1..9]
    center = ((7 - offset - 1) % 9) + 1
    return center

# Luoshu (洛书) natural positions for stars 1-9:
# 4 9 2
# 3 5 7
# 8 1 6
# Position order (luoshu): pos 1→S, 2→SW, 3→E, 4→SE, 5→C, 6→NW, 7→W, 8→NE, 9→N
LUOSHU_NATURAL: Dict[int, str] = {
    1: "北",   2: "西南", 3: "东",
    4: "东南", 5: "中",   6: "西北",
    7: "西",   8: "东北", 9: "南",
}

DIRECTION_TO_LUOSHU: Dict[str, int] = {v: k for k, v in LUOSHU_NATURAL.items()}

# Yang (forward) flying order for annual stars:
# Center → then fly in luoshu sequence 5→6→7→8→9→1→2→3→4
YANG_FLY_ORDER = [5, 6, 7, 8, 9, 1, 2, 3, 4]  # palace position order

def calculate_annual_flying_stars(year: int) -> Dict[str, Any]:
    """
    Calculate the nine-palace flying star chart for a year.
    Returns a dict with direction → star number mapping.
    """
    center = get_annual_center_star(year)

    # Stars fly in yang order starting from center's natural position
    # Each palace position gets a star by rotating from center
    palace_to_star: Dict[int, int] = {}
    for i, palace_pos in enumerate(YANG_FLY_ORDER):
        star = ((center - 1 + i) % 9) + 1
        palace_to_star[palace_pos] = star

    # Build direction → star mapping
    direction_stars: Dict[str, Dict[str, Any]] = {}
    for palace_pos, star_num in palace_to_star.items():
        direction = LUOSHU_NATURAL[palace_pos]
        star_info = NINE_STARS[star_num].copy()
        direction_stars[direction] = {
            "star_num": star_num,
            "direction": direction,
            **star_info,
        }

    # Identify special positions for this year
    auspicious = [d for d, s in direction_stars.items() if s["nature"] in ("吉", "大吉")]
    inauspicious = [d for d, s in direction_stars.items() if s["nature"] in ("凶", "大凶")]
    five_yellow = next((d for d, s in direction_stars.items() if s["star_num"] == 5), "")
    two_black = next((d for d, s in direction_stars.items() if s["star_num"] == 2), "")
    eight_white = next((d for d, s in direction_stars.items() if s["star_num"] == 8), "")
    four_green = next((d for d, s in direction_stars.items() if s["star_num"] == 4), "")
    one_white = next((d for d, s in direction_stars.items() if s["star_num"] == 1), "")

    return {
        "year": year,
        "center_star": center,
        "center_star_name": NINE_STARS[center]["name"],
        "direction_stars": direction_stars,
        "auspicious_directions": auspicious,
        "inauspicious_directions": inauspicious,
        "five_yellow_direction": five_yellow,
        "two_black_direction": two_black,
        "wealth_direction": eight_white,      # 八白当运为财位
        "study_direction": four_green,         # 四绿文昌为学位
        "romance_direction": one_white,        # 一白桃花
        "annual_summary": _build_annual_summary(year, center, eight_white, five_yellow, four_green),
    }

def _build_annual_summary(year: int, center: int, wealth_dir: str, danger_dir: str, study_dir: str) -> str:
    center_name = NINE_STARS[center]["name"]
    return (
        f"{year}年，{center_name}入中宫。"
        f"财位在{wealth_dir}方（八白旺财），宜在此方摆放招财物品；"
        f"文昌位在{study_dir}方（四绿文昌），宜在此方设书房；"
        f"五黄在{danger_dir}方，此方绝对禁止动土装修，宜放六帝钱化煞；"
        f"二黑病符位需摆铜葫芦化病气。"
    )

# ─────────────────────────────────────────────────────────────
# 3. Personal Lucky Directions (个人吉方)
#    基于命卦的 4 吉位 + 4 凶位
#
# 单一数据源：直接从 core.fengshui.calculator.EIGHT_MANSION 派生
# 避免两个表数据漂移
# ─────────────────────────────────────────────────────────────

def _derive_ming_gua_lucky_from_eight_mansion() -> Dict[int, Dict[str, Any]]:
    """从 EIGHT_MANSION 反查表派生命卦个人方位字典"""
    from core.fengshui.calculator import EIGHT_MANSION
    STAR_TO_KEY = {
        "生气": "shengqi", "天医": "tianyi", "延年": "niannian", "伏位": "fuwei",
        "绝命": "jueming", "五鬼": "wugui", "六煞": "liusha", "祸害": "huohai",
    }
    out = {}
    for gua, sectors in EIGHT_MANSION.items():
        gua_info = {}
        for direction, star in sectors.items():
            key = STAR_TO_KEY.get(star)
            if key:
                gua_info[key] = direction
        # 衍生字段
        gua_info["best_bed_dir"]  = f"{gua_info.get('shengqi','')}（生气）"
        gua_info["best_desk_dir"] = f"{gua_info.get('tianyi','')}（天医）"
        gua_info["wealth_spot"]   = f"{gua_info.get('shengqi','')}方"
        gua_info["health_spot"]   = f"{gua_info.get('tianyi','')}方"
        # 桃花位 = 延年位（《八宅明镜》：延年武曲星主婚姻）
        gua_info["romance_spot"]  = f"{gua_info.get('niannian','')}方"
        out[gua] = gua_info
    return out

# Ming Gua → 4 lucky directions (生气/天医/延年/伏位) and 4 unlucky
MING_GUA_LUCKY: Dict[int, Dict[str, Any]] = _derive_ming_gua_lucky_from_eight_mansion()

def get_personal_directions(ming_gua: int) -> Dict[str, Any]:
    """Return personal lucky and unlucky directions for a Ming Gua."""
    info = MING_GUA_LUCKY.get(ming_gua, MING_GUA_LUCKY[1])
    return {
        "ming_gua": ming_gua,
        "shengqi": {"direction": info["shengqi"], "meaning": "生气位（最旺财丁，宜主卧门向）"},
        "tianyi": {"direction": info["tianyi"], "meaning": "天医位（利健康求医，宜卧室）"},
        "niannian": {"direction": info["niannian"], "meaning": "延年位（利婚姻家庭，宜客厅）"},
        "fuwei": {"direction": info["fuwei"], "meaning": "伏位（稳定守成，宜储藏）"},
        "jueming": {"direction": info["jueming"], "meaning": "绝命位（最凶，忌卧室厨房）"},
        "wugui": {"direction": info["wugui"], "meaning": "五鬼位（官非灾祸，忌主要房间）"},
        "liusha": {"direction": info["liusha"], "meaning": "六煞位（破财损丁，忌财位）"},
        "huohai": {"direction": info["huohai"], "meaning": "祸害位（口舌疾病，忌卧室）"},
        "best_bed_dir": info.get("best_bed_dir", ""),
        "best_desk_dir": info.get("best_desk_dir", ""),
        "wealth_spot": info.get("wealth_spot", ""),
        "health_spot": info.get("health_spot", ""),
        "romance_spot": info.get("romance_spot", ""),
        "room_advice": [
            f"主卧建议朝向{info.get('best_bed_dir','')}，最有利于休息和健康",
            f"书桌/工作台面朝{info.get('best_desk_dir','')}，有助提升专注力和贵人运",
            f"财位在{info.get('wealth_spot','')}，宜摆放招财貔貅、绿植或流水盆",
            f"忌在绝命位（{info.get('jueming','')}）设置主卧或厨房",
        ],
    }

# ─────────────────────────────────────────────────────────────
# 4. Combined Analysis (合参八宅 + 飞星)
# ─────────────────────────────────────────────────────────────

def comprehensive_fengshui_analysis(
    ming_gua: int,
    house_gua: int,
    year: int,
    house_facing: str,
) -> Dict[str, Any]:
    """Combine Eight Mansion + Flying Stars + Personal Directions."""
    annual = calculate_annual_flying_stars(year)
    personal = get_personal_directions(ming_gua)

    # Cross-reference: which personal lucky directions also have good annual stars?
    lucky_dir = personal["shengqi"]["direction"]
    annual_star_at_lucky = annual["direction_stars"].get(lucky_dir, {})

    combined_wealth = personal.get("wealth_spot", "")
    annual_wealth = annual.get("wealth_direction", "")

    return {
        "annual_chart": annual,
        "personal_directions": personal,
        "year": year,
        "combined_advice": _build_combined_advice(
            ming_gua, annual, personal, annual_star_at_lucky, combined_wealth, annual_wealth
        ),
    }

def _build_combined_advice(
    ming_gua: int, annual: Dict, personal: Dict,
    annual_at_lucky: Dict, personal_wealth: str, annual_wealth: str,
) -> List[str]:
    advice = []

    # Wealth
    if personal_wealth == annual_wealth:
        advice.append(f"✦ 大利财运：个人生气位（{personal_wealth}）与年飞星财位重合，是难得的双重旺财方位！强烈建议在此方摆放招财物品或设置财位。")
    else:
        advice.append(f"◆ 个人财位在{personal_wealth}方（生气），年飞星财位在{annual_wealth}方（八白），两者兼顾最佳。")

    # Five Yellow warning
    fy_dir = annual.get("five_yellow_direction", "")
    if fy_dir:
        advice.append(f"⚠ 重要警示：{annual.get('year','')}年五黄凶星飞临{fy_dir}方，此方位绝对禁止动土装修，需放六帝钱或铜葫芦化煞。")

    # Study direction
    sd = annual.get("study_direction", "")
    pd = personal.get("tianyi", {}).get("direction", "")
    if sd:
        advice.append(f"◆ 文昌学位在{sd}方（四绿文昌星），学生建议在此方向学习，或将书桌朝向此方。")

    # Romance
    romance = personal.get("romance_spot", "")
    if romance:
        advice.append(f"◆ 桃花情缘位在{romance}方，单身者可在此方摆放粉晶、鲜花以催旺感情。")

    return advice


# ─────────────────────────────────────────────────────────────
# 山星向星双星盘 (Xuan Kong Double-Star Chart)
# ─────────────────────────────────────────────────────────────

# 三元九运表: each 运 spans 20 years, identifies the 旺星 (prosperous star)
YUAN_YUN_TABLE: Dict[int, Dict[str, Any]] = {
    1: {"yuan": "上元", "years": (1864,1883), "wang_star": 1},
    2: {"yuan": "上元", "years": (1884,1903), "wang_star": 2},
    3: {"yuan": "上元", "years": (1904,1923), "wang_star": 3},
    4: {"yuan": "中元", "years": (1924,1943), "wang_star": 4},
    5: {"yuan": "中元", "years": (1944,1963), "wang_star": 5},
    6: {"yuan": "中元", "years": (1964,1983), "wang_star": 6},
    7: {"yuan": "下元", "years": (1984,2003), "wang_star": 7},
    8: {"yuan": "下元", "years": (2004,2023), "wang_star": 8},
    9: {"yuan": "下元", "years": (2024,2043), "wang_star": 9},
}

def get_current_yun(year: int = 2026) -> int:
    """Return the current 运 (1-9) for a given year."""
    for yun, data in YUAN_YUN_TABLE.items():
        if data["years"][0] <= year <= data["years"][1]:
            return yun
    return 9  # default to 9th yun (2024-2043)


# 二十四山方位 → 度数中心 (for flying star chart)
# Each of 24 directions covers 15°; we map to a Luoshu palace
ERSHI_SHAN_TO_PALACE: Dict[str, int] = {
    # 坎宫 (北, 337.5°-22.5°): 壬子癸
    "壬": 1, "子": 1, "癸": 1,
    # 艮宫 (东北, 22.5°-67.5°): 丑艮寅
    "丑": 8, "艮": 8, "寅": 8,
    # 震宫 (东, 67.5°-112.5°): 甲卯乙
    "甲": 3, "卯": 3, "乙": 3,
    # 巽宫 (东南, 112.5°-157.5°): 辰巽巳
    "辰": 4, "巽": 4, "巳": 4,
    # 离宫 (南, 157.5°-202.5°): 丙午丁
    "丙": 9, "午": 9, "丁": 9,
    # 坤宫 (西南, 202.5°-247.5°): 未坤申
    "未": 2, "坤": 2, "申": 2,
    # 兑宫 (西, 247.5°-292.5°): 庚酉辛
    "庚": 7, "酉": 7, "辛": 7,
    # 乾宫 (西北, 292.5°-337.5°): 戌乾亥
    "戌": 6, "乾": 6, "亥": 6,
}

# 向 → 对应坐 (opposite direction)
XIANG_TO_ZUO: Dict[str, str] = {
    "子": "午", "午": "子", "壬": "丙", "丙": "壬",
    "癸": "丁", "丁": "癸", "丑": "未", "未": "丑",
    "艮": "坤", "坤": "艮", "寅": "申", "申": "寅",
    "甲": "庚", "庚": "甲", "卯": "酉", "酉": "卯",
    "乙": "辛", "辛": "乙", "辰": "戌", "戌": "辰",
    "巽": "乾", "乾": "巽", "巳": "亥", "亥": "巳",
    "丙": "壬", "午": "子", "丁": "癸", "未": "丑",
}


def _fly_star(base_star: int, steps: int, forward: bool = True) -> int:
    """Fly a star by 'steps' positions. Forward = 顺飞, backward = 逆飞."""
    direction = 1 if forward else -1
    return (base_star - 1 + direction * steps) % 9 + 1


# 旺星入中宫 flying order (洛书顺序)
LUOSHU_FORWARD  = [5, 1, 8, 3, 4, 9, 2, 7, 6]  # center→positions 顺飞
LUOSHU_BACKWARD = [5, 9, 2, 7, 6, 1, 8, 3, 4]  # center→positions 逆飞


def _fly_to_nine_palaces(center_star: int, forward: bool) -> Dict[int, int]:
    """
    Given the center palace star, fly it to all 9 palaces.
    Returns {luoshu_pos: star_number}.
    顺飞 (forward): center goes 5→1→8→3→4→9→2→7→6 decreasing by 1 each step
    逆飞 (backward): center goes 5→9→2→7→6→1→8→3→4 increasing by 1 each step
    """
    POSITIONS = [5, 1, 8, 3, 4, 9, 2, 7, 6]  # Luoshu flying order
    result: Dict[int, int] = {}
    for i, pos in enumerate(POSITIONS):
        if forward:
            star = (center_star - 1 - i) % 9 + 1
        else:
            star = (center_star - 1 + i) % 9 + 1
        result[pos] = star
    return result


def calculate_xuankong_chart(
    xiang: str,
    year: int = 2026,
    yun: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculate the full Xuan Kong Flying Star double chart (玄空飞星双星盘).

    Args:
        xiang: 向首方位 (one of 24 mountains), e.g. '子', '午', '壬', '癸'
        year:  Year for annual star overlay
        yun:   运 (1-9). If None, derives from year.

    Returns dict with:
        zuo:         坐山
        xiang:       向首
        yun:         运数
        wang_star:   当运旺星
        mountain_chart: {pos: star} — 山星盘 (静/丁星)
        facing_chart:   {pos: star} — 向星盘 (动/财星)
        combined:       [{pos, palace_name, mountain_star, facing_star, annual_star, verdict}]
        pattern:        旺山旺向/上山下水/双星到向/双星到坐 etc.
        advice:         list of placement recommendations
    """
    if yun is None:
        yun = get_current_yun(year)

    wang_star = YUAN_YUN_TABLE[yun]["wang_star"]

    # 坐山 = opposite of 向首
    zuo = XIANG_TO_ZUO.get(xiang, "")

    # 向首宫位 and 坐山宫位 (Luoshu palace number)
    xiang_palace = ERSHI_SHAN_TO_PALACE.get(xiang, 9)
    zuo_palace   = ERSHI_SHAN_TO_PALACE.get(zuo, 1)

    # ── 运盘 (Period chart): 旺星入中 ────────────────────────
    # 运星入中顺飞 always in Xuan Kong
    yun_chart = _fly_to_nine_palaces(wang_star, forward=True)

    # ── 向星盘 (Facing star / 财星) ───────────────────────────
    # Facing star for 向首 palace = same as yun_chart[xiang_palace]
    xiang_center_star = yun_chart[xiang_palace]
    # Direction: odd stars (1,3,5,7,9) fly forward; even (2,4,6,8) fly backward
    xiang_forward = (xiang_center_star % 2 == 1)
    facing_chart  = _fly_to_nine_palaces(xiang_center_star, xiang_forward)

    # ── 山星盘 (Mountain star / 丁星) ────────────────────────
    zuo_center_star = yun_chart[zuo_palace]
    zuo_forward     = (zuo_center_star % 2 == 1)
    mountain_chart  = _fly_to_nine_palaces(zuo_center_star, zuo_forward)

    # ── Annual flying star overlay ────────────────────────────
    annual_center = get_annual_center_star(year)
    annual_chart  = _fly_to_nine_palaces(annual_center, forward=True)

    # ── 格局判断 ─────────────────────────────────────────────
    # 旺星: whether wang_star is at 向首 (facing) or 坐山 (sitting)
    mt_at_zuo    = mountain_chart.get(zuo_palace, 0) == wang_star
    fa_at_xiang  = facing_chart.get(xiang_palace, 0) == wang_star
    mt_at_xiang  = mountain_chart.get(xiang_palace, 0) == wang_star
    fa_at_zuo    = facing_chart.get(zuo_palace, 0) == wang_star

    if mt_at_zuo and fa_at_xiang:
        pattern      = "旺山旺向"
        pattern_desc = "山星旺气在坐山，向星旺气在向首，丁财两旺，最吉格局"
        pattern_level = "大吉"
    elif mt_at_xiang and fa_at_zuo:
        pattern      = "上山下水"
        pattern_desc = "山星旺气在向首，向星旺气在坐山，丁财两败，最凶格局"
        pattern_level = "大凶"
    elif mt_at_xiang and fa_at_xiang:
        pattern      = "双星到向"
        pattern_desc = "山星向星旺气皆在向首，利财不利丁，宜开门放水"
        pattern_level = "中吉（利财）"
    elif mt_at_zuo and fa_at_zuo:
        pattern      = "双星到坐"
        pattern_desc = "山星向星旺气皆在坐山，利丁不利财，宜背山面水"
        pattern_level = "中吉（利丁）"
    else:
        pattern      = "一般格局"
        pattern_desc = "旺星未到向首或坐山，需借助后天布局化解"
        pattern_level = "平"

    # ── Combined 9-palace display ─────────────────────────────
    DIRECTION_MAP = {
        5:"中", 1:"北", 9:"南", 3:"东", 7:"西",
        8:"东北", 4:"东南", 2:"西南", 6:"西北",
    }
    combined = []
    for pos in range(1, 10):
        ms = mountain_chart.get(pos, 0)
        fs = facing_chart.get(pos, 0)
        an = annual_chart.get(pos, 0)
        ms_nature = NINE_STARS.get(ms, {}).get("nature", "")
        fs_nature = NINE_STARS.get(fs, {}).get("nature", "")

        verdict = "平"
        if ms == wang_star or fs == wang_star:
            verdict = "旺"
        if ms in (2, 5) and fs in (2, 5):
            verdict = "煞"
        elif ms in (2, 5) or fs in (2, 5):
            verdict = "凶"
        if an in (8, 9, 1) and verdict not in ("煞", "凶"):
            verdict += "（流年吉）"

        combined.append({
            "position":       pos,
            "direction":      DIRECTION_MAP.get(pos, ""),
            "palace_name":    JIUGONG_POSITIONS.get(pos, ""),
            "mountain_star":  ms,
            "facing_star":    fs,
            "annual_star":    an,
            "ms_name":        NINE_STARS.get(ms, {}).get("name", ""),
            "fs_name":        NINE_STARS.get(fs, {}).get("name", ""),
            "verdict":        verdict,
        })

    # ── Placement advice ──────────────────────────────────────
    advice = []
    five_yellow_pos  = next((c["direction"] for c in combined if c["facing_star"]==5 or c["mountain_star"]==5), "")
    two_black_pos    = next((c["direction"] for c in combined if c["annual_star"]==2), "")
    eight_white_pos  = next((c["direction"] for c in combined if c["facing_star"]==8 or c["annual_star"]==8), "")

    if five_yellow_pos:
        advice.append(f"五黄在{five_yellow_pos}方，绝对不可动土开门，放六帝钱化煞")
    if two_black_pos:
        advice.append(f"流年二黑在{two_black_pos}方，放铜葫芦或六枚铜钱压制")
    if eight_white_pos:
        advice.append(f"八白旺星在{eight_white_pos}方，此处为财位，宜开门、放水或置财物")

    return {
        "zuo":             zuo,
        "xiang":           xiang,
        "yun":             yun,
        "wang_star":       wang_star,
        "pattern":         pattern,
        "pattern_desc":    pattern_desc,
        "pattern_level":   pattern_level,
        "mountain_chart":  mountain_chart,
        "facing_chart":    facing_chart,
        "annual_chart":    annual_chart,
        "combined":        combined,
        "advice":          advice,
    }
