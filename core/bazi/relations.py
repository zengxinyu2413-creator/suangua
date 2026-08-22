"""
core/bazi/relations.py
======================
B-1: 八字地支刑冲合害自动检测引擎。

涵盖：
  1. 六合（子丑、寅亥、卯戌、辰酉、巳申、午未）
  2. 三合局（申子辰水、亥卯未木、寅午戌火、巳酉丑金）
  3. 三会方（寅卯辰东方木、巳午未南方火、申酉戌西方金、亥子丑北方水）
  4. 六冲（子午、丑未、寅申、卯酉、辰戌、巳亥）
  5. 相刑（寅巳申、丑戌未三刑；子卯互刑；辰午酉亥自刑）
  6. 相害（子未、丑午、寅巳、卯辰、申亥、酉戌）
  7. 相破（子酉、午卯、巳申、寅亥、辰丑、戌未）

每个事件附带：
  · 类型 / 涉及柱位 / 涉及地支
  · 命理学吉凶判断
  · 应期触发条件（大运/流年触发哪种生克）
  · 中文解读
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple

# ─────────────────────────────────────────────────────────────
# 1. 地支关系字典（成对/三组关系）
# ─────────────────────────────────────────────────────────────

# 六合：合后所化五行
LIU_HE: Dict[frozenset, str] = {
    frozenset({"子", "丑"}): "土",
    frozenset({"寅", "亥"}): "木",
    frozenset({"卯", "戌"}): "火",
    frozenset({"辰", "酉"}): "金",
    frozenset({"巳", "申"}): "水",
    frozenset({"午", "未"}): "土",  # 一说火土
}

# 三合局：必须有3个地支
SAN_HE: Dict[frozenset, str] = {
    frozenset({"申", "子", "辰"}): "水",
    frozenset({"亥", "卯", "未"}): "木",
    frozenset({"寅", "午", "戌"}): "火",
    frozenset({"巳", "酉", "丑"}): "金",
}

# 三合局的"半合"：两支也算（中神+生神或中神+墓神）
SAN_HE_HALF: List[Tuple[frozenset, str]] = [
    (frozenset({"申", "子"}), "水"), (frozenset({"子", "辰"}), "水"),
    (frozenset({"亥", "卯"}), "木"), (frozenset({"卯", "未"}), "木"),
    (frozenset({"寅", "午"}), "火"), (frozenset({"午", "戌"}), "火"),
    (frozenset({"巳", "酉"}), "金"), (frozenset({"酉", "丑"}), "金"),
]

# 三会方：必须有3个地支
SAN_HUI: Dict[frozenset, str] = {
    frozenset({"寅", "卯", "辰"}): "木",  # 东方
    frozenset({"巳", "午", "未"}): "火",  # 南方
    frozenset({"申", "酉", "戌"}): "金",  # 西方
    frozenset({"亥", "子", "丑"}): "水",  # 北方
}

# 六冲
LIU_CHONG: Set[frozenset] = {
    frozenset({"子", "午"}),
    frozenset({"丑", "未"}),
    frozenset({"寅", "申"}),
    frozenset({"卯", "酉"}),
    frozenset({"辰", "戌"}),
    frozenset({"巳", "亥"}),
}

# 三刑（无恩之刑、恃势之刑）
SAN_XING_GROUPS: List[Tuple[Set[str], str]] = [
    (set("寅巳申"), "无恩之刑"),   # 寅刑巳、巳刑申、申刑寅
    (set("丑戌未"), "恃势之刑"),   # 丑刑戌、戌刑未、未刑丑
]

# 互刑（两支相刑）
HU_XING: Set[frozenset] = {
    frozenset({"子", "卯"}),  # 无礼之刑
}

# 自刑（同支相见为自刑）
ZI_XING: Set[str] = {"辰", "午", "酉", "亥"}

# 相害（六害）
LIU_HAI: Set[frozenset] = {
    frozenset({"子", "未"}),  # 不和
    frozenset({"丑", "午"}),  # 害义
    frozenset({"寅", "巳"}),  # 相争
    frozenset({"卯", "辰"}),  # 凌长
    frozenset({"申", "亥"}),  # 相忌
    frozenset({"酉", "戌"}),  # 嫉妒
}

# 相破（六破）
LIU_PO: Set[frozenset] = {
    frozenset({"子", "酉"}),
    frozenset({"午", "卯"}),
    frozenset({"巳", "申"}),  # 注：巳申是合也是破
    frozenset({"寅", "亥"}),  # 注：寅亥是合也是破
    frozenset({"辰", "丑"}),
    frozenset({"戌", "未"}),
}

# 柱位名映射
PILLAR_NAMES = {
    "year_pillar": "年柱",
    "month_pillar": "月柱",
    "day_pillar": "日柱",
    "hour_pillar": "时柱",
}


# ─────────────────────────────────────────────────────────────
# 2. 提取四柱地支
# ─────────────────────────────────────────────────────────────

def extract_branches(chart: Dict[str, Any]) -> List[Tuple[str, str]]:
    """从 chart 提取四柱地支，返回 [(pillar_key, 地支), ...]"""
    out = []
    for key in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"):
        p = chart.get(key) or {}
        dz = p.get("dizhi") or ""
        if dz:
            out.append((key, dz))
    return out


# ─────────────────────────────────────────────────────────────
# 3. 各类关系检测函数
# ─────────────────────────────────────────────────────────────

def detect_liu_he(branches: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """六合检测"""
    events = []
    n = len(branches)
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset({branches[i][1], branches[j][1]})
            if pair in LIU_HE:
                wuxing = LIU_HE[pair]
                events.append({
                    "type": "六合",
                    "branches": [branches[i][1], branches[j][1]],
                    "pillars": [PILLAR_NAMES[branches[i][0]], PILLAR_NAMES[branches[j][0]]],
                    "wuxing": wuxing,
                    "auspicious": True,
                    "interpretation": (
                        f"{PILLAR_NAMES[branches[i][0]]}{branches[i][1]}"
                        f"与{PILLAR_NAMES[branches[j][0]]}{branches[j][1]}六合化{wuxing}"
                        f"，主和合、贵人，宜合作"
                    ),
                })
    return events


def detect_san_he(branches: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """三合局检测（含半合）"""
    events = []
    n = len(branches)
    
    # 完整三合（三支齐）
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                triple = frozenset({branches[i][1], branches[j][1], branches[k][1]})
                if triple in SAN_HE:
                    wuxing = SAN_HE[triple]
                    events.append({
                        "type": "三合局",
                        "branches": [branches[i][1], branches[j][1], branches[k][1]],
                        "pillars": [PILLAR_NAMES[branches[i][0]],
                                    PILLAR_NAMES[branches[j][0]],
                                    PILLAR_NAMES[branches[k][0]]],
                        "wuxing": wuxing,
                        "auspicious": True,
                        "interpretation": (
                            f"{'、'.join([branches[i][1], branches[j][1], branches[k][1]])}"
                            f"三支齐聚，三合{wuxing}局，主气势凝聚、力量倍增"
                        ),
                    })
    
    # 半合（两支）— 但避免与完整三合重复
    full_triples = set()
    for e in events:
        full_triples.update(e["branches"])
    
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset({branches[i][1], branches[j][1]})
            for half_pair, wuxing in SAN_HE_HALF:
                if pair == half_pair:
                    # 看是否两支都已在完整三合中
                    if set([branches[i][1], branches[j][1]]).issubset(full_triples):
                        continue  # 已在完整三合中，跳过
                    events.append({
                        "type": "半三合",
                        "branches": [branches[i][1], branches[j][1]],
                        "pillars": [PILLAR_NAMES[branches[i][0]], PILLAR_NAMES[branches[j][0]]],
                        "wuxing": wuxing,
                        "auspicious": True,
                        "interpretation": (
                            f"{branches[i][1]}{branches[j][1]}半合{wuxing}"
                            f"，若大运或流年遇到补齐的第三支则全合"
                        ),
                    })
                    break
    return events


def detect_san_hui(branches: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """三会方检测"""
    events = []
    n = len(branches)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                triple = frozenset({branches[i][1], branches[j][1], branches[k][1]})
                if triple in SAN_HUI:
                    wuxing = SAN_HUI[triple]
                    events.append({
                        "type": "三会方",
                        "branches": [branches[i][1], branches[j][1], branches[k][1]],
                        "pillars": [PILLAR_NAMES[branches[i][0]],
                                    PILLAR_NAMES[branches[j][0]],
                                    PILLAR_NAMES[branches[k][0]]],
                        "wuxing": wuxing,
                        "auspicious": True,
                        "interpretation": (
                            f"{'、'.join([branches[i][1], branches[j][1], branches[k][1]])}"
                            f"三会{wuxing}方，五行气势极旺，比三合更强"
                        ),
                    })
    return events


def detect_liu_chong(branches: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """六冲检测"""
    events = []
    n = len(branches)
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset({branches[i][1], branches[j][1]})
            if pair in LIU_CHONG:
                p1 = PILLAR_NAMES[branches[i][0]]
                p2 = PILLAR_NAMES[branches[j][0]]
                # 日月冲、年时冲等重点解读
                positions = {branches[i][0], branches[j][0]}
                key_chong = (
                    "日月相冲（中年动荡）" if "day_pillar" in positions and "month_pillar" in positions
                    else "年月相冲（少年家境波动）" if "year_pillar" in positions and "month_pillar" in positions
                    else "日时相冲（晚年/子嗣有变）" if "day_pillar" in positions and "hour_pillar" in positions
                    else "年时相冲（首末相冲，根基不稳）" if "year_pillar" in positions and "hour_pillar" in positions
                    else "相冲"
                )
                events.append({
                    "type": "六冲",
                    "branches": [branches[i][1], branches[j][1]],
                    "pillars": [p1, p2],
                    "key": key_chong,
                    "auspicious": False,
                    "interpretation": (
                        f"{p1}{branches[i][1]}与{p2}{branches[j][1]}六冲"
                        f"（{key_chong}）— 主动荡、变化、克冲，吉星受冲减力，凶星受冲反激"
                    ),
                })
    return events


def detect_xing(branches: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """相刑检测（三刑+互刑+自刑）"""
    events = []
    n = len(branches)
    branch_only = [b[1] for b in branches]
    pillar_only = [b[0] for b in branches]
    
    # 三刑组
    for xing_set, xing_name in SAN_XING_GROUPS:
        # 看四柱里是否包含三刑组中至少 2 支
        present = []
        for i, b in enumerate(branch_only):
            if b in xing_set:
                present.append(i)
        if len(present) >= 2:
            # 取出所有出现的支和柱
            shown_branches = [branch_only[i] for i in present]
            shown_pillars = [PILLAR_NAMES[pillar_only[i]] for i in present]
            events.append({
                "type": "三刑" if len(present) >= 3 else "刑（部分三刑）",
                "branches": shown_branches,
                "pillars": shown_pillars,
                "subtype": xing_name,
                "auspicious": False,
                "interpretation": (
                    f"{'、'.join(shown_branches)}见{xing_name}"
                    f"（"
                    + ("三刑齐聚" if len(present) >= 3 else "三刑见两支")
                    + "）— 主刑伤、官非、人际冲突"
                ),
            })
    
    # 互刑（子卯）
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset({branches[i][1], branches[j][1]})
            if pair in HU_XING:
                events.append({
                    "type": "互刑",
                    "branches": [branches[i][1], branches[j][1]],
                    "pillars": [PILLAR_NAMES[branches[i][0]], PILLAR_NAMES[branches[j][0]]],
                    "subtype": "无礼之刑",
                    "auspicious": False,
                    "interpretation": (
                        f"{branches[i][1]}{branches[j][1]}互刑（无礼之刑）"
                        f"— 主人际关系紧张、犯小人"
                    ),
                })
    
    # 自刑（同支重叠）
    branch_counts: Dict[str, List[str]] = {}
    for k, dz in branches:
        if dz in ZI_XING:
            branch_counts.setdefault(dz, []).append(PILLAR_NAMES[k])
    for dz, plist in branch_counts.items():
        if len(plist) >= 2:
            events.append({
                "type": "自刑",
                "branches": [dz] * len(plist),
                "pillars": plist,
                "subtype": f"{dz}自刑",
                "auspicious": False,
                "interpretation": (
                    f"{dz}自刑（{'/'.join(plist)}皆为{dz}）"
                    f"— 主自我冲突、内耗，情绪反复"
                ),
            })
    return events


def detect_hai(branches: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """相害检测"""
    events = []
    n = len(branches)
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset({branches[i][1], branches[j][1]})
            if pair in LIU_HAI:
                events.append({
                    "type": "相害",
                    "branches": [branches[i][1], branches[j][1]],
                    "pillars": [PILLAR_NAMES[branches[i][0]], PILLAR_NAMES[branches[j][0]]],
                    "auspicious": False,
                    "interpretation": (
                        f"{PILLAR_NAMES[branches[i][0]]}{branches[i][1]}"
                        f"与{PILLAR_NAMES[branches[j][0]]}{branches[j][1]}相害"
                        f"— 暗损、内伤、阴损，影响六亲缘分"
                    ),
                })
    return events


def detect_po(branches: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """相破检测（次要语象，已被合掩盖时不重复报）"""
    events = []
    n = len(branches)
    for i in range(n):
        for j in range(i + 1, n):
            pair = frozenset({branches[i][1], branches[j][1]})
            if pair in LIU_PO:
                # 若已经构成六合或六冲，跳过相破
                if pair in LIU_HE or pair in LIU_CHONG:
                    continue
                events.append({
                    "type": "相破",
                    "branches": [branches[i][1], branches[j][1]],
                    "pillars": [PILLAR_NAMES[branches[i][0]], PILLAR_NAMES[branches[j][0]]],
                    "auspicious": False,
                    "interpretation": (
                        f"{branches[i][1]}{branches[j][1]}相破"
                        f"— 破坏、损耗（次要语象）"
                    ),
                })
    return events


# ─────────────────────────────────────────────────────────────
# 4. 主入口
# ─────────────────────────────────────────────────────────────

def analyze_all_relations(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    主分析入口：对一张四柱命盘做全部刑冲合害分析。
    
    Returns:
        {
            "he":     [六合 + 三合 + 半合 + 三会 events ...],
            "chong":  [六冲 events ...],
            "xing":   [刑 events ...],
            "hai":    [害 events ...],
            "po":     [破 events ...],
            "summary": {
                "total_he":     int,
                "total_chong":  int,
                "total_xing":   int,
                "total_hai":    int,
                "total_po":     int,
                "key_warnings": [中文警示...],
                "key_blessings":[中文吉象...],
            }
        }
    """
    branches = extract_branches(chart)
    
    he_events    = detect_liu_he(branches) + detect_san_he(branches) + detect_san_hui(branches)
    chong_events = detect_liu_chong(branches)
    xing_events  = detect_xing(branches)
    hai_events   = detect_hai(branches)
    po_events    = detect_po(branches)
    
    # 生成关键警示和吉象
    key_warnings: List[str] = []
    key_blessings: List[str] = []
    
    for e in chong_events:
        key_warnings.append(f"⚠ {e['interpretation']}")
    for e in xing_events:
        key_warnings.append(f"⚠ {e['interpretation']}")
    for e in hai_events[:2]:  # 害较轻，前2条
        key_warnings.append(f"· {e['interpretation']}")
    
    # 三合/三会优先于六合
    for e in he_events:
        if e["type"] in ("三合局", "三会方"):
            key_blessings.append(f"✦ {e['interpretation']}")
    for e in he_events:
        if e["type"] == "六合":
            key_blessings.append(f"· {e['interpretation']}")
    
    return {
        "he":    he_events,
        "chong": chong_events,
        "xing":  xing_events,
        "hai":   hai_events,
        "po":    po_events,
        "summary": {
            "total_he":     len(he_events),
            "total_chong":  len(chong_events),
            "total_xing":   len(xing_events),
            "total_hai":    len(hai_events),
            "total_po":     len(po_events),
            "key_warnings": key_warnings,
            "key_blessings": key_blessings,
        },
    }


