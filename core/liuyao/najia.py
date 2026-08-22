"""
core/liuyao/najia.py
=====================
Complete Najia (纳甲) system for professional LiuYao divination.

Implements:
  • Branch assignment (纳甲地支) for each line of each hexagram
  • Six Relatives (六亲): 父母/兄弟/妻财/子孙/官鬼
  • Six Spirits (六神/六兽): 青龙/朱雀/勾陈/腾蛇/白虎/玄武
  • World Line (世爻) and Application Line (应爻) positions
  • Void / Emptiness (空亡) calculation
  • Seasonal strength (旺相休囚死) for each line
"""
from __future__ import annotations
from datetime import date
from typing import Dict, List, Tuple, Optional, Any

from core.constants import (
    TIANGAN, DIZHI, TIANGAN_INDEX, DIZHI_INDEX,
    TIANGAN_WUXING, DIZHI_WUXING, WUXING_SHENG, WUXING_KE,
)

# ─────────────────────────────────────────────────────────────
# 1. Najia Branch Assignments (纳甲地支)
#    Each trigram has 3 lines; inner vs outer palace gets different stems.
#    Format: { trigram_name: {"inner": [zhi0, zhi1, zhi2], "outer": [zhi3, zhi4, zhi5]} }
#    Index 0 = 初爻(bottom), Index 2 = 上爻(top for each trigram half)
# ─────────────────────────────────────────────────────────────

NAJIA_BRANCHES: Dict[str, Dict[str, List[str]]] = {
    "乾": {"inner": ["子", "寅", "辰"], "outer": ["午", "申", "戌"]},   # 甲/壬
    "坤": {"inner": ["未", "巳", "卯"], "outer": ["丑", "亥", "酉"]},   # 乙/癸
    "震": {"inner": ["子", "寅", "辰"], "outer": ["午", "申", "戌"]},   # 庚
    "巽": {"inner": ["丑", "亥", "酉"], "outer": ["未", "巳", "卯"]},   # 辛
    "坎": {"inner": ["寅", "子", "戌"], "outer": ["申", "午", "辰"]},   # 戊
    "离": {"inner": ["卯", "巳", "未"], "outer": ["酉", "亥", "丑"]},   # 己
    "艮": {"inner": ["辰", "寅", "子"], "outer": ["戌", "申", "午"]},   # 丙
    "兑": {"inner": ["巳", "未", "酉"], "outer": ["亥", "丑", "卯"]},   # 丁
}

# 纳甲天干（京房纳甲）：乾纳甲壬·坤纳乙癸（内外异干），余六卦内外同干。
#   内卦（下三爻）取 inner 干，外卦（上三爻）取 outer 干。
NAJIA_STEMS: Dict[str, Dict[str, str]] = {
    "乾": {"inner": "甲", "outer": "壬"},
    "坤": {"inner": "乙", "outer": "癸"},
    "震": {"inner": "庚", "outer": "庚"},
    "巽": {"inner": "辛", "outer": "辛"},
    "坎": {"inner": "戊", "outer": "戊"},
    "离": {"inner": "己", "outer": "己"},
    "艮": {"inner": "丙", "outer": "丙"},
    "兑": {"inner": "丁", "outer": "丁"},
}

# Palace (宫) element for six-relative calculation
PALACE_ELEMENT: Dict[str, str] = {
    "乾": "金", "兑": "金",
    "震": "木", "巽": "木",
    "坎": "水",
    "离": "火",
    "艮": "土", "坤": "土",
}

# ─────────────────────────────────────────────────────────────
# 2. Eight-Palace Hexagram Classification
#    Maps King-Wen number → (palace, palace_position 1-8)
#    Position determines 世爻: 1→世6, 2→世1, 3→世2, 4→世3, 5→世4, 6→世5, 7→世4, 8→世3
# ─────────────────────────────────────────────────────────────

