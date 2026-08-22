"""
core/ziwei/perspectives.py
==========================
紫微斗数·多视角整合解读（子模块必尽其用·无孤儿）。

紫微所算之每一子模块（命身格局、三方四正、生年四化与飞星、十二宫主星、
煞曜杂曜、飞化聚焦与冲链）皆须组合进对命主之解释。数子模块拼为「一个视角」：

  ① 命身格局 —— 命宫主星 × 身宫 × 命主身主 × 格局成破
  ② 三方四正 —— 会照明暗 × 拱夹之星
  ③ 四化飞星 —— 生年四化 × 飞入命宫 × 冲命 × 双忌
  ④ 十二宫分布 —— 财官迁夫福疾诸宫主星
  ⑤ 煞曜杂曜 —— 六煞 × 长生十二神 × 博士十二神
  ⑥ 生命焦点 —— 飞化聚焦宫 × 冲链

并随附 coverage，以备核查「尽其用」。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SHA = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}
_KEY_PALACES = ("财帛宫", "官禄宫", "迁移宫", "夫妻宫", "福德宫", "疾厄宫")


def _stars_bright(p):
    out = []
    for s in p.get("major_stars", []) or []:
        br = s.get("brightness", "")
        out.append(f"{s.get('name','')}（{br}）" if br else s.get("name", ""))
    return "、".join(out) if out else "空宫"


def build_perspectives(chart: Dict[str, Any]) -> Dict[str, Any]:
    palaces = chart.get("palaces", []) or []
    if not palaces:
        return {"available": False}

    md = chart.get("metadata", {}) or {}
    ins = chart.get("insights", {}) or {}
    rating = ins.get("rating", {}) or {}
    patterns = ins.get("patterns", {}) or {}
    fs = ins.get("feihua_summary", {}) or {}
    sj = (chart.get("sanjiao_analysis", {}) or {})
    bsp = chart.get("birth_sihua", {}) or {}

    ming = next((p for p in palaces if p.get("is_soul")), None)
    body = next((p for p in palaces if p.get("is_body")), None)
    if not ming:
        return {"available": False}

    lenses: List[Dict[str, Any]] = []

    # ① 命身格局
    bits = [f"命宫坐{ming.get('earthly_branch','')}、主星{_stars_bright(ming)}"]
    if body:
        bits.append(f"身宫在{body.get('name','')}（{_stars_bright(body)}）")
    bits.append(f"命主{md.get('soul_star','')}、身主{md.get('body_star','')}、{md.get('five_elements','')}")
    good = patterns.get("good", []) or []
    bad = patterns.get("bad", []) or []
    if good:
        bits.append("成吉格：" + "、".join(g.get("name", "") for g in good[:3]))
    if bad:
        bits.append("带凶格：" + "、".join(b.get("name", "") for b in bad[:3]))
    lenses.append({
        "id": "mingshen", "title": "命身格局", "icon": "命",
        "modules": ["命宫主星", "身宫", "命主身主", "格局成破"],
        "text": "从命身格局论——" + "；".join(bits) + "。此定一命之本、格局之高低。",
    })

    # ② 三方四正
    conv = sj.get("converging_stars", []) or []
    bright = rating.get("bright_in_sfsz", []) or []
    fallen = rating.get("fallen_in_sfsz", []) or []
    bits = []
    if conv:
        bits.append("会照：" + "、".join(f"{c.get('star','')}（{c.get('palace','')}"
                    + (f"·化{c.get('mutagen')}" if c.get('mutagen') else "") + "）" for c in conv[:5]))
    if bright:
        bits.append("庙旺者" + "、".join(bright[:5]) + "助力广")
    if fallen:
        bits.append("落陷者" + "、".join(fallen[:4]) + "多波折")
    lenses.append({
        "id": "sanfang", "title": "三方四正", "icon": "三",
        "modules": ["三方四正会照", "主星明暗"],
        "text": "从三方四正论——" + "；".join(bits) + "。命宫不孤，恃三方拱照定其成败。",
    })

    # ③ 四化飞星
    bits = []
    sihua = (bsp.get("sihua", {}) or {}) if bsp.get("available") else {}
    if sihua:
        sh = "、".join(f"{k}{v.get('star','')}入{v.get('palace','')}" for k, v in sihua.items() if v.get("star"))
        bits.append("生年四化：" + sh)
    inc = fs.get("soul_incoming", []) or []
    if inc:
        bits.append("飞入命宫：" + "、".join(f"{i.get('from','')}{i.get('hua','')}{i.get('star','')}" for i in inc[:3]))
    chong = fs.get("soul_chong", []) or []
    if chong:
        bits.append("冲命：" + "、".join(f"{c.get('from','')}化忌" for c in chong[:2]) + "——主该宫之事来扰")
    dji = fs.get("double_ji", []) or []
    if dji:
        dji_gong = list(dict.fromkeys(d.get("to", "") for d in dji if d.get("to")))
        bits.append("双忌叠至：" + "、".join(dji_gong[:2]) + "——其事纠缠最重")
    lenses.append({
        "id": "sihua", "title": "四化飞星", "icon": "化",
        "modules": ["生年四化", "飞入命宫", "冲命", "双忌"],
        "text": "从四化飞星论——" + "；".join(bits) + "。四化为紫微之魂，引动诸宫之吉凶得失。",
    })

    # ④ 十二宫分布
    bits = []
    for p in palaces:
        if p.get("name") in _KEY_PALACES:
            bits.append(f"{p.get('name','')[:2]}〔{_stars_bright(p)}〕")
    lenses.append({
        "id": "shiergong", "title": "十二宫分布", "icon": "宫",
        "modules": ["财官迁夫福疾诸宫主星"],
        "text": "从十二宫分布论——" + "；".join(bits) + "。诸宫主星各司其事，财官迁福分见一生之得失向背。",
    })

    # ⑤ 煞曜杂曜
    sj_idx = set((sj.get("sanjiao", {}) or {}).get("palaces", []) or []) | {ming.get("index")}
    sha = []
    for p in palaces:
        if p.get("index") in sj_idx:
            for s in (p.get("minor_stars", []) or []) + (p.get("adj_stars", []) or []):
                if s.get("name") in _SHA:
                    sha.append(f"{s.get('name')}（{p.get('name','')}）")
    bits = []
    if sha:
        bits.append("命三方煞曜：" + "、".join(sha[:4]) + "——主刑伤、阻力、磨折")
    else:
        bits.append("命三方煞曜不显，行事少阻")
    if ming.get("changsheng12"):
        bits.append(f"命宫临长生十二神之「{ming['changsheng12']}」")
    if ming.get("boshi12"):
        bits.append(f"博士十二神之「{ming['boshi12']}」")
    lenses.append({
        "id": "shayao", "title": "煞曜杂曜", "icon": "煞",
        "modules": ["六煞", "长生十二神", "博士十二神"],
        "text": "从煞曜杂曜论——" + "；".join(bits) + "。煞曜杂曜为辅佐，定一生磨折之多寡、气数之消长。",
    })

    # ⑥ 生命焦点
    conc = fs.get("concentration", {}) or {}
    cc = ins.get("chong_chains", {}) or {}
    bits = []
    if conc:
        top = sorted(conc.items(), key=lambda x: -x[1])[:2]
        bits.append("飞化最聚于：" + "、".join(f"{k}（{v}度）" for k, v in top) + "——此乃一生用心、得失最重之处")
    if cc.get("total"):
        bits.append(f"全盘冲链{cc['total']}处")
        ev = cc.get("events", []) or []
        if ev:
            bits.append(f"如{ev[0].get('from_palace','')}{ev[0].get('hua_type','')}冲{ev[0].get('target_palace','')}")
    if not bits:
        bits.append("飞化平和，无显著聚焦或冲突")
    lenses.append({
        "id": "jiaodian", "title": "生命焦点", "icon": "焦",
        "modules": ["飞化聚焦", "冲链"],
        "text": "从生命焦点论——" + "；".join(bits) + "。飞化所聚即命主一生着力之所在，冲链所及即其牵缠之处。",
    })

    # ⑦ 行运运限（大限流年并入 — 后天之行运）
    cf = chart.get("current_fortune", {}) or {}
    if cf.get("available"):
        dx = cf.get("daxian", {}) or {}
        ln = cf.get("liunian", {}) or {}
        rng = dx.get("range", [])
        rng_s = f"{rng[0]}-{rng[1]}岁" if isinstance(rng, (list, tuple)) and len(rng) == 2 else ""
        tbits = [f"现行大限{dx.get('palace','')}（{dx.get('branch','')}，{rng_s}），坐{('、'.join(dx.get('major_stars', [])[:3]) or '无主星')}"]
        if ln and ln.get("palace"):
            tbits.append(f"{cf.get('current_year','')}年流年入{ln.get('palace','')}")
        txt = ("从行运运限论——" + "；".join(tbits) + "。" + cf.get("daxian_tone", "") +
               "。本命定格局高低，大限定十年休咎、流年定一岁吉凶，三盘叠合方知此时此事之应。")
    else:
        txt = "从行运运限论——未能定位当前大限；补全生辰即可叠大限、流年盘，知现行十年与今岁之运。"
    lenses.append({
        "id": "yunxian", "title": "行运运限", "icon": "运",
        "modules": ["大限", "流年", "三盘叠合"],
        "text": txt,
    })

    coverage = {}
    for ln in lenses:
        for m in ln["modules"]:
            coverage[m] = ln["title"]

    return {
        "available": True,
        "ming_branch": ming.get("earthly_branch", ""),
        "lenses": lenses,
        "coverage": coverage,
    }
