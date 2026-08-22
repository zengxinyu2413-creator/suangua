"""
core/liuyao/consistency_audit.py
================================
六爻·断卦一致性审核引擎（确定性层）。

各子模块各自成断，彼此可能潜藏矛盾：综合断言用神不墓、应期却按入墓推算；
极性三处不一；综合力量与吉凶结论相左；用神两现而取舍未明……规则引擎不会
自我报警。本引擎据已知矛盾型态，确定性地逐项核查，产出结构化「审核发现」，
每条标明：涉及哪些模块、轻重几何（矛盾/注意/提示）、缘由、建议。

此为可测试、可复现之硬核检测；其上另有 AI「审定意见」层（judgment），
对这些发现作情境化解释与取舍，明标 AI 辅助、不覆盖引擎结论。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SEV_RANK = {"矛盾": 3, "注意": 2, "提示": 1}


def _polarity_dir(p: str) -> str:
    """极性归向：吉向 / 凶向 / 平。先验凶象（不成/难成等含'成'字仍属凶）。"""
    if not p:
        return ""
    if any(k in p for k in ("凶", "败", "不成", "难", "不利", "不宜")):
        return "凶向"
    if any(k in p for k in ("吉", "成", "利", "可成")):
        return "吉向"
    return "平"


def audit_consistency(result: Dict[str, Any]) -> Dict[str, Any]:
    """据已知型态核查跨模块一致性。"""
    findings: List[Dict[str, Any]] = []

    do = result.get("duan_overview", {}) or {}
    zd = result.get("zonghe_duan", {}) or {}
    tv = result.get("topic_verdict", {}) or {}
    ys = result.get("yongshen_strength", {}) or {}
    yaos = result.get("yaos", []) or []
    roles = zd.get("roles", {}) or {}
    yr = roles.get("用神", {}) or {}
    yong_lq = do.get("yong_liuqin") or yr.get("liu_qin", "")

    # ① 用神两现取舍
    yong_yaos = [y for y in yaos if y.get("liu_qin") == yong_lq]
    if len(yong_yaos) >= 2:
        locs = []
        for y in yong_yaos:
            t = []
            if y.get("is_world"):
                t.append("持世")
            if y.get("is_application"):
                t.append("临应")
            if y.get("is_changing"):
                t.append("发动")
            locs.append(f"第{y.get('position')}爻{y.get('branch','')}"
                        + (f"（{'·'.join(t)}）" if t else "（静）"))
        used = yr.get("branch", "")
        findings.append({
            "id": "yong_duplication",
            "severity": "提示",
            "title": "用神两现 · 取舍宜明",
            "modules": ["用神选取", "综合断卦"],
            "detail": f"用神{yong_lq}两现——{'、'.join(locs)}。系统现取{used}为用。",
            "suggestion": "《增删卜易》云用神两现舍其一：宜取持世者、或独发者、或旬空者为用，"
                          "余爻参看。两现分持世应者，多主自他俱涉、事有两端。",
        })

    # ② 旺衰（综合断）vs 应期（入墓/逢空）矛盾
    yq_text = do.get("yingqi_text", "") or (result.get("yingqi", {}) or {}).get("verdict", "")
    state_mu = bool(yr.get("entombed"))
    state_kong = bool(yr.get("is_kong"))
    yq_mu = ("入墓" in yq_text) or ("墓" in yq_text and "冲墓" in yq_text)
    yq_kong = ("逢空" in yq_text) or ("出空" in yq_text) or ("填实" in yq_text)
    if yq_mu and not state_mu:
        findings.append({
            "id": "mu_conflict",
            "severity": "矛盾",
            "title": "用神入墓 · 两模块判断相左",
            "modules": ["综合断卦", "应期推算"],
            "detail": f"综合断判用神{yong_lq}{yr.get('wangshuai','')}、未入墓（entombed=False），"
                      f"然应期推算却按「用神入墓、冲墓开库」立论。二者对用神是否入墓结论相反。",
            "suggestion": "须核：应期所论之墓，或系用神另一现（如临应之爻坐墓）、或日墓时墓之别。"
                          "宜明确以哪一爻、何种墓论之，免致旺相之用神误作入墓推期。",
        })
    elif state_mu and not yq_mu:
        findings.append({
            "id": "mu_conflict2",
            "severity": "注意",
            "title": "用神入墓 · 应期未及墓象",
            "modules": ["综合断卦", "应期推算"],
            "detail": f"综合断判用神入墓，然应期推算未按冲墓开库立论。",
            "suggestion": "入墓之用神，应期当重冲墓之日；宜复核应期是否已计墓象。",
        })
    if yq_kong and not state_kong:
        findings.append({
            "id": "kong_conflict",
            "severity": "注意",
            "title": "用神逢空 · 两模块判断不一",
            "modules": ["综合断卦", "应期推算"],
            "detail": "应期按用神逢空（填实出空）立论，然综合断未标用神旬空。",
            "suggestion": "宜核用神是否真空：旺不为空、动不为空、有日生扶亦不以空论。",
        })

    # ③ 极性跨模块分歧
    pols = {
        "综合断卦": _polarity_dir(zd.get("conclusion", "")),
        "断卦总览": _polarity_dir(do.get("polarity", "")),
        "占事专断": _polarity_dir(tv.get("polarity", "")),
    }
    dirs = {v for v in pols.values() if v in ("吉向", "凶向")}
    if "吉向" in dirs and "凶向" in dirs:
        detail = "；".join(f"{k}判{v}" for k, v in pols.items() if v)
        findings.append({
            "id": "polarity_split",
            "severity": "矛盾",
            "title": "吉凶极性 · 跨模块分歧",
            "modules": list(pols.keys()),
            "detail": f"各模块吉凶取向不一：{detail}。",
            "suggestion": "宜以用神综合力量为主、占事专断为辅定其吉凶；分歧多因取用神或看法侧重不同所致。",
        })

    # ④ 综合力量 vs 吉凶结论 张力
    comp = ys.get("composite_label", "")
    concl_dir = _polarity_dir(do.get("polarity", "") or zd.get("conclusion", ""))
    if comp in ("综合无力",) and concl_dir == "吉向":
        findings.append({
            "id": "strength_verdict_tension",
            "severity": "注意",
            "title": "用神无力 · 结论却吉",
            "modules": ["用神力量评估", "断卦总览"],
            "detail": f"用神综合力量评为「{comp}」，然总断仍作吉。",
            "suggestion": "用神无力而言吉，多赖应期得力引动或原神来生；若无外援，吉象恐虚，宜降信心。",
        })
    elif comp in ("综合大有力",) and concl_dir == "凶向":
        findings.append({
            "id": "strength_verdict_tension2",
            "severity": "注意",
            "title": "用神大有力 · 结论却凶",
            "modules": ["用神力量评估", "断卦总览"],
            "detail": f"用神综合力量评为「{comp}」，然总断作凶。",
            "suggestion": "用神有力而言凶者，多因忌神更旺、或用神虽旺而临凶神动克；宜复核忌神之势。",
        })

    # ⑤ 动爻众多 · 卦变剧烈
    n_dong = sum(1 for y in yaos if y.get("is_changing"))
    if n_dong >= 3:
        findings.append({
            "id": "high_volatility",
            "severity": "提示",
            "title": f"{n_dong}爻乱动 · 卦变剧烈",
            "modules": ["动爻化变", "综合断卦"],
            "detail": f"卦中{n_dong}爻发动，事多头绪、变数丛生。",
            "suggestion": "乱动之卦，《卜筮正宗》主取独静之爻、或专看用神之动向；事多反复，结论宜留余地。",
        })

    # ⑤' 动静卦自身错算（dong_jing_analysis.moving_count vs 实际动爻）
    dj = result.get("dong_jing_analysis", {}) or {}
    if dj:
        dj_count = dj.get("moving_count")
        if isinstance(dj_count, int) and dj_count != n_dong:
            findings.append({
                "id": "dongjing_count_mismatch",
                "severity": "矛盾",
                "title": "动静卦计数 · 与实际动爻不符",
                "modules": ["动静卦分析", "六爻装卦"],
                "detail": f"动静卦分析判为「{dj.get('type','')}」、动爻数{dj_count}，"
                          f"然实际卦中有 {n_dong} 爻发动。动静模块计数失准。",
                "suggestion": "动静卦须以实际变爻数为准；此为模块内部计数错误，应以装卦之动爻为信。",
            })

    # ⑥ 用神持世又另现临应（自他俱涉）
    w = next((y for y in yong_yaos if y.get("is_world")), None)
    a = next((y for y in yong_yaos if y.get("is_application")), None)
    if w and a and w is not a:
        findings.append({
            "id": "world_app_both_yong",
            "severity": "提示",
            "title": "用神分踞世应 · 自他俱涉",
            "modules": ["用神选取", "世应关系"],
            "detail": "用神既持世、又见于应——所问之事己方他方俱有牵涉。",
            "suggestion": "此象多主事关两造、或己身与外缘交织；宜辨主用神（持世者主己）与次用神（临应者主他）之向背。",
        })

    # 汇总
    n_conflict = sum(1 for f in findings if f["severity"] == "矛盾")
    n_attn = sum(1 for f in findings if f["severity"] == "注意")
    n_tip = sum(1 for f in findings if f["severity"] == "提示")
    findings.sort(key=lambda f: -_SEV_RANK.get(f["severity"], 0))

    if n_conflict:
        verdict = f"发现 {n_conflict} 处跨模块矛盾，宜审定后再据以决断。"
    elif n_attn:
        verdict = f"未见硬性矛盾，有 {n_attn} 处需注意之张力。"
    elif n_tip:
        verdict = f"各模块结论协调一致，余 {n_tip} 处常规提示。"
    else:
        verdict = "各模块结论彼此协调，无矛盾。"

    return {
        "available": True,
        "summary": {"矛盾": n_conflict, "注意": n_attn, "提示": n_tip},
        "verdict": verdict,
        "findings": findings,
        "clean": n_conflict == 0 and n_attn == 0,
    }
