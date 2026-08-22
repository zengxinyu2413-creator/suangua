"""
core/fengshui/xuankong_overview.py
==================================
玄空飞星·宅运总论合成（综合总论层）。

玄空诸果（运盘坐向、三盘山向格局、特殊格局、正零神城门、峦头旺衰方）原散见各处。
本引擎以「三盘山向之格局」为纲，织之成篇，并提炼宅运定盘（旺山旺向/上山下水 +
吉凶等第）置顶 hero。仿八字/紫微 overview 之法。
"""
from __future__ import annotations
from typing import Dict, Any, List

# verdict_level → 吉凶质量
_LEVEL_Q = {
    "auspicious_great": "吉", "auspicious": "吉",
    "inauspicious": "凶", "inauspicious_great": "凶",
    "neutral": "中", "mixed": "中",
}


def synthesize_overview(chart: Dict[str, Any]) -> Dict[str, Any]:
    if not chart or not chart.get("verdict"):
        return {"available": False}

    yun = chart.get("yun", {}) or {}
    yun_name = yun.get("yun_name", "") if isinstance(yun, dict) else str(yun)
    sanyuan = yun.get("sanyuan", "") if isinstance(yun, dict) else ""
    sitting = chart.get("sitting_mountain", "")
    facing = chart.get("facing_mountain", "")
    sit_gua = chart.get("sitting_gua", "")

    verdict = chart.get("verdict", "")
    level = chart.get("verdict_level", "")
    vdesc = chart.get("verdict_desc", "")
    q = _LEVEL_Q.get(level, "中")

    paras: List[Dict[str, str]] = []

    # ① 运盘坐向
    p1 = f"此宅立{sitting}山{facing}向（坐{sit_gua}卦），值{sanyuan}{yun_name}运。"
    p1 += "玄空之法，以三元九运配二十四山，飞布运山向三盘，合参以断宅运吉凶。"
    paras.append({"title": "运盘坐向", "text": p1})

    # ② 三盘格局（答案核心）
    p2 = f"三盘合断，得「{verdict}」之局。{vdesc}"
    paras.append({"title": "山向格局", "text": p2})

    # ③ 特殊格局
    sps = chart.get("special_patterns", []) or []
    if sps:
        good = [s for s in sps if s.get("level", "").startswith("auspicious")]
        bad = [s for s in sps if s.get("level", "").startswith("inauspicious")]
        p3 = ""
        if good:
            p3 += "得吉格：" + "、".join(f"{g.get('name','')}（{g.get('desc','')[:20]}）" for g in good[:2]) + "。"
        if bad:
            p3 += "犯凶象：" + "、".join(f"{b.get('name','')}（{b.get('desc','')[:18]}）" for b in bad[:2]) + "，须化解。"
        if p3:
            paras.append({"title": "特殊格局", "text": p3})

    # ④ 正零神 · 城门
    zls = chart.get("zheng_ling_shen", {}) or {}
    cm = chart.get("chengmen", {}) or {}
    p4 = ""
    zs = zls.get("zhengshen", {}) or {}
    if zs:
        p4 += f"正神在{zs.get('zhengshen_dir','')}（{zs.get('zhengshen_gua','')}）宜静宜高，零神在{zs.get('lingshen_dir','')}宜动宜水。"
    if cm.get("desc"):
        p4 += "　" + cm["desc"][:50]
    if p4:
        paras.append({"title": "正零城门", "text": p4})

    # ⑤ 峦头旺衰方
    lt = chart.get("luantou_summary", {}) or {}
    if lt.get("wang_directions"):
        p5 = f"当运旺方：{('、'.join(lt['wang_directions']))}，宜开门、设灶、置动；"
        if lt.get("shuai_directions"):
            p5 += f"衰死方：{('、'.join(lt['shuai_directions']))}，宜静宜实、忌动忌水。"
        paras.append({"title": "峦头旺衰", "text": p5})

    # ⑤.5 命卦人盘（玄空纳命卦 — 因人而宜）
    mr = chart.get("mingua_renpan", {}) or {}
    if mr.get("available"):
        p55 = (f"以主人{mr.get('ming_gua','')}命（{mr.get('ming_group','')}）配此宅理气：")
        if mr.get("best_dirs"):
            p55 += f"宜居用之方（当运旺方又命卦吉方）：{('、'.join(mr['best_dirs']))}，最宜安主卧、书房、大门；"
        if mr.get("avoid_dirs"):
            p55 += f"切忌之方（衰方又命卦凶方）：{('、'.join(mr['avoid_dirs']))}，宜作储藏、卫浴、避久居。"
        if not mr.get("best_dirs") and not mr.get("avoid_dirs"):
            p55 += "旺衰与命卦吉凶无显著相叠，宜取命卦吉方为主、理气旺方为辅。"
        paras.append({"title": "命卦宜居", "text": p55})

    # ⑥ 总评
    tone = {
        "吉": f"宅得「{verdict}」上吉之局，丁财可期、根基稳固，宜顺其旺方布局、催吉避煞。",
        "中": f"宅局「{verdict}」吉凶相参，须以峦头配理气、趋旺避衰、化解凶煞，方得安稳。",
        "凶": f"宅犯「{verdict}」之失，丁财或损，尤须以城门、化解、峦头补救，避其凶方、缓动凶位。",
    }.get(q)
    paras.append({"title": "宅运总评", "text": tone})

    headline = f"{sanyuan}{yun_name}运·{sitting}山{facing}向·{verdict}"

    return {
        "available": True,
        "headline": headline,
        "quality": q,
        "verdict": verdict,
        "verdict_desc": vdesc,
        "yun_name": yun_name,
        "sitting": sitting,
        "facing": facing,
        "verdict_line": tone,
        "paragraphs": paras,
    }
