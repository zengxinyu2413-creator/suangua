"""
core/date_selection/synthesis.py
================================
择日·吉日力量综合推理链（子模块互助集成层）。

仿八字/玄空 synthesis：择日诸子模块（建除十二神、黄道黑道、吉神、凶煞、
二十八宿、岁破月破、老黄历宜忌）原各自成断，本引擎择「首选吉日」汇于一条
可见推理链——每因子标【来源模块·利/害/中·权重】，合成「吉日力量评定」。
"""
from __future__ import annotations
from typing import Dict, Any, List

_OFFICER_W = {"大吉": 2, "吉": 1, "吉凶互见": 0, "次吉": 1, "小吉": 1, "凶": -1, "大凶": -2}
_STAR_W = {"吉": 1, "大吉": 2, "凶": -1, "中": 0, "平": 0}


def synthesize_zeri(result: Dict[str, Any]) -> Dict[str, Any]:
    best = result.get("best_days", []) or []
    ausp = result.get("auspicious_days", []) or []
    top = best[0] if best else (ausp[0] if ausp else None)
    if not top:
        return {"available": False}

    purpose = result.get("purpose", "")
    factors: List[Dict[str, Any]] = []
    score = 0

    # ① 建除十二神
    on = top.get("officer_nature", "")
    w = _OFFICER_W.get(on, 0)
    score += w
    factors.append({"module": "建除十二神", "factor": f"{top.get('officer','')}日（{on}）",
                    "polarity": "利" if w > 0 else ("害" if w < 0 else "中"), "weight": w,
                    "note": (top.get("officer_detail", "") or "")[:42]})

    # ② 黄道黑道
    hd = top.get("huangdao")
    dg = top.get("day_god", "")
    dgt = top.get("day_god_type", "")
    if hd or "黄道" in str(dgt):
        score += 1
        factors.append({"module": "黄道吉日", "factor": f"黄道·{dg}", "polarity": "利", "weight": 1,
                        "note": "黄道吉日，诸事可为、百无禁忌"})
    elif "黑道" in str(dgt):
        score -= 1
        factors.append({"module": "黑道凶日", "factor": f"黑道·{dg}", "polarity": "害", "weight": -1,
                        "note": "黑道凶日，须吉神化解方可用"})

    # ③ 吉神（天德月德等）
    js = []
    if top.get("tiande"):
        js.append("天德")
    if top.get("yuede"):
        js.append("月德")
    extra = top.get("ji_shen", []) or []
    if isinstance(extra, list):
        js += [str(x) for x in extra[:4]]
    js = list(dict.fromkeys(j for j in js if j))   # 去重保序
    if js:
        w = min(len(js), 3)
        score += w
        factors.append({"module": "吉神", "factor": "、".join(js[:4]), "polarity": "利", "weight": w,
                        "note": "天德月德等吉神临值，能解众凶、增福助吉"})

    # ④ 凶煞
    xs = top.get("xiong_sha", []) or []
    if isinstance(xs, list) and xs:
        w = -min(len(xs), 3)
        score += w
        factors.append({"module": "凶煞", "factor": "、".join(str(x) for x in xs[:4]),
                        "polarity": "害", "weight": w, "note": "凶煞临值，须避其所忌、以吉神制之"})

    # ⑤ 二十八宿
    sn = top.get("star_nature", "")
    w = _STAR_W.get(sn, 0)
    score += w
    factors.append({"module": "二十八宿", "factor": f"{top.get('star','')}宿（{sn or '中'}）",
                    "polarity": "利" if w > 0 else ("害" if w < 0 else "中"), "weight": w,
                    "note": "二十八宿值日，定其宜忌之事"})

    # ⑥ 岁破月破
    if top.get("is_year_breaker"):
        score -= 5
        factors.append({"module": "岁破", "factor": "犯岁破", "polarity": "害", "weight": -5,
                        "note": "日支冲太岁，百事不宜，纵有吉神亦不可用"})
    elif top.get("is_month_breaker"):
        score -= 3
        factors.append({"module": "月破", "factor": "犯月破", "polarity": "害", "weight": -3,
                        "note": "日支冲月建，大耗破败，举事不利"})

    # ⑦ 老黄历宜忌与所择之事
    yi = top.get("yi", []) or []
    ji = top.get("ji", []) or []
    _SYN = {
        "结婚": ["嫁娶", "婚", "纳采", "订盟"], "婚嫁": ["嫁娶", "婚", "纳采"],
        "搬家": ["移徙", "入宅", "搬"], "入宅": ["入宅", "移徙"],
        "动土": ["动土", "破土"], "开业": ["开市", "开业"], "开市": ["开市", "开业"],
        "安葬": ["安葬", "破土", "启钻"], "出行": ["出行", "远行"],
    }
    keys = [purpose] + _SYN.get(purpose, [])
    yi_hit = purpose and any(any(k in str(y) for k in keys) for y in yi)
    ji_hit = purpose and any(any(k in str(j) for k in keys) for j in ji)
    if yi_hit:
        score += 1
        factors.append({"module": "老黄历宜忌", "factor": f"宜「{purpose}」", "polarity": "利", "weight": 1,
                        "note": "老黄历此日正宜所择之事，名实相符"})
    elif ji_hit:
        score -= 2
        factors.append({"module": "老黄历宜忌", "factor": f"忌「{purpose}」", "polarity": "害", "weight": -2,
                        "note": "老黄历此日忌所择之事，虽分数尚可亦须慎用"})

    # ⑧ 吉日力量评定
    if score >= 6:
        label, desc = "上吉之日", "建除黄道俱吉、吉神拱照、宜事相符，乃举事之上选良辰。"
    elif score >= 3:
        label, desc = "吉日可用", "吉多于凶、堪为良辰，配本人八字择时则更稳妥。"
    elif score >= 0:
        label, desc = "平和之日", "吉凶相参，可用而不为上选，须细避冲煞、择吉时为之。"
    elif score >= -3:
        label, desc = "次日宜慎", "凶多于吉，非佳期，若无他选须重重化解、谨慎用之。"
    else:
        label, desc = "凶日勿用", "犯岁破月破或凶煞重重，百事不宜，务另择吉日。"

    seg = []
    for f in factors:
        pol = {"利": "＋", "害": "－", "中": "·"}.get(f["polarity"], "·")
        seg.append(f"〔{f['module']}〕{pol}{f['factor']}")
    chain_text = "　→　".join(seg) + f"　⟹　{label}（综合力{score:+d}）"

    return {
        "available": True,
        "top_date": top.get("date", ""),
        "top_ganzhi": top.get("ganzhi", ""),
        "factors": factors,
        "composite_score": score,
        "composite_label": label,
        "composite_desc": desc,
        "chain_text": chain_text,
    }
