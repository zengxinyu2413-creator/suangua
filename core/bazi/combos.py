"""
core/bazi/combos.py
===================
八字·组合断综合引擎（D 封顶层）——把已有的十神、格局、神煞、大运流年
诸单点，按"组合"熔炼成断：

  1. 神煞组合断  shensha_combos      —— 神煞重叠 + 两两相会之复合断
                                       （桃花带马、华盖空亡、文昌学堂、天罗地网…）
  2. 格局成破评断 evaluate_geju      —— 不止列成格/破格条件，更据本命十神之有无，
                                       评此格"已成 / 已破 / 破而有救"（《子平真诠》成败救应）
  3. 岁运组合断  analyze_suiyun     —— 大运 × 流年 之岁运并临、岁运天克地冲（相战）、
                                       引动命局用忌（补足只比流年-命局之不足）
  4. 顶层综合    bazi_combos        —— 神煞组合 + 格局评断 一并产出

复用 analyzer 的 chart（含 shishen_summary / pattern / geju_cheng_bai / shensha /
strength）与 relations 的冲合表，与排盘同源，不另立基元。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set

from core.constants import TIANGAN_WUXING, DIZHI_WUXING, WUXING_KE

# ─────────────────────────────────────────────────────────────
# 0. 基础表（天干五合 / 天干相克 / 地支六冲）
# ─────────────────────────────────────────────────────────────
TIANGAN_WUHE: Dict[frozenset, str] = {
    frozenset({"甲", "己"}): "土", frozenset({"乙", "庚"}): "金",
    frozenset({"丙", "辛"}): "水", frozenset({"丁", "壬"}): "木",
    frozenset({"戊", "癸"}): "火",
}
DIZHI_CHONG: Dict[str, str] = {
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}


def _gan_ke(a: str, b: str) -> bool:
    """天干 a 克 b？"""
    return WUXING_KE.get(TIANGAN_WUXING.get(a, ""), "") == TIANGAN_WUXING.get(b, "")


# ─────────────────────────────────────────────────────────────
# 1. 神煞组合断
# ─────────────────────────────────────────────────────────────

# 重叠（同一神煞≥2）之断
_OVERLAP_NOTE: Dict[str, Dict[str, str]] = {
    "华盖": {"nature": "中", "d": "华盖重重，孤高玄思之性愈烈，主聪慧而孤，宜艺术、宗教、玄学、独立专业，不利群处。"},
    "桃花": {"nature": "凶", "d": "桃花重叠，情多缘杂、易招酒色风流之扰，男女皆宜守正自持。"},
    "咸池": {"nature": "凶", "d": "咸池（桃花）重叠，多情风流、异性缘浓而杂，慎防色累。"},
    "驿马": {"nature": "中", "d": "驿马重叠，一生奔波动荡、迁徙变动频繁，宜外出、经商、流动谋生。"},
    "羊刃": {"nature": "凶", "d": "羊刃重叠，性刚烈、易招刑伤血光、克妻破财，须以官杀制之方吉。"},
    "魁罡": {"nature": "中", "d": "魁罡叠见，性刚果决、聪明权重，然过刚易折，逢冲刑则祸。"},
    "孤辰": {"nature": "凶", "d": "孤辰叠见，孤僻寡合、六亲缘薄，婚姻宜迟。"},
    "寡宿": {"nature": "凶", "d": "寡宿叠见，孤寡之性，夫妻缘分淡薄，宜修心广交。"},
    "天乙贵人": {"nature": "吉", "d": "天乙贵人多见，一生贵人扶持、逢凶化吉、多得提携之福。"},
    "禄神": {"nature": "吉", "d": "禄神叠见，食禄丰厚、自立之力强，衣食无忧。"},
}

# 两两组合（无序对）之复合断
_PAIR_COMBOS: List[Dict[str, Any]] = [
    {"set": {"桃花", "驿马"}, "name": "桃花带马", "nature": "中",
     "d": "桃花会驿马，风流走四方、异地情缘、动中生情，主多外缘而漂泊。"},
    {"set": {"咸池", "驿马"}, "name": "咸池带马", "nature": "中",
     "d": "咸池会驿马，多情而好动、异乡桃花，宜防情累分心。"},
    {"set": {"桃花", "红艳煞"}, "name": "桃花红艳", "nature": "凶",
     "d": "桃花会红艳，异性缘极旺、风情万种，最易招情色是非，宜守德。"},
    {"set": {"咸池", "红艳煞"}, "name": "咸池红艳", "nature": "凶",
     "d": "咸池会红艳，多情多欲、桃花极盛，须慎色戒淫。"},
    {"set": {"华盖", "孤辰"}, "name": "华盖孤辰", "nature": "中",
     "d": "华盖会孤辰，孤高出尘之象，宜艺术、宗教、独行专业，六亲缘薄。"},
    {"set": {"华盖", "寡宿"}, "name": "华盖寡宿", "nature": "中",
     "d": "华盖会寡宿，孤清自守、宜方外艺文，婚姻缘迟。"},
    {"set": {"华盖", "文昌贵人"}, "name": "华盖文昌", "nature": "吉",
     "d": "华盖会文昌，才艺聪慧、悟性极高，利文艺、玄学、专业著述。"},
    {"set": {"华盖", "学堂"}, "name": "华盖学堂", "nature": "吉",
     "d": "华盖会学堂，慧根深、宜钻研学问与术数，利专精之学。"},
    {"set": {"文昌贵人", "学堂"}, "name": "文昌学堂", "nature": "吉",
     "d": "文昌会学堂，主聪颖好学、利读书科甲、功名文途顺遂。"},
    {"set": {"文昌贵人", "词馆"}, "name": "文昌词馆", "nature": "吉",
     "d": "文昌会词馆，文采斐然、利文章著述、舌耕笔耕之业。"},
    {"set": {"天乙贵人", "天德贵人"}, "name": "天乙天德", "nature": "吉",
     "d": "天乙会天德，福厚德深、贵人云集、一生逢凶化吉。"},
    {"set": {"天乙贵人", "月德贵人"}, "name": "天乙月德", "nature": "吉",
     "d": "天乙会月德，仁厚多助、灾难自消、贵气绵长。"},
    {"set": {"将星", "华盖"}, "name": "将星华盖", "nature": "吉",
     "d": "将星会华盖，文武兼资、权贵带艺，宜掌权而具才学。"},
    {"set": {"将星", "驿马"}, "name": "将星驿马", "nature": "吉",
     "d": "将星会驿马，出将入相、外出掌权，宜远方建功、武职或外务。"},
    {"set": {"将星", "桃花"}, "name": "将星桃花", "nature": "中",
     "d": "将星会桃花，才貌出众、领袖魅力，异性缘佳，宜防色累权。"},
    {"set": {"孤辰", "寡宿"}, "name": "孤辰寡宿", "nature": "凶",
     "d": "孤辰会寡宿，孤独刑克、六亲冷淡、婚姻多舛，宜迟婚修性。"},
    {"set": {"亡神", "劫煞"}, "name": "亡神劫煞", "nature": "凶",
     "d": "亡神会劫煞，主破耗失盗、暗中小人、谋事多阻，宜守财慎交。"},
    {"set": {"金舆", "天乙贵人"}, "name": "金舆天乙", "nature": "吉",
     "d": "金舆会天乙，富贵得乘、出入有车马之贵，多得尊荣。"},
    {"set": {"天罗", "地网"}, "name": "天罗地网", "nature": "凶",
     "d": "天罗地网齐见，主羁绊缠身、易陷官非牢狱、病灾困顿，逢冲解则吉。"},
    {"set": {"禄神", "天乙贵人"}, "name": "禄神天乙", "nature": "吉",
     "d": "禄神会天乙，福禄双全、衣食丰足兼得贵助。"},
]


def shensha_combos(chart: Dict[str, Any]) -> Dict[str, Any]:
    """从命盘已激活之神煞中，析出重叠与两两组合之复合断。"""
    shensha = chart.get("shensha", []) or []
    counts: Dict[str, int] = {}
    for s in shensha:
        counts[s.get("name", "")] = counts.get(s.get("name", ""), 0) + 1
    present: Set[str] = set(counts.keys())

    combos: List[Dict[str, Any]] = []

    # 重叠
    for name, cnt in counts.items():
        if cnt >= 2 and name in _OVERLAP_NOTE:
            note = _OVERLAP_NOTE[name]
            combos.append({
                "type": "重叠", "name": f"{name}×{cnt}", "members": [name],
                "nature": note["nature"], "desc": note["d"],
            })

    # 两两组合
    for rule in _PAIR_COMBOS:
        if rule["set"].issubset(present):
            combos.append({
                "type": "相会", "name": rule["name"], "members": sorted(rule["set"]),
                "nature": rule["nature"], "desc": rule["d"],
            })

    ji = sum(1 for c in combos if c["nature"] == "吉")
    xiong = sum(1 for c in combos if c["nature"] == "凶")
    if not combos:
        summary = "命中神煞无显著重叠或相会之组合，各神煞独论即可。"
    elif ji > xiong:
        summary = f"神煞组合以吉为主（吉{ji}·凶{xiong}），贵气、才艺、助力之象较显。"
    elif xiong > ji:
        summary = f"神煞组合凶象偏多（吉{ji}·凶{xiong}），桃花孤克、破耗羁绊须留意化解。"
    else:
        summary = f"神煞组合吉凶相参（吉{ji}·凶{xiong}），福祸互见，宜趋吉避凶。"

    return {"success": True, "combos": combos, "summary": summary,
            "ji_count": ji, "xiong_count": xiong}


# ─────────────────────────────────────────────────────────────
# 2. 格局成破评断（据本命十神有无）
# ─────────────────────────────────────────────────────────────

# 每格之成/破判据（以十神有无论；身强弱由 strength 调节）
#   key: 格名；cheng/po 为 (条件十神集合, 文字)，需全部出现方算命中
_GEJU_RULES: Dict[str, Dict[str, Any]] = {
    "正官格": {
        "cheng": [(["正财"], "财生官、官星有根"), (["正印"], "官印相生、贵气流通")],
        "po": [(["伤官"], "伤官见官、克破贵气"), (["七杀"], "官杀混杂、贵气驳浊")],
        "jiu": "官杀混杂者，去杀留官（合杀/制杀）则清；伤官见官者，以印制伤护官。",
    },
    "七杀格": {
        "cheng": [(["食神"], "食神制杀、英雄得用"), (["正印"], "印化杀生身、化险为夷"),
                  (["羊刃"], "羊刃驾杀、武贵之格")],
        "po": [(["正财"], "财党杀攻身、身弱难任")],
        "jiu": "杀重无制者，喜食神制之或印星化之；身弱者忌财生杀。",
    },
    "正财格": {
        "cheng": [(["正官"], "财生官、既富且贵"), (["食神"], "食神生财、财源不竭")],
        "po": [(["比肩"], "比劫夺财、破财争利"), (["劫财"], "劫财分夺、财不归我")],
        "jiu": "比劫夺财者，喜官杀制劫护财，或食伤通关化劫生财。",
    },
    "偏财格": {
        "cheng": [(["正官"], "财旺生官、富而能贵"), (["食神"], "食伤生财、广进财源")],
        "po": [(["比肩"], "比劫争夺、众人分财"), (["劫财"], "劫财夺利、聚散无常")],
        "jiu": "比劫重者，得官杀制劫则财得守。",
    },
    "正印格": {
        "cheng": [(["正官"], "官印相生、最为清贵"), (["七杀"], "杀印相生、化杀为权")],
        "po": [(["正财"], "财星坏印、贪财坏印则贫"), (["偏财"], "财重破印、富屋贫人")],
        "jiu": "财星坏印者，喜比劫制财护印；印重者反喜财损印取中和。",
    },
    "偏印格": {
        "cheng": [(["七杀"], "杀生偏印、有官可化反成贵"), (["偏财"], "偏财制枭、化忌为用")],
        "po": [(["食神"], "枭神夺食、主孤克贫困")],
        "jiu": "枭神夺食者，必得财星制枭，则食神得用反成贵格。",
    },
    "食神格": {
        "cheng": [(["正财"], "食神生财、聪慧富足"), (["偏财"], "食神生财、财源广进"),
                  (["七杀"], "食神制杀、英雄之格")],
        "po": [(["偏印"], "枭神夺食、福气受夺")],
        "jiu": "枭神夺食者，喜财星制枭以护食神。",
    },
    "伤官格": {
        "cheng": [(["正财"], "伤官生财、财艺双收"), (["偏财"], "伤官生财、富而多能"),
                  (["正印"], "伤官佩印、贵而有制")],
        "po": [(["正官"], "伤官见官、为祸百端")],
        "jiu": "伤官见官者，喜印制伤、或财化伤生官以转祸为福。",
    },
    "建禄格": {
        "cheng": [(["正官"], "禄逢官护、贵显"), (["正财"], "禄透财、富足"),
                  (["七杀"], "禄逢杀制、威权"), (["食神"], "禄逢食泄秀、聪秀")],
        "po": [],
        "jiu": "建禄无财官食伤透泄者，平常之命；最忌印重身旺无泄。",
    },
    "月刃格": {
        "cheng": [(["七杀"], "羊刃驾杀、武贵"), (["正官"], "刃逢官制、贵显")],
        "po": [(["伤官"], "刃逢伤官、刚暴易祸")],
        "jiu": "月刃喜官杀制刃，最忌刃旺无制、再行刃运则祸。",
    },
}


def _present_shishen(chart: Dict[str, Any]) -> Set[str]:
    out: Set[str] = set()
    for s in chart.get("shishen_summary", []) or []:
        nm = s.get("shishen", "")
        if nm:
            out.add(nm)
    return out


def evaluate_geju(chart: Dict[str, Any]) -> Dict[str, Any]:
    """据本命十神有无，评本格已成/已破/破而有救。"""
    pattern = chart.get("pattern", "")
    rules = _GEJU_RULES.get(pattern)
    strength = chart.get("strength", "")
    if isinstance(strength, dict):
        strength = strength.get("label", "")
    present = _present_shishen(chart)

    if not rules:
        # 专旺/化气/从格等特殊格：从 geju_cheng_bai / pattern_desc 取概述
        return {
            "available": False, "pattern": pattern,
            "verdict": f"【{pattern}】属专旺/化气/从格之类，以顺其旺神之势为用，"
                       f"忌逆其气；详参格局总论与调候。",
        }

    cheng_hit = []
    for need, txt in rules["cheng"]:
        if set(need).issubset(present) and txt not in cheng_hit:
            cheng_hit.append(txt)
    po_hit = []
    for need, txt in rules["po"]:
        if set(need).issubset(present) and txt not in po_hit:
            po_hit.append(txt)

    if cheng_hit and not po_hit:
        status, q = "格成", "吉"
        verdict = f"【{pattern}】已成——{('；'.join(cheng_hit))}。" \
                  f"{'身' + strength + '，' if strength else ''}格局清纯，主富贵可期。"
    elif po_hit and cheng_hit:
        status, q = "破而有救", "中"
        verdict = (f"【{pattern}】见破（{('；'.join(po_hit))}），"
                   f"幸有救应（{('；'.join(cheng_hit))}）——{rules['jiu']}"
                   f"破中有救，先抑后扬。")
    elif po_hit:
        status, q = "格破", "凶"
        verdict = (f"【{pattern}】已破——{('；'.join(po_hit))}，"
                   f"本命未见救应之神。救法：{rules['jiu']}须赖大运补救。")
    else:
        status, q = "格局未显", "平"
        verdict = (f"【{pattern}】成格之神未透显，格局未充——平常之造，待运引发。"
                   f"成法：{('；'.join(t for _, t in rules['cheng'][:2]))}。")

    return {
        "available": True, "pattern": pattern, "status": status, "quality": q,
        "cheng_hit": cheng_hit, "po_hit": po_hit, "jiu": rules["jiu"],
        "strength": strength, "verdict": verdict,
    }


# ─────────────────────────────────────────────────────────────
# 3. 岁运组合断（大运 × 流年）
# ─────────────────────────────────────────────────────────────

def analyze_suiyun(chart: Dict[str, Any],
                   dayun_gan: str, dayun_zhi: str,
                   liunian_gan: str, liunian_zhi: str) -> Dict[str, Any]:
    """大运 × 流年 之岁运组合断。"""
    tags: List[str] = []
    notes: List[str] = []

    dy = f"{dayun_gan}{dayun_zhi}"
    ln = f"{liunian_gan}{liunian_zhi}"

    # 岁运并临
    if dy == ln:
        tags.append("岁运并临")
        notes.append(f"大运与流年同为【{dy}】——岁运并临。古云『岁运并临，灾殃立至』，"
                     f"主该年变动至大；若临喜用则大吉大利，临忌神则祸咎尤重。")

    # 岁运天克地冲（相战）
    gan_chong = _gan_ke(dayun_gan, liunian_gan) or _gan_ke(liunian_gan, dayun_gan)
    zhi_chong = DIZHI_CHONG.get(dayun_zhi) == liunian_zhi
    if gan_chong and zhi_chong:
        tags.append("岁运相战(天克地冲)")
        notes.append(f"大运【{dy}】与流年【{ln}】天克地冲——岁运相战，"
                     f"主该年反复颠覆、动荡不宁、内外交迫，诸事宜守不宜进。")
    elif zhi_chong:
        tags.append("岁运地支相冲")
        notes.append(f"大运{dayun_zhi}与流年{liunian_zhi}相冲，主动象、迁移变动、宜防冲处之事生变。")

    # 引动命局（大运/流年地支 冲 命局四柱地支）
    chart_zhis = {
        "年支": chart.get("year_pillar", {}).get("dizhi", ""),
        "月支": chart.get("month_pillar", {}).get("dizhi", ""),
        "日支": chart.get("day_pillar", {}).get("dizhi", ""),
        "时支": chart.get("hour_pillar", {}).get("dizhi", ""),
    }
    for src_label, src_zhi in (("流年", liunian_zhi), ("大运", dayun_zhi)):
        for pos, cz in chart_zhis.items():
            if cz and DIZHI_CHONG.get(src_zhi) == cz:
                notes.append(f"{src_label}{src_zhi}冲命局{pos}（{cz}），引动{pos}之事——"
                             f"{'婚姻情感/健康' if pos=='日支' else '事业根基' if pos=='月支' else '长辈祖业' if pos=='年支' else '子女晚景'}有动。")

    if not tags and len(notes) <= 0:
        tags.append("岁运平和")
        notes.append(f"大运【{dy}】流年【{ln}】无并临相战之险，岁运相安，运势平稳。")

    return {
        "success": True, "dayun": dy, "liunian": ln,
        "tags": tags, "notes": notes,
    }


# ─────────────────────────────────────────────────────────────
# 4. 顶层综合
# ─────────────────────────────────────────────────────────────

def bazi_combos(chart: Dict[str, Any]) -> Dict[str, Any]:
    """命局层之组合综合：神煞组合 + 格局成破评断。"""
    return {
        "success": True,
        "shensha_combos": shensha_combos(chart),
        "geju_evaluation": evaluate_geju(chart),
    }


# ─────────────────────────────────────────────────────────────
# 5. 流年逐年组合断（深化：完整十神 + 喜忌 + 应事 + 大运×流年组合）
# ─────────────────────────────────────────────────────────────

# 十神 → 应事主题
_SHISHEN_THEME: Dict[str, str] = {
    "正财": "求财置业、稳定收入，男命主妻缘、父事",
    "偏财": "投机横财、外快机遇，男命主异性缘、父事",
    "正官": "升迁考公、责任名位，女命主婚姻夫星，亦防官非",
    "七杀": "压力竞争、变动魄力，女命主情缘，亦防是非病灾",
    "正印": "文书学业、贵人母事、房产合同、名声护身",
    "偏印": "偏门学术、思虑孤高、宗教玄学，亦主继母",
    "食神": "子女口福、才艺投资、悠然进财",
    "伤官": "表现创作、外出生变、口舌才秀，逢官则防官非",
    "比肩": "兄弟同辈、合作自立、竞争分立",
    "劫财": "破耗争夺、合伙不利，男命防克妻破财",
}

_BANG = {"正印", "偏印", "比肩", "劫财"}    # 帮身（生扶）
_XIE = {"正财", "偏财", "正官", "七杀", "食神", "伤官"}   # 耗身（克泄耗）


def _liunian_xiji(shishen: str, strength_label: str,
                  liunian_wx: str, xiyong_wx: str) -> str:
    """流年十神之喜忌：身强喜耗、身弱喜帮、中和以调候用神五行论。"""
    if "强" in (strength_label or "") or "旺" in (strength_label or ""):
        return "喜" if shishen in _XIE else "忌"
    if "弱" in (strength_label or ""):
        return "喜" if shishen in _BANG else "忌"
    # 中和：流年五行合调候用神则喜
    if xiyong_wx and liunian_wx == xiyong_wx:
        return "喜"
    return "平"


# 大运 × 流年 十神组合典型
def _dy_ln_combo(dy_ss: str, ln_ss: str, parent_label: str = "大运") -> str:
    fin = {"正财", "偏财"}
    off = {"正官", "七杀"}
    seal = {"正印", "偏印"}
    out = {"食神", "伤官"}
    rob = {"比肩", "劫财"}
    if dy_ss in fin and ln_ss in off:
        return f"{parent_label}财运逢本期官杀——财生官旺，宜借财力求名位、财禄双美（身能任则吉）。"
    if (dy_ss in off and ln_ss in seal) or (dy_ss in seal and ln_ss in off):
        return "官印相生——升迁、文书、考核、贵人之喜，名位有进。"
    if dy_ss in out and ln_ss in fin:
        return "食伤生财——才艺、表现化为财源，财路活络、宜进取经营。"
    if dy_ss in rob and ln_ss in fin:
        return "比劫夺财——破财、合伙争利、为人作保宜慎，财去人安。"
    if (dy_ss in fin and ln_ss in seal) or (dy_ss in seal and ln_ss in fin):
        return "财印交争——重财则伤文书学业、重学则碍财利，须权衡取舍。"
    if dy_ss in out and ln_ss in off:
        return "伤官见官——易招是非官非、与上司长辈相忤，言行宜收敛。"
    return ""


def analyze_liunian_combo(chart: Dict[str, Any],
                          dayun_gan: str, dayun_zhi: str,
                          liunian_gan: str, liunian_zhi: str) -> Dict[str, Any]:
    """单个流年之逐年组合断（完整十神 + 喜忌 + 应事 + 大运组合）。"""
    from core.bazi.analyzer import get_shishen
    from core.constants import CANGGAN, TIANGAN_WUXING, DIZHI_WUXING

    dm = chart.get("day_master", "")
    strength = chart.get("strength", "")
    if isinstance(strength, dict):
        strength = strength.get("label", "")
    tiaohou = chart.get("tiaohou", {}) or {}
    xiyong_gan = tiaohou.get("primary", "")
    xiyong_wx = TIANGAN_WUXING.get(xiyong_gan, "")

    # 流年完整十神（天干 + 地支本气）
    ln_gan_ss = get_shishen(dm, liunian_gan)
    ln_zhi_hidden = (CANGGAN.get(liunian_zhi, []) or [""])[0]
    ln_zhi_ss = get_shishen(dm, ln_zhi_hidden) if ln_zhi_hidden else ""
    ln_wx = TIANGAN_WUXING.get(liunian_gan, "")

    # 喜忌
    xiji = _liunian_xiji(ln_gan_ss, strength, ln_wx, xiyong_wx)

    # 应事主题（天干十神主，地支辅）
    themes = []
    if ln_gan_ss in _SHISHEN_THEME:
        themes.append(f"{ln_gan_ss}：{_SHISHEN_THEME[ln_gan_ss]}")
    if ln_zhi_ss and ln_zhi_ss != ln_gan_ss and ln_zhi_ss in _SHISHEN_THEME:
        themes.append(f"{ln_zhi_ss}（藏）：{_SHISHEN_THEME[ln_zhi_ss]}")

    # 大运 × 流年组合
    dy_gan_ss = get_shishen(dm, dayun_gan)
    combo_note = _dy_ln_combo(dy_gan_ss, ln_gan_ss)

    # 吉凶结论
    if xiji == "喜":
        verdict = f"{liunian_gan}{liunian_zhi}年，流年{ln_gan_ss}为喜用——主吉，所主之事顺遂可进。"
        quality = "吉"
    elif xiji == "忌":
        verdict = f"{liunian_gan}{liunian_zhi}年，流年{ln_gan_ss}为忌神——主阻，所主之事多耗费波折，宜守。"
        quality = "凶"
    else:
        verdict = f"{liunian_gan}{liunian_zhi}年，流年{ln_gan_ss}力量中平——吉凶随事而分，平稳之年。"
        quality = "平"

    return {
        "success": True,
        "ganzhi": f"{liunian_gan}{liunian_zhi}",
        "shishen_gan": ln_gan_ss, "shishen_zhi": ln_zhi_ss,
        "xiji": xiji, "quality": quality,
        "themes": themes,
        "dayun_combo": combo_note,
        "verdict": verdict + (("　" + combo_note) if combo_note else ""),
    }


def analyze_period_combo(chart: Dict[str, Any],
                         parent_gan: str, parent_zhi: str,
                         cur_gan: str, cur_zhi: str,
                         label: str = "流月",
                         parent_label: str = "流年") -> Dict[str, Any]:
    """
    通用逐期组合断（流月/流日，与流年同深度）：
    完整十神 + 喜忌 + 应事 + 上期×本期十神组合。
    parent = 上一级周期（流月之上为流年、流日之上为流月）。
    """
    from core.bazi.analyzer import get_shishen
    from core.constants import CANGGAN, TIANGAN_WUXING

    dm = chart.get("day_master", "")
    strength = chart.get("strength", "")
    if isinstance(strength, dict):
        strength = strength.get("label", "")
    tiaohou = chart.get("tiaohou", {}) or {}
    xiyong_wx = TIANGAN_WUXING.get(tiaohou.get("primary", ""), "")

    cur_gan_ss = get_shishen(dm, cur_gan)
    cur_zhi_hidden = (CANGGAN.get(cur_zhi, []) or [""])[0]
    cur_zhi_ss = get_shishen(dm, cur_zhi_hidden) if cur_zhi_hidden else ""
    cur_wx = TIANGAN_WUXING.get(cur_gan, "")

    xiji = _liunian_xiji(cur_gan_ss, strength, cur_wx, xiyong_wx)

    themes = []
    if cur_gan_ss in _SHISHEN_THEME:
        themes.append(f"{cur_gan_ss}：{_SHISHEN_THEME[cur_gan_ss]}")
    if cur_zhi_ss and cur_zhi_ss != cur_gan_ss and cur_zhi_ss in _SHISHEN_THEME:
        themes.append(f"{cur_zhi_ss}（藏）：{_SHISHEN_THEME[cur_zhi_ss]}")

    parent_ss = get_shishen(dm, parent_gan) if parent_gan else ""
    combo_note = _dy_ln_combo(parent_ss, cur_gan_ss, parent_label) if parent_ss else ""

    if xiji == "喜":
        verdict = f"{cur_gan}{cur_zhi}{label}，{cur_gan_ss}为喜用——主吉，所主之事顺遂可进。"
        quality = "吉"
    elif xiji == "忌":
        verdict = f"{cur_gan}{cur_zhi}{label}，{cur_gan_ss}为忌神——主阻，所主之事多耗费波折，宜守。"
        quality = "凶"
    else:
        verdict = f"{cur_gan}{cur_zhi}{label}，{cur_gan_ss}力量中平——吉凶随事而分，平稳之期。"
        quality = "平"

    return {
        "success": True,
        "label": label,
        "ganzhi": f"{cur_gan}{cur_zhi}",
        "shishen_gan": cur_gan_ss, "shishen_zhi": cur_zhi_ss,
        "xiji": xiji, "quality": quality,
        "themes": themes,
        "parent_combo": combo_note,
        "verdict": verdict + (("　" + combo_note) if combo_note else ""),
    }
