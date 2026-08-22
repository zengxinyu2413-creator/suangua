"""
core/fengshui/calculator.py
============================
FengShui core calculations:
  • Ming Gua (命卦) — personal trigram number
  • House Gua (宅卦) — house trigram
  • Eight Mansion (八宅) sector analysis
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple


# ─────────────────────────────────────────────────────────────
# 1. Ming Gua (命卦)
# ─────────────────────────────────────────────────────────────
# 后天八卦：1坎、2坤、3震、4巽、6乾、7兑、8艮、9离（5中宫无卦）

# 东四命/东四宅：坎(1)、离(9)、震(3)、巽(4) — 水火木木，相生
EAST_FOUR_LIFE = {1, 3, 4, 9}
# 西四命/西四宅：乾(6)、坤(2)、艮(8)、兑(7) — 金土土金，相生
# 注：5 在 calculate_ming_gua 内已转换（男→2 女→8），此处仅供保险
WEST_FOUR_LIFE = {2, 6, 7, 8}

def calculate_ming_gua(birth_year: int, gender: str) -> int:
    """
    Calculate the Ming Gua (命卦) number for a person.
    Uses the traditional formula:
      Male:   (10 - (year digit sum % 9)) % 9, or 9 if result = 0
      Female: (year digit sum + 5) % 9, or 9 if result = 0
      After 2000: male subtract from 9 instead of 10.
    """
    # Sum year digits until single digit
    y = birth_year % 100  # last 2 digits
    while y >= 10:
        y = sum(int(d) for d in str(y))
    if y == 0:
        y = 9

    male = gender in ("male", "男")

    if birth_year < 2000:
        gua = (10 - y) % 9 if male else (y + 5) % 9
    else:
        gua = (9 - y) % 9 if male else (y + 6) % 9

    if gua == 0:
        gua = 9
    if gua == 5:
        gua = 2 if male else 8   # 5 is converted to 2(male) or 8(female)

    return gua


def get_ming_gua_group(gua: int) -> str:
    return "东四命" if gua in EAST_FOUR_LIFE else "西四命"


# ─────────────────────────────────────────────────────────────
# 2. House Gua (宅卦)
# ─────────────────────────────────────────────────────────────
# 八宅风水主流规则：宅卦 = 坐山所属卦（《八宅明镜》《阳宅三要》）
#   坐北朝南 → 坎宅（北为坐）
#   坐南朝北 → 离宅
#   坐东朝西 → 震宅
#   坐西朝东 → 兑宅
#   坐东南朝西北 → 巽宅
#   坐西南朝东北 → 坤宅
#   坐西北朝东南 → 乾宅
#   坐东北朝西南 → 艮宅

# 坐山方位 → 宅卦
SITTING_GUA: Dict[str, int] = {
    "南":  9,  # 坐南 = 离宅
    "北":  1,  # 坐北 = 坎宅
    "东":  3,  # 坐东 = 震宅
    "西":  7,  # 坐西 = 兑宅
    "东南": 4, # 坐东南 = 巽宅
    "西北": 6, # 坐西北 = 乾宅
    "东北": 8, # 坐东北 = 艮宅
    "西南": 2, # 坐西南 = 坤宅
}

# 朝向反转表（朝向 → 坐山）
FACING_TO_SITTING: Dict[str, str] = {
    "南": "北", "北": "南", "东": "西", "西": "东",
    "东南": "西北", "西北": "东南", "东北": "西南", "西南": "东北",
}

# 兼容老代码：DIRECTION_GUA 仍可用，但语义改为"坐山 → 宅卦"
DIRECTION_GUA = SITTING_GUA


def get_house_gua(direction: str, direction_is_facing: bool = True) -> int:
    """
    根据方位获取宅卦。
    
    Args:
        direction: 方位（南、北、东、西、东南、西北、东北、西南）
        direction_is_facing: 
            True（默认）= 参数是"朝向"，内部反转为坐山查表
            False = 参数已经是"坐山"，直接查表
    
    Returns:
        卦号（1坎 2坤 3震 4巽 6乾 7兑 8艮 9离）
    """
    if direction_is_facing:
        sitting = FACING_TO_SITTING.get(direction, direction)
    else:
        sitting = direction
    return SITTING_GUA.get(sitting, 9)


EAST_FOUR_HOUSE = {1, 3, 4, 9}  # 坎离震巽
WEST_FOUR_HOUSE = {2, 6, 7, 8}  # 乾坤艮兑


def get_house_group(gua: int) -> str:
    return "东四宅" if gua in EAST_FOUR_HOUSE else "西四宅"


def check_compatibility(ming_gua: int, house_gua: int) -> str:
    """
    Check compatibility between person's Ming Gua and house Gua.
    Now includes 《八宅明镜》详细判断 and 《阳宅三要》建议.
    """
    ming_group  = get_ming_gua_group(ming_gua)
    house_group = get_house_group(house_gua)

    _MING_NAME = {1:"坎（水）",2:"坤（土）",3:"震（木）",4:"巽（木）",
                  6:"乾（金）",7:"兑（金）",8:"艮（土）",9:"离（火）"}
    _HOUSE_NAME = {1:"坎宅（北向）",2:"坤宅（西南）",3:"震宅（东向）",4:"巽宅（东南）",
                   6:"乾宅（西北）",7:"兑宅（西向）",8:"艮宅（东北）",9:"离宅（南向）"}

    mn = _MING_NAME.get(ming_gua, str(ming_gua))
    hn = _HOUSE_NAME.get(house_gua, str(house_gua))

    if ming_group[0] == house_group[0]:
        level = "相配"
        detail = (f"命卦{mn}（{ming_group}）与{hn}（{house_group}）同属{ming_group[:1]}四宅，"
                  f"《八宅明镜》云：东四命住东四宅，西四命住西四宅，同类相得则吉。")
    else:
        level = "不相配"
        detail = (f"命卦{mn}（{ming_group}）与{hn}（{house_group}）不同类，"
                  f"《八宅明镜》云：东命住西宅，或西命住东宅，命宅相克则凶，"
                  f"建议重点布局生气位（{get_sector_direction(ming_gua, '生气')}）弥补。")

    return f"{level}｜{detail}"


def get_sector_direction(ming_gua: int, sector: str) -> str:
    """Return the compass direction of a specific sector for a given ming_gua."""
    sectors = EIGHT_MANSION.get(ming_gua, {})
    for direction, name in sectors.items():
        if name == sector:
            return direction
    return "未知"


def get_sector_analysis(house_gua: int) -> List[Dict[str, str]]:
    """
    Return sector analysis for a house based on its Gua.
    Now enriched with 《八宅明镜》《阳宅三要》classical guidance.
    """
    sectors = EIGHT_MANSION.get(house_gua, EIGHT_MANSION[1])

    # Load classical enrichment
    _CLASSICAL_DETAIL = {}
    try:
        from knowledge.fengshui_classical import BAYUAN_JIUXING
        _CLASSICAL_DETAIL = BAYUAN_JIUXING
    except Exception as _e1:
        from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e1)

    result = []
    for direction, sector_name in sectors.items():
        sq = SECTOR_QUALITY.get(sector_name, {})
        classical = _CLASSICAL_DETAIL.get(sector_name, {})

        # Use classical main symbol if available
        main_symbol = classical.get("主象", sq.get("desc", ""))
        classical_use = classical.get("适宜", "")

        # Build usage advice
        base_advice = sq.get("advice", "")
        if classical_use:
            if isinstance(classical_use, list):
                advice_ext = "宜：" + "、".join(classical_use[:3])
            else:
                advice_ext = str(classical_use)
            full_advice = f"{base_advice}；{advice_ext}"
        else:
            full_advice = base_advice

        result.append({
            "direction": direction,
            "star":      sector_name,
            "quality":   sq.get("quality", "中"),
            "meaning":   main_symbol,
            "advice":    full_advice,
            "classical_name": classical.get("星名", ""),
        })
    return result



# ─────────────────────────────────────────────────────────────
# 3. Eight Mansion (八宅) sectors
# ─────────────────────────────────────────────────────────────

# 八宅游年法 — 用翻爻法系统生成，与《八宅明镜》《阳宅三要》完全一致
# 翻爻口诀：上一生气下一祸 / 上二五鬼下二天 / 上下六煞中绝命 / 不动伏位全变延
# 
# 验证规则：
#   1. 每宫八游年星完整且不重复（伏/生/天/延/绝/五/六/祸 各 1 次）
#   2. 本宫方位为伏位
#   3. 东四宅（坎离震巽）的四吉方在东四方位（北南东东南）；西四同理
#   4. 与《八宅明镜》《阳宅三要》《八宅风水百科》多源权威表一致
EIGHT_MANSION: Dict[int, Dict[str, str]] = {
    1: {  # 坎宅 (北) 坐北朝南
        "北":"伏位", "南":"延年", "东":"天医", "西":"祸害",
        "东南":"生气", "西北":"六煞", "东北":"五鬼", "西南":"绝命",
    },
    2: {  # 坤宅 (西南) 坐西南朝东北
        "北":"绝命", "南":"六煞", "东":"祸害", "西":"天医",
        "东南":"五鬼", "西北":"延年", "东北":"生气", "西南":"伏位",
    },
    3: {  # 震宅 (东) 坐东朝西
        "北":"天医", "南":"生气", "东":"伏位", "西":"绝命",
        "东南":"延年", "西北":"五鬼", "东北":"六煞", "西南":"祸害",
    },
    4: {  # 巽宅 (东南) 坐东南朝西北
        "北":"生气", "南":"天医", "东":"延年", "西":"六煞",
        "东南":"伏位", "西北":"祸害", "东北":"绝命", "西南":"五鬼",
    },
    6: {  # 乾宅 (西北) 坐西北朝东南
        "北":"六煞", "南":"绝命", "东":"五鬼", "西":"生气",
        "东南":"祸害", "西北":"伏位", "东北":"天医", "西南":"延年",
    },
    7: {  # 兑宅 (西) 坐西朝东
        "北":"祸害", "南":"五鬼", "东":"绝命", "西":"伏位",
        "东南":"六煞", "西北":"生气", "东北":"延年", "西南":"天医",
    },
    8: {  # 艮宅 (东北) 坐东北朝西南
        "北":"五鬼", "南":"祸害", "东":"六煞", "西":"延年",
        "东南":"绝命", "西北":"天医", "东北":"伏位", "西南":"生气",
    },
    9: {  # 离宅 (南) 坐南朝北
        "北":"延年", "南":"伏位", "东":"生气", "西":"五鬼",
        "东南":"天医", "西北":"绝命", "东北":"祸害", "西南":"六煞",
    },
}

SECTOR_QUALITY: Dict[str, Dict[str, str]] = {
    "生气": {"quality": "吉", "desc": "最吉，利发展、求财、婚姻", "advice": "宜置卧室、书房"},
    "天医": {"quality": "吉", "desc": "利健康、求医、贵人", "advice": "宜置卧室、厨房"},
    "延年": {"quality": "吉", "desc": "利长寿、家庭和睦", "advice": "宜置主卧、客厅"},
    "伏位": {"quality": "中", "desc": "稳定守成，无大吉凶", "advice": "宜置储藏室、卫生间"},
    "祸害": {"quality": "凶", "desc": "有口舌、疾病之忧", "advice": "宜置厕所、储藏室"},
    "六煞": {"quality": "凶", "desc": "六煞损丁，主破财", "advice": "宜置厕所、车库"},
    "五鬼": {"quality": "凶", "desc": "五鬼作祟，主官非灾祸", "advice": "宜置厕所"},
    "绝命": {"quality": "大凶", "desc": "最凶，主重病、绝嗣", "advice": "宜置厕所、车库，切忌卧室"},
}