# {hex_num: (palace_trigram, palace_position_1_to_8)}
HEXAGRAM_PALACE: Dict[int, Tuple[str, int]] = {
    # 乾宫
    1: ("乾",1), 44:("乾",2), 33:("乾",3), 12:("乾",4),
    20:("乾",5), 23:("乾",6), 35:("乾",7), 14:("乾",8),
    # 坤宫
    2: ("坤",1), 24:("坤",2), 19:("坤",3), 11:("坤",4),
    34:("坤",5), 43:("坤",6),  5:("坤",7),  8:("坤",8),
    # 震宫
    51:("震",1), 16:("震",2), 40:("震",3), 32:("震",4),
    46:("震",5), 48:("震",6), 28:("震",7), 17:("震",8),
    # 巽宫
    57:("巽",1),  9:("巽",2), 37:("巽",3), 42:("巽",4),
    25:("巽",5), 21:("巽",6), 27:("巽",7), 18:("巽",8),
    # 坎宫
    29:("坎",1), 60:("坎",2),  3:("坎",3), 63:("坎",4),
    49:("坎",5), 55:("坎",6), 36:("坎",7),  7:("坎",8),
    # 离宫
    30:("离",1), 56:("离",2), 50:("离",3), 64:("离",4),
     4:("离",5), 59:("离",6),  6:("离",7), 13:("离",8),
    # 艮宫
    52:("艮",1), 22:("艮",2), 26:("艮",3), 41:("艮",4),
    38:("艮",5), 10:("艮",6), 61:("艮",7), 53:("艮",8),
    # 兑宫
    58:("兑",1), 47:("兑",2), 45:("兑",3), 31:("兑",4),
    39:("兑",5), 15:("兑",6), 62:("兑",7), 54:("兑",8),
}

# Palace position → 世爻 position (1-indexed, 1=初爻, 6=上爻)
PALACE_POS_TO_WORLD: Dict[int, int] = {
    1: 6,  # 本宫卦：世在上爻
    2: 1,  # 一爻变：世在初爻
    3: 2,  # 二爻变：世在二爻
    4: 3,  # 三爻变：世在三爻
    5: 4,  # 四爻变：世在四爻
    6: 5,  # 五爻变：世在五爻
    7: 4,  # 游魂：世在四爻
    8: 3,  # 归魂：世在三爻
}

def _get_world_line(hex_num: int) -> Tuple[int, int]:
    """Return (world_line_pos, application_line_pos) for a hexagram. 1-indexed."""
    palace, pos = HEXAGRAM_PALACE.get(hex_num, ("乾", 1))
    world = PALACE_POS_TO_WORLD.get(pos, 6)
    application = ((world - 1 + 3) % 6) + 1  # always 3 positions ahead
    return world, application

# ─────────────────────────────────────────────────────────────
# 3. Six Spirits (六神) Assignment
#    Starting spirit for 初爻 depends on the day stem.
#    Order: 青龙→朱雀→勾陈→腾蛇→白虎→玄武 (repeating)
# ─────────────────────────────────────────────────────────────

LIU_SHEN = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]

LIU_SHEN_START: Dict[str, int] = {
    "甲": 0, "乙": 0,   # 青龙起
    "丙": 1, "丁": 1,   # 朱雀起
    "戊": 2,             # 勾陈起
    "己": 3,             # 腾蛇起
    "庚": 4, "辛": 4,   # 白虎起
    "壬": 5, "癸": 5,   # 玄武起
}

LIU_SHEN_MEANINGS: Dict[str, Dict[str, str]] = {
    "青龙": {"nature": "吉", "color": "#27ae60", "desc": "青龙主吉庆、贵人、婚姻喜事、酒食、贵气、文采"},
    "朱雀": {"nature": "凶", "color": "#e74c3c", "desc": "朱雀主口舌、文书、信息消息、争讼、是非"},
    "勾陈": {"nature": "凶", "color": "#f39c12", "desc": "勾陈主勾连、田土、迟滞、牵绊、契约纠纷、缓慢之事"},
    "腾蛇": {"nature": "凶", "color": "#9b59b6", "desc": "腾蛇主虚惊、怪异、梦幻、神秘事、心神不宁、缠绕"},
    "白虎": {"nature": "凶", "color": "#e74c3c", "desc": "白虎主凶险、疾病、血光、丧事、刀剑、武职"},
    "玄武": {"nature": "凶", "color": "#34495e", "desc": "玄武主盗贼、暗昧、私情、奸邪、欺诈、暗中之事"},
}

def assign_liu_shen(day_stem: str) -> List[str]:
    """Return list of 6 spirits from 初爻(index 0) to 上爻(index 5)."""
    start = LIU_SHEN_START.get(day_stem, 0)
    return [LIU_SHEN[(start + i) % 6] for i in range(6)]

