"""
core/ziwei/chong_analysis.py
=============================
Z-8: 冲宫连锁深度分析。

化忌冲对宫是飞星派论命的核心语象之一，但单层"冲"信息不够 — 命理师
真正关心的是：**同一个冲宫事件，在本命/大限/流年三层 layout 下，
冲击的语义是什么。**

例如：本命疾厄宫化忌巨门 → 迁移宫，冲【命宫】
  · 本命层  → 冲本命命宫（终身健康影响自身）
  · 大限层  → 冲大限官禄宫（这十年健康冲击事业）
  · 流年层  → 冲流年父母宫（这年健康问题牵连父母）

= 一冲多义，让 AI 真正用上"飞星派"的精髓。

设计：
  1. collect_chong_events() — 从 feihua records 收集所有 chong 事件
  2. multilayer_chong_semantics() — 对每个事件，查三层 layout
  3. analyze_person_impact() — 人物影响（父/母/伴侣/子女...）
  4. format_for_prompt() — 给 LLM 的中文解读
  5. format_for_ui() — 给前端的结构化数据
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# 1. 人物/事项映射 — 宫名 → 影响的人物或主题
# ─────────────────────────────────────────────────────────────

PALACE_TO_PERSON: Dict[str, str] = {
    "命宫":   "本人",
    "兄弟宫": "兄弟姐妹/合伙人/朋友(深交)",
    "夫妻宫": "配偶/恋人",
    "子女宫": "子女/学生/下属",
    "财帛宫": "财运/现金流",
    "疾厄宫": "健康/身体",
    "迁移宫": "外出/远方/对外环境",
    "交友宫": "朋友/同事/平辈",
    "官禄宫": "事业/学业",
    "田宅宫": "家庭/不动产/家产",
    "福德宫": "精神/兴趣/福报",
    "父母宫": "父母/长辈/上司",
}

PALACE_THEME_SHORT: Dict[str, str] = {
    "命宫":   "本人",
    "兄弟宫": "兄弟",
    "夫妻宫": "配偶",
    "子女宫": "子女",
    "财帛宫": "财运",
    "疾厄宫": "健康",
    "迁移宫": "外出",
    "交友宫": "朋友",
    "官禄宫": "事业",
    "田宅宫": "家庭",
    "福德宫": "精神",
    "父母宫": "父母",
}


# ─────────────────────────────────────────────────────────────
# 2. 化象冲击严重度
# ─────────────────────────────────────────────────────────────

HUA_IMPACT_LEVEL: Dict[str, int] = {
    "化忌": 4,    # 最重 — 真正的"冲"
    "化权": 2,    # 次重 — 权力冲突
    "化禄": 1,    # 较轻 — 反而是吉冲（财气来）
    "化科": 1,    # 较轻 — 名气冲（可能受关注）
}

HUA_DIR_MEANING: Dict[str, str] = {
    "化忌": "受损",
    "化权": "受冲击",
    "化禄": "得利",  # 反吉
    "化科": "受名声波及",
}


# ─────────────────────────────────────────────────────────────
# 3. 单个冲宫事件解读
# ─────────────────────────────────────────────────────────────

def interpret_single_chong_event(
    event: Dict[str, Any],
) -> str:
    """
    Single chong event → 一行简洁解读。
    
    Args:
        event: {
            "from_palace":   "疾厄宫",
            "hua_type":      "化忌",
            "star":          "巨门",
            "target_palace": "迁移宫",
            "chong_palace":  "命宫",
            "layer":         "natal" / "decade" / "annual",
            "fh_type":       "普通飞宫" / "离心自化" / "向心自化",
        }
    """
    from_p = event.get("from_palace", "")
    hua = event.get("hua_type", "")
    star = event.get("star", "")
    target = event.get("target_palace", "")
    chong = event.get("chong_palace", "")
    layer = event.get("layer", "natal")
    fh_type = event.get("fh_type", "")
    
    layer_prefix = {"natal": "本命", "decade": "大限", "annual": "流年"}.get(layer, "")
    person = PALACE_TO_PERSON.get(chong, chong)
    impact = HUA_DIR_MEANING.get(hua, "受影响")
    
    # 自化冲：能量在原宫直接释放
    if fh_type in ("离心自化", "向心自化"):
        return (
            f"{layer_prefix}{from_p} 自化{hua[-1]}（{star}） 冲【{chong}】"
            f" — {person}{impact}（{fh_type}）"
        )
    
    return (
        f"{layer_prefix}{from_p} {hua}{star} → {target} 冲【{chong}】"
        f" — {person}{impact}"
    )


# ─────────────────────────────────────────────────────────────
# 4. 多层语义解读 — 同一冲宫在三层 layout 下是什么宫
# ─────────────────────────────────────────────────────────────

def get_chong_multilayer_semantics(
    chong_natal_idx: int,
    palaces_by_idx: Dict[int, Dict[str, Any]],
    decade_layout: Optional[Dict[int, Dict[str, str]]] = None,
    annual_layout: Optional[Dict[int, Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    给定被冲宫位的 natal_idx，返回它在三层下的宫名解读。
    
    Returns:
        {
          "natal":  {"palace_name": "命宫",      "theme": "本人"},
          "decade": {"palace_name": "大限官禄宫", "theme": "事业"},
          "annual": {"palace_name": "流年父母宫", "theme": "父母"},
        }
    """
    result = {}
    natal_palace = palaces_by_idx.get(chong_natal_idx)
    if natal_palace:
        nm = natal_palace.get("name", "")
        result["natal"] = {
            "palace_name": nm,
            "theme": PALACE_THEME_SHORT.get(nm, nm),
        }
    if decade_layout and chong_natal_idx in decade_layout:
        info = decade_layout[chong_natal_idx]
        # 大限宫名如 "大限父母" → 提取"父母"做主题
        full = info.get("name", "")
        short_name = full.replace("大限", "")  # "父母"
        result["decade"] = {
            "palace_name": full + "宫" if not full.endswith("宫") else full,
            "theme": PALACE_THEME_SHORT.get(short_name + "宫", short_name),
        }
    if annual_layout and chong_natal_idx in annual_layout:
        info = annual_layout[chong_natal_idx]
        full = info.get("name", "")
        short_name = full.replace("流年", "")
        result["annual"] = {
            "palace_name": full + "宫" if not full.endswith("宫") else full,
            "theme": PALACE_THEME_SHORT.get(short_name + "宫", short_name),
        }
    return result


