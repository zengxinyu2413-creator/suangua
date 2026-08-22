"""
core/ziwei/birth_sihua.py
=========================
紫微斗数·生年四化盘 + 来因宫（飞星派论命第一步）。

飞星派论命，以「生年四化」为体、「来因宫」为根：
  · 生年四化 —— 生年天干所引之禄·权·科·忌四星，各落一宫，定一生福源、
    权柄、贵显、执念之所在。
  · 来因宫 —— 生年化忌所落之宫，为一生命题之「来因」、课题与亏欠之根，
    飞星派论命必先点出此宫。

原排盘已于各星标 mutagen（禄/权/科/忌），但未汇成四化盘，亦未定来因宫。
本模块自各宫之星汇集四化、定来因宫，并出飞星派基础解读，与排盘同源。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

# 十二宫飞星派含义（四化落宫之象）
PALACE_THEME: Dict[str, str] = {
    "命宫": "自身、性格、一生总格", "兄弟宫": "手足、母亲、合作、财库（成就位）",
    "夫妻宫": "配偶、婚姻、异性缘、内心情感", "子女宫": "子女、桃花、合伙、性、晚辈",
    "财帛宫": "财富、现金流、价值观、赚钱方式", "疾厄宫": "身体、健康、情绪、潜意识、脾性",
    "迁移宫": "外出、社会、机遇、外缘、晚年", "交友宫": "朋友、同事、人际、竞争对手",
    "仆役宫": "朋友、同事、人际、竞争对手",
    "官禄宫": "事业、工作、考运、丈夫（女命）", "事业宫": "事业、工作、考运、丈夫（女命）",
    "田宅宫": "不动产、家庭、财库、根基", "福德宫": "福分、兴趣、精神、寿元、祖荫",
    "父母宫": "父母、长辈、文书、上司、相貌",
}

HUA_MEANING: Dict[str, Dict[str, str]] = {
    "化禄": {"nature": "吉", "d": "福源、财源、顺遂、缘起、喜悦——此宫之事得财得缘、轻松有得"},
    "化权": {"nature": "吉", "d": "权柄、掌控、能量、成就、变动——此宫之事主导有力、能成大局"},
    "化科": {"nature": "吉", "d": "名声、贵人、文采、化解、平顺——此宫之事得名得助、逢凶化吉"},
    "化忌": {"nature": "凶", "d": "执念、亏欠、课题、是非、收藏——此宫之事最在意、最易困、为一生须了之债"},
}

_MUT_MAP = {"禄": "化禄", "权": "化权", "科": "化科", "忌": "化忌",
            "化禄": "化禄", "化权": "化权", "化科": "化科", "化忌": "化忌"}


def _stem_of_year(chart: Dict[str, Any]) -> str:
    cd = chart.get("metadata", {}).get("chinese_date", "")
    return cd.split()[0][0] if cd else ""


def extract_birth_sihua(chart: Dict[str, Any]) -> Dict[str, Any]:
    """自各宫之星汇集生年四化（禄权科忌 → 星 + 落宫）。"""
    out: Dict[str, Dict[str, Any]] = {}
    for p in chart.get("palaces", []):
        pname = p.get("name", "")
        for s in (p.get("major_stars", []) or []) + (p.get("minor_stars", []) or []):
            if not isinstance(s, dict):
                continue
            mut = s.get("mutagen") or ""
            hua = _MUT_MAP.get(mut)
            if hua and hua not in out:
                out[hua] = {
                    "star": s.get("name", ""),
                    "palace": pname,
                    "palace_idx": p.get("index"),
                    "theme": PALACE_THEME.get(pname, ""),
                }
    return out


def analyze_laiyin(chart: Dict[str, Any], birth_sihua: Dict[str, Any],
                   year_stem: str) -> Dict[str, Any]:
    """
    来因宫（梁若瑜飞星派正解）= 宫干同生年干之宫——命主此生因果之源、
    禀赋与课题之所从来。另记生年化忌所入之宫为「执念/债」之点。
    """
    laiyin_palace = None
    for p in chart.get("palaces", []):
        if p.get("heavenly_stem") == year_stem:
            laiyin_palace = p.get("name", "")
            break
    ji = birth_sihua.get("化忌")
    ji_palace = ji["palace"] if ji else ""

    if not laiyin_palace:
        return {"available": False, "desc": "未能定来因宫（无宫干同生年干之宫）。"}

    theme = PALACE_THEME.get(laiyin_palace, "")
    desc = (f"来因宫在【{laiyin_palace}】（宫干同生年干「{year_stem}」）——"
            f"此为命主此生因果之源、禀赋与课题之所从来：{theme}。"
            f"飞星派论命第一步先观此宫，凡{laiyin_palace}之事，乃此人立命之根、"
            f"一生际遇所自来。")
    if ji_palace:
        desc += (f"　另，生年化忌（{ji['star']}）入【{ji_palace}】，"
                 f"为一生最在意、最易牵绊、须了之执念与债。")
    return {
        "available": True,
        "palace": laiyin_palace, "theme": theme, "year_stem": year_stem,
        "ji_palace": ji_palace, "ji_star": ji["star"] if ji else "",
        "desc": desc,
    }


def interpret_birth_sihua(birth_sihua: Dict[str, Any]) -> Dict[str, Any]:
    """生年四化盘飞星派基础解读 + 禄忌格局。"""
    rows: List[Dict[str, str]] = []
    for hua in ("化禄", "化权", "化科", "化忌"):
        info = birth_sihua.get(hua)
        if not info:
            continue
        m = HUA_MEANING[hua]
        rows.append({
            "hua": hua, "star": info["star"], "palace": info["palace"],
            "nature": m["nature"],
            "desc": f"{hua}·{info['star']}入【{info['palace']}】：{m['d']}（{info['theme']}）。",
        })

    # 禄忌格局（飞星派重象）
    geju = ""
    lu = birth_sihua.get("化禄")
    ji = birth_sihua.get("化忌")
    if lu and ji:
        lp, jp = lu["palace"], ji["palace"]
        if lp == jp:
            geju = f"禄忌同宫于【{lp}】——「禄随忌走」，福中藏患、得而复失，此宫之事成败相依、用神宜慎。"
        else:
            # 对宫判断（简：命-迁/兄-友/夫-官/子-田/财-福/疾-父 为对宫）
            DUI = {"命宫": "迁移宫", "兄弟宫": "交友宫", "夫妻宫": "官禄宫",
                   "子女宫": "田宅宫", "财帛宫": "福德宫", "疾厄宫": "父母宫"}
            dui_pairs = {**DUI, **{v: k for k, v in DUI.items()}}
            if dui_pairs.get(lp) == jp:
                geju = f"禄忌对冲（{lp}↔{jp}）——「禄忌成串」，一喜一忧两宫相牵，此二事此消彼长、互为因果。"
            else:
                geju = f"生年禄入【{lp}】（福源）、忌入【{jp}】（课题）——趋禄宫以得助、了忌宫以解结。"

    return {"rows": rows, "lu_ji_geju": geju}


def build_birth_sihua_panel(chart: Dict[str, Any]) -> Dict[str, Any]:
    """生年四化盘 + 来因宫 总成（飞星派论命起手）。"""
    bs = extract_birth_sihua(chart)
    if not bs:
        return {"available": False}
    year_stem = _stem_of_year(chart)
    laiyin = analyze_laiyin(chart, bs, year_stem)
    interp = interpret_birth_sihua(bs)
    return {
        "available": True,
        "year_stem": year_stem,
        "sihua": bs,
        "laiyin": laiyin,
        "interpretation": interp["rows"],
        "lu_ji_geju": interp["lu_ji_geju"],
        "summary": (laiyin.get("desc", "") if laiyin.get("available") else "")
                   + (("　" + interp["lu_ji_geju"]) if interp["lu_ji_geju"] else ""),
    }
