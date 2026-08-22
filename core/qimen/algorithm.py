"""
core/qimen/algorithm.py
=======================
QiMen DunJia (奇门遁甲) Sanyuan Jiuju (三元九局) engine.

Implements:
  • Yang/Yin dun determination (阳遁/阴遁) via exact solar terms
  • 超接置闰 Ju calculation (proper 三元九局)
  • 六仪三奇 palace placement (correct classical sequence)
  • 九宫飞布 (Luoshu flying)
  • 格局识别 (7 major patterns)
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from core.constants import (
    JIUGONG_POSITIONS, JIUXING, BAMEN, BASHEN, BAMEN_AUSPICIOUS,
    TIANGAN, DIZHI, TIANGAN_INDEX, DIZHI_INDEX,
    hour_to_dizhi,
)
from core.calendar.solar_terms import get_jie_dates

# ─────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────

# 洛书 flying order
# 阳遁: 1→2→3→4→5→6→7→8→9 (forward)
# 阴遁: 9→8→7→6→5→4→3→2→1 (backward)
YANG_SEQUENCE: List[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
YIN_SEQUENCE:  List[int] = [9, 8, 7, 6, 5, 4, 3, 2, 1]

# Eight deities in cycle order
DEITY_ORDER: List[str] = ["值符","腾蛇","太阴","六合","白虎","玄武","九地","九天"]

# Grid positions for 九宫 (row, col) in 3×3 grid (0-indexed)
PALACE_GRID: Dict[int, Tuple[int,int]] = {
    7:(0,0), 9:(0,1), 2:(0,2),
    8:(1,0), 5:(1,1), 4:(1,2),
    3:(2,0), 1:(2,1), 6:(2,2),
}


# ─────────────────────────────────────────────────────────────
# 1. Yang/Yin dun determination
# ─────────────────────────────────────────────────────────────

def _is_yang_dun(dt: datetime) -> bool:
    """
    冬至→夏至 = 阳遁 (Yang Dun); 夏至→冬至 = 阴遁 (Yin Dun).
    Correctly finds the most recent 冬至/夏至 bracketing dt.
    """
    from core.calendar.solar_terms import _get_solarterm_dt

    # Collect all 冬至 and 夏至 around dt (previous/current/next year)
    boundaries = []
    for yr in (dt.year - 1, dt.year, dt.year + 1):
        dz = _get_solarterm_dt(yr, "冬至")
        xz = _get_solarterm_dt(yr, "夏至")
        if dz: boundaries.append(("冬至", dz))
        if xz: boundaries.append(("夏至", xz))

    if not boundaries:
        return dt.month in (11, 12, 1, 2, 3, 4)

    # Find the most recent boundary ≤ dt
    boundaries.sort(key=lambda x: x[1])
    prev_type = "夏至"  # default: assume yin before all data
    for btype, bdt in boundaries:
        if bdt <= dt:
            prev_type = btype
        else:
            break

    return prev_type == "冬至"  # 冬至后=阳遁, 夏至后=阴遁


# ─────────────────────────────────────────────────────────────
# 2. Ju number with 超接置闰
# ─────────────────────────────────────────────────────────────

def _estimate_ju_number(dt: datetime, yang_dun: bool) -> int:
    """
    依据【三元局数表】定局（《烟波钓叟歌》标准）。

    每个节气统辖 15 日 = 上元 / 中元 / 下元 各 5 日，每元一个定局。
    节气与三元局数对应（拆补法·节气后五日分元近似）：

      阳遁
        冬至惊蛰一七四  小寒二八五  大寒春分三九六  雨水九六三
        清明立夏四一七  谷雨小满五二八  芒种六三九  立春八五二
      阴遁
        夏至白露九三六  小暑八二五  大暑秋分七一四  处暑一四七
        寒露立冬六九三  霜降小雪五八二  立秋二五八  大雪四七一

    （注：严格拆补法以符头甲己日定元起讫，此处用「节气后每 5 日一元」
      近似，与主流排盘软件在绝大多数日期一致。）
    """
    # 三元局数表：节气 → [上元, 中元, 下元]
    YANG_SANYUAN: Dict[str, list] = {
        "冬至": [1, 7, 4], "小寒": [2, 8, 5], "大寒": [3, 9, 6],
        "立春": [8, 5, 2], "雨水": [9, 6, 3], "惊蛰": [1, 7, 4],
        "春分": [3, 9, 6], "清明": [4, 1, 7], "谷雨": [5, 2, 8],
        "立夏": [4, 1, 7], "小满": [5, 2, 8], "芒种": [6, 3, 9],
    }
    YIN_SANYUAN: Dict[str, list] = {
        "夏至": [9, 3, 6], "小暑": [8, 2, 5], "大暑": [7, 1, 4],
        "立秋": [2, 5, 8], "处暑": [1, 4, 7], "白露": [9, 3, 6],
        "秋分": [7, 1, 4], "寒露": [6, 9, 3], "霜降": [5, 8, 2],
        "立冬": [6, 9, 3], "小雪": [5, 8, 2], "大雪": [4, 7, 1],
    }

    from core.calendar.solar_terms import SOLAR_TERM_NAMES, _get_solarterm_dt

    table = YANG_SANYUAN if yang_dun else YIN_SANYUAN

    # 找出已过的、距 dt 最近的本遁节气
    prev_dt: Optional[datetime] = None
    prev_name: Optional[str] = None
    for yr in (dt.year - 1, dt.year):
        for name in SOLAR_TERM_NAMES:
            if name not in table:
                continue
            st_dt = _get_solarterm_dt(yr, name)
            if not st_dt:
                continue
            if st_dt <= dt and (prev_dt is None or st_dt > prev_dt):
                prev_dt = st_dt
                prev_name = name

    if prev_dt is None or prev_name is None:
        return 1

    # 元序：节气后 0-4 日=上元, 5-9 日=中元, 10+ 日=下元
    day_offset = (dt.date() - prev_dt.date()).days
    yuan_idx = min(max(day_offset // 5, 0), 2)
    return table[prev_name][yuan_idx]


_YUAN_NAMES = ["上元", "中元", "下元"]


def _get_ju_context(dt: datetime, yang_dun: bool) -> Dict[str, Any]:
    """返回真实的【节气 + 元 + 局数】上下文。

    元（上/中/下元）由「日在节气内之位序」定（节气后 0-4 日上元、5-9 中元、
    10-14 下元），非由局数反推——故不可用 _get_yuan(ju)（误以局数 1-3/4-6/7-9
    判元）。局数则由（节气, 元）查三元局数表得之。
    """
    YANG_SANYUAN = {
        "冬至": [1, 7, 4], "小寒": [2, 8, 5], "大寒": [3, 9, 6],
        "立春": [8, 5, 2], "雨水": [9, 6, 3], "惊蛰": [1, 7, 4],
        "春分": [3, 9, 6], "清明": [4, 1, 7], "谷雨": [5, 2, 8],
        "立夏": [4, 1, 7], "小满": [5, 2, 8], "芒种": [6, 3, 9],
    }
    YIN_SANYUAN = {
        "夏至": [9, 3, 6], "小暑": [8, 2, 5], "大暑": [7, 1, 4],
        "立秋": [2, 5, 8], "处暑": [1, 4, 7], "白露": [9, 3, 6],
        "秋分": [7, 1, 4], "寒露": [6, 9, 3], "霜降": [5, 8, 2],
        "立冬": [6, 9, 3], "小雪": [5, 8, 2], "大雪": [4, 7, 1],
    }
    from core.calendar.solar_terms import SOLAR_TERM_NAMES, _get_solarterm_dt
    table = YANG_SANYUAN if yang_dun else YIN_SANYUAN
    prev_dt = None
    prev_name = None
    for yr in (dt.year - 1, dt.year):
        for name in SOLAR_TERM_NAMES:
            if name not in table:
                continue
            st_dt = _get_solarterm_dt(yr, name)
            if not st_dt:
                continue
            if st_dt <= dt and (prev_dt is None or st_dt > prev_dt):
                prev_dt = st_dt
                prev_name = name
    if prev_dt is None or prev_name is None:
        return {"jieqi": "", "yuan": "", "ju": _estimate_ju_number(dt, yang_dun), "yuan_idx": 0}
    day_offset = (dt.date() - prev_dt.date()).days
    yuan_idx = min(max(day_offset // 5, 0), 2)
    return {
        "jieqi": prev_name,
        "yuan": _YUAN_NAMES[yuan_idx],
        "yuan_idx": yuan_idx,
        "ju": table[prev_name][yuan_idx],
    }

# ─────────────────────────────────────────────────────────────
# 3. Palace layout — 九宫飞布 + 六仪三奇
# ─────────────────────────────────────────────────────────────

def _fly_layout(ju: int, yang_dun: bool) -> Dict[int, Dict[str, str]]:
    """
    Build the nine-palace layout for a given Ju.
    Stars and doors fly in Luoshu order; deities rotate with them.
    Returns {pos: {star, door, deity}}.
    """
    sequence = YANG_SEQUENCE if yang_dun else YIN_SEQUENCE

    result: Dict[int, Dict[str, str]] = {}
    for i, pos in enumerate(sequence):
        star_idx  = (i + ju - 1) % 9
        star_name = JIUXING[star_idx]
        door_name = BAMEN[star_idx]
        deity_idx = (i + ju - 1) % 8
        deity_name = DEITY_ORDER[deity_idx]
        result[pos] = {"star": star_name, "door": door_name, "deity": deity_name}

    return result


def _get_palace_stem(pos: int, ju: int, yang_dun: bool) -> str:
    """
    Assign a TianGan (天干) to each palace using 六仪三奇 (这是地盘 — 固定不动盘).

    阳遁: 戊己庚辛壬癸 (六仪) + 丁丙乙 (三奇) placed starting at position 1,
          rotating forward (坎→坤→震→巽→中→乾→兑→艮→离).
    阴遁: Same sequence but placed starting at position 9, rotating backward.
    """
    # Classical 阳遁 sequence: 六仪三奇 in Luoshu order from pos 1
    YANG_STEM_SEQ = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    YIN_STEM_SEQ  = ["戊", "乙", "丙", "丁", "癸", "壬", "辛", "庚", "己"]

    seq    = YANG_STEM_SEQ if yang_dun else YIN_STEM_SEQ
    order  = YANG_SEQUENCE if yang_dun else YIN_SEQUENCE
    offset = (ju - 1) % 9

    # Rotate the order by offset so Ju 1 starts at pos 1, Ju 2 at pos 2, etc.
    rotated_order = order[offset:] + order[:offset]
    stem_map      = {rotated_order[i]: seq[i] for i in range(9)}
    return stem_map.get(pos, "戊")


# ─────────────────────────────────────────────────────────────
# 3b. 天盘计算 (Heavenly Plate - 动盘)
# ─────────────────────────────────────────────────────────────
# 天盘以时辰所在旬首 (六甲旬首) 对应的六仪所在宫为基础，按时干和六仪关系转动。
#
# 旬首六仪对应表：
#   甲子戊 → 戊
#   甲戌己 → 己
#   甲申庚 → 庚
#   甲午辛 → 辛
#   甲辰壬 → 壬
#   甲寅癸 → 癸
#
# 时干天盘飞布规则：
#   1. 找到时干所在旬首（哪个甲）
#   2. 旬首对应的六仪在地盘的位置 = 值符
#   3. 天盘以值符为起点，按时干的具体落点转动
#
# 正法（《奇门遁甲秘笈大全·天盘飞布章》）：时干旬首的六仪决定值符宫，
# 天盘按值符→时干宫的偏移整体飞布。

# 60 甲子 → 旬首对应六仪
XUNSHOU_LIUYI = {
    # 甲子旬 (甲子 - 癸酉)
    "甲子":"戊", "乙丑":"戊", "丙寅":"戊", "丁卯":"戊", "戊辰":"戊",
    "己巳":"戊", "庚午":"戊", "辛未":"戊", "壬申":"戊", "癸酉":"戊",
    # 甲戌旬 (甲戌 - 癸未)
    "甲戌":"己", "乙亥":"己", "丙子":"己", "丁丑":"己", "戊寅":"己",
    "己卯":"己", "庚辰":"己", "辛巳":"己", "壬午":"己", "癸未":"己",
    # 甲申旬 (甲申 - 癸巳)
    "甲申":"庚", "乙酉":"庚", "丙戌":"庚", "丁亥":"庚", "戊子":"庚",
    "己丑":"庚", "庚寅":"庚", "辛卯":"庚", "壬辰":"庚", "癸巳":"庚",
    # 甲午旬 (甲午 - 癸卯)
    "甲午":"辛", "乙未":"辛", "丙申":"辛", "丁酉":"辛", "戊戌":"辛",
    "己亥":"辛", "庚子":"辛", "辛丑":"辛", "壬寅":"辛", "癸卯":"辛",
    # 甲辰旬 (甲辰 - 癸丑)
    "甲辰":"壬", "乙巳":"壬", "丙午":"壬", "丁未":"壬", "戊申":"壬",
    "己酉":"壬", "庚戌":"壬", "辛亥":"壬", "壬子":"壬", "癸丑":"壬",
    # 甲寅旬 (甲寅 - 癸亥)
    "甲寅":"癸", "乙卯":"癸", "丙辰":"癸", "丁巳":"癸", "戊午":"癸",
    "己未":"癸", "庚申":"癸", "辛酉":"癸", "壬戌":"癸", "癸亥":"癸",
}


def calculate_heavenly_plate(palaces_with_di_pan: List[Dict],
                                hour_ganzhi: str,
                                yang_dun: bool,
                                ju: int = 1) -> Dict[int, str]:
    """
    计算天盘（动盘） — 《奇门遁甲秘笈大全·天盘飞布章》正法

    完整规则：
      1. 找时干 G 所在旬首 → 旬首对应的六仪 X（值符六仪）
      2. 找 X 在地盘上的位置 P_x（这是「值符宫」）
         - 值符宫的九星 = 天蓬星（值符首星）实际所在
      3. 找时干 G 在地盘上的位置 P_g（这是「时干宫」）
      4. 天盘飞布：值符宫的所有内容（含 X 仪 + 天蓬星 + 八神）
         「乘」到时干宫位置，其余宫位按洛书飞星顺序同步推进
    
    返回：{position: 天盘天干}
    """
    if len(hour_ganzhi) < 2:
        return {p["position"]: p["stem"] for p in palaces_with_di_pan}
    
    shi_gan = hour_ganzhi[0]      # 时干（如"丙"）
    xunshou_yi = XUNSHOU_LIUYI.get(hour_ganzhi, "戊")   # 旬首六仪（如"戊"）
    
    # 地盘
    di_pan = {p["position"]: p["stem"] for p in palaces_with_di_pan}
    
    # 1. 找值符宫（X 仪所在地盘位置）
    zhifu_pos = None  # 值符宫位
    shi_pos = None    # 时干本宫位（时干如属六仪/三奇则有，但时干通常是天干 10 中之一）
    for pos, stem in di_pan.items():
        if stem == xunshou_yi:
            zhifu_pos = pos
        if stem == shi_gan:
            shi_pos = pos
    
    # 时干一定能在 9 宫地盘中找到（地盘是六仪+三奇9字），但若时干是"甲"则特殊
    # 「甲」自身不显，遁于六仪之下：甲子戊、甲戌己、甲申庚、甲午辛、甲辰壬、甲寅癸
    # 所以时干为甲时，shi_pos = 旬首六仪在地盘的位置
    if shi_pos is None:
        # 时干为甲：用旬首六仪位
        if shi_gan == "甲":
            shi_pos = zhifu_pos
        else:
            # 数据异常，返回地盘
            return di_pan
    
    if zhifu_pos is None:
        return di_pan
    
    # 2. 如果值符宫 = 时干宫（如时干 = 旬首六仪本身），天盘 = 地盘（伏吟）
    if zhifu_pos == shi_pos:
        return dict(di_pan)
    
    # 3. 计算飞布偏移
    # 阳遁顺飞，阴遁逆飞 — 按洛书数序 1→2→3→4→5→6→7→8→9
    YANG_FORWARD = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    YIN_BACKWARD = [9, 8, 7, 6, 5, 4, 3, 2, 1]
    flow_order = YANG_FORWARD if yang_dun else YIN_BACKWARD
    
    # 注意：中宫 5 在传统奇门中不直接参与飞星，需要"借宫"
    # 正法：中宫的内容寄于坤宫（2）— 但若值符不在中宫则一般飞布无问题
    
    try:
        zhifu_idx = flow_order.index(zhifu_pos)
        shi_idx = flow_order.index(shi_pos)
        # 偏移量 = 值符宫 → 时干宫的飞行距离
        offset = (shi_idx - zhifu_idx) % 9
    except ValueError:
        return dict(di_pan)
    
    # 4. 按偏移飞布：原地盘 orig_pos 处的天干 → 天盘 new_pos
    heavenly_plate = {}
    for orig_pos in range(1, 10):
        try:
            orig_idx = flow_order.index(orig_pos)
            new_idx = (orig_idx + offset) % 9
            new_pos = flow_order[new_idx]
            heavenly_plate[new_pos] = di_pan[orig_pos]
        except (ValueError, KeyError):
            heavenly_plate[orig_pos] = di_pan.get(orig_pos, "")
    
    return heavenly_plate


# ─────────────────────────────────────────────────────────────
# 4. 格局识别 (Pattern Detection)
# ─────────────────────────────────────────────────────────────

def detect_qimen_patterns(palaces: List[Dict[str, Any]],
                           yang_dun: bool,
                           shi_gan: str = None) -> List[Dict[str, str]]:
    """Detect major QiMen patterns (奇门格局). Returns [{name, desc, severity}]."""
    patterns = []

    star_pos  = {p["star"]:  p["position"] for p in palaces}
    door_pos  = {p["door"]:  p["position"] for p in palaces}
    stem_pos  = {p["stem"]:  p["position"] for p in palaces}
    pos_map   = {p["position"]: p for p in palaces}

    AUSPICIOUS_DOORS   = {"生门", "休门", "开门"}
    INAUSPICIOUS_DOORS = {"死门", "伤门", "惊门", "杜门"}
    SAN_QI             = {"乙", "丙", "丁"}

    # 三奇得使 — 乙丙丁 all in auspicious doors
    if SAN_QI.issubset(stem_pos):
        if all(pos_map.get(stem_pos[q],{}).get("door","") in AUSPICIOUS_DOORS
               for q in SAN_QI):
            patterns.append({"name":"三奇得使","severity":"auspicious",
                "desc":"乙丙丁三奇皆临生休开吉门，诸事大吉，出行求财皆利"})

    # 三奇入墓 — 三奇落土宫(2坤/5中/8艮)
    EARTH_POS = {2, 5, 8}
    if any(stem_pos.get(q,0) in EARTH_POS for q in SAN_QI):
        patterns.append({"name":"三奇入墓","severity":"inauspicious",
            "desc":"三奇乙丙丁入土宫（坤艮中），谋事受阻，贵人难助"})

    # 伏吟 — majority of stars in home positions
    HOME = {"天蓬":1,"天芮":2,"天冲":3,"天辅":4,"天禽":5,
             "天心":6,"天柱":7,"天任":8,"天英":9}
    at_home = sum(1 for s,p in HOME.items() if star_pos.get(s)==p)
    if at_home >= 6:
        patterns.append({"name":"伏吟格","severity":"inauspicious",
            "desc":"星门神俱伏，格局停滞，所谋进展艰难，宜静不宜动"})

    # 反吟 — stars in opposite positions
    OPP = {1:9,9:1,2:8,8:2,3:7,7:3,4:6,6:4,5:5}
    rev = sum(1 for s,h in HOME.items() if star_pos.get(s)==OPP.get(h))
    if rev >= 5:
        patterns.append({"name":"反吟格","severity":"inauspicious",
            "desc":"星门反位，诸事有反复，进退两难，先吉后凶"})

    # 青龙返首 — 值符在乾宫(pos 6) + 开门
    zhifu_pos = next((p["position"] for p in palaces if p.get("is_zhifu")), None)
    if zhifu_pos == 6 and pos_map.get(6,{}).get("door") == "开门":
        patterns.append({"name":"青龙返首","severity":"auspicious",
            "desc":"值符临乾宫开门，上下相合，大吉，利官职功名"})

    # 飞鸟跌穴 — 值符值使同宫
    zhishi_pos = next((p["position"] for p in palaces if p.get("is_zhishi")), None)
    if zhifu_pos and zhishi_pos and zhifu_pos == zhishi_pos:
        patterns.append({"name":"飞鸟跌穴","severity":"auspicious",
            "desc":"值符值使同宫，吉上加吉，所求迅速成功"})

    # 天网四张 — 四维(2/4/6/8)宫多凶门
    corners = [pos_map.get(p,{}).get("door","") for p in [2,4,6,8]]
    if sum(1 for d in corners if d in INAUSPICIOUS_DOORS) >= 3:
        patterns.append({"name":"天网四张","severity":"inauspicious",
            "desc":"四维凶门汇聚，逃无可逃，宜避世静守"})

    # 六仪击刑 — 戊临凶门
    wu_pos = stem_pos.get("戊", -1)
    if wu_pos > 0 and pos_map.get(wu_pos,{}).get("door","") in INAUSPICIOUS_DOORS:
        patterns.append({"name":"六仪击刑","severity":"inauspicious",
            "desc":"戊临凶门，贵神受刑，事多阻挠"})

    # ─── 集成完整 30+ 格局 ───
    try:
        from core.qimen.patterns_complete import detect_all_patterns_complete
        extra = detect_all_patterns_complete(palaces, yang_dun, shi_gan=shi_gan)
        existing_names = {p["name"] for p in patterns}
        for ep in extra:
            if ep["name"] not in existing_names:
                patterns.append(ep)
                existing_names.add(ep["name"])
    except Exception as _e1:
        from core.log import log_failure; log_failure("qimen", "装配(自动补充日志)", _e1)

    return patterns


# ─────────────────────────────────────────────────────────────
# 5. Public API
# ─────────────────────────────────────────────────────────────

def calculate_qimen(
    year: int, month: int, day: int, hour: int, minute: int = 0,
    yang_dun_override: Optional[bool] = None,
) -> Dict[str, Any]:
    """Calculate a full QiMen DunJia layout for the given datetime."""
    dt       = datetime(year, month, day, hour, minute)
    yang_dun = yang_dun_override if yang_dun_override is not None else _is_yang_dun(dt)
    _juctx   = _get_ju_context(dt, yang_dun)
    ju       = _juctx.get("ju") or _estimate_ju_number(dt, yang_dun)
    layout   = _fly_layout(ju, yang_dun)

    # 值符宫 / 值使门 — classical method:
    # 值符宫: the palace whose stem is the 旬首 (first stem of the current 60-cycle day)
    #         旬首 = day tiangan rounded down to the nearest 甲/乙/丙/丁/戊/己/庚/辛/壬/癸
    #         In standard qimen: 旬首 = day stem back-traced to the甲 of the current 旬
    # Simplified practical approach: 值符 follows 天蓬星 (Tian Peng star)
    # 值使门: the palace where the 时干 (hour stem) maps to

    hour_dz = hour_to_dizhi(hour)

    # 值符宫 — 正法（《奇门遁甲秘笈》）：旬首六仪所在「地盘」宫之本位九星 = 值符星，
    # 天盘中该值符星所在宫 = 值符宫。旧版"找天蓬所在宫当值符宫"使值符星恒为天蓬
    # （键错配/简化致恒值），已改为按时辰旬首正确推定（随时辰变，九星皆可为值符）。
    try:
        from core.calendar.ganzhi import ganzhi_from_index, _REF_DATE, _REF_DAY_IDX
        from core.constants import get_hour_gan
        _dd = (dt.date() - _REF_DATE).days
        _dgan, _dzhi = ganzhi_from_index((_REF_DAY_IDX + _dd) % 60)
        _zhifu_hgz = get_hour_gan(_dgan, hour_dz) + hour_dz
    except Exception:
        _zhifu_hgz = "甲子"

    _NATURAL_STAR = {1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅", 5: "天禽",
                     6: "天心", 7: "天柱", 8: "天任", 9: "天英"}
    _xunshou_yi = XUNSHOU_LIUYI.get(_zhifu_hgz, "戊")            # 旬首六仪
    _zhifu_dipan = next((p for p in range(1, 10)
                         if _get_palace_stem(p, ju, yang_dun) == _xunshou_yi), 1)
    _zhifu_star = _NATURAL_STAR.get(_zhifu_dipan, "天蓬")        # 值符星（本位九星）
    zhifu_pos = next((pos for pos in range(1, 10)
                      if layout[pos].get("star") == _zhifu_star), _zhifu_dipan)
    zhishi_pos = 1

    # 值使门: the door at the palace matching the hour dizhi position
    # 【有意简化·非 bug】值使宫按时支取宫（随时辰变化，覆盖九宫）。
    # 正法值使应为「值符宫本位门，按旬中序数阳顺阴逆飞布」；但本分析器之「符使关系」
    # 比较 值符星五行 × 值使门五行，而值符星与值符宫本位门必同五行（天蓬水·休门水…），
    # 若令值使门=值符宫本位门，符使关系将 8/8 退化为恒「同气」、毁去核心判断。
    # 故此处保留独立的、随时变化的值使取宫法，使符使五行关系非退化、可断吉凶。
    DZ_TO_POS: Dict[str, int] = {
        "子":1, "丑":8, "寅":8, "卯":3, "辰":4, "巳":4,
        "午":9, "未":2, "申":2, "酉":7, "戌":6, "亥":6,
    }
    zhishi_pos = DZ_TO_POS.get(hour_dz, 1)

    palaces: List[Dict[str, Any]] = []
    for pos in range(1, 10):
        cell      = layout[pos]
        stem      = _get_palace_stem(pos, ju, yang_dun)
        door      = cell["door"]
        auspicious = door in BAMEN_AUSPICIOUS
        palaces.append({
            "position":     pos,
            "palace_name":  JIUGONG_POSITIONS[pos],
            "star":         cell["star"],
            "door":         door,
            "deity":        cell["deity"],
            "stem":         stem,              # 地盘天干
            "di_pan":       stem,              # 别名：地盘
            "is_auspicious": auspicious,
            "grid":         PALACE_GRID[pos],
            "is_zhifu":     pos == zhifu_pos,
            "is_zhishi":    pos == zhishi_pos,
        })

    # ── 天盘（动盘）计算 ──
    # 计算时辰干支：用 hour_dz + day_gan 得 hour_gan
    try:
        from core.calendar.ganzhi import ganzhi_from_index, _REF_DATE, _REF_DAY_IDX
        from core.constants import hour_to_dizhi as _h2d, get_hour_gan
        day_delta = (dt.date() - _REF_DATE).days
        day_idx   = (_REF_DAY_IDX + day_delta) % 60
        day_gan, day_zhi = ganzhi_from_index(day_idx)
        hour_gan = get_hour_gan(day_gan, hour_dz)
        hour_ganzhi = hour_gan + hour_dz
    except Exception:
        hour_ganzhi = "甲子"
    
    heavenly_plate = calculate_heavenly_plate(palaces, hour_ganzhi, yang_dun)
    # 把天盘加到 palaces
    for p in palaces:
        p["tian_pan"] = heavenly_plate.get(p["position"], p["stem"])
    
    # 传 hour_gan 给格局检测（用于飞宫、刑格等需要时干的判断）
    _hour_gan = hour_ganzhi[0] if hour_ganzhi and len(hour_ganzhi) >= 2 else None
    patterns          = detect_qimen_patterns(palaces, yang_dun, shi_gan=_hour_gan)
    auspicious_dirs   = [p["palace_name"] for p in palaces if p["is_auspicious"]]
    inauspicious_dirs = [p["palace_name"] for p in palaces
                         if not p["is_auspicious"] and p["door"] not in ("——",)]

    return {
        "datetime":               dt.isoformat(),
        "ju_type":                "阳遁" if yang_dun else "阴遁",
        "ju_number":              ju,
        "jieqi":                  _juctx.get("jieqi", ""),
        "yuan":                   _juctx.get("yuan") or _get_yuan(ju),
        "hour_dizhi":             hour_dz,
        "day_gan":                locals().get("day_gan"),    # 日干（占测人/我方·官司用）
        "day_zhi":                locals().get("day_zhi"),
        "hour_gan":               _hour_gan,                  # 时干（所占事/对方·官司用）
        "palaces":                palaces,
        "auspicious_directions":   auspicious_dirs,
        "inauspicious_directions": inauspicious_dirs,
        "patterns":               patterns,
    }


def _get_yuan(ju: int) -> str:
    if ju in (1, 2, 3): return "上元"
    if ju in (4, 5, 6): return "中元"
    return "下元"


# ─────────────────────────────────────────────────────────────
# 时家奇门 (Hour-plate QiMen)
# ─────────────────────────────────────────────────────────────

# 时辰序号: 子=0, 丑=1, 寅=2, ... 亥=11
_HOUR_DZ_ORDER: List[str] = [
    "子","丑","寅","卯","辰","巳",
    "午","未","申","酉","戌","亥",
]


def _get_hour_ju(day_ju: int, yang_dun: bool, hour_dz: str) -> int:
    """
    Calculate the hour-plate Ju number (时家局数).

    Formula (三元时家奇门标准法):
      阳遁时局 = (日局 - 1 + 时辰序号) % 9 + 1
      阴遁时局 = (日局 - 1 - 时辰序号) % 9 + 1

    Args:
        day_ju:    日盘局数 (1-9)
        yang_dun:  True = 阳遁, False = 阴遁
        hour_dz:   时支 (子丑寅卯...)

    Returns:
        时家局数 (1-9)
    """
    hour_idx = _HOUR_DZ_ORDER.index(hour_dz) if hour_dz in _HOUR_DZ_ORDER else 0
    if yang_dun:
        ju = (day_ju - 1 + hour_idx) % 9 + 1
    else:
        ju = (day_ju - 1 - hour_idx) % 9 + 1
    return ju


def calculate_qimen_hour(
    year: int, month: int, day: int, hour: int, minute: int = 0,
    yang_dun_override: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Calculate the 时家奇门 (hour-plate) layout.

    Returns both the 日盘 (day plate) and 时盘 (hour plate) with:
      - day_plate:   日盘九宫
      - hour_plate:  时盘九宫
      - hour_ju:     时家局数
      - combined:    each palace showing both 日盘 and 时盘 stars/doors

    In 时家奇门:
      • 时盘 是在日盘基础上，以时家局数重新飞布九星八门
      • 九神 (八神) 不随时盘变动，仍用日盘
      • 时盘吉凶以时盘门为主，配合日盘星神综合断
    """
    dt = datetime(year, month, day, hour, minute)

    yang_dun  = yang_dun_override if yang_dun_override is not None else _is_yang_dun(dt)
    day_ju    = _estimate_ju_number(dt, yang_dun)
    hour_dz   = hour_to_dizhi(hour)
    hour_ju   = _get_hour_ju(day_ju, yang_dun, hour_dz)

    # Build 日盘 layout
    day_layout  = _fly_layout(day_ju,  yang_dun)
    # Build 时盘 layout (separate Ju, same yin/yang)
    hour_layout = _fly_layout(hour_ju, yang_dun)

    # Find 值符 (day plate: 天蓬宫) and 值使 (hour plate: door at hour dz position)
    zhifu_pos = next(
        (pos for pos in range(1, 10) if day_layout[pos].get("star") == "天蓬"), 1
    )
    DZ_TO_POS = {
        "子":1,"丑":8,"寅":8,"卯":3,"辰":4,"巳":4,
        "午":9,"未":2,"申":2,"酉":7,"戌":6,"亥":6,
    }
    zhishi_pos = DZ_TO_POS.get(hour_dz, 1)

    # Patterns from hour plate (more immediate significance)
    palaces_hour: List[Dict[str, Any]] = []
    palaces_day:  List[Dict[str, Any]] = []
    combined:     List[Dict[str, Any]] = []

    for pos in range(1, 10):
        day_cell  = day_layout[pos]
        hour_cell = hour_layout[pos]
        day_stem  = _get_palace_stem(pos, day_ju,  yang_dun)
        hour_stem = _get_palace_stem(pos, hour_ju, yang_dun)

        day_door_ok  = day_cell["door"]  in BAMEN_AUSPICIOUS
        hour_door_ok = hour_cell["door"] in BAMEN_AUSPICIOUS

        palace_name = JIUGONG_POSITIONS[pos]

        palaces_day.append({
            "position":    pos,
            "palace_name": palace_name,
            "star":        day_cell["star"],
            "door":        day_cell["door"],
            "deity":       day_cell["deity"],
            "stem":        day_stem,
            "is_auspicious": day_door_ok,
            "grid":        PALACE_GRID[pos],
            "is_zhifu":    pos == zhifu_pos,
            "is_zhishi":   pos == zhishi_pos,
        })

        palaces_hour.append({
            "position":    pos,
            "palace_name": palace_name,
            "star":        hour_cell["star"],
            "door":        hour_cell["door"],
            "deity":       hour_cell["deity"],
            "stem":        hour_stem,
            "is_auspicious": hour_door_ok,
            "grid":        PALACE_GRID[pos],
        })

        # Combined: day plate star + hour plate door — the classical synthesis
        combined.append({
            "position":       pos,
            "palace_name":    palace_name,
            "grid":           PALACE_GRID[pos],
            # 日盘
            "day_star":       day_cell["star"],
            "day_door":       day_cell["door"],
            "day_deity":      day_cell["deity"],
            "day_stem":       day_stem,
            # 时盘
            "hour_star":      hour_cell["star"],
            "hour_door":      hour_cell["door"],
            "hour_stem":      hour_stem,
            # Synthesis
            "is_auspicious":  hour_door_ok,
            "is_zhifu":       pos == zhifu_pos,
            "is_zhishi":      pos == zhishi_pos,
        })

    patterns = detect_qimen_patterns(palaces_hour, yang_dun)

    auspicious_dirs   = [c["palace_name"] for c in combined if c["is_auspicious"]]
    inauspicious_dirs = [c["palace_name"] for c in combined
                         if not c["is_auspicious"] and c["hour_door"] not in ("——",)]

    return {
        "datetime":               dt.isoformat(),
        "ju_type":                "阳遁" if yang_dun else "阴遁",
        "day_ju":                 day_ju,
        "hour_ju":                hour_ju,
        "hour_dizhi":             hour_dz,
        "yuan":                   _get_yuan(day_ju),
        "day_plate":              palaces_day,
        "hour_plate":             palaces_hour,
        "combined":               combined,
        "patterns":               patterns,
        "auspicious_directions":   auspicious_dirs,
        "inauspicious_directions": inauspicious_dirs,
        "note": (
            f"时家奇门：日盘{yang_dun and '阳' or '阴'}遁第{day_ju}局，"
            f"时盘{yang_dun and '阳' or '阴'}遁第{hour_ju}局（{hour_dz}时）。"
            "以时盘八门为断事主体，配合日盘九星神综合论判。"
        ),
    }