# ─────────────────────────────────────────────────────────────
# 5. 主入口：从 feihua records 汇总三层冲宫事件
# ─────────────────────────────────────────────────────────────

def collect_chong_events_from_feihua_records(
    feihua_records: List[Dict[str, Any]],
    layer: str = "natal",
    only_ji: bool = True,
) -> List[Dict[str, Any]]:
    """
    从 feihua_advanced.analyze_palace_feihua 返回的 records，
    提取所有 chong_palace != "" 的事件。
    
    Args:
        feihua_records: analyze_palace_feihua 返回值
        layer:          "natal" | "decade" | "annual"
        only_ji:        True 时只收集化忌（默认 — 真正的"冲")
    """
    events = []
    for r in feihua_records:
        from_p = r.get("palace_name", "")
        from_idx = r.get("palace_idx", -1)
        for tr in r.get("transformations", []):
            chong = tr.get("chong_palace", "")
            if not chong:
                continue
            hua = tr.get("hua_type", "")
            if only_ji and hua != "化忌":
                continue
            events.append({
                "from_palace":      from_p,
                "from_palace_idx":  from_idx,
                "hua_type":         hua,
                "star":             tr.get("target_star", ""),
                "target_palace":    tr.get("target_palace_name", ""),
                "target_palace_idx": tr.get("target_palace_idx", -1),
                "chong_palace":     chong,
                "fh_type":          tr.get("fh_type", ""),
                "layer":            layer,
                "impact_level":     HUA_IMPACT_LEVEL.get(hua, 0),
            })
    # 按严重度排序
    events.sort(key=lambda e: -e["impact_level"])
    return events