# ─────────────────────────────────────────────────────────────
# 4. Six Relatives (六亲)
#    Compare each line's element with the palace element.
# ─────────────────────────────────────────────────────────────

LIU_QIN_NAMES = {
    "same":     "兄弟",   # same element as palace
    "generates":"子孙",   # palace generates this line's element
    "generated":"父母",   # this line's element generates palace
    "controls": "妻财",   # palace controls this line's element
    "controlled":"官鬼",  # this line's element controls palace
}

LIU_QIN_MEANINGS: Dict[str, Dict[str, str]] = {
    "父母": {
        "nature": "中", "color": "#8e44ad",
        "meaning": "主文书印信、父母长辈、车船房屋、官方文件、学业知识",
        "favorable_for": "求学考试（父母为文书）、签合同、官方审批、占父母安康",
        "unfavorable_for": "占子嗣（父母克子孙）、占求财（财克父母反伤）、夏占父母不利",
    },
    "兄弟": {
        "nature": "凶", "color": "#e67e22",
        "meaning": "主兄弟姐妹、朋友同事、竞争对手、阻财、夺财",
        "favorable_for": "求助同辈、合作共事（兄弟比和）、占兄弟安康",
        "unfavorable_for": "求财（兄弟克妻财，主破财）、占婚姻（兄弟夺财，财不归我）、占父母（兄弟生子孙、子孙克官，妨碍）",
    },
    "子孙": {
        "nature": "吉", "color": "#27ae60",
        "meaning": "主子女晚辈、福德、医药、僧道、六畜、忧愁解、化解凶煞",
        "favorable_for": "求医问药（子孙为药）、占子嗣、占六畜、官司中得救（子孙克官鬼）",
        "unfavorable_for": "占功名（子孙克官鬼，损功名）、占求官（同上）、女占夫病忌子孙动（克夫）",
    },
    "妻财": {
        "nature": "吉", "color": "#f1c40f",
        "meaning": "主财帛、男占妻妾、食物日用、奴仆、货物",
        "favorable_for": "求财、经商、嫁娶（男占以财为妻）、占奴仆",
        "unfavorable_for": "占父母病（妻财克父母）、考功名（财克印信文书）、占求学（财动伤父母印星）",
    },
    "官鬼": {
        "nature": "中", "color": "#c0392b",
        "meaning": "主官职功名、女占丈夫、疾病鬼祟、灾祸盗贼、雷火",
        "favorable_for": "求官求职（官为功名）、女占婚（官鬼为夫）、官司中（求官鬼旺主胜）、占贵人",
        "unfavorable_for": "占身体疾病（官鬼为病符）、占兄弟（官鬼克兄弟）、占行人（官鬼临身主灾）",
    },
}

def _wx_relation(palace_wx: str, line_wx: str) -> str:
    """Return relation type: same/generates/generated/controls/controlled."""
    if palace_wx == line_wx:
        return "same"
    if WUXING_SHENG.get(palace_wx) == line_wx:
        return "generates"  # palace generates line → 子孙
    if WUXING_SHENG.get(line_wx) == palace_wx:
        return "generated"  # line generates palace → 父母
    if WUXING_KE.get(palace_wx) == line_wx:
        return "controls"   # palace controls line → 妻财
    if WUXING_KE.get(line_wx) == palace_wx:
        return "controlled" # line controls palace → 官鬼
    return "same"

def get_liu_qin(palace_trigram: str, line_zhi: str) -> str:
    """Get the Six Relative name for a line."""
    palace_wx = PALACE_ELEMENT.get(palace_trigram, "金")
    line_wx = DIZHI_WUXING.get(line_zhi, "金")
    relation = _wx_relation(palace_wx, line_wx)
    return LIU_QIN_NAMES[relation]

# ─────────────────────────────────────────────────────────────
# 5. Void / Emptiness (空亡) Calculation
#    Based on the day's GanZhi: each 10-day cycle has 2 void branches.
# ─────────────────────────────────────────────────────────────

