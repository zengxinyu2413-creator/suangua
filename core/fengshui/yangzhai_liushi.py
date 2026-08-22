"""
core/fengshui/yangzhai_liushi.py
================================
阳宅·论六事（路·井·灶·厕·碓磨·畜栏），补全《阳宅三要》之外、
《阳宅十书·论六事》一门，将"门主灶"以外的六事安置吉凶纳入同一大游年体系。

一、六事纲领（《阳宅十书》）
   "宅以门、路、井、灶、碓磨、厕、畜栏为六事（连门主则曰七事）。"
   总则 ── **净者居吉方，秽者镇凶方。**
     · 净/旺之物（门、来路、井）—— 宜安宅之吉方（生气/天医/延年/伏位），
       置吉则引旺纳财；若误置凶方，则吉物失位、反受凶气。
     · 秽/动之物（灶座、厕、碓磨、畜栏）—— 宜压宅之凶方（祸害/六煞/五鬼/绝命），
       "以秽压凶、以动制煞"，凶不为害；若误占吉方，则污秽吉气、损丁破财。
   灶最特殊 ── **坐煞向吉**：灶座宜坐凶方（压煞），灶口宜向吉方（纳生气），
     此节已于《阳宅三要》灶座/灶口详断，本module仅提其则、不重出。

二、中宫之忌
   中宫为一宅之皇极、太极所钟。井、厕、碓磨、畜栏皆忌居中宫 ──
   秽居中则秽气攻心、主百病丛生、家道暗损；动器居中则震动宅心、不宁。

三、各事专则（除大游年方位吉凶外，另参形理通则）
   · 来路：宜从吉方蜿蜒而来（引旺气），忌凶方直冲、忌反弓割脚、忌当门直射。
   · 井  ：水为财源，属水。宜居吉方（尤【天医】主财、【生气】主旺）；
            五行上居金/水方（金生水、水比和）井泉清旺，居离火方（水火相激）、
            居坤艮土方（土克水，井浊易淤）则次。忌当门冲、忌逼近灶（水火相射主目疾口舌）。
   · 厕  ：秽污至阴，宜压凶方使凶不为害；忌占吉方、忌当门（开门见厕退财）、忌居中宫。
   · 碓磨：动器属土，宜安凶方以动制煞；忌居中宫、忌压吉方、忌当门。
   · 畜栏：秽臊，宜置下手凶方；忌近门、近井、近灶。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.fengshui.yangzhai_sanyao import (
    GUA_NAME_NUM, GUA_NUM_NAME, GUA_NUM_DIR, GUA_WUXING,
    YOUNIAN_STAR, JI_STARS, XIONG_STARS,
    _to_gua_name, _younian_between, _group,
)
from core.constants import WUXING_SHENG, WUXING_KE

# ─────────────────────────────────────────────────────────────
# 六事（七事）元数据
#   prefers : "吉" 净旺之物宜吉方 / "凶" 秽动之物宜凶方（压煞）
#   center_taboo : 是否忌居中宫
#   in_sanyao    : 是否已于《阳宅三要》专论（门、灶），本module仅引其则
# ─────────────────────────────────────────────────────────────
LIUSHI_META: Dict[str, Dict[str, Any]] = {
    "门": {
        "nature": "纳气之口", "wuxing": None, "prefers": "吉",
        "center_taboo": False, "in_sanyao": True,
        "principle": "门为一宅纳气之口，宜开本宅吉方（生气/天医/延年），引旺纳福；详见三要门主局。",
    },
    "路": {
        "nature": "引气之脉", "wuxing": None, "prefers": "吉",
        "center_taboo": False, "in_sanyao": False,
        "principle": "来路宜从吉方蜿蜒而来，引旺气入宅；忌凶方直冲、反弓割脚、当门直射。",
    },
    "井": {
        "nature": "水财之源", "wuxing": "水", "prefers": "吉",
        "center_taboo": True, "in_sanyao": False,
        "principle": "井为水财之源，宜居吉方（尤天医主财、生气主旺）；忌当门冲、忌逼近灶（水火相射）、忌居中宫。",
    },
    "灶": {
        "nature": "养命之火", "wuxing": "火", "prefers": "凶",
        "center_taboo": True, "in_sanyao": True,
        "principle": "灶宜坐煞向吉——灶座压凶方、灶口向吉方；详见三要灶座灶口。",
    },
    "厕": {
        "nature": "秽污至阴", "wuxing": "水", "prefers": "凶",
        "center_taboo": True, "in_sanyao": False,
        "principle": "厕为秽污，宜压凶方使凶不为害；忌占吉方、忌当门（开门见厕退财）、忌居中宫（秽攻心主百病）。",
    },
    "碓磨": {
        "nature": "动器属土", "wuxing": "土", "prefers": "凶",
        "center_taboo": True, "in_sanyao": False,
        "principle": "碓磨为动器，宜安凶方以动制煞；忌居中宫（震宅心）、忌压吉方、忌当门。",
    },
    "畜栏": {
        "nature": "秽臊之所", "wuxing": "土", "prefers": "凶",
        "center_taboo": True, "in_sanyao": False,
        "principle": "畜栏秽臊，宜置下手凶方；忌近门、近井、近灶。",
    },
}

# 六事别名归一
_ITEM_ALIAS: Dict[str, str] = {
    "门": "门", "大门": "门", "门户": "门",
    "路": "路", "来路": "路", "道路": "路", "马路": "路",
    "井": "井", "水井": "井", "水池": "井", "鱼池": "井",
    "灶": "灶", "厨": "灶", "厨房": "灶", "灶台": "灶",
    "厕": "厕", "厕所": "厕", "卫生间": "厕", "洗手间": "厕", "茅厕": "厕",
    "碓磨": "碓磨", "碓": "碓磨", "磨": "碓磨", "石磨": "碓磨", "磨坊": "碓磨",
    "畜栏": "畜栏", "畜": "畜栏", "牲畜栏": "畜栏", "猪圈": "畜栏", "栏": "畜栏",
}

# 中宫别名（位置输入为"中/中宫/太极"判为居中）
_CENTER_TOKENS = {"中", "中宫", "中心", "太极", "皇极", "宅心"}


def _wx_rel_brief(a: str, b: str) -> str:
    """a 物五行 对 b 方位五行 的生克简述（用于井之五行宜忌）。"""
    if not a or not b:
        return ""
    if a == b:
        return f"{a}比和"
    if WUXING_SHENG.get(b) == a:
        return f"{b}生{a}"        # 方生物
    if WUXING_SHENG.get(a) == b:
        return f"{a}生{b}"        # 物生方（泄）
    if WUXING_KE.get(b) == a:
        return f"{b}克{a}"        # 方克物
    if WUXING_KE.get(a) == b:
        return f"{a}克{b}"        # 物克方
    return ""


def analyze_one_item(men_gua: str, item: str, place: str) -> Dict[str, Any]:
    """
    断一事之安置吉凶。

    men_gua : 门卦（本宅以门定吉凶方，与三要一致）
    item    : 事名（门/路/井/灶/厕/碓磨/畜栏，含别名）
    place   : 安置方位（卦名/八方位/二十四山/洛书数），或"中宫"
    """
    norm_item = _ITEM_ALIAS.get(str(item).strip())
    if norm_item is None:
        return {"success": False, "error": f"未知六事项：{item}"}
    meta = LIUSHI_META[norm_item]
    men_g = _to_gua_name(men_gua)
    if not men_g:
        return {"success": False, "error": f"门卦无法识别：{men_gua}"}

    place_str = str(place).strip()

    # ── 中宫情形 ──
    if place_str in _CENTER_TOKENS:
        if meta["center_taboo"]:
            return {
                "success": True, "item": norm_item, "place": "中宫",
                "younian": None, "quality": "凶", "is_auspicious": False,
                "judgment": (f"{norm_item}居中宫（皇极）：大忌。"
                             + ("秽气攻心、主百病暗损、家运不彰；" if meta["prefers"] == "凶"
                                else "")
                             + "中宫为一宅太极所钟，"
                             + ("秽动之物" if meta["prefers"] == "凶" else "此物")
                             + "居之则伤宅气，宜亟迁出中宫。"),
                "warnings": ["居中宫为大忌"],
            }
        return {
            "success": True, "item": norm_item, "place": "中宫",
            "younian": None, "quality": "平", "is_auspicious": False,
            "judgment": f"{norm_item}居中宫：{meta['principle']}",
            "warnings": [],
        }

    place_g = _to_gua_name(place_str)
    if not place_g:
        return {"success": False, "error": f"安置方位无法识别：{place}"}

    star = _younian_between(men_g, place_g)
    star_info = YOUNIAN_STAR[star]
    in_ji = star in JI_STARS
    direction = GUA_NUM_DIR[GUA_NAME_NUM[place_g]]
    prefers = meta["prefers"]

    # ── 吉凶判定（按 净者宜吉方 / 秽者宜凶方）──
    if prefers == "吉":
        is_good = in_ji
        if is_good:
            verdict = (f"安于{place_g}（{direction}方）得【{star}】，正合"
                       f"{norm_item}宜居吉方之则：{star_info['duan']}。")
            quality = "吉"
        else:
            verdict = (f"安于{place_g}（{direction}方）犯【{star}】，"
                       f"{norm_item}为{meta['nature']}、宜居吉方而误落凶方，"
                       f"吉物失位、反纳凶气，主不利。")
            quality = "凶"
    else:  # prefers == "凶"：秽动之物，压凶方为合用
        is_good = (star in XIONG_STARS)
        if is_good:
            verdict = (f"安于{place_g}（{direction}方）压【{star}】，正合"
                       f"{norm_item}宜镇凶方之则：以秽（动）压煞，凶不为害，得用。")
            quality = "吉"
        else:
            verdict = (f"安于{place_g}（{direction}方）占【{star}】吉方，"
                       f"{norm_item}为{meta['nature']}、宜压凶方而误占吉方，"
                       f"污秽（扰动）吉气、损丁破财，宜迁。")
            quality = "凶"

    # ── 专则附断（五行/相冲）──
    extra: List[str] = []
    if norm_item == "井" and meta["wuxing"]:
        place_wx = GUA_WUXING.get(place_g, "")
        rel = _wx_rel_brief(meta["wuxing"], place_wx)
        if place_wx in ("金", "水"):
            extra.append(f"井属水，居{place_g}（{place_wx}方·{rel}）：井泉清旺。")
        elif place_wx == "火":
            extra.append(f"井属水，居{place_g}（火方·水火相激）：井气次，宜远灶。")
        elif place_wx == "土":
            extra.append(f"井属水，居{place_g}（土方·土克水）：井水易浊淤，宜常浚。")

    return {
        "success": True,
        "item": norm_item,
        "nature": meta["nature"],
        "place": place_g,
        "direction": direction,
        "younian": star,
        "jiuxing": star_info["jiuxing"],
        "level": star_info["level"],
        "prefers": prefers,
        "quality": quality,
        "is_auspicious": (quality == "吉"),
        "principle": meta["principle"],
        "judgment": verdict + ("".join("　" + e for e in extra) if extra else ""),
        "extra": extra,
    }


def liushi_best_positions(men_gua: str) -> Dict[str, Any]:
    """
    给定门卦，列出六事各自的"宜方/忌方"——
    净物列吉方，秽物列凶方，供安置择吉。
    """
    men_g = _to_gua_name(men_gua)
    if not men_g:
        return {"success": False, "error": f"门卦无法识别：{men_gua}"}

    # 门八方游年
    star_by_gua = {g: _younian_between(men_g, g) for g in GUA_NAME_NUM}
    ji_dirs = [(g, GUA_NUM_DIR[GUA_NAME_NUM[g]], s)
               for g, s in star_by_gua.items() if s in JI_STARS]
    xiong_dirs = [(g, GUA_NUM_DIR[GUA_NAME_NUM[g]], s)
                  for g, s in star_by_gua.items() if s in XIONG_STARS]

    def _fmt(lst):
        return [{"gua": g, "direction": d, "younian": s} for g, d, s in lst]

    items: Dict[str, Any] = {}
    for name, meta in LIUSHI_META.items():
        if meta["prefers"] == "吉":
            yi, ji = _fmt(ji_dirs), _fmt(xiong_dirs)
            tip = f"{name}宜安吉方（" + "、".join(
                f"{x['gua']}{x['direction']}·{x['younian']}" for x in yi) + "）。"
        else:
            yi, ji = _fmt(xiong_dirs), _fmt(ji_dirs)
            tip = f"{name}宜镇凶方（" + "、".join(
                f"{x['gua']}{x['direction']}·{x['younian']}" for x in yi) + "），忌占吉方。"
        items[name] = {
            "nature": meta["nature"],
            "prefers": meta["prefers"],
            "center_taboo": meta["center_taboo"],
            "recommend": yi,
            "avoid": ji,
            "principle": meta["principle"],
            "tip": tip,
        }

    return {
        "success": True,
        "men": men_g,
        "men_group": _group(men_g) + "卦宅",
        "items": items,
        "general": LIUSHI_GENERAL,
    }


def analyze_liushi(men_gua: str, placements: Dict[str, str]) -> Dict[str, Any]:
    """
    六事综合断：给定门卦与各事安置方位，逐项断吉凶，并出形理交互警示与总评。

    placements: { "井": "巽", "厕": "艮", "碓磨": "乾", "路": "震" … }
                方位可为卦名/八方位/二十四山/洛书数，或"中宫"。
    """
    men_g = _to_gua_name(men_gua)
    if not men_g:
        return {"success": False, "error": f"门卦无法识别：{men_gua}"}
    if not placements:
        return {"success": False, "error": "未提供任何六事安置"}

    results: List[Dict[str, Any]] = []
    norm_places: Dict[str, str] = {}     # 归一项名 → 卦名(或'中宫')
    for raw_item, place in placements.items():
        one = analyze_one_item(men_g, raw_item, place)
        results.append(one)
        if one.get("success"):
            norm_places[one["item"]] = one["place"]

    # ── 形理交互警示（相冲/相射/相邻）──
    warnings: List[str] = []
    door_gua = men_g  # 门即在门卦方
    # 当门冲：井/厕/路 与门同方或对宫
    opposite = {  # 八卦对宫
        "坎": "离", "离": "坎", "震": "兑", "兑": "震",
        "巽": "乾", "乾": "巽", "艮": "坤", "坤": "艮",
    }
    for it in ("井", "厕"):
        if it in norm_places and norm_places[it] != "中宫":
            pg = norm_places[it]
            if pg == door_gua:
                warnings.append(f"{it}与门同处{pg}方，犯『{it}当门』——"
                                + ("开门见厕、退财不聚。" if it == "厕" else "井口冲门、气漏。"))
            elif opposite.get(door_gua) == pg:
                warnings.append(f"{it}在门之对宫（{pg}方），与门相照，宜屏蔽化解。")
    # 井近灶：水火相射（同方或相邻方简化为同卦判）
    if "井" in norm_places and "灶" in norm_places:
        if norm_places["井"] == norm_places["灶"] and norm_places["井"] != "中宫":
            warnings.append("井灶同方，水火相射，主目疾、口舌、夫妻不和，宜分隔。")
    # 畜栏近门/近井/近灶
    if "畜栏" in norm_places and norm_places["畜栏"] != "中宫":
        cg = norm_places["畜栏"]
        for other, label in (("门", "门"), ("井", "井"), ("灶", "灶")):
            if other == "门":
                clash = (cg == door_gua)
            else:
                clash = (other in norm_places and norm_places[other] == cg
                         and norm_places[other] != "中宫")
            if clash:
                warnings.append(f"畜栏近{label}（同处{cg}方），秽臊冲{label}，宜远置下手。")

    ok = [r for r in results if r.get("success")]
    good = sum(1 for r in ok if r.get("quality") == "吉")
    bad = sum(1 for r in ok if r.get("quality") == "凶")
    n = len(ok)
    if n == 0:
        return {"success": False, "error": "六事项全部无法识别"}

    if bad == 0 and not warnings:
        grade = "六事俱合"
        summary = "净物居吉、秽物压凶，各得其位，六事无破，主家宅安宁、丁财顺遂。"
    elif good >= bad and bad <= 1 and len(warnings) <= 1:
        grade = "六事大体合度"
        summary = "六事大体得位，惟个别项或形理稍有瑕疵，依下列警示微调即全其吉。"
    elif bad > good:
        grade = "六事多有失位"
        summary = "净秽错置、吉凶倒位者多，主暗耗丁财、是非疾病，宜按各项宜方逐一迁正。"
    else:
        grade = "六事吉凶参半"
        summary = "六事得失相参，平稳之中藏小患，先正失位之秽物、再化形理之冲射。"

    return {
        "success": True,
        "method": "《阳宅十书·论六事》大游年安置断（净者居吉方·秽者镇凶方）",
        "men": men_g,
        "men_group": _group(men_g) + "卦宅",
        "items": results,
        "interaction_warnings": warnings,
        "good_count": good,
        "bad_count": bad,
        "grade": grade,
        "summary": summary,
        "general": LIUSHI_GENERAL,
    }


# ── 六事总则文案 ──
LIUSHI_GENERAL: Dict[str, str] = {
    "principle": "净者居吉方，秽者镇凶方。",
    "detail": (
        "《阳宅十书》以门、路、井、灶、碓磨、厕、畜栏为六事（连门主曰七事）。"
        "门、来路、井等净旺之物宜安宅之吉方（生气/天医/延年），引旺纳财；"
        "灶座、厕、碓磨、畜栏等秽动之物宜压宅之凶方（祸害/六煞/五鬼/绝命），"
        "以秽压凶、以动制煞，凶不为害。灶独取『坐煞向吉』。"
        "井、厕、碓磨、畜栏皆忌居中宫，秽居皇极则攻心主病。"
    ),
}
