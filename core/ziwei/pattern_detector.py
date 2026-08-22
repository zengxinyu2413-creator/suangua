"""
core/ziwei/pattern_detector.py
================================
紫微斗数经典格局自动检测引擎（Z-4）。

实现 15 个吉格 + 8 个凶格的精确成格条件检测。所有规则均来源于多源权威
（紫微斗数全书、神机阁、令东来、紫微取象派、查查起名网 等）校对。

设计原则：
  · 命理界对同一格局的成格条件经常有"严格版"和"宽松版"，本模块统一取
    宽松版判定（成格），同时记录"破格条件"作为额外标签
  · 不主观判定富贵等级，只标识"成格 + 命理含义"
  · 检测结果均含【成格条件验证】列表，让 LLM 能引用具体的星耀作为依据
  · 与 brightness.py 协作：很多格局依赖庙旺判定（如"日月并明"要求太阳太阴
    都庙旺），我们调用 brightness.py 的工具函数

依赖：
  · core.ziwei.context_builder.find_soul_palace / get_san_fang_si_zheng
  · core.ziwei.brightness.is_brightness_sensitive
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple


# ─────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────

FOURTEEN_MAJOR: Set[str] = {
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
}

SIX_JI:  Set[str] = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺"}
SIX_SHA: Set[str] = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}

# 太阳庙旺地支（卯/辰/巳/午为庙旺，子/亥/戌/酉为陷）
TAIYANG_MIAOWANG_BRANCHES: Set[str] = {"卯", "辰", "巳", "午"}
TAIYANG_LUOXIAN_BRANCHES:  Set[str] = {"申", "酉", "戌", "亥", "子"}

# 太阴庙旺地支（酉/戌/亥/子为庙旺）
TAIYIN_MIAOWANG_BRANCHES:  Set[str] = {"酉", "戌", "亥", "子"}
TAIYIN_LUOXIAN_BRANCHES:   Set[str] = {"卯", "辰", "巳", "午"}


# ─────────────────────────────────────────────────────────────
# 通用辅助
# ─────────────────────────────────────────────────────────────

def _star_name(s: Any) -> str:
    if isinstance(s, dict):
        return s.get("name", "")
    return str(s) if s else ""


def _star_brightness(s: Any) -> str:
    if isinstance(s, dict):
        return s.get("brightness", "")
    return ""


def _star_mutagen(s: Any) -> str:
    if isinstance(s, dict):
        return s.get("mutagen", "")
    return ""


def _all_stars_in_palace(palace: Dict[str, Any]) -> List[Dict[str, Any]]:
    """返回该宫的所有星耀（major+minor+adj 合并）。"""
    result = []
    for key in ("major_stars", "minor_stars", "adj_stars"):
        for s in (palace.get(key) or []):
            if isinstance(s, dict):
                result.append(s)
    return result


def _palace_has_star(palace: Dict[str, Any], star_name: str) -> bool:
    """该宫是否有某星。"""
    for s in _all_stars_in_palace(palace):
        if _star_name(s) == star_name:
            return True
    return False


def _palace_has_any_star(palace: Dict[str, Any], star_names: Set[str]) -> List[str]:
    """该宫包含集合中哪些星 — 返回名字列表。"""
    found = []
    for s in _all_stars_in_palace(palace):
        nm = _star_name(s)
        if nm in star_names:
            found.append(nm)
    return found


def _by_index(palaces: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {p.get("index", -1): p for p in palaces}


def _opp_idx(idx: int) -> int:
    return (idx + 6) % 12


def _adjacent_indices(idx: int) -> Tuple[int, int]:
    """返回该宫两邻宫 index（前一个、后一个）"""
    return ((idx - 1) % 12, (idx + 1) % 12)


def _san_fang_si_zheng_indices(soul_idx: int) -> List[int]:
    """三方四正 4 宫的 index 列表（本/三合+4/三合+8/对宫+6）。"""
    return [soul_idx, (soul_idx + 4) % 12, (soul_idx + 8) % 12, (soul_idx + 6) % 12]


def _collect_stars_in_palaces(
    palaces: List[Dict[str, Any]],
    indices: List[int],
) -> Dict[str, str]:
    """收集这些宫中所有星，返回 {星名: 所在宫名} 映射。"""
    by_idx = _by_index(palaces)
    result: Dict[str, str] = {}
    for i in indices:
        p = by_idx.get(i)
        if not p:
            continue
        p_name = p.get("name", "")
        for s in _all_stars_in_palace(p):
            nm = _star_name(s)
            if nm and nm not in result:
                result[nm] = p_name
    return result


def _find_soul_palace(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """优先用 is_soul 标志，退而求其次按 name=='命宫'。"""
    for p in palaces:
        if p.get("is_soul"):
            return p
    for p in palaces:
        if p.get("name") == "命宫":
            return p
    return None


# ─────────────────────────────────────────────────────────────
# 单个格局检测函数
# 每个函数返回 dict 或 None：
#   {"name": str, "category": "吉格"/"凶格", "evidence": [str], "meaning": str, "破格条件": [str]}
# ─────────────────────────────────────────────────────────────

# ════════════════════════════════════════════════
# 吉格 G1: 紫府同宫格
# ════════════════════════════════════════════════
def detect_zifu_tonggong(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    紫府同宫格：命宫在寅或申，且紫微+天府同坐命宫。
    （紫微+天府仅在寅/申宫同坐）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"寅", "申"}:
        return None
    if not _palace_has_star(soul, "紫微"):
        return None
    if not _palace_has_star(soul, "天府"):
        return None
    
    return {
        "name": "紫府同宫格",
        "category": "吉格",
        "evidence": [
            f"命宫在{soul.get('earthly_branch')}宫",
            "紫微+天府同坐命宫",
        ],
        "meaning": "终身福厚，主大富大贵；甲己年生人最佳。紫微为君、天府为库，等同有库的帝王",
        "break_conditions": [
            "命宫三方四正若见空劫，则为'露库'，外光鲜实空乏",
            "命宫煞星多，则降为'奴欺主'平常之命",
        ],
    }


# ════════════════════════════════════════════════
# 吉格 G2: 君臣庆会格
# ════════════════════════════════════════════════
def detect_junchen_qinghui(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    君臣庆会格：命宫有紫微，三方四正会照天府/天相/左辅/右弼/文昌/文曲，无煞冲破。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if not _palace_has_star(soul, "紫微"):
        return None
    
    soul_idx = soul.get("index", -1)
    sfsz_indices = _san_fang_si_zheng_indices(soul_idx)
    by_idx = _by_index(palaces)
    
    # 收集三方四正中的星
    chen_stars: List[str] = []  # 找到的"臣"
    sha_stars: List[str] = []   # 煞星
    
    target_chen_stars = {"天府", "天相", "左辅", "右弼", "文昌", "文曲"}
    
    for i in sfsz_indices:
        p = by_idx.get(i)
        if not p:
            continue
        for s in _all_stars_in_palace(p):
            nm = _star_name(s)
            if nm in target_chen_stars and nm not in chen_stars:
                chen_stars.append(nm)
            if nm in SIX_SHA:
                sha_stars.append(nm)
    
    # 至少 3 颗"臣"
    if len(chen_stars) < 3:
        return None
    
    has_sha = bool(sha_stars)
    return {
        "name": "君臣庆会格",
        "category": "吉格",
        "evidence": [
            f"命宫坐紫微（{soul.get('earthly_branch')}宫）",
            f"三方四正会齐 {len(chen_stars)} 颗辅佐星：{ '、'.join(chen_stars) }",
            "无煞冲破" if not has_sha else f"⚠ 但有煞星 {'、'.join(set(sha_stars))} 冲破，转为'奴欺主'，破格",
        ],
        "meaning": "紫微为君，府相昌曲为臣；不大贵即当大富。但若见空劫煞忌则反主祸乱",
        "break_conditions": [
            "见四煞空劫忌则反为'奴欺主，臣蔽君'败局",
        ] if not has_sha else ["此盘已见煞，格局减分"],
        "is_partial": has_sha,
    }


# ════════════════════════════════════════════════
# 吉格 G3: 府相朝垣格
# ════════════════════════════════════════════════
def detect_fuxiang_chaoyuan(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    府相朝垣格：天府在财帛宫、天相在官禄宫（或互换）会照命宫，无煞冲破。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    
    soul_idx = soul.get("index", -1)
    by_idx = _by_index(palaces)
    
    # 财帛宫是 soul_idx+8，官禄宫是 soul_idx+4（按三方）
    # 注意：在 12 宫顺序中财官的实际宫位需查 palace.name
    caibao = None
    guanlu = None
    for p in palaces:
        if p.get("name") == "财帛宫":
            caibao = p
        elif p.get("name") == "官禄宫":
            guanlu = p
    
    if not caibao or not guanlu:
        return None
    
    fu_in_cb = _palace_has_star(caibao, "天府")
    xiang_in_cb = _palace_has_star(caibao, "天相")
    fu_in_gl = _palace_has_star(guanlu, "天府")
    xiang_in_gl = _palace_has_star(guanlu, "天相")
    
    # 府相分占财官（含互换）
    if not ((fu_in_cb and xiang_in_gl) or (fu_in_gl and xiang_in_cb)):
        return None
    
    # 检查煞
    sfsz_indices = _san_fang_si_zheng_indices(soul_idx)
    sha_found = []
    for i in sfsz_indices:
        p = by_idx.get(i)
        if not p:
            continue
        for s in _all_stars_in_palace(p):
            if _star_name(s) in SIX_SHA:
                sha_found.append(_star_name(s))
    
    fu_loc = "财帛" if fu_in_cb else "官禄"
    xiang_loc = "官禄" if fu_in_cb else "财帛"
    
    return {
        "name": "府相朝垣格",
        "category": "吉格",
        "evidence": [
            f"天府坐{fu_loc}宫",
            f"天相坐{xiang_loc}宫",
            "两者会照命宫" + ("（无煞）" if not sha_found else f"，但有煞{ '、'.join(set(sha_found)) }"),
        ],
        "meaning": "府相为衣禄之神，主富贵双全、入仕亨通；适合做公司高管、从政；继承祖业",
        "break_conditions": [
            "煞星冲破则降为平常",
        ],
        "is_partial": bool(sha_found),
    }


# ════════════════════════════════════════════════
# 吉格 G4: 七杀朝斗格
# ════════════════════════════════════════════════
def detect_qisha_chaodou(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    七杀朝斗格：七杀在寅或申宫坐命，对宫紫微天府。
    （寅称仰斗，申称朝斗）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"寅", "申"}:
        return None
    if not _palace_has_star(soul, "七杀"):
        return None
    
    # 对宫应有紫微天府
    opp_idx = _opp_idx(soul.get("index", 0))
    opp = _by_index(palaces).get(opp_idx)
    if not opp:
        return None
    has_ziwei = _palace_has_star(opp, "紫微")
    has_tianfu = _palace_has_star(opp, "天府")
    if not (has_ziwei and has_tianfu):
        return None
    
    name_subtype = "仰斗" if soul.get("earthly_branch") == "寅" else "朝斗"
    return {
        "name": f"七杀朝斗格（{name_subtype}）",
        "category": "吉格",
        "evidence": [
            f"七杀坐命于{soul.get('earthly_branch')}宫",
            "对宫紫微+天府来朝",
        ],
        "meaning": "武职显贵，统领百万；现代多为公司创始人、商界英才。化杀为权，必有大成",
        "break_conditions": [
            "煞星冲破则降为平常之命",
            "无吉星扶持则一生孤辛",
        ],
    }


# ════════════════════════════════════════════════
# 吉格 G5: 杀破狼格
# ════════════════════════════════════════════════
def detect_shapolang(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    杀破狼格：命/财/官三方会齐七杀+破军+贪狼。
    （按紫微星系排盘规律，七杀+破军+贪狼必三合）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    soul_idx = soul.get("index", -1)
    # 命财官三方（不含对宫）
    sfsz_indices = [soul_idx, (soul_idx + 4) % 12, (soul_idx + 8) % 12]
    stars_map = _collect_stars_in_palaces(palaces, sfsz_indices)
    
    has_qisha = "七杀" in stars_map
    has_pojun = "破军" in stars_map
    has_tanlang = "贪狼" in stars_map
    
    if not (has_qisha and has_pojun and has_tanlang):
        return None
    
    return {
        "name": "杀破狼格",
        "category": "吉格",
        "evidence": [
            f"七杀坐{stars_map['七杀']}",
            f"破军坐{stars_map['破军']}",
            f"贪狼坐{stars_map['贪狼']}",
            "命财官三合会齐",
        ],
        "meaning": "易动不易静，一生变动大；做事爱走捷径、不安于现状；适合创业、开拓；需大限运势配合方有大成",
        "break_conditions": [
            "煞星冲破则一生辛劳无成",
            "煞星过多则成败起伏剧烈",
        ],
    }


# ════════════════════════════════════════════════
# 吉格 G6: 机月同梁格
# ════════════════════════════════════════════════
def detect_jiyue_tongliang(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    机月同梁格（公务员格）：
    
    古书定义：命/财/官三方四正会齐天机+太阴+天同+天梁四星（或至少 3 颗，无煞）。
    
    现行紫云派/正统派通说：四颗会齐方为正格，三颗为偏格。
    要求四颗都不落陷（陷地者格局减色）。
    
    本实现采用：至少 3 颗会照（含命宫见星），<3 颗不成格。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    soul_idx = soul.get("index", -1)
    # 命/财/官三方（不含对宫；对宫是迁移宫，对机月同梁来说不算）
    sfsz_indices = [soul_idx, (soul_idx + 4) % 12, (soul_idx + 8) % 12]
    
    by_idx = _by_index(palaces)
    
    target = {"天机", "太阴", "天同", "天梁"}
    found_with_brightness: Dict[str, Dict[str, str]] = {}
    
    for i in sfsz_indices:
        p = by_idx.get(i)
        if not p:
            continue
        for s in _all_stars_in_palace(p):
            nm = _star_name(s)
            if nm in target and nm not in found_with_brightness:
                found_with_brightness[nm] = {
                    "palace": p.get("name", ""),
                    "brightness": _star_brightness(s),
                }
    
    # 至少 3 颗才成格（古书标准）
    if len(found_with_brightness) < 3:
        return None
    
    is_full = len(found_with_brightness) == 4
    # 检查是否有落陷
    fallen = [nm for nm, info in found_with_brightness.items()
              if info["brightness"] in {"陷", "不"}]
    
    return {
        "name": "机月同梁格",
        "category": "吉格",
        "evidence": [
            f"命财官三方会齐 {len(found_with_brightness)}/4 颗（{'正格' if is_full else '偏格'}）：" + 
            "、".join(f"{nm}@{info['palace']}({info['brightness'] or '无亮度'})"
                     for nm, info in found_with_brightness.items())
        ],
        "meaning": "公务员格，按部就班、中正平和；适合教师、研究、行政、文职；不宜创业",
        "break_conditions": (
            ["四星齐会方为正格"] if not is_full else []
        ) + (
            [f"⚠ {'、'.join(fallen)} 落陷，格局减色"] if fallen else []
        ) + ["煞星过多则成格不显"],
        "is_partial": (not is_full) or bool(fallen),
    }


# ════════════════════════════════════════════════
# 吉格 G7: 日月并明格
# ════════════════════════════════════════════════
def detect_riyue_bingming(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    日月并明格：太阳庙旺（在卯/辰/巳/午），太阴庙旺（在酉/戌/亥/子），同时存在。
    """
    sun_palace = None
    moon_palace = None
    sun_bright = ""
    moon_bright = ""
    
    for p in palaces:
        for s in _all_stars_in_palace(p):
            nm = _star_name(s)
            if nm == "太阳":
                sun_palace = p
                sun_bright = _star_brightness(s)
            elif nm == "太阴":
                moon_palace = p
                moon_bright = _star_brightness(s)
    
    if not sun_palace or not moon_palace:
        return None
    
    sun_in_miao = (
        sun_palace.get("earthly_branch") in TAIYANG_MIAOWANG_BRANCHES
        or sun_bright in {"庙", "旺"}
    )
    moon_in_miao = (
        moon_palace.get("earthly_branch") in TAIYIN_MIAOWANG_BRANCHES
        or moon_bright in {"庙", "旺"}
    )
    
    if not (sun_in_miao and moon_in_miao):
        return None
    
    return {
        "name": "日月并明格",
        "category": "吉格",
        "evidence": [
            f"太阳在{sun_palace.get('name','')}（{sun_palace.get('earthly_branch','')}宫）{sun_bright}",
            f"太阴在{moon_palace.get('name','')}（{moon_palace.get('earthly_branch','')}宫）{moon_bright}",
            "两大中天主星皆庙旺",
        ],
        "meaning": "富贵双全，先天命格优异；男命旺事业，女命旺夫益子；六亲缘佳",
        "break_conditions": [
            "若两星都化忌则减格",
        ],
    }


