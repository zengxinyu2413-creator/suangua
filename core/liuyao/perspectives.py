"""
core/liuyao/perspectives.py
===========================
六爻·多视角整合解读 —— 「子模块必尽其用」之落地。

最基本之理：一卦所算之每一子模块，都须组合进对所问之解释，不得算而不用、
沦为孤立面板。数子模块拼合，即成「一个视角」之解读。本模块据此把全部分析
结果编为六视角，每视角言明其所汇之子模块，使无一孤儿、且各成一专业之观照：

  ① 用神得失 —— 用神四位 × 力量推理链 × 伏神 × 占事专断
  ② 人我向背 —— 世应概况 × 持世断 × 世身 × 世应生克
  ③ 动变趋势 —— 动爻化变 × 变爻 × 动静卦 × 化合化冲
  ④ 格局聚散 —— 卦体六冲六合 × 三合三会 × 卦身
  ⑤ 生克情态 —— 六神 × 深度关系(十二长生·五行)
  ⑥ 时机应期 —— 应期推算 × 用神旺衰墓空

并随附 coverage：列明每一子模块归于何视角，以备核查「尽其用」。
"""
from __future__ import annotations
from typing import Dict, Any, List

try:
    from core.liuyao.full_reading import _gua_he_chong
except Exception:  # pragma: no cover
    def _gua_he_chong(branches):
        return ""

_LIU_SHEN_BRIEF = {
    "青龙": "青龙主喜庆正派", "朱雀": "朱雀主文书口舌", "勾陈": "勾陈主迟滞牵缠",
    "螣蛇": "螣蛇主虚惊缠绕", "白虎": "白虎主刚猛凶丧", "玄武": "玄武主暗昧阴私",
}