# ─────────────────────────────────────────────────────────────
# 5. 大运/流年应期分析 — 触发现有刑冲合害的"激活"
# ─────────────────────────────────────────────────────────────

def analyze_dayun_liunian_trigger(
    chart: Dict[str, Any],
    target_branch: str,
    target_label: str = "大运",
) -> List[Dict[str, Any]]:
    """
    某个大运/流年地支与本命四柱的刑冲合害关系。
    
    用于："2025 流年丙午"会冲哪个柱、合哪个柱。
    """
    natal_branches = extract_branches(chart)
    triggers = []
    
    for pillar_key, natal_dz in natal_branches:
        pair = frozenset({target_branch, natal_dz})
        pname = PILLAR_NAMES[pillar_key]
        
        if pair in LIU_CHONG:
            triggers.append({
                "type": "冲",
                "trigger": f"{target_label}{target_branch}",
                "target": f"{pname}{natal_dz}",
                "auspicious": False,
                "interpretation": (
                    f"{target_label}{target_branch}冲{pname}{natal_dz}"
                    f" — 触发该柱所代表的人事动荡"
                ),
            })
        if pair in LIU_HE:
            wx = LIU_HE[pair]
            triggers.append({
                "type": "合",
                "trigger": f"{target_label}{target_branch}",
                "target": f"{pname}{natal_dz}",
                "auspicious": True,
                "wuxing": wx,
                "interpretation": (
                    f"{target_label}{target_branch}合{pname}{natal_dz}化{wx}"
                    f" — 触发合化、贵人、机缘"
                ),
            })
        # 半合
        for half_pair, wx in SAN_HE_HALF:
            if pair == half_pair:
                triggers.append({
                    "type": "半合",
                    "trigger": f"{target_label}{target_branch}",
                    "target": f"{pname}{natal_dz}",
                    "auspicious": True,
                    "wuxing": wx,
                    "interpretation": (
                        f"{target_label}{target_branch}与{pname}{natal_dz}半合{wx}"
                    ),
                })
                break
        if pair in LIU_HAI:
            triggers.append({
                "type": "害",
                "trigger": f"{target_label}{target_branch}",
                "target": f"{pname}{natal_dz}",
                "auspicious": False,
                "interpretation": (
                    f"{target_label}{target_branch}害{pname}{natal_dz} — 暗损、阴亏"
                ),
            })
        if target_branch == natal_dz and target_branch in ZI_XING:
            triggers.append({
                "type": "自刑",
                "trigger": f"{target_label}{target_branch}",
                "target": f"{pname}{natal_dz}",
                "auspicious": False,
                "interpretation": f"{target_label}{target_branch}遇本命同支{natal_dz}（自刑）— 内耗加重",
            })
    
    return triggers


