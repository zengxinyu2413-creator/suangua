"""
core/qimen/perspectives.py
==========================
奇门遁甲·多视角整合解读（子模块必尽其用·无孤儿）。

奇门所算之每一子模块（用神成败、值符值使、方位时机、格局成破、三盘四宝、
赋文征验）皆须组合进对所问之解释。数子模块拼为「一个视角」：

  ① 用神成败 —— 用神落宫 × 力量推理链 × 用神宫
  ② 值符值使 —— 值符宫 × 值使宫 × 关系
  ③ 方位时机 —— 吉凶方位 × 应期 × 马星空亡
  ④ 格局成破 —— 格局 × 伏吟反吟 × 击刑入墓
  ⑤ 三盘四宝 —— 天地人神盘 × 局数元
  ⑥ 赋文征验 —— 烟波钓叟赋 × 用事原则
"""
from __future__ import annotations
from typing import Dict, Any, List


def build_perspectives(chart: Dict[str, Any]) -> Dict[str, Any]:
    palaces = chart.get("palaces", []) or []
    if not palaces:
        return {"available": False}

    ys = chart.get("yong_shen", {}) or {}
    ysf = chart.get("yongshen_synthesis", {}) or {}
    ysp = chart.get("yongshen_palaces", {}) or {}
    zf = chart.get("zhifu_analysis", {}) or {}
    patterns = chart.get("patterns", []) or []
    best = chart.get("best_palaces", []) or []
    worst = chart.get("worst_palaces", []) or []
    timing = chart.get("yingqi", {}) or chart.get("timing", {}) or {}
    ff = chart.get("fuyin_fanyin", {}) or {}
    ls = chart.get("layer_summary", {}) or {}
    yanbo = chart.get("yanbo_notes", []) or []

    items = {it.get("role", ""): it for it in (ysp.get("items", []) or [])}
    lenses: List[Dict[str, Any]] = []

    # ① 用神成败
    bits = [f"所问「{ys.get('topic','')}」以{ys.get('name','用神')[:6]}为用，落{ys.get('palace','')}、品「{ys.get('quality','平')}」"]
    if ysf.get("available"):
        bits.append(f"综合力量评「{ysf.get('composite_label','')}」（{ysf.get('composite_desc','')[:24]}）")
    if "用神宫" in items:
        bits.append(f"用神宫{items['用神宫'].get('layer','')}")
    lenses.append({
        "id": "yongshen", "title": "用神成败", "icon": "用",
        "modules": ["用神落宫", "力量推理链", "用神宫"],
        "text": "从用神成败论——" + "；".join(bits) + "。此为所问成败之根本。",
    })

    # ② 值符值使
    zfs = zf.get("zhifu", {}) or {}
    zss = zf.get("zhishi", {}) or {}
    rel = zf.get("relationship", {}) or {}
    bits = []
    if zfs:
        bits.append(f"值符{zfs.get('star','')}临{zfs.get('palace','')}（{zfs.get('wangshuai','')}）——主长远前景、贵人")
    if zss:
        bits.append(f"值使{zss.get('door','')}临{zss.get('palace','')}——主事之经过结果")
    if rel.get("name"):
        bits.append(f"二者{rel['name']}（{rel.get('level','')}）：{rel.get('detail','')[:20]}")
    lenses.append({
        "id": "zhifu", "title": "值符值使", "icon": "符",
        "modules": ["值符宫", "值使宫", "符使关系"],
        "text": "从值符值使论——" + "；".join(bits) + "。值符值使为一局枢纽，定主客先后、贵人助力。",
    })

    # ③ 方位时机
    bits = []
    if best:
        bits.append("吉方：" + "、".join(best[:4]) + "——宜向此行事求谋")
    if worst:
        bits.append("凶方：" + "、".join(worst[:3]) + "——避之")
    tv = timing.get("verdict") or timing.get("text") or ""
    if tv:
        bits.append("应期：" + tv[:36])
    sp = ls.get("special", {}) or {}
    if sp.get("马星宫"):
        bits.append("马星动于" + "、".join(sp["马星宫"][:2]) + "——主动象、出行迁动")
    if sp.get("空亡宫"):
        bits.append("空亡于" + "、".join(sp["空亡宫"][:2]) + "——其方其事多落空")
    lenses.append({
        "id": "fangwei", "title": "方位时机", "icon": "方",
        "modules": ["吉凶方位", "应期", "马星空亡"],
        "text": "从方位时机论——" + "；".join(bits) + "。择吉方吉时而动，则借天时地利之助。",
    })

    # ④ 格局成破
    bits = []
    good = [p for p in patterns if p.get("severity") == "auspicious"]
    bad = [p for p in patterns if p.get("severity") == "inauspicious"]
    if good:
        bits.append("吉格：" + "、".join(p.get("name", "") for p in good[:3]))
    if bad:
        bits.append("凶格：" + "、".join(p.get("name", "") for p in bad[:3]))
    if ff.get("detected"):
        bits.append(f"全局{ff.get('type','')}——{ff.get('desc','')[:24]}")
    sp = ls.get("special", {}) or {}
    if sp.get("击刑宫"):
        bits.append("击刑于" + "、".join(sp["击刑宫"][:2]))
    if sp.get("入墓宫"):
        bits.append("入墓于" + "、".join(sp["入墓宫"][:2]))
    lenses.append({
        "id": "geju", "title": "格局成破", "icon": "格",
        "modules": ["格局", "伏吟反吟", "击刑入墓"],
        "text": "从格局成破论——" + "；".join(bits) + "。格局为奇门之筋骨，吉格助成、凶格须避须化。",
    })

    # ⑤ 三盘四宝
    sibao = chart.get("sibao_desc", "") or "天盘九星×人盘八门×地盘九宫×神盘八神"
    ju = f"{chart.get('ju_type','')}{chart.get('ju_number','')}局（{chart.get('yuan','')}）"
    lenses.append({
        "id": "sanpan", "title": "三盘四宝", "icon": "盘",
        "modules": ["天地人神盘", "局数元"],
        "text": f"从三盘四宝论——此局{ju}。{sibao}。四盘叠合，天时、人和、地利、神助合参，方为完整之局。",
    })

    # ⑥ 赋文征验
    bits = []
    if yanbo:
        bits.append("《烟波钓叟赋》云：" + "；".join(y[:24] for y in yanbo[:2]))
    if ys.get("rules"):
        bits.append("用事之法：" + ys["rules"][:40])
    lenses.append({
        "id": "fuwen", "title": "赋文征验", "icon": "赋",
        "modules": ["烟波钓叟赋", "用事原则"],
        "text": "从赋文征验论——" + ("；".join(bits) if bits else "以古赋断验为凭") + "。以经典赋诀印证此局之吉凶取舍。",
    })

    coverage = {}
    for ln in lenses:
        for m in ln["modules"]:
            coverage[m] = ln["title"]

    return {
        "available": True,
        "topic": ys.get("topic", ""),
        "lenses": lenses,
        "coverage": coverage,
    }