# ════════════════════════════════════════════════
# 吉格 G8: 明珠出海格
# ════════════════════════════════════════════════
def detect_mingzhu_chuhai(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    明珠出海格：命宫在未空宫，对宫迁移宫天同+巨门，官禄宫太阴庙旺亥，
    财帛宫太阳+天梁卯。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") != "未":
        return None
    # 命宫空宫
    soul_majors = [_star_name(s) for s in (soul.get("major_stars") or [])]
    if any(nm in FOURTEEN_MAJOR for nm in soul_majors):
        return None
    
    # 迁移宫（对宫）— 命未宫，对宫为丑
    opp = _by_index(palaces).get(_opp_idx(soul.get("index", 0)))
    if not opp:
        return None
    if not (_palace_has_star(opp, "天同") and _palace_has_star(opp, "巨门")):
        return None
    
    # 官禄宫太阴在亥
    guanlu = None
    caibao = None
    for p in palaces:
        if p.get("name") == "官禄宫":
            guanlu = p
        elif p.get("name") == "财帛宫":
            caibao = p
    if not guanlu or not caibao:
        return None
    if guanlu.get("earthly_branch") != "亥":
        return None
    if not _palace_has_star(guanlu, "太阴"):
        return None
    if caibao.get("earthly_branch") != "卯":
        return None
    if not (_palace_has_star(caibao, "太阳") and _palace_has_star(caibao, "天梁")):
        return None
    
    return {
        "name": "明珠出海格",
        "category": "吉格",
        "evidence": [
            "命宫在未空宫",
            "迁移宫（丑）有天同+巨门",
            "官禄宫太阴@亥（庙旺）",
            "财帛宫太阳+天梁@卯",
        ],
        "meaning": "财官双美、声名远播；适合文艺类工作，易出名；借宫看而成大局",
        "break_conditions": ["煞星冲破则减格"],
    }


# ════════════════════════════════════════════════
# 吉格 G9: 石中隐玉格
# ════════════════════════════════════════════════
def detect_shizhong_yinyu(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    石中隐玉格：巨门坐命在子或午宫。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"子", "午"}:
        return None
    if not _palace_has_star(soul, "巨门"):
        return None
    
    return {
        "name": "石中隐玉格",
        "category": "吉格",
        "evidence": [
            f"巨门坐命于{soul.get('earthly_branch')}宫",
            f"子宫者与禄存同度（必），力量较午宫强",
        ],
        "meaning": "才华内敛、因辞惊众；适合演讲、外交、教学；一生需取得表现机会方有大成",
        "break_conditions": ["午宫者不如子宫"],
    }


# ════════════════════════════════════════════════
# 吉格 G10: 马头带箭格
# ════════════════════════════════════════════════
def detect_matou_daijian(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    马头带箭格：擎羊在午宫坐命（贪狼/天同/太阴都可成立），三方无杀冲。
    （古名"马头带剑"也通用）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") != "午":
        return None
    # 命宫有擎羊
    if not _palace_has_star(soul, "擎羊"):
        return None
    
    # 命宫主星（贪狼/天同/太阴更典型）
    main_star_candidates = ["贪狼", "天同", "太阴"]
    main_at_soul = [
        nm for nm in main_star_candidates
        if _palace_has_star(soul, nm)
    ]
    
    return {
        "name": "马头带箭格",
        "category": "吉格",
        "evidence": [
            "擎羊坐命于午宫",
            f"命宫主星：{ '/'.join(main_at_soul) }" if main_at_soul else "命宫无典型主星",
        ],
        "meaning": "威权出众，边疆立功；现代多为军警、行业开拓者、独当一面；做事冲锋陷阵",
        "break_conditions": [
            "三方四正若多杀则减为平常",
            "需三方有禄存或化禄稳定方为大成",
        ],
    }


# ════════════════════════════════════════════════
# 吉格 G11: 日照雷门格
# ════════════════════════════════════════════════
def detect_rizhao_leimen(
    palaces: List[Dict[str, Any]],
    birth_hour_index: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    日照雷门格：太阳+天梁同坐卯宫为命宫，昼生人为佳。
    （birth_hour_index 0-11，3-9 为白天 = 卯辰巳午未申）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") != "卯":
        return None
    if not (_palace_has_star(soul, "太阳") and _palace_has_star(soul, "天梁")):
        return None
    
    is_day_birth = None
    if birth_hour_index is not None:
        # iztro_py 中 birth_hour_index 0=子 1=丑 2=寅 3=卯 ... 11=亥
        # 白天为 卯-申 (index 3-8)
        is_day_birth = 3 <= birth_hour_index <= 8
    
    evidence = [
        "太阳+天梁同坐命于卯宫",
    ]
    if is_day_birth is True:
        evidence.append("昼生人 — 上格")
    elif is_day_birth is False:
        evidence.append("⚠ 夜生人 — 格局减半")
    
    return {
        "name": "日照雷门格",
        "category": "吉格",
        "evidence": evidence,
        "meaning": "富贵声扬，太阳照亮天梁的孤；昼生人最吉，主大贵；一生光明磊落",
        "break_conditions": [
            "夜生人则减为中等",
            "见煞则减格",
        ],
        "is_partial": is_day_birth is False,
    }


# ════════════════════════════════════════════════
# 吉格 G12: 月朗天门格
# ════════════════════════════════════════════════
def detect_yuelang_tianmen(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    月朗天门格：太阴在亥宫坐命 + 庙旺。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") != "亥":
        return None
    if not _palace_has_star(soul, "太阴"):
        return None
    
    # 亮度检查
    moon_bright = ""
    for s in (soul.get("major_stars") or []):
        if _star_name(s) == "太阴":
            moon_bright = _star_brightness(s)
            break
    
    if moon_bright not in {"庙", "旺", "得"}:
        return None  # 亥宫太阴应庙旺
    
    return {
        "name": "月朗天门格",
        "category": "吉格",
        "evidence": [
            f"太阴坐命于亥宫（{moon_bright}）",
            "亥宫为天门，月光最盛",
        ],
        "meaning": "富贵之命，女命尤吉；秀气逼人、文艺天赋强；夜生人尤佳",
        "break_conditions": ["太阴化忌则减格"],
    }


# ════════════════════════════════════════════════
# 吉格 G13: 火贪格
# ════════════════════════════════════════════════
def detect_huotan(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    火贪格：命宫贪狼+火星同宫 + 贪狼庙旺方为正格。
    
    古书：贪狼为「暴发星」，得火星「催发」方主暴发。
    贪狼若落陷，则反主「暴起暴败」，不入吉格。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if not _palace_has_star(soul, "贪狼"):
        return None
    if not _palace_has_star(soul, "火星"):
        return None
    
    # 贪狼亮度（必须庙/旺/得 才成格）
    tanlang_bright = ""
    for s in (soul.get("major_stars") or []):
        if _star_name(s) == "贪狼":
            tanlang_bright = _star_brightness(s)
            break
    
    # 贪狼落陷 → 不成格
    if tanlang_bright in {"陷", "不", "平"}:
        return None
    
    is_full = tanlang_bright in {"庙", "旺"}
    
    return {
        "name": "火贪格",
        "category": "吉格",
        "evidence": [
            f"贪狼+火星同坐命宫（{soul.get('earthly_branch')}宫）",
            f"贪狼{tanlang_bright}（{'正格' if is_full else '偏格'}）",
        ],
        "meaning": "暴发资财、意外之财；从投机、赌博、突发机遇获利；适合金融、风投",
        "break_conditions": [
            "若再见擎羊陀罗冲破，则暴发暴败",
            "贪狼若落陷则不成格（已自动剔除）",
        ],
        "is_partial": not is_full,
    }


# ════════════════════════════════════════════════
# 吉格 G14: 铃贪格
# ════════════════════════════════════════════════
def detect_lingtan(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    铃贪格：命宫贪狼+铃星同宫 + 贪狼庙旺方为正格。
    
    比火贪更稳，发后能守。但贪狼落陷同样不成格。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if not _palace_has_star(soul, "贪狼"):
        return None
    if not _palace_has_star(soul, "铃星"):
        return None
    
    tanlang_bright = ""
    for s in (soul.get("major_stars") or []):
        if _star_name(s) == "贪狼":
            tanlang_bright = _star_brightness(s)
            break
    
    if tanlang_bright in {"陷", "不", "平"}:
        return None
    
    is_full = tanlang_bright in {"庙", "旺"}
    
    return {
        "name": "铃贪格",
        "category": "吉格",
        "evidence": [
            f"贪狼+铃星同坐命宫（{soul.get('earthly_branch')}宫）",
            f"贪狼{tanlang_bright}（{'正格' if is_full else '偏格'}）",
        ],
        "meaning": "同火贪，主暴发；但比火贪更稳，发后能守",
        "break_conditions": [
            "若再见擎羊陀罗冲破，则暴败",
            "贪狼若落陷则不成格（已自动剔除）",
        ],
        "is_partial": not is_full,
    }


# ════════════════════════════════════════════════
# 吉格 G15: 阳梁昌禄格
# ════════════════════════════════════════════════
def detect_yangliang_changlu(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    阳梁昌禄格：命宫三方四正会齐太阳+天梁+文昌+化禄(或禄存)。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    soul_idx = soul.get("index", -1)
    sfsz_indices = _san_fang_si_zheng_indices(soul_idx)
    
    by_idx = _by_index(palaces)
    has_sun = False
    has_liang = False
    has_chang = False
    has_lu = False    # 禄存 或 化禄
    locations = {}
    
    for i in sfsz_indices:
        p = by_idx.get(i)
        if not p:
            continue
        p_name = p.get("name", "")
        for s in _all_stars_in_palace(p):
            nm = _star_name(s)
            if nm == "太阳":
                has_sun = True
                locations["太阳"] = p_name
            elif nm == "天梁":
                has_liang = True
                locations["天梁"] = p_name
            elif nm == "文昌":
                has_chang = True
                locations["文昌"] = p_name
            elif nm == "禄存":
                has_lu = True
                locations["禄存"] = p_name
            elif _star_mutagen(s) == "禄":
                has_lu = True
                locations[f"{nm}化禄"] = p_name
    
    if not (has_sun and has_liang and has_chang and has_lu):
        return None
    
    return {
        "name": "阳梁昌禄格",
        "category": "吉格",
        "evidence": [
            f"太阳坐{locations.get('太阳','?')}",
            f"天梁坐{locations.get('天梁','?')}",
            f"文昌坐{locations.get('文昌','?')}",
            f"禄存/化禄：{', '.join(k for k in locations if '禄' in k)}",
            "命宫三方四正会齐",
        ],
        "meaning": "考运极佳，主大贵；最宜公务员考试、各类资格考试；先天聪颖，文学/学术天赋",
        "break_conditions": ["四星缺一则不成格", "煞星冲破则降为普通"],
    }


# ════════════════════════════════════════════════
# 凶格 B1: 羊陀夹忌格
# ════════════════════════════════════════════════
def detect_yangtuo_jiaji(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    羊陀夹忌格：禄存在命宫且命宫坐生年化忌
    （禄存前后必有擎羊陀罗，所以禄存所在宫永远被羊陀夹）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    
    has_lucun = _palace_has_star(soul, "禄存")
    if not has_lucun:
        return None
    
    # 命宫坐生年化忌？
    has_natal_ji = False
    ji_star = ""
    for s in _all_stars_in_palace(soul):
        if _star_mutagen(s) == "忌":
            has_natal_ji = True
            ji_star = _star_name(s)
            break
    
    if not has_natal_ji:
        return None
    
    return {
        "name": "羊陀夹忌格",
        "category": "凶格",
        "evidence": [
            "禄存坐命宫",
            f"命宫同时坐生年化忌（{ji_star}化忌）",
            "禄存前后必有擎羊陀罗，构成羊陀夹忌",
        ],
        "meaning": "败局，多灾多难；化忌之凶因羊陀之夹得以充分发挥；一生孤贫刑克；走在法律边缘的钱易招官司",
        "break_conditions": [
            "三奇嘉会（化禄权科齐会）或吉星多可解",
            "若有空劫则雪上加霜，如'半天折翼，浪里行舟'",
        ],
    }


# ════════════════════════════════════════════════
# 凶格 B2: 铃昌陀武格
# ════════════════════════════════════════════════
def detect_lingchang_tuowu(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    铃昌陀武格：铃星+文昌+陀罗+武曲同时会照命宫（三方四正）。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    soul_idx = soul.get("index", -1)
    sfsz_indices = _san_fang_si_zheng_indices(soul_idx)
    stars_map = _collect_stars_in_palaces(palaces, sfsz_indices)
    
    required = {"铃星", "文昌", "陀罗", "武曲"}
    if not required.issubset(set(stars_map.keys())):
        return None
    
    return {
        "name": "铃昌陀武格",
        "category": "凶格",
        "evidence": [
            f"铃星@{stars_map['铃星']}",
            f"文昌@{stars_map['文昌']}",
            f"陀罗@{stars_map['陀罗']}",
            f"武曲@{stars_map['武曲']}",
            "命宫三方四正同时会四星",
        ],
        "meaning": "主大凶，古书云'投河自缢'；现代多主严重意外、抑郁、健康危机；遇大限流年触发需谨防",
        "break_conditions": [
            "若有禄存/化禄强力解救，可降为'多波折'",
        ],
    }


# ════════════════════════════════════════════════
# 凶格 B3: 火铃夹命格
# ════════════════════════════════════════════════
def detect_huoling_jiaming(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    火铃夹命格：命宫两邻宫分别坐火星和铃星。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    soul_idx = soul.get("index", -1)
    prev_idx, next_idx = _adjacent_indices(soul_idx)
    
    by_idx = _by_index(palaces)
    prev_p = by_idx.get(prev_idx)
    next_p = by_idx.get(next_idx)
    if not prev_p or not next_p:
        return None
    
    # 火星在一邻、铃星在另一邻
    fire_prev = _palace_has_star(prev_p, "火星")
    fire_next = _palace_has_star(next_p, "火星")
    ling_prev = _palace_has_star(prev_p, "铃星")
    ling_next = _palace_has_star(next_p, "铃星")
    
    is_hl_jiaming = (fire_prev and ling_next) or (ling_prev and fire_next)
    if not is_hl_jiaming:
        return None
    
    fire_palace = prev_p.get("name", "?") if fire_prev else next_p.get("name", "?")
    ling_palace = next_p.get("name", "?") if ling_next else prev_p.get("name", "?")
    
    return {
        "name": "火铃夹命格",
        "category": "凶格",
        "evidence": [
            f"火星在{fire_palace}",
            f"铃星在{ling_palace}",
            "两邻宫夹命",
        ],
        "meaning": "败局，主多麻烦、急躁、命途多舛；吉多尚可，惟夹忌（命宫坐化忌）尤凶",
        "break_conditions": [
            "命宫三方四正多吉星可解",
        ],
    }


# ════════════════════════════════════════════════
# 凶格 B4: 巨火羊格
# ════════════════════════════════════════════════
def detect_juhuo_yang(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    巨火羊格：巨门+火星+擎羊同宫。
    （古云"巨火擎羊，终身缢死"）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if not _palace_has_star(soul, "巨门"):
        return None
    if not _palace_has_star(soul, "火星"):
        return None
    if not _palace_has_star(soul, "擎羊"):
        return None
    
    return {
        "name": "巨火羊格",
        "category": "凶格",
        "evidence": [
            f"巨门+火星+擎羊三星同坐命宫（{soul.get('earthly_branch')}宫）",
        ],
        "meaning": "古书列为极凶之格，主多忧虑、情绪起伏大、易遇意外。现代命理多主精神压力大、心理健康需特别留意；若从事高风险职业（消防、急救等），可化凶为用",
        "break_conditions": [
            "若巨门化禄或化权，则可化解部分凶象",
            "三方有禄存/化禄强力会照可解",
            "现代社会中此格更多警示，不可对号入座",
        ],
    }


# ════════════════════════════════════════════════
# 凶格 B5: 风流彩杖格
# ════════════════════════════════════════════════
def detect_fengliu_caizhang(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    风流彩杖格：贪狼在子宫独坐，同宫有擎羊或天刑。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") != "子":
        return None
    if not _palace_has_star(soul, "贪狼"):
        return None
    
    has_yang = _palace_has_star(soul, "擎羊")
    has_tianxing = _palace_has_star(soul, "天刑")
    
    if not (has_yang or has_tianxing):
        return None
    
    return {
        "name": "风流彩杖格",
        "category": "凶格",
        "evidence": [
            "贪狼坐命于子宫",
            f"同宫有 { '擎羊' if has_yang else '' }{'+' if has_yang and has_tianxing else ''}{ '天刑' if has_tianxing else '' }",
        ],
        "meaning": "因桃花生官非诉讼；男女易陷情欲纠纷；做事易因色坏事",
        "break_conditions": [
            "三方有禄存/化禄/空劫可空掉桃花力量，转向艺术工作",
        ],
    }


# ════════════════════════════════════════════════
# 凶格 B6: 泛水桃花格
# ════════════════════════════════════════════════
def detect_fanshui_taohua(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    泛水桃花格：贪狼坐命于亥或子宫（亥宫贪狼必与廉贞同宫）。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"亥", "子"}:
        return None
    if not _palace_has_star(soul, "贪狼"):
        return None
    
    # 检查同宫桃花/解破 星
    has_jiekong = _palace_has_star(soul, "地空") or _palace_has_star(soul, "地劫")
    has_lucun = _palace_has_star(soul, "禄存")
    
    if has_jiekong or has_lucun:
        # 桃花被空，反能习正
        return None
    
    return {
        "name": "泛水桃花格",
        "category": "凶格",
        "evidence": [
            f"贪狼坐命于{soul.get('earthly_branch')}宫（水乡）",
            "亥宫者必廉贞同宫，双桃花叠加" if soul.get("earthly_branch") == "亥" else "子宫癸水加强桃花",
            "无空劫、禄存解破",
        ],
        "meaning": "桃花太重，男女易陷情欲，无禄解则败；多主感情纠葛、滥交、感情破财",
        "break_conditions": [
            "三方四正有空劫则桃花被空，反能习正",
            "贪狼化禄/化权可转化桃花为才艺",
        ],
    }


# ════════════════════════════════════════════════
# 凶格 B7: 命无正曜格
# ════════════════════════════════════════════════
def detect_ming_wu_zhengyao(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    命无正曜格：命宫无 14 主星（空宫）。
    （需借对宫论命）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    
    main_stars = [_star_name(s) for s in (soul.get("major_stars") or [])]
    main_stars = [nm for nm in main_stars if nm in FOURTEEN_MAJOR]
    if main_stars:
        return None
    
    # 看对宫
    opp = _by_index(palaces).get(_opp_idx(soul.get("index", 0)))
    opp_majors = []
    if opp:
        opp_majors = [_star_name(s) for s in (opp.get("major_stars") or [])]
        opp_majors = [nm for nm in opp_majors if nm in FOURTEEN_MAJOR]
    
    return {
        "name": "命无正曜格",
        "category": "凶格",
        "evidence": [
            f"命宫（{soul.get('earthly_branch')}宫）无 14 主星",
            f"对宫{opp.get('name','?') if opp else '?'}有：{ '、'.join(opp_majors) if opp_majors else '亦空宫'}",
        ],
        "meaning": "本命无主，需借对宫论命；性情多元，先天命格弱；需后天努力方能立业",
        "break_conditions": [
            "三方有庙旺吉星及禄存科权禄会照，仍可飞黄腾达",
            "对宫亦空则更差",
        ],
    }


# ════════════════════════════════════════════════
# 凶格 B8: 刑囚夹印格
# ════════════════════════════════════════════════
def detect_xingqiu_jiayin(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    刑囚夹印格：命宫廉贞+天相+擎羊同坐子或午宫。
    （廉贞=囚，天相=印，擎羊=刑）
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"子", "午"}:
        return None
    if not _palace_has_star(soul, "廉贞"):
        return None
    if not _palace_has_star(soul, "天相"):
        return None
    if not _palace_has_star(soul, "擎羊"):
        return None
    
    return {
        "name": "刑囚夹印格",
        "category": "凶格",
        "evidence": [
            f"廉贞+天相+擎羊同坐命于{soul.get('earthly_branch')}宫",
            "廉贞为囚，天相为印，擎羊为刑",
        ],
        "meaning": "主官非牢狱、刑伤；一生易卷入诉讼是非；现代多主公检法、律师等职业（化凶为吉的方式）",
        "break_conditions": [
            "若有禄存/化禄解化",
            "若廉贞化禄则减凶",
        ],
    }


# ─────────────────────────────────────────────────────────────
# 总检测函数
# ─────────────────────────────────────────────────────────────

# ════════════════════════════════════════════════
# 吉格 G16: 禄合鸳鸯格
# ════════════════════════════════════════════════
def detect_lu_he_yuanyang(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """禄合鸳鸯：命宫或财官见禄存 + 化禄同宫（两禄相合）"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    stars = [_star_name(s) for s in _all_stars_in_palace(soul)]
    has_lu_cun = "禄存" in stars
    # 化禄检测：iztro adj_stars 中 mutagen 字段
    has_hua_lu = any(
        (s.get("mutagen") == "禄" if isinstance(s, dict) else False)
        for s in _all_stars_in_palace(soul)
    )
    if has_lu_cun and has_hua_lu:
        return {
            "name": "禄合鸳鸯格",
            "category": "吉格",
            "evidence": ["命宫见禄存", "命宫见化禄", "两禄相合"],
            "meaning": "禄存与化禄同宫，「禄合鸳鸯」，主财禄丰厚、衣食无忧、富贵双全。古书云「双禄朝垣，富贵荣华」。",
            "break_conditions": ["见空亡或地空地劫则禄气漏空"],
        }
    return None


# ════════════════════════════════════════════════
# 吉格 G17: 武曲守垣格
# ════════════════════════════════════════════════
def detect_wuqu_shouyuan(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """武曲守垣：武曲坐命宫在辰戌丑未四墓库宫"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"辰", "戌", "丑", "未"}:
        return None
    if not _palace_has_star(soul, "武曲"):
        return None
    sha_in_soul = [_star_name(s) for s in _all_stars_in_palace(soul) if _star_name(s) in SIX_SHA]
    return {
        "name": "武曲守垣格",
        "category": "吉格",
        "evidence": [
            f"命宫在{soul.get('earthly_branch')}（四墓库之地）",
            "武曲坐命",
            "武贵之命，最利军警、金融、武职",
        ],
        "meaning": "武曲入墓库守垣，「武曲守垣，威震边夷」，主威武刚毅、文武双全、金融武职大利。古书谓之「将相之命」。",
        "break_conditions": ["见羊陀火铃则反主刑伤", "化忌则财运受阻"],
        "is_partial": bool(sha_in_soul),
    }


# ════════════════════════════════════════════════
# 吉格 G18: 阳梁昌禄格（完整版 — 检查三方四正全部 4 星）
# ════════════════════════════════════════════════
def detect_yangliang_changlu_full(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """阳梁昌禄：三方四正会齐太阳 + 天梁 + 文昌 + 禄存"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    # 三方四正星
    three_dir_stars = _stars_in_three_directions(palaces, soul)
    needed = {"太阳", "天梁", "文昌", "禄存"}
    found = needed & three_dir_stars
    if len(found) == 4:
        return {
            "name": "阳梁昌禄格",
            "category": "吉格",
            "evidence": [
                "三方四正会太阳、天梁、文昌、禄存四星",
                "古来状元宰相之命",
            ],
            "meaning": "阳梁昌禄主大利科考、学术、清贵之职，「文章秀气，名扬天下」。古书云「阳梁昌禄，传胪第一名」（状元）。",
            "break_conditions": ["见羊陀夹冲则贵气受损", "见空劫则功名虚浮"],
        }
    elif len(found) == 3:
        return {
            "name": "阳梁昌禄格（部分）",
            "category": "吉格",
            "evidence": [f"三方会 {'、'.join(found)} （缺 {'、'.join(needed - found)}）"],
            "meaning": "部分成格，学术清贵之气仍存。",
            "is_partial": True,
        }
    return None


def _stars_in_three_directions(palaces: List[Dict[str, Any]], soul: Dict[str, Any]) -> set:
    """收集三方四正所有星名"""
    stars = set()
    soul_idx = soul.get("index", 0)
    # 三方四正：命宫 + 财帛 + 官禄 + 迁移 = 索引 +0, +4, +6, +8
    for offset in [0, 4, 6, 8]:
        idx = (soul_idx + offset) % 12
        for p in palaces:
            if p.get("index") == idx:
                for s in _all_stars_in_palace(p):
                    nm = _star_name(s)
                    if nm:
                        stars.add(nm)
    return stars


# ════════════════════════════════════════════════
# 吉格 G19: 廉贞清白格
# ════════════════════════════════════════════════
def detect_lianzhen_qingbai(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """廉贞清白：廉贞坐命于寅申宫且无煞"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"寅", "申"}:
        return None
    if not _palace_has_star(soul, "廉贞"):
        return None
    sha = [_star_name(s) for s in _all_stars_in_palace(soul) if _star_name(s) in SIX_SHA]
    if sha:
        return None  # 见煞破格
    return {
        "name": "廉贞清白格",
        "category": "吉格",
        "evidence": [
            f"命宫在{soul.get('earthly_branch')}（寅申之地）",
            "廉贞坐命",
            "命宫无煞星，廉贞清纯",
        ],
        "meaning": "廉贞守命于寅申，无煞冲破，「廉贞清白，威权显达」，主官贵清廉、政事亨通。",
        "break_conditions": ["逢羊陀火铃则廉贞带刑", "化忌则官非缠身"],
    }


# ════════════════════════════════════════════════
# 吉格 G20: 巨日同宫格
# ════════════════════════════════════════════════
def detect_juri_tonggong(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """巨日同宫：巨门 + 太阳同坐命宫于寅或申宫"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"寅", "申"}:
        return None
    if not _palace_has_star(soul, "巨门"):
        return None
    if not _palace_has_star(soul, "太阳"):
        return None
    return {
        "name": "巨日同宫格",
        "category": "吉格",
        "evidence": [
            f"命宫在{soul.get('earthly_branch')}",
            "巨门+太阳同坐命宫",
            "口才显达、外交名声大利",
        ],
        "meaning": "巨日同宫，「巨日同宫，官封三代」，主声名远播、口才出众、利文教外交。寅宫为最，申宫稍弱。",
        "break_conditions": ["逢化忌则口舌官非", "见羊陀则功名受损"],
    }


# ════════════════════════════════════════════════
# 凶格 B9: 君臣不义格
# ════════════════════════════════════════════════
def detect_junchen_buyi(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """君臣不义：紫微独坐命宫而无左辅右弼会照"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if not _palace_has_star(soul, "紫微"):
        return None
    three_dir = _stars_in_three_directions(palaces, soul)
    has_left = "左辅" in three_dir
    has_right = "右弼" in three_dir
    if not has_left and not has_right:
        return {
            "name": "君臣不义格",
            "category": "凶格",
            "evidence": [
                "紫微坐命",
                "三方四正不见左辅、右弼",
                "孤君无臣辅佐",
            ],
            "meaning": "紫微为帝、无左右辅佐，「君臣不义」，主孤高自傲、独断专行、得志而无人相助；事业难成大格局。",
            "break_conditions": ["见天魁天钺贵人星可稍减孤", "化禄化权可独自显贵"],
        }
    return None


# ════════════════════════════════════════════════
# 凶格 B10: 刑忌夹印格
# ════════════════════════════════════════════════
def detect_xingji_jiayin(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """刑忌夹印：天相坐命，前后宫被擎羊（刑）和化忌夹"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if not _palace_has_star(soul, "天相"):
        return None
    soul_idx = soul.get("index", 0)
    prev_idx = (soul_idx - 1) % 12
    next_idx = (soul_idx + 1) % 12
    prev_p = next((p for p in palaces if p.get("index") == prev_idx), None)
    next_p = next((p for p in palaces if p.get("index") == next_idx), None)
    if not prev_p or not next_p:
        return None
    # 一宫见擎羊（刑），另一宫见化忌
    pp_stars = [_star_name(s) for s in _all_stars_in_palace(prev_p)]
    np_stars = [_star_name(s) for s in _all_stars_in_palace(next_p)]
    pp_has_yang = "擎羊" in pp_stars
    np_has_yang = "擎羊" in np_stars
    pp_has_ji = any((s.get("mutagen") == "忌" if isinstance(s, dict) else False)
                     for s in _all_stars_in_palace(prev_p))
    np_has_ji = any((s.get("mutagen") == "忌" if isinstance(s, dict) else False)
                     for s in _all_stars_in_palace(next_p))
    if (pp_has_yang and np_has_ji) or (pp_has_ji and np_has_yang):
        return {
            "name": "刑忌夹印格",
            "category": "凶格",
            "evidence": ["天相坐命", "前后宫被擎羊与化忌相夹", "刑忌夹印"],
            "meaning": "天相为印星，被刑（擎羊）忌（化忌）双夹，「刑忌夹印」之大凶。主一生官非缠身、是非不断、健康多忧。",
            "break_conditions": ["见禄存或化禄能稍解", "见天魁天钺贵人可化解大半"],
        }
    return None


# ════════════════════════════════════════════════
# 凶格 B11: 马落空亡格
# ════════════════════════════════════════════════
def detect_ma_luo_kongwang(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """马落空亡：天马星临空亡（旬空 + 截空 + 地空 + 地劫）"""
    for p in palaces:
        has_ma = _palace_has_star(p, "天马")
        if not has_ma:
            continue
        all_stars = [_star_name(s) for s in _all_stars_in_palace(p)]
        kong_stars = {"旬空", "截路", "空亡", "地空", "地劫"}
        kong_found = [s for s in all_stars if s in kong_stars]
        if kong_found:
            is_soul = p.get("is_soul") or p.get("name") == "命宫"
            label = "命宫" if is_soul else p.get("name", "")
            return {
                "name": "马落空亡格",
                "category": "凶格",
                "evidence": [
                    f"天马在{label}",
                    f"同宫见 {'、'.join(set(kong_found))}",
                ],
                "meaning": "天马为驿动之星，「马落空亡」主奔波无果、劳碌而无成、远行不利；多次更换工作或居所。",
                "break_conditions": ["大限流年补禄存可解", "见化禄则马有归处"],
            }
    return None


def detect_zitan_tonggong(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    紫贪同宫格：紫微+贪狼同坐命宫（仅在卯/酉宫）。
    《紫微斗数全书》：紫贪卯酉主桃花，喜动喜变，多才多艺。
    """
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") not in {"卯", "酉"}:
        return None
    if not _palace_has_star(soul, "紫微"):
        return None
    if not _palace_has_star(soul, "贪狼"):
        return None
    
    # 检查煞星
    sha_in_soul = [_star_name(s) for s in _all_stars_in_palace(soul)
                   if _star_name(s) in SIX_SHA]
    
    return {
        "name": "紫贪同宫格",
        "category": "吉格",
        "evidence": [
            f"命宫在{soul.get('earthly_branch')}宫",
            "紫微+贪狼同坐命宫",
            "桃花格局，主多才多艺、人缘极佳",
            f"⚠ 命宫见煞星 {'、'.join(set(sha_in_soul))}，桃花带刑" if sha_in_soul else "命宫清净，桃花纯正",
        ],
        "meaning": "紫微为帝、贪狼为桃花，紫贪卯酉乃风流贵格；主一生际遇多变、才华横溢；男主风流好色、女主美貌多情；适合艺术、外交、销售；逢化禄化权则贵显，逢化忌则败于色",
        "break_conditions": [
            "见空亡则才华不显",
            "见煞重则因色破财",
            "贪狼化忌则一生情感波折",
        ],
        "is_partial": bool(sha_in_soul),
    }



# ════════════════════════════════════════════════
# 补遗·高价值经典吉格 G21–G30
# ════════════════════════════════════════════════
def _sfsz_stars(palaces):
    """命宫三方四正所会之星 {星名:宫名} + 化曜集合。"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return {}, {}, None
    idx = soul.get("index", -1)
    indices = _san_fang_si_zheng_indices(idx)
    stars = _collect_stars_in_palaces(palaces, indices)
    # 化曜：扫三方四正各宫之星 mutagen
    by_idx = _by_index(palaces)
    mut = {}     # 化 → "星名"
    for i in indices:
        p = by_idx.get(i)
        if not p:
            continue
        for s in _all_stars_in_palace(p):
            m = _star_mutagen(s)
            if m in ("禄", "权", "科", "忌"):
                mut.setdefault(m, _star_name(s))
    return stars, mut, soul


def detect_sanqi_jiahui(palaces):
    """三奇加会格：化禄+化权+化科三奇会于命宫三方四正——大贵之格。"""
    stars, mut, soul = _sfsz_stars(palaces)
    if not soul:
        return None
    if all(k in mut for k in ("禄", "权", "科")):
        return {
            "name": "三奇加会格", "category": "吉格",
            "evidence": [f"化禄（{mut['禄']}）", f"化权（{mut['权']}）", f"化科（{mut['科']}）", "三奇会照命垣"],
            "meaning": "禄权科三奇会命，谓「三奇加会」，主大贵——功名显达、富贵双全、出将入相之格，一生得贵人提携、声名远播。",
            "break_conditions": ["三方见空劫则减力", "若三奇之一又化忌则破"],
            "is_partial": "忌" in mut,
        }
    return None


def detect_shuanglu_chaoyuan(palaces):
    """双禄朝垣格：禄存与化禄并会命垣——富贵之格。"""
    stars, mut, soul = _sfsz_stars(palaces)
    if not soul:
        return None
    has_luc = "禄存" in stars
    has_hualu = "禄" in mut
    if has_luc and has_hualu:
        return {
            "name": "双禄朝垣格", "category": "吉格",
            "evidence": [f"禄存在{stars['禄存']}", f"化禄（{mut['禄']}）会照", "双禄交流朝命"],
            "meaning": "禄存、化禄双禄会命，谓「双禄朝垣」，主财官双美、衣食丰足、富而且贵，一生财源广进、福泽深厚。",
            "break_conditions": ["逢空劫冲破则禄气受损", "化忌冲禄则先得后失"],
            "is_partial": "忌" in mut,
        }
    return None


def detect_luma_jiaochi(palaces):
    """禄马交驰格：天马与禄存（或化禄）同宫或会照——富而奔波得财。"""
    stars, mut, soul = _sfsz_stars(palaces)
    if not soul:
        return None
    if "天马" in stars and ("禄存" in stars or "禄" in mut):
        lu = "禄存" if "禄存" in stars else f"{mut.get('禄','')}化禄"
        return {
            "name": "禄马交驰格", "category": "吉格",
            "evidence": [f"天马在{stars['天马']}", f"会{lu}", "禄马交驰"],
            "meaning": "天马得禄，谓「禄马交驰」，主动中生财、外出发达、营商远行获利，宜经商、外贸、奔走四方求财，富而有得。",
            "break_conditions": ["马落空亡则奔波无果", "截路空亡则财来财去"],
            "is_partial": False,
        }
    return None


def detect_cailin_jiayin(palaces):
    """财荫夹印格：命坐天相（印），左右邻宫一为化禄（财）、一为天梁（荫）相夹——贵格。"""
    soul = _find_soul_palace(palaces)
    if not soul or not _palace_has_star(soul, "天相"):
        return None
    idx = soul.get("index", -1)
    a, b = _adjacent_indices(idx)
    by_idx = _by_index(palaces)
    pa, pb = by_idx.get(a), by_idx.get(b)
    if not pa or not pb:
        return None

    def _has_hualu(p):
        return any(_star_mutagen(s) == "禄" for s in _all_stars_in_palace(p))
    lu_a, lu_b = _has_hualu(pa), _has_hualu(pb)
    liang_a, liang_b = _palace_has_star(pa, "天梁"), _palace_has_star(pb, "天梁")
    if (lu_a and liang_b) or (lu_b and liang_a):
        return {
            "name": "财荫夹印格", "category": "吉格",
            "evidence": ["命坐天相（印星）", "一邻宫化禄（财）", "一邻宫天梁（荫）", "财荫夹印"],
            "meaning": "天相为印，得化禄之财、天梁之荫左右夹辅，谓「财荫夹印」，主受荫庇、有权印、财官两全，常得长上提拔、掌实权而进财。",
            "break_conditions": ["若为擎羊与化忌夹则反成「刑忌夹印」之凶"],
            "is_partial": False,
        }
    return None


def detect_riyue_jiaming(palaces):
    """日月夹命格：命宫左右邻宫为太阳、太阴所夹——主贵显。"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    idx = soul.get("index", -1)
    a, b = _adjacent_indices(idx)
    by_idx = _by_index(palaces)
    pa, pb = by_idx.get(a), by_idx.get(b)
    if not pa or not pb:
        return None
    sun_a, sun_b = _palace_has_star(pa, "太阳"), _palace_has_star(pb, "太阳")
    moon_a, moon_b = _palace_has_star(pa, "太阴"), _palace_has_star(pb, "太阴")
    if (sun_a and moon_b) or (sun_b and moon_a):
        return {
            "name": "日月夹命格", "category": "吉格",
            "evidence": ["太阳、太阴分居命宫左右邻宫", "日月夹命"],
            "meaning": "日月夹命，阴阳调和、明照左右，主一生光明显达、得人扶助、财官双美，尤以日月庙旺夹之为上格。",
            "break_conditions": ["日月落陷夹之则力减", "中间逢空劫则夹气受阻"],
            "is_partial": False,
        }
    return None


def detect_changqu_jiaming(palaces):
    """文桂文华格（昌曲夹命/会命）：文昌文曲夹命或会照命垣——文贵之格。"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    idx = soul.get("index", -1)
    a, b = _adjacent_indices(idx)
    by_idx = _by_index(palaces)
    pa, pb = by_idx.get(a), by_idx.get(b)
    jia = pa and pb and (
        (_palace_has_star(pa, "文昌") and _palace_has_star(pb, "文曲")) or
        (_palace_has_star(pa, "文曲") and _palace_has_star(pb, "文昌")))
    stars, _, _ = _sfsz_stars(palaces)
    hui = "文昌" in stars and "文曲" in stars
    if jia or hui:
        return {
            "name": "文桂文华格", "category": "吉格",
            "evidence": (["文昌文曲夹命"] if jia else ["文昌文曲会照命垣"]),
            "meaning": "昌曲拱命，谓「文桂文华」，主聪明博学、文采斐然、利科甲功名，宜文教、学术、文书之职，一生近贵得名。",
            "break_conditions": ["昌曲落陷或逢空劫则华而不实", "见火铃冲则减"],
            "is_partial": False,
        }
    return None


def detect_zuogui_xianggui(palaces):
    """坐贵向贵格：天魁坐命、天钺在对宫（或互换）——贵人扶助之格。"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    idx = soul.get("index", -1)
    opp = _by_index(palaces).get(_opp_idx(idx))
    if not opp:
        return None
    kui_s, yue_s = _palace_has_star(soul, "天魁"), _palace_has_star(soul, "天钺")
    kui_o, yue_o = _palace_has_star(opp, "天魁"), _palace_has_star(opp, "天钺")
    if (kui_s and yue_o) or (yue_s and kui_o):
        return {
            "name": "坐贵向贵格", "category": "吉格",
            "evidence": ["天魁天钺一坐命、一守对宫", "坐贵向贵"],
            "meaning": "魁钺夹辅命迁，谓「坐贵向贵」，主一生多得贵人提携、逢凶化吉、考试升迁有人助力，人缘佳、机遇多。",
            "break_conditions": ["逢空劫则贵人无力", "化忌冲则助力反成阻"],
            "is_partial": False,
        }
    return None


def detect_jixiang_liming(palaces):
    """极向离明格：紫微在午宫坐命——帝星得垣，大贵之格。"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") == "午" and _palace_has_star(soul, "紫微"):
        return {
            "name": "极向离明格", "category": "吉格",
            "evidence": ["紫微在午宫坐命（帝星居离）", "极向离明"],
            "meaning": "紫微午宫庙旺坐命，谓「极向离明」，帝星得位、向明而治，主大贵——领袖之才、位高权重、声名显赫，尤喜会左右昌曲魁钺。",
            "break_conditions": ["独守无辅则为孤君", "见空劫煞忌则贵气受损"],
            "is_partial": False,
        }
    return None


def detect_jincan_guanghui(palaces):
    """金灿光辉格（日丽中天）：太阳在午宫坐命庙旺——贵显之格。"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") == "午" and _palace_has_star(soul, "太阳"):
        return {
            "name": "金灿光辉格", "category": "吉格",
            "evidence": ["太阳在午宫坐命（日丽中天，最旺）", "金灿光辉"],
            "meaning": "太阳午宫最旺坐命，谓「金灿光辉」「日丽中天」，主光明磊落、贵显扬名、利公门官贵，富贵荣华、声名远播，惟稍嫌过刚宜防目疾。",
            "break_conditions": ["逢化忌则光辉受掩", "见空劫则贵而不实"],
            "is_partial": False,
        }
    return None


def detect_yuesheng_canghai(palaces):
    """月生沧海格：太阴在子宫坐命（庙旺）——清贵富足之格。"""
    soul = _find_soul_palace(palaces)
    if not soul:
        return None
    if soul.get("earthly_branch") == "子" and _palace_has_star(soul, "太阴"):
        return {
            "name": "月生沧海格", "category": "吉格",
            "evidence": ["太阴在子宫坐命（水澄月朗，庙旺）", "月生沧海"],
            "meaning": "太阴子宫庙旺坐命，谓「月生沧海」，主清贵秀丽、富足安康、心思细腻，宜文职、财经、不动产，财富积厚、晚景尤佳。",
            "break_conditions": ["逢化忌则阴损", "见空劫煞则富气受耗"],
            "is_partial": False,
        }
    return None


# 注册所有格局检测函数（末尾定义后注册，避免前向引用）
ALL_GOOD_PATTERNS = [
    detect_zifu_tonggong,        # G1 紫府同宫
    detect_junchen_qinghui,      # G2
    detect_fuxiang_chaoyuan,     # G3
    detect_qisha_chaodou,        # G4
    detect_shapolang,            # G5
    detect_jiyue_tongliang,      # G6
    detect_riyue_bingming,       # G7
    detect_mingzhu_chuhai,       # G8
    detect_shizhong_yinyu,       # G9
    detect_matou_daijian,        # G10
    detect_yuelang_tianmen,      # G12
    detect_huotan,               # G13
    detect_lingtan,              # G14
    detect_yangliang_changlu,    # G15 旧版
    detect_lu_he_yuanyang,       # G16 禄合鸳鸯
    detect_wuqu_shouyuan,        # G17 武曲守垣
    detect_yangliang_changlu_full, # G18 阳梁昌禄（完整版）
    detect_lianzhen_qingbai,     # G19 廉贞清白
    detect_juri_tonggong,        # G20 巨日同宫
    detect_sanqi_jiahui,         # G21 三奇加会
    detect_shuanglu_chaoyuan,    # G22 双禄朝垣
    detect_luma_jiaochi,         # G23 禄马交驰
    detect_cailin_jiayin,        # G24 财荫夹印
    detect_riyue_jiaming,        # G25 日月夹命
    detect_changqu_jiaming,      # G26 文桂文华
    detect_zuogui_xianggui,      # G27 坐贵向贵
    detect_jixiang_liming,       # G28 极向离明
    detect_jincan_guanghui,      # G29 金灿光辉
    detect_yuesheng_canghai,     # G30 月生沧海
]

ALL_BAD_PATTERNS = [
    detect_yangtuo_jiaji,        # B1
    detect_lingchang_tuowu,      # B2
    detect_huoling_jiaming,      # B3
    detect_juhuo_yang,           # B4
    detect_fengliu_caizhang,     # B5
    detect_fanshui_taohua,       # B6
    detect_ming_wu_zhengyao,     # B7
    detect_xingqiu_jiayin,       # B8
    detect_junchen_buyi,         # B9 君臣不义
    detect_xingji_jiayin,        # B10 刑忌夹印
    detect_ma_luo_kongwang,      # B11 马落空亡
]


def detect_all_patterns(
    palaces: List[Dict[str, Any]],
    birth_hour_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    主入口：对整张命盘做格局自动检测。
    
    Args:
        palaces:           build_ziwei_chart 输出的 palaces
        birth_hour_index:  出生时辰索引（0-11），用于"日照雷门格"等昼夜判定
    
    Returns:
        {
          "good_patterns":  [格局记录, ...],
          "bad_patterns":   [格局记录, ...],
          "total_count":    int,
        }
    """
    good_found: List[Dict[str, Any]] = []
    bad_found: List[Dict[str, Any]] = []
    
    for detector in ALL_GOOD_PATTERNS:
        try:
            result = detector(palaces)
            if result:
                good_found.append(result)
        except Exception:
            continue  # 任一格局检测失败不影响其他
    
    # 紫贪同宫格（前向引用，单独调用）
    try:
        result = detect_zitan_tonggong(palaces)
        if result:
            good_found.append(result)
    except Exception as _e1:
        from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e1)
    
    # 日照雷门格 需要 birth_hour_index
    if birth_hour_index is not None:
        try:
            rizhao = detect_rizhao_leimen(palaces, birth_hour_index)
            if rizhao:
                good_found.append(rizhao)
        except Exception as _e2:
            from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e2)
    else:
        # 仍尝试检测（不带时辰参数）
        try:
            rizhao = detect_rizhao_leimen(palaces, None)
            if rizhao:
                good_found.append(rizhao)
        except Exception as _e3:
            from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e3)
    
    for detector in ALL_BAD_PATTERNS:
        try:
            result = detector(palaces)
            if result:
                bad_found.append(result)
        except Exception:
            continue
    
    return {
        "good_patterns": good_found,
        "bad_patterns":  bad_found,
        "total_count":   len(good_found) + len(bad_found),
    }


# ─────────────────────────────────────────────────────────────
# Prompt 格式化
# ─────────────────────────────────────────────────────────────

def format_patterns_for_prompt(patterns_result: Dict[str, Any]) -> str:
    """把格局检测结果格式化为 LLM prompt 可读文本。"""
    if not patterns_result:
        return ""
    
    good = patterns_result.get("good_patterns", [])
    bad = patterns_result.get("bad_patterns", [])
    
    if not good and not bad:
        return (
            "【经典格局检测】\n"
            "  · 本命盘未触发明显的经典吉格或凶格\n"
            "  · 命格属"
            "中性盘"
            "，需结合主星亮度评级、四化、煞星综合论"
        )
    
    lines: List[str] = []
    lines.append("【经典格局检测】（基于命盘自动识别 15 吉格 + 8 凶格）")
    
    if good:
        lines.append(f"  ◆ 吉格（{len(good)} 个）：")
        for p in good:
            partial_mark = "  ⚠（部分成格/破格风险）" if p.get("is_partial") else ""
            lines.append(f"    · 【{p['name']}】{partial_mark}")
            for ev in p["evidence"]:
                lines.append(f"      - {ev}")
            lines.append(f"      · 含义：{p['meaning']}")
            if p.get("break_conditions"):
                lines.append(f"      · 破格风险：{ '；'.join(p['break_conditions']) }")
    
    if bad:
        lines.append(f"  ◆ 凶格（{len(bad)} 个）：")
        for p in bad:
            lines.append(f"    · 【{p['name']}】")
            for ev in p["evidence"]:
                lines.append(f"      - {ev}")
            lines.append(f"      · 含义：{p['meaning']}")
            if p.get("break_conditions"):
                lines.append(f"      · 化解条件：{ '；'.join(p['break_conditions']) }")
    
    # 综合提示
    if good and not bad:
        lines.append("  → 此命以吉格为主，先天格局优异")
    elif bad and not good:
        lines.append("  → 此命以凶格为主，需多注意化解；后天努力很重要")
    elif good and bad:
        lines.append(f"  → 此命吉凶并见（吉{len(good)}个，凶{len(bad)}个），需结合大限流年分别引爆")
    
    lines.append("")
    lines.append("  说明：")
    lines.append("    · 格局判定是先天格局参考，最终命格还需结合主星亮度评级、四化分析、煞星分布综合论")
    lines.append("    · 吉格不必然主大富大贵，凶格也未必主大祸；后天努力和环境同样重要")
    
    return "\n".join(lines)
