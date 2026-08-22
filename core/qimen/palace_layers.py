"""
core/qimen/palace_layers.py
===========================
奇门遁甲·九宫多层级综合断（补足排盘后每宫之"层"分析）。

奇门一宫，自上而下叠四盘一星：
    神（八神）· 星（九星）· 门（八门）· 天盘奇仪 · 地盘奇仪，
每层各有吉凶，更须层层论生克旺衰，方成一宫之断。本模块补全原排盘
中留空之三层与五大格态：

  · 宫五行旺衰      gong_wx + 星/门临宫之生克
  · 奇仪生克(天地盘) 天盘奇仪 vs 地盘奇仪 —— 上克下利客、下克上利主…
  · 门迫            宫克门为「迫」，门受制不得力
  · 入墓            天盘奇仪入其墓库之宫，气闭事滞
  · 六仪击刑        六仪落其击刑之宫（戊震·己坤·庚艮·辛离·壬巽·癸巽）
  · 旬空            宫之地支逢时旬之空亡，其事虚而待填实/冲空
  · 马星            时支三合之驿马所落之宫，主动、迁移、远行、速

复用 analyzer 之宫/星/门五行表，并以 lunar_python 取时柱定旬空，与排盘同源。

断法体例（奇门风格）：天盘为客为动为来意，地盘为主为静为根基；
上克下利客先动、下克上利主守成、上生下我耗于彼、下生上得助有援、比和平顺。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.constants import WUXING_SHENG, WUXING_KE

# ── 九宫五行 / 纳支 ──
GONG_WX: Dict[str, str] = {
    "坎宫": "水", "坤宫": "土", "震宫": "木", "巽宫": "木", "中宫": "土",
    "乾宫": "金", "兑宫": "金", "艮宫": "土", "离宫": "火",
}
GONG_DIZHI: Dict[str, List[str]] = {
    "坎宫": ["子"], "艮宫": ["丑", "寅"], "震宫": ["卯"], "巽宫": ["辰", "巳"],
    "离宫": ["午"], "坤宫": ["未", "申"], "兑宫": ["酉"], "乾宫": ["戌", "亥"],
    "中宫": ["未", "申"],   # 中宫寄坤
}

STAR_WX: Dict[str, str] = {
    "天蓬": "水", "天芮": "土", "天冲": "木", "天辅": "木", "天禽": "土",
    "天心": "金", "天柱": "金", "天任": "土", "天英": "火",
}
DOOR_WX: Dict[str, str] = {
    "休门": "水", "生门": "土", "伤门": "木", "杜门": "木",
    "景门": "火", "死门": "土", "惊门": "金", "开门": "金",
}
GAN_WX: Dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

# 六仪击刑宫（仪 → 击刑所落宫）
JIXING_GONG: Dict[str, str] = {
    "戊": "震宫", "己": "坤宫", "庚": "艮宫", "辛": "离宫", "壬": "巽宫", "癸": "巽宫",
}

# 五行墓库地支
WX_MU: Dict[str, str] = {"木": "未", "火": "戌", "金": "丑", "水": "辰", "土": "辰"}

# 三合驿马（时支 → 马星地支）
SANHE_MA: Dict[str, str] = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}

_GAN_ORDER = "甲乙丙丁戊己庚辛壬癸"
_ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"


def _wx_relation(a: str, b: str) -> str:
    """a 对 b 之五行关系（a比b / a生b / b生a / a克b / b克a）。"""
    if not a or not b:
        return ""
    if a == b:
        return "比和"
    if WUXING_SHENG.get(a) == b:
        return "我生"      # a 生 b
    if WUXING_SHENG.get(b) == a:
        return "生我"      # b 生 a
    if WUXING_KE.get(a) == b:
        return "我克"      # a 克 b
    if WUXING_KE.get(b) == a:
        return "克我"      # b 克 a
    return ""


def _hour_xunkong(dt: datetime) -> List[str]:
    """以时柱定旬空（两地支）。"""
    try:
        from lunar_python import Solar
        ec = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, 0, 0)\
            .getLunar().getEightChar()
        gz = ec.getTime()
        g = _GAN_ORDER.index(gz[0])
        z = _ZHI_ORDER.index(gz[1])
        xun_start = (z - g) % 12          # 旬首地支（甲所在）
        return [_ZHI_ORDER[(xun_start + 10) % 12], _ZHI_ORDER[(xun_start + 11) % 12]]
    except Exception:
        return []


# 八神吉凶倾向（与 analyzer 同源简表）
_DEITY_JI = {"值符", "太阴", "六合", "九天", "九地"}
_DEITY_XIONG = {"腾蛇", "白虎", "玄武"}


def analyze_palace_layers(palace: Dict[str, Any],
                          xunkong: List[str],
                          ma_zhi: str) -> Dict[str, Any]:
    """单宫多层级断：补宫五行旺衰、奇仪生克、门迫/入墓/击刑/旬空/马星。"""
    pname = palace.get("palace_name", "")
    gong_wx = GONG_WX.get(pname, "")
    tian = palace.get("tian_pan", "")
    di = palace.get("di_pan", palace.get("stem", ""))
    door = palace.get("door", "")
    star = palace.get("star", "")
    deity = palace.get("deity", "")

    tian_wx = GAN_WX.get(tian, "")
    di_wx = GAN_WX.get(di, "")
    star_wx = STAR_WX.get(star, "")
    door_wx = DOOR_WX.get(door, "")

    flags: List[Dict[str, str]] = []

    # ── 1. 奇仪生克（天盘 vs 地盘）──
    sd = _wx_relation(tian_wx, di_wx)
    SD_NOTE = {
        "我克": ("天盘克地盘——上克下，客胜主，利为客、宜主动出击、先发制人，求测人占先机。", "吉客"),
        "克我": ("地盘克天盘——下克上，主胜客，利为主、宜按兵守成，彼方占先、来意受制。", "利主"),
        "我生": ("天盘生地盘——上生下，我耗于彼、付出多而收获缓，为他人作嫁。", "耗"),
        "生我": ("地盘生天盘——下生上，根基生助、得力得援，事有后台、渐入佳境。", "得助"),
        "比和": ("天地盘比和——上下和顺，平稳无争、其事易谐。", "和"),
    }
    sd_desc, sd_tag = SD_NOTE.get(sd, ("", ""))
    sd_rel = f"{tian}加{di}（{sd}）：{sd_desc}" if sd_desc else ""

    # ── 2. 星临宫 / 门临宫 旺衰 ──
    star_gong = _wx_relation(star_wx, gong_wx)
    door_gong = _wx_relation(door_wx, gong_wx)

    # ── 3. 门迫（宫克门）──
    men_po = (door_gong == "克我")   # 宫五行克门五行 → 门迫
    if men_po:
        flags.append({"type": "门迫", "nature": "凶",
                      "desc": f"{door}（{door_wx}）受{pname}（{gong_wx}）所克——门迫，门受制不得力，吉门减吉、凶门增凶。"})

    # ── 4. 入墓（天盘奇仪入其墓库之宫）──
    ru_mu = False
    if tian_wx and WX_MU.get(tian_wx) in GONG_DIZHI.get(pname, []):
        ru_mu = True
        flags.append({"type": "入墓", "nature": "凶",
                      "desc": f"天盘{tian}（{tian_wx}）墓于{pname}（{WX_MU.get(tian_wx)}）——入墓，气闭神昏、其事滞塞难展，待冲墓之日方动。"})

    # ── 5. 六仪击刑 ──
    ji_xing = (JIXING_GONG.get(di) == pname)
    if ji_xing:
        flags.append({"type": "击刑", "nature": "凶",
                      "desc": f"地盘六仪{di}落{pname}——六仪击刑，主刑伤、是非、官讼、谋事自惹其祸。"})

    # ── 6. 旬空 ──
    kong = any(z in xunkong for z in GONG_DIZHI.get(pname, []))
    if kong:
        flags.append({"type": "空亡", "nature": "中",
                      "desc": f"{pname}（{'/'.join(GONG_DIZHI.get(pname, []))}）逢旬空——其事虚而不实，吉者减力、凶者亦缓，待填实/冲空之时方应。"})

    # ── 7. 马星 ──
    ma = (ma_zhi in GONG_DIZHI.get(pname, []))
    if ma:
        flags.append({"type": "马星", "nature": "吉",
                      "desc": f"驿马（{ma_zhi}）临{pname}——主动象、迁移、远行、速达，凡求速、求动、出行之事见此宫大利。"})

    # ── 综合层断 ──
    deity_q = "吉" if deity in _DEITY_JI else ("凶" if deity in _DEITY_XIONG else "中")
    _SG_LABEL = {"我生": "星生宫", "生我": "宫生星", "我克": "星克宫",
                 "克我": "宫克星", "比和": "星宫比和"}
    star_gong_label = _SG_LABEL.get(star_gong, "")
    layers = [
        f"神【{deity}·{deity_q}】",
        f"星【{star}·{star_wx}】{('·'+star_gong_label) if star_gong_label else ''}",
        f"门【{door}·{door_wx}】{'（门迫）' if men_po else ''}",
        f"天盘【{tian}】地盘【{di}】",
    ]
    flag_txt = "；".join(f["desc"] for f in flags)
    layer_judgment = (
        f"{pname}：" + " · ".join(layers) + "。"
        + (sd_rel if sd_rel else "")
        + (("　" + flag_txt) if flag_txt else "")
    )

    # ── 层级吉凶微调 ──
    xiong_flags = sum(1 for f in flags if f["nature"] == "凶")
    ma_bonus = 1 if ma else 0
    layer_score_adj = -2 * xiong_flags + ma_bonus

    return {
        "gong_wx": gong_wx,
        "stem_info": f"天盘{tian}（{tian_wx}）／地盘{di}（{di_wx}）",
        "sd_rel": sd_rel,
        "sd_tag": sd_tag,
        "star_vs_gong": star_gong,
        "door_vs_gong": door_gong,
        "flags": flags,
        "men_po": men_po, "ru_mu": ru_mu, "ji_xing": ji_xing,
        "kong": kong, "ma": ma,
        "layer_judgment": layer_judgment,
        "layer_score_adj": layer_score_adj,
    }


def enrich_palace_layers(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    为整盘九宫补全多层级断，并汇总特殊宫（空亡/马星/击刑/入墓/门迫）。
    直接在 layout['palaces'] 各宫填入层级字段，并加 layout['layer_summary']。
    """
    dt_str = layout.get("datetime", "")
    try:
        dt = datetime.fromisoformat(dt_str) if dt_str else datetime.now()
    except Exception:
        dt = datetime.now()
    xunkong = _hour_xunkong(dt)
    hour_zhi = layout.get("hour_dizhi", "")
    ma_zhi = SANHE_MA.get(hour_zhi, "")

    special = {"空亡宫": [], "马星宫": [], "击刑宫": [], "入墓宫": [], "门迫宫": []}
    for p in layout.get("palaces", []):
        layer = analyze_palace_layers(p, xunkong, ma_zhi)
        p["gong_wx"] = layer["gong_wx"]
        p["stem_info"] = layer["stem_info"]
        p["sd_rel"] = layer["sd_rel"]
        p["sd_tag"] = layer["sd_tag"]
        p["layers"] = layer
        pn = p.get("palace_name", "")
        if layer["kong"]:
            special["空亡宫"].append(pn)
        if layer["ma"]:
            special["马星宫"].append(pn)
        if layer["ji_xing"]:
            special["击刑宫"].append(pn)
        if layer["ru_mu"]:
            special["入墓宫"].append(pn)
        if layer["men_po"]:
            special["门迫宫"].append(pn)

    parts = []
    if ma_zhi:
        parts.append(f"本局时支{hour_zhi}，驿马在{ma_zhi}（{'/'.join(special['马星宫']) or '不入九宫'}）")
    if xunkong:
        parts.append(f"旬空{'/'.join(xunkong)}（空亡宫：{'/'.join(special['空亡宫']) or '无'}）")
    for k in ("门迫宫", "入墓宫", "击刑宫"):
        if special[k]:
            parts.append(f"{k}：{'/'.join(special[k])}")
    layout["layer_summary"] = {
        "xunkong": xunkong, "ma_zhi": ma_zhi, "special": special,
        "desc": "；".join(parts) + "。" if parts else "本局无显著空亡马星门迫击刑入墓之特宫。",
    }
    return layout