# ─────────────────────────────────────────────────────────────
# 6. Prompt 格式化
# ─────────────────────────────────────────────────────────────

def format_relations_for_prompt(result: Dict[str, Any]) -> str:
    """把 analyze_all_relations 的结果格式化为 prompt 中文段。"""
    if not result:
        return ""
    summary = result.get("summary", {})
    total = (summary.get("total_he", 0) + summary.get("total_chong", 0)
             + summary.get("total_xing", 0) + summary.get("total_hai", 0)
             + summary.get("total_po", 0))
    if total == 0:
        return "【地支刑冲合害】无明显刑冲合害关系，命盘相对平和。"
    
    lines = [f"【地支刑冲合害】（共 {total} 项关系，论命必参）"]
    
    if summary.get("key_blessings"):
        lines.append("  ◆ 吉象：")
        for b in summary["key_blessings"][:6]:
            lines.append(f"    {b}")
    
    if summary.get("key_warnings"):
        lines.append("  ◆ 警示：")
        for w in summary["key_warnings"][:8]:
            lines.append(f"    {w}")
    
    # 简要明细
    if result.get("chong"):
        chong_list = []
        for c in result["chong"][:4]:
            chong_list.append(f"{c['pillars'][0]}{c['branches'][0]}↔{c['pillars'][1]}{c['branches'][1]}")
        lines.append(f"  ◆ 冲：{' / '.join(chong_list)}")
    
    if result.get("he"):
        he_list = []
        for h in result["he"][:5]:
            if h["type"] in ("三合局", "三会方"):
                he_list.append(f"{h['type']}{h['wuxing']}局({'-'.join(h['branches'])})")
            else:
                he_list.append(f"{h['branches'][0]}{h['branches'][1]}{h['type']}")
        lines.append(f"  ◆ 合：{' / '.join(he_list)}")
    
    lines.append("")
    lines.append("  说明：")
    lines.append("    · 合主和，冲主散，刑主伤，害主损，破主败 — 但需视所合冲的是用神还是忌神判吉凶")
    lines.append("    · 合掉用神 = 用神被合住反受其害；冲掉忌神 = 凶星受冲反为吉")
    lines.append("    · 大运流年触发本命的刑冲合害时，应期才真正显现")
    
    return "\n".join(lines)