# The 60-cycle is divided into 6 groups of 10; each group has 2 void branches.
# Cycle index 0-9: 子亥 (甲子旬), 10-19: 戌酉 (甲戌旬), 20-29: 申未,
# 30-39: 午巳, 40-49: 辰卯, 50-59: 寅丑
KONG_WANG_TABLE: Dict[int, List[str]] = {
    0: ["戌", "亥"],   # 甲子旬空戌亥
    1: ["申", "酉"],   # 甲戌旬空申酉
    2: ["午", "未"],   # 甲申旬空午未
    3: ["辰", "巳"],   # 甲午旬空辰巳
    4: ["寅", "卯"],   # 甲辰旬空寅卯
    5: ["子", "丑"],   # 甲寅旬空子丑
}

def get_kong_wang(day_ganzhi_index: int) -> List[str]:
    """
    Return the 2 void DiZhi for a given day GanZhi cycle index (0-59).
    The 旬空 is based on which 10-day group the day falls in.
    """
    group = (day_ganzhi_index // 10) % 6
    return KONG_WANG_TABLE[group]

# ─────────────────────────────────────────────────────────────
# 6. Seasonal Strength (旺相休囚死)
#    Already in constants; expose convenience function here.
# ─────────────────────────────────────────────────────────────

from core.constants import (
    get_wuxing_strength as _get_wx_strength_qishi,
    get_wuxing_strength_strict as _get_wx_strength,
)

STRENGTH_LABELS = {
    "旺": {"label": "旺", "color": "#e74c3c", "desc": "当令最旺，力量最强"},
    "相": {"label": "相", "color": "#e67e22", "desc": "相气有力，力量较强"},
    "休": {"label": "休", "color": "#95a5a6", "desc": "退气休歇，力量一般"},
    "囚": {"label": "囚", "color": "#7f8c8d", "desc": "受制被囚，力量较弱"},
    "死": {"label": "死", "color": "#bdc3c7", "desc": "死绝无气，力量最弱"},
}

def get_line_strength(line_zhi: str, month_zhi: str) -> Dict[str, str]:
    """
    Return strength info for a line in the current month.
    
    使用《增删卜易》《卜筮正宗》六爻传统四时旺相休囚死表（严格派）：
      春（寅卯辰）：木旺、火相、水休、金囚、土死
      夏（巳午未）：火旺、土相、木休、水囚、金死
      秋（申酉戌）：金旺、水相、土休、火囚、木死
      冬（亥子丑）：水旺、木相、金休、土囚、火死
    
    注意：八字"气势派"在辰戌丑未四季月有差异，但六爻论旺衰
    严格按节气月令地支当令五行论，不考虑藏干。
    """
    wx = DIZHI_WUXING.get(line_zhi, "土")
    s = _get_wx_strength(wx, month_zhi)
    return STRENGTH_LABELS.get(s, {"label": s, "color": "#95a5a6", "desc": ""})

# ─────────────────────────────────────────────────────────────
# 7. Master annotate function
#    Takes a divination result + query date and adds Najia data.
# ─────────────────────────────────────────────────────────────

def annotate_with_najia(
    result: Dict[str, Any],
    hex_num: int,
    lower_trigram: str,
    upper_trigram: str,
    day_stem: str,
    day_ganzhi_index: int,
    month_zhi: str,
) -> Dict[str, Any]:
    """
    Enrich each yao in result['yaos'] with:
      - branch (纳甲地支)
      - element (五行)
      - liu_qin (六亲)
      - liu_shen (六神)
      - kong_wang (是否空亡)
      - strength (旺相休囚死)
      - world/application marker
    """
    palace_trig, _ = HEXAGRAM_PALACE.get(hex_num, (lower_trigram, 1))
    world_pos, app_pos = _get_world_line(hex_num)
    kong_wang_branches = get_kong_wang(day_ganzhi_index)
    liu_shen_list = assign_liu_shen(day_stem)

    yaos = result.get("yaos", [])
    enriched_yaos = []
    
    # 计算变卦的爻支（如果有变卦）
    changed_branches = [""] * 6
    changed_stems = [""] * 6
    changed_hex = result.get("changed")
    if changed_hex:
        changed_lower = changed_hex.get("lower", {}).get("name", lower_trigram)
        changed_upper = changed_hex.get("upper", {}).get("name", upper_trigram)
        for i in range(6):
            if i < 3:
                ch_branches = NAJIA_BRANCHES.get(changed_lower, {}).get("inner", ["",""])
                changed_branches[i] = ch_branches[i] if i < len(ch_branches) else ""
                changed_stems[i] = NAJIA_STEMS.get(changed_lower, {}).get("inner", "")
            else:
                ch_branches = NAJIA_BRANCHES.get(changed_upper, {}).get("outer", ["",""])
                changed_branches[i] = ch_branches[i - 3] if (i - 3) < len(ch_branches) else ""
                changed_stems[i] = NAJIA_STEMS.get(changed_upper, {}).get("outer", "")

    for i, yao in enumerate(yaos):
        pos = i + 1  # 1-indexed
        # Which trigram half?
        if pos <= 3:
            trigram = lower_trigram
            branch = NAJIA_BRANCHES.get(trigram, {}).get("inner", ["子","寅","辰"])[i]
            stem = NAJIA_STEMS.get(trigram, {}).get("inner", "")
        else:
            trigram = upper_trigram
            branch = NAJIA_BRANCHES.get(trigram, {}).get("outer", ["午","申","戌"])[i - 3]
            stem = NAJIA_STEMS.get(trigram, {}).get("outer", "")

        wx = DIZHI_WUXING.get(branch, "土")
        liu_qin = get_liu_qin(palace_trig, branch)
        liu_shen = liu_shen_list[i]
        is_kong_wang = branch in kong_wang_branches
        strength = get_line_strength(branch, month_zhi)
        is_world = (pos == world_pos)
        is_application = (pos == app_pos)
        
        # 化爻地支（仅在动爻上有意义；静爻 changed_branch 即为本爻）
        is_changing = yao.get("is_changing", False)
        changed_branch = changed_branches[i] if is_changing else ""
        changed_stem = changed_stems[i] if is_changing else ""
        # 计算变爻的六亲（动爻变出后的六亲）
        changed_liu_qin = ""
        if is_changing and changed_branch:
            changed_liu_qin = get_liu_qin(palace_trig, changed_branch)

        enriched_yaos.append({
            **yao,
            "stem": stem,                        # 纳甲天干
            "branch": branch,
            "ganzhi": f"{stem}{branch}",         # 纳甲干支（如「甲子」）
            "element": wx,
            "liu_qin": liu_qin,
            "liu_shen": liu_shen,
            "liu_shen_meaning": LIU_SHEN_MEANINGS.get(liu_shen, {}),
            "liu_qin_meaning": LIU_QIN_MEANINGS.get(liu_qin, {}),
            "kong_wang": is_kong_wang,
            "strength": strength,
            "is_world": is_world,
            "is_application": is_application,
            "changed_stem": changed_stem,
            "changed_branch": changed_branch,
            "changed_ganzhi": (f"{changed_stem}{changed_branch}" if changed_branch else ""),
            "changed_liu_qin": changed_liu_qin,
        })

    result["yaos"] = enriched_yaos
    result["world_line"] = world_pos
    result["application_line"] = app_pos
    result["kong_wang_branches"] = kong_wang_branches
    result["palace_trigram"] = palace_trig
    result["palace_element"] = PALACE_ELEMENT.get(palace_trig, "金")
    result["najia_summary"] = _build_najia_summary(enriched_yaos, world_pos, app_pos, kong_wang_branches)

    # ── 六合/六冲卦型精确判断 ───────────────────────────────────────────────
    # 六合: 各爻地支两两相合 (子丑/寅亥/卯戌/辰酉/巳申/午未)
    # 六冲: 各爻地支两两相冲 (子午/丑未/寅申/卯酉/辰戌/巳亥)
    _LIUHE_PAIRS  = {("子","丑"),("寅","亥"),("卯","戌"),("辰","酉"),("巳","申"),("午","未")}
    _LIUHE_PAIRS |= {(b,a) for a,b in _LIUHE_PAIRS}

    branches = [y.get("branch","") for y in enriched_yaos]
    # Six-harmony: check if all 6 branches form 3 合 pairs
    if len(branches) == 6:
        b_set = list(branches)
        he_pairs = 0
        chong_pairs = 0
        for i in range(3):
            pair = (b_set[i], b_set[i+3])  # 初↔四, 二↔五, 三↔六 positions
            rev  = (pair[1], pair[0])
            if pair in _LIUHE_PAIRS or rev in _LIUHE_PAIRS:
                he_pairs += 1
            # 六冲 check
            from core.constants import LIUCHONG
            if LIUCHONG.get(b_set[i]) == b_set[i+3]:
                chong_pairs += 1

        hex_type_enriched = result.get("hex_type", "")
        if he_pairs == 3:
            hex_type_enriched = "六合卦"
        elif chong_pairs == 3:
            hex_type_enriched = "六冲卦"
        if hex_type_enriched:
            result["hex_type"] = hex_type_enriched

    # ── 三合局 / 三会方 / 半三合 检测（古书《增删卜易·三合局》）──────────
    sanhe_result = detect_sanhe_sanhui(enriched_yaos)
    result["sanhe_sanhui"] = sanhe_result

    return result


def _build_najia_summary(yaos: List[Dict], world: int, application: int, kong: List[str]) -> Dict[str, Any]:
    """Build a professional summary of the Najia analysis."""
    world_yao = next((y for y in yaos if y.get("is_world")), None)
    app_yao = next((y for y in yaos if y.get("is_application")), None)

    changing = [y for y in yaos if y.get("is_changing")]
    active_liu_qin = {}
    for y in changing:
        qin = y.get("liu_qin", "")
        if qin:
            active_liu_qin.setdefault(qin, []).append(y.get("branch", ""))

    world_desc = ""
    if world_yao:
        wq = world_yao.get("liu_qin", "")
        ws = world_yao.get("strength", {}).get("label", "")
        wk = "（空亡！）" if world_yao.get("kong_wang") else ""
        world_desc = f"世爻为{wq}爻（{world_yao.get('branch','')}），{ws}{wk}"

    app_desc = ""
    if app_yao:
        aq = app_yao.get("liu_qin", "")
        ak = "（空亡！）" if app_yao.get("kong_wang") else ""
        app_desc = f"应爻为{aq}爻（{app_yao.get('branch','')}）{ak}"

    kong_desc = f"旬空地支：{'、'.join(kong)}" if kong else ""

    return {
        "world_desc": world_desc,
        "app_desc": app_desc,
        "kong_desc": kong_desc,
        "active_liu_qin": active_liu_qin,
        "changing_count": len(changing),
    }


# ─────────────────────────────────────────────────────────────
# 化气分析 (Complete Transformation Analysis)
# ─────────────────────────────────────────────────────────────

# 入墓地支表 (which branches are 墓库 for each element)
_MU_KU: Dict[str, str] = {
    "木": "未", "火": "戌", "金": "丑", "水": "辰", "土": "戌",
}

# 十二长生 顺序 (阳干 顺行)
_CHANGSHENG_ORDER = ["长生","沐浴","冠带","临官","帝旺","衰","病","死","墓","绝","胎","养"]

def _get_wuxing(zhi: str) -> str:
    """Get the primary wuxing for a DiZhi."""
    ZHI_WX = {
        "子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
        "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水",
    }
    return ZHI_WX.get(zhi, "")


def analyze_hua_qi(yao: Dict[str, Any], changed_yao: Dict[str, Any],
                   kong_wang: List[str], month_zhi: str) -> Dict[str, str]:
    """
    Analyze the transformation quality of a moving yao.
    
    Returns dict with keys:
        hua_type: '化进神'|'化退神'|'化绝'|'化墓'|'化空'|'化破'|'化回头生'|'化回头克'|''
        hua_desc: Chinese description
        severity: 'auspicious'|'inauspicious'|'neutral'
    """
    orig_zhi    = yao.get("branch", "")
    changed_zhi = changed_yao.get("branch", "")
    orig_wx     = _get_wuxing(orig_zhi)
    changed_wx  = _get_wuxing(changed_zhi)

    if not orig_zhi or not changed_zhi:
        return {"hua_type": "", "hua_desc": "", "severity": "neutral"}

    # 化空 — 变爻落入旬空
    if changed_zhi in kong_wang:
        return {
            "hua_type": "化空",
            "hua_desc": f"动爻化空（{changed_zhi}入旬空），有始无终，事难成",
            "severity": "inauspicious",
        }

    # 化破 — 变爻与月建相冲
    from core.constants import LIUCHONG
    if changed_zhi == LIUCHONG.get(month_zhi, ""):
        return {
            "hua_type": "化破",
            "hua_desc": f"动爻化破（{changed_zhi}冲月建{month_zhi}），功败垂成",
            "severity": "inauspicious",
        }

    # 化墓 — 变爻五行入墓
    mu_zhi = _MU_KU.get(orig_wx, "")
    if changed_zhi == mu_zhi:
        return {
            "hua_type": "化墓",
            "hua_desc": f"动爻化墓（{orig_wx}墓于{mu_zhi}），用神入墓难发，须冲墓方出",
            "severity": "inauspicious",
        }

    # 化绝 — 变爻五行处于绝地
    # 绝: 每五行在特定地支绝灭
    _JUE_ZHI = {"木":"申","火":"亥","土":"亥","金":"寅","水":"巳"}
    if changed_zhi == _JUE_ZHI.get(orig_wx, ""):
        return {
            "hua_type": "化绝",
            "hua_desc": f"动爻化绝（{orig_wx}绝于{changed_zhi}），力量瓦解，所谋必败",
            "severity": "inauspicious",
        }

    # 化回头克 — 变爻五行克动爻五行
    from core.constants import WUXING_KE
    if WUXING_KE.get(changed_wx, "") == orig_wx:
        return {
            "hua_type": "化回头克",
            "hua_desc": f"回头克（{changed_wx}克{orig_wx}），大凶，事必反",
            "severity": "inauspicious",
        }

    # 化回头生 — 变爻五行生动爻五行
    from core.constants import WUXING_SHENG
    if WUXING_SHENG.get(changed_wx, "") == orig_wx:
        return {
            "hua_type": "化回头生",
            "hua_desc": f"回头生（{changed_wx}生{orig_wx}），大吉，事必成",
            "severity": "auspicious",
        }

    # 化进神 / 化退神
    # 古书《增删卜易》《卜筮正宗》：进退神为"同五行地支递进/递退"
    #   进神（四正）: 寅→卯木, 巳→午火, 申→酉金, 亥→子水
    #   退神（四正）: 卯→寅木, 午→巳火, 酉→申金, 子→亥水
    # （注：四库土"辰丑戌未"按部分流派轮转进退；严格派认为土不进不退）
    _JIN_SHEN_MAP = {
        "寅":"卯", "巳":"午", "申":"酉", "亥":"子",   # 四正进神
        "辰":"丑", "丑":"戌", "戌":"未", "未":"辰",   # 四库土进神（部分流派）
    }
    _TUI_SHEN_MAP = {v: k for k, v in _JIN_SHEN_MAP.items()}
    if _JIN_SHEN_MAP.get(orig_zhi) == changed_zhi:
        return {
            "hua_type": "化进神",
            "hua_desc": f"化进神（{orig_zhi}→{changed_zhi}），气势渐增，所问之事向前发展，利于动进",
            "severity": "auspicious",
        }
    if _TUI_SHEN_MAP.get(orig_zhi) == changed_zhi:
        return {
            "hua_type": "化退神",
            "hua_desc": f"化退神（{orig_zhi}→{changed_zhi}），气势渐衰，所问之事退缩不前，不利进取",
            "severity": "inauspicious",
        }

    return {"hua_type": "", "hua_desc": "变爻五行中性变化，结合整体卦象论断", "severity": "neutral"}


# ─────────────────────────────────────────────────────────────
# 9. 三合局 / 三会局 / 半三合 检测
# ─────────────────────────────────────────────────────────────
#
# 古书《增删卜易·三合局》《卜筮正宗·三合三会》：
#
# 三合局（地支三合，五行成局）：
#   申子辰水局
#   亥卯未木局
#   寅午戌火局
#   巳酉丑金局
#
# 三会方（地支三会，方向成方）：
#   亥子丑北方水会
#   寅卯辰东方木会
#   巳午未南方火会
#   申酉戌西方金会
#
# 半三合（缺一字，但有"长生 + 帝旺"或"帝旺 + 墓库"）：
#   申子=半三合水（长生+帝旺）
#   子辰=半三合水（帝旺+墓库）
#   申辰=拱合水（弱）
#   类推其他局
#
# 应用：
#   1) 三合/三会同时成立，五行力量大增，原神得力
#   2) 半三合次之
#   3) 三合/三会需要"局中之爻动"才生效（古书《增删卜易》："静则不应"）
# ─────────────────────────────────────────────────────────────

SANHE_JU = {
    frozenset(["申","子","辰"]): "水局",
    frozenset(["亥","卯","未"]): "木局",
    frozenset(["寅","午","戌"]): "火局",
    frozenset(["巳","酉","丑"]): "金局",
}

SANHUI_FANG = {
    frozenset(["亥","子","丑"]): "北方水会",
    frozenset(["寅","卯","辰"]): "东方木会",
    frozenset(["巳","午","未"]): "南方火会",
    frozenset(["申","酉","戌"]): "西方金会",
}

# 半三合（长生 + 帝旺 或 帝旺 + 墓库）
BAN_SANHE = {
    # 水局：申(长生)、子(帝旺)、辰(墓库)
    frozenset(["申","子"]): "半三合水（长生+帝旺，力较强）",
    frozenset(["子","辰"]): "半三合水（帝旺+墓库，力较强）",
    # 木局：亥(长生)、卯(帝旺)、未(墓库)
    frozenset(["亥","卯"]): "半三合木（长生+帝旺）",
    frozenset(["卯","未"]): "半三合木（帝旺+墓库）",
    # 火局：寅(长生)、午(帝旺)、戌(墓库)
    frozenset(["寅","午"]): "半三合火（长生+帝旺）",
    frozenset(["午","戌"]): "半三合火（帝旺+墓库）",
    # 金局：巳(长生)、酉(帝旺)、丑(墓库)
    frozenset(["巳","酉"]): "半三合金（长生+帝旺）",
    frozenset(["酉","丑"]): "半三合金（帝旺+墓库）",
}


def detect_sanhe_sanhui(yaos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    检测卦中是否形成三合局或三会局。
    
    Args:
        yaos: enrich 过的 6 爻列表（含 branch 字段）
    
    Returns:
        {
            'sanhe':       [{'positions': [1,3,5], 'branches':['申','子','辰'], 'name':'水局'}, ...],
            'sanhui':      [...同上],
            'ban_sanhe':   [...半三合],
            'summary':     "本卦构成 X 局"
        }
    """
    branches = [(i+1, y.get("branch", "")) for i, y in enumerate(yaos)]
    
    # 全三合
    sanhe_found = []
    for combo in [(0,1,2),(0,1,3),(0,1,4),(0,1,5),(0,2,3),(0,2,4),(0,2,5),
                  (0,3,4),(0,3,5),(0,4,5),(1,2,3),(1,2,4),(1,2,5),(1,3,4),
                  (1,3,5),(1,4,5),(2,3,4),(2,3,5),(2,4,5),(3,4,5)]:
        positions = [branches[i][0] for i in combo]
        zhis = [branches[i][1] for i in combo]
        if "" in zhis: continue
        key = frozenset(zhis)
        if len(key) != 3:  # 重复地支不算
            continue
        if key in SANHE_JU:
            sanhe_found.append({
                "positions": positions,
                "branches": zhis,
                "name": SANHE_JU[key],
            })
        elif key in SANHUI_FANG:
            sanhe_found.append({
                "positions": positions,
                "branches": zhis,
                "name": SANHUI_FANG[key],
                "is_sanhui": True,
            })
    
    # 半三合（仅在没有全三合时才看）
    ban_found = []
    if not sanhe_found:
        for i, (p1, z1) in enumerate(branches):
            for p2, z2 in branches[i+1:]:
                if not z1 or not z2 or z1 == z2:
                    continue
                key = frozenset([z1, z2])
                if key in BAN_SANHE:
                    ban_found.append({
                        "positions": [p1, p2],
                        "branches": [z1, z2],
                        "name": BAN_SANHE[key],
                    })
    
    # 分类
    full_sanhe = [x for x in sanhe_found if not x.get("is_sanhui")]
    sanhui     = [x for x in sanhe_found if x.get("is_sanhui")]
    
    summary_parts = []
    if full_sanhe:
        summary_parts.append("三合局：" + "、".join(x["name"] for x in full_sanhe))
    if sanhui:
        summary_parts.append("三会方：" + "、".join(x["name"] for x in sanhui))
    if ban_found:
        summary_parts.append(f"半三合 {len(ban_found)} 组")
    if not summary_parts:
        summary_parts.append("无三合三会")
    
    return {
        "sanhe":     full_sanhe,
        "sanhui":    sanhui,
        "ban_sanhe": ban_found,
        "summary":   "；".join(summary_parts),
    }