def build_perspectives(result: Dict[str, Any]) -> Dict[str, Any]:
    yaos = result.get("yaos", []) or []
    if not yaos:
        return {"available": False}

    zd = result.get("zonghe_duan", {}) or {}
    roles = zd.get("roles", {}) or {}
    do = result.get("duan_overview", {}) or {}
    ys = result.get("yongshen_strength", {}) or {}
    yong_lq = do.get("yong_liuqin") or (roles.get("用神", {}) or {}).get("liu_qin", "")
    topic = result.get("topic", "")

    lenses: List[Dict[str, Any]] = []

    # ① 用神得失视角
    yr = roles.get("用神", {}) or {}
    ta = result.get("topic_analysis", {}) or {}
    fu = result.get("fu_shen")
    bits = []
    if ys.get("available"):
        bits.append(f"用神{yong_lq}综合评为「{ys.get('composite_label','')}」（{ys.get('composite_desc','')}）")
    elif yr.get("present"):
        bits.append(f"用神{yong_lq}{yr.get('branch','')}{yr.get('wangshuai','')}")
    yuan = roles.get("原神", {}) or {}
    ji = roles.get("忌神", {}) or {}
    if yuan.get("present"):
        bits.append(f"原神{yuan.get('liu_qin','')}{'有力生扶' if yuan.get('force',0) >= 1 else '力弱难生'}")
    if ji.get("present"):
        bits.append(f"忌神{ji.get('liu_qin','')}{'旺而克用' if ji.get('force',0) >= 1 else '休囚无力为害'}")
    if fu and isinstance(fu, dict):
        bits.append(f"用神伏藏（伏{fu.get('fu_branch','')}），待出伏方应")
    if ta.get("verdict"):
        bits.append("专断要旨：" + ta["verdict"].split("。")[0] + "。")
    lenses.append({
        "id": "yongshen", "title": "用神得失", "icon": "◉",
        "modules": ["用神四位", "用神力量推理链", "伏神", "占事专断"],
        "text": "从用神得失论——" + "；".join(bits) + "。此为所问成败之根本。",
    })

    # ② 人我向背视角
    ws = result.get("world_summary", "")
    cs = result.get("chi_shi", {}) or {}
    ss_self = result.get("shi_shen", {}) or {}
    bits = []
    if ws:
        bits.append(ws.replace("‖", "；"))
    if cs.get("world_liu_qin"):
        kj = cs.get("kou_jue", "")
        bits.append(f"{cs['world_liu_qin']}持世" + (f"——{kj.split('。')[0]}" if kj else ""))
    if ss_self.get("desc"):
        bits.append("世身：" + ss_self["desc"].split("。")[0])
    # 用神持世/临应 一句
    yong_world = any(y.get("is_world") for y in yaos if y.get("liu_qin") == yong_lq)
    yong_app = any(y.get("is_application") for y in yaos if y.get("liu_qin") == yong_lq)
    if yong_world:
        bits.append("用神持世，事主在我、主动可期")
    elif yong_app:
        bits.append("用神临应，事系于人、外缘所定")
    lenses.append({
        "id": "renwo", "title": "人我向背", "icon": "⚌",
        "modules": ["世应概况", "持世断", "世身", "世应生克"],
        "text": "从人我向背论——" + "；".join(b for b in bits if b) + "。此辨事之在己在人、主从向背。",
    })

    # ③ 动变趋势视角（动静以 yaos 实算，不信可能失准的 dong_jing count）
    moving = [y for y in yaos if y.get("is_changing")]
    hb = (result.get("hua_bian", {}) or {}).get("moving_lines", []) or []
    hhc = result.get("hua_he_chong", []) or []
    bits = []
    if not moving:
        bits.append("六爻尽静，事无近变，以本卦用神旺衰、世应论之")
    else:
        bits.append(f"{len(moving)}爻发动，事态有变")
        tend = [m.get("tendency", "") for m in hb if m.get("tendency")]
        if tend:
            bits.append("化变之势：" + "、".join(dict.fromkeys(tend)))
        if hhc:
            bits.append("动爻间复有化合化冲之纠葛")
    lenses.append({
        "id": "dongbian", "title": "动变趋势", "icon": "☲",
        "modules": ["动爻化变", "变爻", "动静卦", "化合化冲"],
        "text": "从动变趋势论——" + "；".join(bits) + "。此观事态演变、先后吉凶之转移。",
    })

    # ④ 格局聚散视角
    branches = [y.get("branch", "") for y in yaos]
    hc = _gua_he_chong(branches)
    ss = result.get("sanhe_sanhui", {}) or {}
    locals_ = (ss.get("sanhe", []) or []) + (ss.get("sanhui", []) or [])
    gs = result.get("gua_shen", {}) or {}
    bits = []
    if hc == "六合":
        bits.append("本卦六合，诸事聚合、易就")
    elif hc == "六冲":
        bits.append("本卦六冲，诸事散乱、难久")
    else:
        bits.append("卦体非冲非合，聚散以三合及用神论")
    if locals_:
        bits.append("卦中结「" + "、".join(l.get("name", "") for l in locals_) + "」之局，气有所聚")
    if gs.get("zhi"):
        bits.append(f"卦身在{gs['zhi']}" + ("（现于卦中，事有主体可凭）" if gs.get("in_chart") else "（不上卦，事或无定体）"))
    lenses.append({
        "id": "geju", "title": "格局聚散", "icon": "☶",
        "modules": ["卦体六冲六合", "三合三会", "卦身"],
        "text": "从格局聚散论——" + "；".join(bits) + "。此察事之成局与否、聚散之大势。",
    })

    # ⑤ 生克情态视角（六神 + 深度关系）
    dr = result.get("deep_relations", {}) or {}
    bits = []
    yong_yao = next((y for y in yaos if y.get("liu_qin") == yong_lq), None)
    if yong_yao and yong_yao.get("liu_shen") in _LIU_SHEN_BRIEF:
        bits.append(f"用神临{yong_yao['liu_shen']}——{_LIU_SHEN_BRIEF[yong_yao['liu_shen']]}")
    # 全卦六神点睛（取吉凶六神）
    shen_present = [y.get("liu_shen") for y in yaos if y.get("liu_shen")]
    aux = [s for s in ("白虎", "玄武", "青龙") if s in shen_present]
    if aux:
        bits.append("卦中" + "、".join(aux) + "临爻，情态各异")
    yyjc = dr.get("yong_yuan_ji_chou", {})
    if yyjc:
        bits.append(f"用神{yyjc.get('用神_wx','')}、原神{yyjc.get('原神_wx','')}、忌神{yyjc.get('忌神_wx','')}，五行生克成局")
    lenses.append({
        "id": "qingtai", "title": "生克情态", "icon": "☵",
        "modules": ["六神", "深度关系·五行十二长生"],
        "text": "从生克情态论——" + "；".join(b for b in bits if b) + "。此味事之吉凶氛围、神煞情性。",
    })

    # ⑥ 时机应期视角
    yq_text = do.get("yingqi_text", "")
    yq = result.get("yingqi", {}) or {}
    bits = []
    if yq_text:
        bits.append(yq_text)
    elif yq.get("verdict"):
        bits.append(yq["verdict"])
    if yr.get("entombed"):
        bits.append("（用神入墓，重在冲墓之日）")
    elif yr.get("is_kong"):
        bits.append("（用神逢空，重在填实出空之日）")
    lenses.append({
        "id": "shiji", "title": "时机应期", "icon": "☷",
        "modules": ["应期推算", "用神旺衰墓空"],
        "text": "从时机应期论——" + "".join(bits) + (" " if bits else "应期未明，以应月应年论之。") + "此定事之何时见验。",
    })

    # coverage 汇总（子模块归属，供尽其用核查）
    coverage = {}
    for ln in lenses:
        for m in ln["modules"]:
            coverage[m] = ln["title"]

    return {
        "available": True,
        "question": result.get("question", ""),
        "topic": topic,
        "lenses": lenses,
        "coverage": coverage,
    }