def find_chong_target_idx(
    chong_palace_name: str,
    palaces: List[Dict[str, Any]],
) -> int:
    """根据冲宫的中文名，查它的 natal_idx。"""
    for p in palaces:
        if p.get("name") == chong_palace_name:
            return p.get("index", -1)
    return -1


def analyze_chong_chains(
    palaces: List[Dict[str, Any]],
    natal_feihua_records: List[Dict[str, Any]],
    decade_overlay_record: Optional[Dict[str, Any]] = None,
    annual_overlay_record: Optional[Dict[str, Any]] = None,
    decade_layout: Optional[Dict[int, Dict[str, str]]] = None,
    annual_layout: Optional[Dict[int, Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    主分析入口：从所有三层飞化数据，提炼冲宫连锁警示。
    
    Returns:
        {
          "events":            [冲宫事件 + 多层语义, ...],   # 排好序的全部
          "by_target_idx":     {natal_idx: [事件, ...]},     # 按被冲宫索引
          "top_warnings":      [严重警示文本, ...],          # 前 N 条
          "key_palaces_hit":   {palace_name: 命中次数},      # 多次被冲的宫
        }
    """
    palaces_by_idx = {p.get("index", -1): p for p in palaces}
    
    # 1. 收集三层化忌冲事件
    all_events: List[Dict[str, Any]] = []
    
    # natal layer
    natal_events = collect_chong_events_from_feihua_records(
        natal_feihua_records, layer="natal", only_ji=True
    )
    all_events.extend(natal_events)
    
    # decade layer — 把 record 包成 list 单元
    if decade_overlay_record:
        decade_record_as_list = [{
            "palace_name": "大限干起",
            "palace_idx":  decade_overlay_record.get("overlay_palace_idx", -1),
            "transformations": decade_overlay_record.get("transformations", []),
        }]
        decade_events = collect_chong_events_from_feihua_records(
            decade_record_as_list, layer="decade", only_ji=True
        )
        all_events.extend(decade_events)
    
    # annual layer
    if annual_overlay_record:
        annual_record_as_list = [{
            "palace_name": "流年干起",
            "palace_idx":  annual_overlay_record.get("overlay_palace_idx", -1),
            "transformations": annual_overlay_record.get("transformations", []),
        }]
        annual_events = collect_chong_events_from_feihua_records(
            annual_record_as_list, layer="annual", only_ji=True
        )
        all_events.extend(annual_events)
    
    # 2. 给每个事件附加多层语义
    enriched: List[Dict[str, Any]] = []
    by_target_idx: Dict[int, List[Dict[str, Any]]] = {}
    palaces_hit: Dict[str, int] = {}
    
    for e in all_events:
        chong_idx = find_chong_target_idx(e["chong_palace"], palaces)
        if chong_idx < 0:
            continue
        e["chong_palace_idx"] = chong_idx
        e["multilayer"] = get_chong_multilayer_semantics(
            chong_idx, palaces_by_idx, decade_layout, annual_layout
        )
        e["interpretation"] = interpret_single_chong_event(e)
        enriched.append(e)
        by_target_idx.setdefault(chong_idx, []).append(e)
        palaces_hit[e["chong_palace"]] = palaces_hit.get(e["chong_palace"], 0) + 1
    
    # 3. 重大警示 — 命中次数 ≥ 2 的宫 + 多层语义警示
    top_warnings: List[str] = []
    
    # 多次被冲的宫
    for palace, cnt in sorted(palaces_hit.items(), key=lambda x: -x[1]):
        if cnt >= 2:
            theme = PALACE_THEME_SHORT.get(palace, palace)
            top_warnings.append(
                f"⚠ 【{palace}】被冲 {cnt} 次，{theme}相关事项有多重风险，需重点关注"
            )
    
    # 多层冲：同一被冲宫在多层下角色不同时的连锁警示
    for chong_idx, events in by_target_idx.items():
        # 至少有 1 个事件，并且 multilayer 含 decade 或 annual 时才生成连锁警示
        e0 = events[0]
        ml = e0.get("multilayer", {})
        layers_with_data = [k for k in ("natal", "decade", "annual") if k in ml]
        if len(layers_with_data) >= 2:
            parts = []
            if "natal" in ml:
                parts.append(f"本命{ml['natal']['palace_name']}")
            if "decade" in ml:
                parts.append(f"大限{ml['decade']['palace_name'].replace('大限', '')}")
            if "annual" in ml:
                parts.append(f"流年{ml['annual']['palace_name'].replace('流年', '')}")
            
            themes = list(set([ml[l]["theme"] for l in layers_with_data]))
            if len(themes) >= 2:
                top_warnings.append(
                    f"⚠ 同一冲宫连锁：{ '/'.join(parts) } — "
                    f"影响主题跨【{ '/'.join(themes) }】，连锁效应明显"
                )
    
    return {
        "events":          enriched,
        "by_target_idx":   by_target_idx,
        "top_warnings":    top_warnings,
        "key_palaces_hit": palaces_hit,
        "total":           len(enriched),
    }


# ─────────────────────────────────────────────────────────────
# 6. Prompt 格式化（给 LLM）
# ─────────────────────────────────────────────────────────────

def format_chong_chains_for_prompt(chains_result: Dict[str, Any]) -> str:
    """把 chong chains 格式化为 LLM 可读文本。"""
    if not chains_result or chains_result.get("total", 0) == 0:
        return ""
    
    events = chains_result.get("events", [])
    warnings = chains_result.get("top_warnings", [])
    
    lines: List[str] = []
    lines.append(
        f"【冲宫连锁警示】（{chains_result['total']} 个化忌冲宫事件，跨层影响分析）"
    )
    
    if warnings:
        lines.append("  ◆ 关键警示：")
        for w in warnings[:8]:
            lines.append(f"    · {w}")
    
    # 按 layer 分组列详情
    by_layer: Dict[str, List[Dict[str, Any]]] = {"natal": [], "decade": [], "annual": []}
    for e in events:
        by_layer.setdefault(e.get("layer", "natal"), []).append(e)
    
    if by_layer["natal"]:
        lines.append("  ◆ 本命层冲宫（{}条）：".format(len(by_layer["natal"])))
        for e in by_layer["natal"][:6]:
            ml = e.get("multilayer", {})
            chain_parts = []
            if ml.get("decade"):
                chain_parts.append(f"大限={ml['decade']['palace_name']}({ml['decade']['theme']})")
            if ml.get("annual"):
                chain_parts.append(f"流年={ml['annual']['palace_name']}({ml['annual']['theme']})")
            chain_str = f"  → 此宫在 {' / '.join(chain_parts)}" if chain_parts else ""
            lines.append(f"    · {e['interpretation']}{chain_str}")
    
    if by_layer["decade"]:
        lines.append("  ◆ 大限层冲宫（{}条）：".format(len(by_layer["decade"])))
        for e in by_layer["decade"][:4]:
            lines.append(f"    · {e['interpretation']}")
    
    if by_layer["annual"]:
        lines.append("  ◆ 流年层冲宫（{}条）：".format(len(by_layer["annual"])))
        for e in by_layer["annual"][:4]:
            lines.append(f"    · {e['interpretation']}")
    
    lines.append("")
    lines.append("  说明：")
    lines.append("    · 冲宫连锁是飞星派最重要语象 — 同一冲宫在多层下角色不同时，影响主题随之扩散")
    lines.append("    · 例：'疾厄宫化忌冲命宫' 若大限层此命宫=大限官禄，则该十年健康影响事业")
    lines.append("    · 多个化忌冲同一宫位（次数 ≥ 2）= 此宫主题重灾区，必须重点防范")
    
    return "\n".join(lines)
