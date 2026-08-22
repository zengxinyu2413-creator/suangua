"""
core/ziwei/feihua_advanced.py
==============================
飞星派紫微斗数四化引擎（Z-2 实现）。

对比 chart.py 中的 calculate_feihua（一代旧实现）：
  - 旧版只识别"自化"概念（且没区分离心/向心）
  - 旧版不识别"忌冲"
  - 旧版没有"禄解忌"、"双忌叠加"、"禄忌交战"等语象
  - 旧版没有"我宫/他宫"分类
  - 旧版没有"质能变"（生年四化遇自化）的检测
  - 旧版的"自化"断语只看化类，不看星情

本模块按飞星派（北派钦天/梁若瑜系）严格定义重写：

【核心区分】（来源：紫微斗数学堂 / 梁若瑜入门 / 飞星派权威）
  P 宫宫干 G 起 4 化 → 4 颗化星 S_x（x ∈ 禄/权/科/忌）
  设 S_x 实际落在 K 宫，P 的对宫为 OPP(P)：

  1. K == P 本宫               → 离心自化 (Self-Out)
     · 箭头向外，能量"流出/消耗"
     · 化忌不冲对宫（"忌出去了不会回冲"）
     · 主"有变无、放弃、消耗"

  2. K == OPP(P)              → 向心自化 (Self-In)
     · 箭头从 P 射向对宫，能量"聚向对宫"
     · 力度大于离心
     · 主"对宫受影响、新的开展"

  3. K 既非 P 又非 OPP(P)     → 普通飞宫 (Flying-Out)
     · P 飞 X 入 K 宫
     · 化忌 还要"冲" K 的对宫

【特殊语象】
  · 禄解忌：化禄入本命化忌宫（来因宫）→ 转机
  · 双忌叠加：化忌入本命化忌宫 → 极凶
  · 禄忌交战：化禄与化忌同宫 → 虚禄/财损
  · 质能变：本宫坐生年同类四化且产生自化 → "绝对有"，事必发生

【我宫他宫】
  我宫（六内）：命、财、官、田、福、疾
  他宫（六外）：兄、夫、子、迁、交、父
  · 禄入我宫为得，禄入他宫为出（损失）
  · 忌冲我宫为损失

调用入口：
  >>> from core.ziwei.feihua_advanced import analyze_palace_feihua
  >>> result = analyze_palace_feihua(palaces, school="zhongzhou")
  >>> # result 是 12 个宫位的飞化记录，每条含 4 个 transformations + 衍生语象
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple


# ─────────────────────────────────────────────────────────────
# 1. 派别四化表
# ─────────────────────────────────────────────────────────────

# 中州派 / 紫云派 / iztro 默认表 — 与 SylarLong/iztro 一致
ZHONGZHOU_SIHUA: Dict[str, Dict[str, str]] = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "右弼", "化忌": "天机"},
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "太阴", "化忌": "天同"},
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "左辅", "化忌": "武曲"},
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}

# 钦天派四化表 — 庚干/壬干与中州派不同
# 来源：四余独步钦天讲义、东派紫微等
# 注意：钦天派内部也有版本差异，这里取最常见的一种
QINTIAN_SIHUA: Dict[str, Dict[str, str]] = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "太阳", "化忌": "天机"},  # 戊科太阳（vs 中州右弼）
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "天府", "化忌": "天同"},  # 庚科天府（vs 中州太阴）
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "天府", "化忌": "武曲"},  # 壬科天府（vs 中州左辅）
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}

# 飞星派梁若瑜传承 — 与钦天派接近，但庚干部分版本不同
LIANG_FEIXING_SIHUA: Dict[str, Dict[str, str]] = {
    # 同钦天派
    **QINTIAN_SIHUA,
    # 部分流派认为庚科太阴（同中州）；这里采用 SylarLong iztro 一致以求稳定
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "太阴", "化忌": "天同"},
}

SCHOOLS: Dict[str, Dict[str, Dict[str, str]]] = {
    "zhongzhou": ZHONGZHOU_SIHUA,
    "qintian":   QINTIAN_SIHUA,
    "liang":     LIANG_FEIXING_SIHUA,
}

SCHOOL_NAMES_CN: Dict[str, str] = {
    "zhongzhou": "中州派（紫云派 / iztro 默认）",
    "qintian":   "钦天派（四余独步）",
    "liang":     "飞星派（梁若瑜传承）",
}


# ─────────────────────────────────────────────────────────────
# 2. 我宫 / 他宫 分类（六内六外）
# ─────────────────────────────────────────────────────────────

PALACE_INNER: Set[str] = {"命宫", "财帛宫", "官禄宫", "田宅宫", "福德宫", "疾厄宫"}  # 六内/我宫
PALACE_OUTER: Set[str] = {"兄弟宫", "夫妻宫", "子女宫", "迁移宫", "交友宫", "父母宫"}  # 六外/他宫


def is_inner_palace(palace_name: str) -> bool:
    """是否我宫（六内）。"""
    return palace_name in PALACE_INNER


def is_outer_palace(palace_name: str) -> bool:
    """是否他宫（六外）。"""
    return palace_name in PALACE_OUTER


# ─────────────────────────────────────────────────────────────
# 3. 飞化类型常量
# ─────────────────────────────────────────────────────────────

FH_SELF_OUT  = "离心自化"   # 化星落本宫
FH_SELF_IN   = "向心自化"   # 化星落对宫
FH_FLY_OUT   = "普通飞宫"   # 化星落其他宫


# ─────────────────────────────────────────────────────────────
# 4. 辅助：建立星到宫的索引
# ─────────────────────────────────────────────────────────────

def _build_star_to_palace_idx(palaces: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    建立"星名 → 所在宫 index"映射。
    
    会扫描 major_stars + minor_stars + adj_stars 全部，让辅星（左辅右弼文昌文曲）
    也能被四化捕捉到（壬科左辅、辛忌文昌等）。
    """
    star_to_idx: Dict[str, int] = {}
    for p in palaces:
        idx = p.get("index", -1)
        if idx < 0:
            continue
        for key in ("major_stars", "minor_stars", "adj_stars"):
            for s in (p.get(key) or []):
                if isinstance(s, dict):
                    name = s.get("name", "")
                else:
                    name = str(s) if s else ""
                if name and name not in star_to_idx:
                    star_to_idx[name] = idx
    return star_to_idx


def _star_mutagen(s: Any) -> str:
    """提取一个星耀的 mutagen 字段（生年四化标记）。"""
    if isinstance(s, dict):
        m = s.get("mutagen", "")
        return m if m else ""
    return ""


def _palace_stars_with_mutagen(palace: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    返回该宫位上所有带 mutagen 的星，按 mutagen 类型分组。
    
    返回示例：{"禄": ["太阳"], "权": ["武曲"], "忌": []}
    """
    result: Dict[str, List[str]] = {"禄": [], "权": [], "科": [], "忌": []}
    for key in ("major_stars", "minor_stars", "adj_stars"):
        for s in (palace.get(key) or []):
            m = _star_mutagen(s)
            if m and m in result:
                name = s.get("name", "") if isinstance(s, dict) else str(s)
                if name:
                    result[m].append(name)
    return result


# ─────────────────────────────────────────────────────────────
# 5. 单宫位的飞化分析
# ─────────────────────────────────────────────────────────────

def _classify_feihua(p_idx: int, target_idx: int) -> str:
    """
    对一颗化星，根据 P 宫位 index 和化星落点 index 分类。
    
    Rules:
      target_idx == p_idx       → 离心自化
      target_idx == (p_idx+6)%12 → 向心自化
      其它                       → 普通飞宫
    """
    if target_idx < 0:
        return "未排到"
    if target_idx == p_idx:
        return FH_SELF_OUT
    if target_idx == (p_idx + 6) % 12:
        return FH_SELF_IN
    return FH_FLY_OUT


# ─────────────────────────────────────────────────────────────
# 6. 主分析函数
# ─────────────────────────────────────────────────────────────

def analyze_palace_feihua(
    palaces: List[Dict[str, Any]],
    school: str = "zhongzhou",
) -> List[Dict[str, Any]]:
    """
    对全盘 12 宫做飞星派飞化分析。
    
    Args:
        palaces: build_ziwei_chart 输出的 palaces 列表（已含 mutagen、heavenly_stem 等）
        school: 派别 — "zhongzhou" / "qintian" / "liang"，默认中州派
    
    Returns:
        12 条记录，每条结构：
          {
            "palace_idx":   int,
            "palace_name":  str,    # 如 "命宫"
            "stem":         str,    # 宫干
            "branch":       str,    # 宫支
            "opp_palace_name": str, # 对宫名
            "transformations": [    # 4 个化象（禄/权/科/忌）
              {
                "hua_type":         "化禄"/"化权"/"化科"/"化忌",
                "target_star":      str,    # 化哪颗星
                "target_palace_idx": int,    # 化星落哪宫 index
                "target_palace_name": str,   # 化星落哪宫名
                "fh_type":          "离心自化"/"向心自化"/"普通飞宫"/"未排到",
                "is_inner":         bool,   # 落点是否我宫
                "chong_palace":     str,    # 化忌冲哪个宫（仅化忌+普通飞宫时填）
                "is_he_won_ji":     bool,   # 禄解忌：化禄入本命化忌宫
                "is_double_ji":     bool,   # 双忌叠加：化忌入本命化忌宫
                "is_lu_ji_war":     bool,   # 禄忌交战：化禄入本命已坐生年忌的宫
                "is_quality_change": bool,  # 质能变：本宫坐生年同类四化且自化
                "natal_overlap":    [str],  # 落点宫位的生年四化（如有）
                "tags":             [str],  # 一组语象标签，便于 LLM 论命
                "interpretation":   str,    # 一句话断语
              },
              ...
            ],
            # 衍生标签（整宫级别）
            "self_out_count":   int,   # 本宫离心自化数
            "self_in_count":    int,   # 本宫向心自化数（射向对宫）
            "fly_out_count":    int,   # 本宫飞出数
            "incoming_count":   int,   # 他宫飞入本宫的化象数（二次扫描得出）
            "incoming_list":    [...]  # 哪些宫的什么化飞入本宫
          }
    """
    if not palaces:
        return []
    
    sihua_table = SCHOOLS.get(school, ZHONGZHOU_SIHUA)
    star_to_idx = _build_star_to_palace_idx(palaces)
    
    # 建立 index → palace 映射
    by_index: Dict[int, Dict[str, Any]] = {p.get("index", -1): p for p in palaces}
    
    # 找出本命化忌所在宫（来因宫），用于后续"禄解忌""双忌叠加"判断
    natal_ji_idx = -1
    for p in palaces:
        mut = _palace_stars_with_mutagen(p)
        if mut["忌"]:
            natal_ji_idx = p.get("index", -1)
            break
    
    # 找出本命化禄所在宫（用于"禄忌交战"判断时辨识"已坐生年禄"的宫）
    natal_lu_idx = -1
    for p in palaces:
        mut = _palace_stars_with_mutagen(p)
        if mut["禄"]:
            natal_lu_idx = p.get("index", -1)
            break
    
    # 第一遍：算每宫的 4 化
    results: List[Dict[str, Any]] = []
    for p in palaces:
        p_idx = p.get("index", -1)
        if p_idx < 0:
            continue
        stem = p.get("heavenly_stem", "")
        branch = p.get("earthly_branch", "")
        p_name = p.get("name", "")
        opp_idx = (p_idx + 6) % 12
        opp_name = by_index.get(opp_idx, {}).get("name", "")
        
        # 该宫生年四化分布（用于检测质能变）
        natal_at_self = _palace_stars_with_mutagen(p)
        
        hua_table = sihua_table.get(stem, {})
        transformations: List[Dict[str, Any]] = []
        
        for hua_type in ("化禄", "化权", "化科", "化忌"):
            target_star = hua_table.get(hua_type, "")
            target_idx = star_to_idx.get(target_star, -1)
            target_name = by_index.get(target_idx, {}).get("name", "") if target_idx >= 0 else ""
            fh_type = _classify_feihua(p_idx, target_idx)
            
            # 标签集合
            tags: List[str] = []
            
            # 1. 离心 / 向心 / 飞宫 / 未排到 — 基础标签
            if fh_type != "未排到":
                tags.append(fh_type)
            else:
                tags.append("未排到（化星不在盘上）")
            
            # 2. 我宫 / 他宫
            target_is_inner = is_inner_palace(target_name)
            if target_name:
                tags.append("入我宫" if target_is_inner else "入他宫")
            
            # 3. 化忌专属：忌冲哪宫（仅普通飞宫时；自化忌不冲对宫）
            chong_palace = ""
            if hua_type == "化忌" and fh_type == FH_FLY_OUT and target_idx >= 0:
                chong_idx = (target_idx + 6) % 12
                chong_palace = by_index.get(chong_idx, {}).get("name", "")
                if chong_palace:
                    tags.append(f"忌冲{chong_palace}")
            
            # 4. 落点宫的生年四化重叠
            natal_overlap_list: List[str] = []
            if target_idx >= 0:
                target_natal = _palace_stars_with_mutagen(by_index[target_idx])
                for mut_type, stars_list in target_natal.items():
                    for star_n in stars_list:
                        natal_overlap_list.append(f"{star_n}·生年化{mut_type}")
            
            # 5. 禄解忌：化禄入本命化忌宫
            is_he_won_ji = (
                hua_type == "化禄"
                and natal_ji_idx >= 0
                and target_idx == natal_ji_idx
            )
            if is_he_won_ji:
                tags.append("禄解忌（转机）")
            
            # 6. 双忌叠加：化忌入本命化忌宫
            is_double_ji = (
                hua_type == "化忌"
                and natal_ji_idx >= 0
                and target_idx == natal_ji_idx
                and fh_type != FH_SELF_OUT  # 自化忌的本宫坐忌另外算"质能变"
            )
            if is_double_ji:
                tags.append("双忌叠加（极凶）")
            
            # 7. 禄忌交战：化禄入本命化忌宫位 已经包含在 is_he_won_ji 里
            #    化忌入本命化禄宫位（虚禄/财损）
            is_lu_ji_war = (
                hua_type == "化忌"
                and natal_lu_idx >= 0
                and target_idx == natal_lu_idx
            )
            if is_lu_ji_war:
                tags.append("禄忌交战（虚禄财损）")
            
            # 8. 质能变：本宫坐生年同类化 + 本宫宫干起的同类自化
            mut_short = hua_type.replace("化", "")  # 禄/权/科/忌
            is_quality_change = (
                fh_type in (FH_SELF_OUT, FH_SELF_IN)
                and bool(natal_at_self.get(mut_short, []))
            )
            if is_quality_change:
                tags.append(f"质能变（本宫坐生年{hua_type}+自化{hua_type}=绝对有）")
            
            # 9. 同类抵消：本宫坐生年化禄，宫干又化禄（不限自化）
            #    例如：父母宫坐生年化禄太阳，父母宫宫干是甲，甲化禄廉贞落他宫——这不算同类抵消
            #    严格来说同类抵消必须是"同星同化"。我们这里不简单写"同类相抵消"。
            
            # —— 生成断语 ——
            interp = _build_interpretation(
                hua_type=hua_type,
                target_star=target_star,
                target_palace_name=target_name,
                fh_type=fh_type,
                chong_palace=chong_palace,
                is_he_won_ji=is_he_won_ji,
                is_double_ji=is_double_ji,
                is_lu_ji_war=is_lu_ji_war,
                is_quality_change=is_quality_change,
                target_is_inner=target_is_inner,
            )
            
            transformations.append({
                "hua_type":           hua_type,
                "target_star":        target_star,
                "target_palace_idx":  target_idx,
                "target_palace_name": target_name,
                "fh_type":            fh_type,
                "is_inner":           target_is_inner,
                "chong_palace":       chong_palace,
                "is_he_won_ji":       is_he_won_ji,
                "is_double_ji":       is_double_ji,
                "is_lu_ji_war":       is_lu_ji_war,
                "is_quality_change":  is_quality_change,
                "natal_overlap":      natal_overlap_list,
                "tags":               tags,
                "interpretation":     interp,
            })
        
        # 衍生统计
        self_out_count = sum(1 for t in transformations if t["fh_type"] == FH_SELF_OUT)
        self_in_count  = sum(1 for t in transformations if t["fh_type"] == FH_SELF_IN)
        fly_out_count  = sum(1 for t in transformations if t["fh_type"] == FH_FLY_OUT)
        
        results.append({
            "palace_idx":      p_idx,
            "palace_name":     p_name,
            "stem":            stem,
            "branch":          branch,
            "opp_palace_name": opp_name,
            "transformations": transformations,
            "self_out_count":  self_out_count,
            "self_in_count":   self_in_count,
            "fly_out_count":   fly_out_count,
            "incoming_count":  0,         # 待第二遍填
            "incoming_list":   [],        # 待第二遍填
        })
    
    # 第二遍：扫描所有 transformations，统计他宫飞入本宫的化
    # （注意：自化属于本宫自己的飞化，不计入"他宫飞入"）
    incoming_by_idx: Dict[int, List[Dict[str, str]]] = {p.get("index", -1): [] for p in palaces}
    for record in results:
        from_idx = record["palace_idx"]
        from_name = record["palace_name"]
        for tr in record["transformations"]:
            target_idx = tr["target_palace_idx"]
            if target_idx < 0:
                continue
            # 自化（无论离心向心）的"target"虽然是本宫或对宫，但语义上是本宫自己产生的
            # 我们这里"incoming"特指 from != target，即跨宫飞入
            if from_idx == target_idx:
                continue  # 离心自化不算 incoming
            # 向心自化是 from → from 的对宫；这算 incoming（影响对宫）
            incoming_by_idx.setdefault(target_idx, []).append({
                "from_palace": from_name,
                "hua_type":    tr["hua_type"],
                "star":        tr["target_star"],
                "fh_type":     tr["fh_type"],
                "chong_palace": tr.get("chong_palace", ""),
            })
    
    for record in results:
        incoming = incoming_by_idx.get(record["palace_idx"], [])
        record["incoming_count"] = len(incoming)
        record["incoming_list"] = incoming
    
    return results


# ─────────────────────────────────────────────────────────────
# 7. 单条飞化的中文断语生成
# ─────────────────────────────────────────────────────────────

def _build_interpretation(
    hua_type: str,
    target_star: str,
    target_palace_name: str,
    fh_type: str,
    chong_palace: str,
    is_he_won_ji: bool,
    is_double_ji: bool,
    is_lu_ji_war: bool,
    is_quality_change: bool,
    target_is_inner: bool,
) -> str:
    """
    生成单条飞化的中文断语。
    
    断语模板按 fh_type 分支构造，并在末尾追加特殊语象（禄解忌等）。
    """
    if fh_type == "未排到":
        return f"{hua_type}化{target_star or '?'}，但该星未在盘上"
    
    if not target_star:
        return f"{hua_type}（化星未确定）"
    
    # 基础断语
    base = ""
    if fh_type == FH_SELF_OUT:
        # 离心自化
        if hua_type == "化禄":
            base = f"{target_star}离心自化禄：本宫好事留不住，财来财往，难持久"
        elif hua_type == "化权":
            base = f"{target_star}离心自化权：本宫主导欲过强，操之过急，难成大局"
        elif hua_type == "化科":
            base = f"{target_star}离心自化科：本宫名声虚而不实，才华难以持续发挥"
        elif hua_type == "化忌":
            base = f"{target_star}离心自化忌：本宫事务散漫无章，执念深重；忌出去不冲对宫，但本宫自损"
    elif fh_type == FH_SELF_IN:
        # 向心自化
        if hua_type == "化禄":
            base = f"{target_star}向心自化禄：能量射向对宫{target_palace_name}，对宫得力"
        elif hua_type == "化权":
            base = f"{target_star}向心自化权：将主导权让予对宫{target_palace_name}"
        elif hua_type == "化科":
            base = f"{target_star}向心自化科：声名才华聚向对宫{target_palace_name}"
        elif hua_type == "化忌":
            base = f"{target_star}向心自化忌：本宫之忌反射向对宫{target_palace_name}，对宫受拖累"
    else:
        # 普通飞宫
        wo_ta = "我宫" if target_is_inner else "他宫"
        if hua_type == "化禄":
            if target_is_inner:
                base = f"{target_star}化禄入【{target_palace_name}】（{wo_ta}）：在此领域有获益"
            else:
                base = f"{target_star}化禄入【{target_palace_name}】（{wo_ta}）：禄出他宫，付出助人或为他人作嫁"
        elif hua_type == "化权":
            base = f"{target_star}化权入【{target_palace_name}】（{wo_ta}）：在此领域有主导力、决断力"
        elif hua_type == "化科":
            base = f"{target_star}化科入【{target_palace_name}】（{wo_ta}）：在此领域有声名、文书、贵人"
        elif hua_type == "化忌":
            chong_str = f"，同时冲【{chong_palace}】" if chong_palace else ""
            if target_is_inner:
                base = f"{target_star}化忌入【{target_palace_name}】（{wo_ta}）：在此领域执念深重、多阻碍{chong_str}"
            else:
                base = f"{target_star}化忌入【{target_palace_name}】（{wo_ta}）：此领域有所失、有所损{chong_str}"
    
    # 追加特殊语象
    suffix_parts: List[str] = []
    if is_quality_change:
        suffix_parts.append(f"⚠ 质能变（本宫坐生年{hua_type}+自化），事必发生")
    if is_he_won_ji:
        suffix_parts.append(f"✦ 禄解忌（本命化忌宫得禄入，主转机）")
    if is_double_ji:
        suffix_parts.append(f"⚠ 双忌叠加（本命化忌宫再得化忌，极凶）")
    if is_lu_ji_war:
        suffix_parts.append(f"⚠ 禄忌交战（化忌入本命化禄宫，财损虚禄）")
    
    if suffix_parts:
        base += "；" + "；".join(suffix_parts)
    
    return base


# ─────────────────────────────────────────────────────────────
# 8. 全盘性的综合分析
# ─────────────────────────────────────────────────────────────

def summarize_feihua_landscape(
    feihua_records: List[Dict[str, Any]],
    palaces: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    从全盘飞化记录中抽取关键语象，做整体性总结。
    
    Returns:
      {
        "key_quality_changes": [...],   # 质能变发生的宫位（飞星派论命起点）
        "lu_jie_ji":           [...],   # 所有禄解忌
        "double_ji":           [...],   # 所有双忌叠加
        "lu_ji_war":           [...],   # 所有禄忌交战
        "soul_palace_incoming": [...],  # 飞入命宫的化象（影响一生）
        "soul_palace_chong":   [...],   # 化忌冲命宫的飞化
        "self_out_palaces":    [...],   # 哪些宫有离心自化（漏点）
        "self_in_palaces":     [...],   # 哪些宫有向心自化（被对宫拖累/受益）
        "concentration":       {...},   # 哪些宫聚集了多个飞化（重点宫）
      }
    """
    summary: Dict[str, Any] = {
        "key_quality_changes": [],
        "lu_jie_ji": [],
        "double_ji": [],
        "lu_ji_war": [],
        "soul_palace_incoming": [],
        "soul_palace_chong": [],
        "self_out_palaces": [],
        "self_in_palaces": [],
        "concentration": {},
    }
    
    # 找命宫 index
    soul_idx = -1
    for p in palaces:
        if p.get("is_soul") or p.get("name") == "命宫":
            soul_idx = p.get("index", -1)
            break
    
    palace_hit_count: Dict[str, int] = {}
    
    for record in feihua_records:
        from_palace = record["palace_name"]
        for tr in record["transformations"]:
            # 各种特殊语象
            target_p = tr.get("target_palace_name", "")
            if tr.get("is_quality_change"):
                summary["key_quality_changes"].append({
                    "palace": from_palace,
                    "hua":    tr["hua_type"],
                    "star":   tr["target_star"],
                    "fh_type": tr["fh_type"],
                    "interpretation": tr["interpretation"],
                })
            if tr.get("is_he_won_ji"):
                summary["lu_jie_ji"].append({
                    "from": from_palace,
                    "star": tr["target_star"],
                    "to":   target_p,
                })
            if tr.get("is_double_ji"):
                summary["double_ji"].append({
                    "from": from_palace,
                    "star": tr["target_star"],
                    "to":   target_p,
                })
            if tr.get("is_lu_ji_war"):
                summary["lu_ji_war"].append({
                    "from": from_palace,
                    "star": tr["target_star"],
                    "to":   target_p,
                })
            
            # 命宫汇入
            if tr.get("target_palace_idx") == soul_idx and tr.get("target_palace_idx") != record["palace_idx"]:
                summary["soul_palace_incoming"].append({
                    "from": from_palace,
                    "hua":  tr["hua_type"],
                    "star": tr["target_star"],
                    "fh_type": tr["fh_type"],
                })
            
            # 化忌冲命宫
            if tr.get("hua_type") == "化忌" and tr.get("chong_palace") == "命宫":
                summary["soul_palace_chong"].append({
                    "from": from_palace,
                    "star": tr["target_star"],
                })
            
            # 飞化集中度统计
            if target_p:
                palace_hit_count[target_p] = palace_hit_count.get(target_p, 0) + 1
        
        # 离心 / 向心 宫位列表
        if record["self_out_count"] > 0:
            summary["self_out_palaces"].append({
                "palace": from_palace,
                "count":  record["self_out_count"],
            })
        if record["self_in_count"] > 0:
            summary["self_in_palaces"].append({
                "palace": from_palace,
                "count":  record["self_in_count"],
            })
    
    # 飞化集中宫位（接收 ≥ 5 个化象的，才算"集中"）
    summary["concentration"] = {
        p: cnt for p, cnt in palace_hit_count.items() if cnt >= 5
    }
    
    return summary


# ─────────────────────────────────────────────────────────────
# 9. 友好的中文格式化（给 LLM prompt 用）
# ─────────────────────────────────────────────────────────────

def format_feihua_for_prompt(
    feihua_records: List[Dict[str, Any]],
    summary: Dict[str, Any],
    school: str = "zhongzhou",
    focus_palaces: Optional[List[str]] = None,
) -> str:
    """
    把飞化分析结果格式化成 LLM prompt 可读的多行中文文本。
    
    Args:
        feihua_records: analyze_palace_feihua 的输出
        summary:        summarize_feihua_landscape 的输出
        school:         派别名
        focus_palaces:  重点显示哪些宫位的完整飞化（默认命财官迁夫福6 宫）
    
    Returns:
        多行格式化字符串
    """
    if focus_palaces is None:
        focus_palaces = ["命宫", "财帛宫", "官禄宫", "迁移宫", "夫妻宫", "福德宫"]
    focus_set = set(focus_palaces)
    
    school_cn = SCHOOL_NAMES_CN.get(school, school)
    sections: List[str] = []
    
    # 头部
    sections.append(f"【飞星派飞化分析】（派别：{school_cn}）")
    sections.append(
        "  说明：每宫宫干起 4 化（禄/权/科/忌），可能"
        "落本宫（离心自化）、落对宫（向心自化）或飞入其他宫（普通飞宫）。"
        "下方列出 6 大重点宫位完整飞化，并汇总全盘关键语象。"
    )
    
    # 整盘关键语象（先列出来 — 飞星派论命的"起手"）
    landscape_lines = ["\n【全盘关键语象】"]
    
    if summary["key_quality_changes"]:
        landscape_lines.append("  ◆ 质能变（生年四化+自化 = 必发生的事，飞星派论命起手）：")
        for item in summary["key_quality_changes"]:
            landscape_lines.append(
                f"    · 【{item['palace']}】{item['star']}{item['hua']}（{item['fh_type']}）→ {item['interpretation']}"
            )
    
    if summary["double_ji"]:
        landscape_lines.append("  ⚠ 双忌叠加（极凶）：")
        for item in summary["double_ji"]:
            landscape_lines.append(
                f"    · 【{item['from']}】化忌{item['star']}→【{item['to']}】（本命化忌已在此，再得化忌）"
            )
    
    if summary["lu_ji_war"]:
        landscape_lines.append("  ⚠ 禄忌交战（虚禄/财损）：")
        for item in summary["lu_ji_war"]:
            landscape_lines.append(
                f"    · 【{item['from']}】化忌{item['star']}→【{item['to']}】（化忌入本命化禄宫）"
            )
    
    if summary["lu_jie_ji"]:
        landscape_lines.append("  ✦ 禄解忌（转机）：")
        for item in summary["lu_jie_ji"]:
            landscape_lines.append(
                f"    · 【{item['from']}】化禄{item['star']}→【{item['to']}】（化禄入本命化忌宫，主转机）"
            )
    
    if summary["soul_palace_incoming"]:
        landscape_lines.append("  ⊕ 飞入命宫的四化（影响一生格局）：")
        for item in summary["soul_palace_incoming"]:
            landscape_lines.append(
                f"    · 【{item['from']}】{item['hua']}{item['star']}→ 命宫（{item['fh_type']}）"
            )
    
    if summary["soul_palace_chong"]:
        landscape_lines.append("  ⚠ 化忌冲命宫（一生有此宫干扰）：")
        for item in summary["soul_palace_chong"]:
            landscape_lines.append(
                f"    · 【{item['from']}】化忌{item['star']}→ 冲命宫"
            )
    
    if summary["self_out_palaces"]:
        names = "、".join(f"{x['palace']}×{x['count']}" for x in summary["self_out_palaces"])
        landscape_lines.append(f"  · 离心自化宫位（漏点）：{names}")
    
    if summary["self_in_palaces"]:
        names = "、".join(f"{x['palace']}×{x['count']}" for x in summary["self_in_palaces"])
        landscape_lines.append(f"  · 向心自化宫位（射向对宫）：{names}")
    
    if summary["concentration"]:
        concs = "、".join(f"{p}({c})" for p, c in summary["concentration"].items())
        landscape_lines.append(f"  · 飞化汇聚宫位（≥5条化象汇入，重点宫）：{concs}")
    
    if len(landscape_lines) > 1:
        sections.append("\n".join(landscape_lines))
    else:
        sections.append("\n【全盘关键语象】无显著语象（飞化分布平均，无特殊汇聚）")
    
    # 6 大重点宫位的完整飞化
    detail_lines = ["\n【6 大重点宫位的完整飞化】"]
    for record in feihua_records:
        if record["palace_name"] not in focus_set:
            continue
        detail_lines.append(
            f"\n  ◆ 【{record['palace_name']}（{record['stem']}{record['branch']}）】"
            f" 对宫：{record['opp_palace_name']}"
        )
        for tr in record["transformations"]:
            target_p = tr.get("target_palace_name", "?")
            fh_t = tr.get("fh_type", "?")
            interp = tr.get("interpretation", "")
            detail_lines.append(f"    · {fh_t} | {interp}")
        # 他宫飞入本宫的化象
        if record["incoming_list"]:
            detail_lines.append(f"    · 他宫飞入此宫：")
            for inc in record["incoming_list"][:6]:
                detail_lines.append(
                    f"      ← 【{inc['from_palace']}】{inc['hua_type']}{inc['star']}（{inc['fh_type']}）"
                )
    
    sections.append("\n".join(detail_lines))
    
    return "\n".join(sections)


# ─────────────────────────────────────────────────────────────
# 10. 叠合飞化分析（大限 + 流年）
# ─────────────────────────────────────────────────────────────

def analyze_overlay_feihua(
    palaces: List[Dict[str, Any]],
    overlay_stem: str,
    overlay_palace_idx: int,
    overlay_label: str = "大限",
    school: str = "zhongzhou",
) -> Dict[str, Any]:
    """
    分析单层叠合盘（大限或流年）的四化，按飞星派标准方法。
    
    与 analyze_palace_feihua 区别：
      - palace 飞化：每宫宫干起 4 化，全盘 12×4 条
      - overlay 飞化：只一个干（大限命宫干 或 流年太岁干），起 4 化，飞入本命盘
    
    与 calculate_decade_feihua（旧实现）区别：
      - 旧版只看落点宫名 + 简单断语
      - 新版：识别飞入命宫、化忌冲命宫、自化（限自化）、禄解忌、双忌、禄忌交战
    
    Args:
        palaces:             本命盘 12 宫数据
        overlay_stem:        叠合盘的天干（大限命宫宫干 或 流年太岁干）
        overlay_palace_idx:  叠合盘的"命宫"在本命盘的哪个宫（大限命宫的 index）
                             对流年来说，是流年命宫所在的本命宫 index
        overlay_label:       中文标签 — "大限" / "流年"
        school:              派别
    
    Returns:
        {
          "overlay_label":      "大限"/"流年",
          "overlay_stem":       天干,
          "overlay_palace_idx": int,
          "overlay_palace_name": str,
          "opp_palace_name":    str,
          "transformations":    [4 条化象，含完整语象],
          "key_warnings":       [关键警示],
        }
    """
    if not palaces:
        return {"error": "no palaces"}
    
    sihua_table = SCHOOLS.get(school, ZHONGZHOU_SIHUA)
    star_to_idx = _build_star_to_palace_idx(palaces)
    by_index: Dict[int, Dict[str, Any]] = {p.get("index", -1): p for p in palaces}
    
    overlay_palace = by_index.get(overlay_palace_idx, {})
    overlay_palace_name = overlay_palace.get("name", "?宫")
    opp_idx = (overlay_palace_idx + 6) % 12
    opp_name = by_index.get(opp_idx, {}).get("name", "")
    
    # 找本命化忌、化禄宫位（用于禄解忌、禄忌交战判断）
    natal_ji_idx = -1
    natal_lu_idx = -1
    for p in palaces:
        mut = _palace_stars_with_mutagen(p)
        if mut["忌"] and natal_ji_idx < 0:
            natal_ji_idx = p.get("index", -1)
        if mut["禄"] and natal_lu_idx < 0:
            natal_lu_idx = p.get("index", -1)
    
    # 找本命命宫 index
    natal_soul_idx = -1
    for p in palaces:
        if p.get("is_soul") or p.get("name") == "命宫":
            natal_soul_idx = p.get("index", -1)
            break
    
    hua_table = sihua_table.get(overlay_stem, {})
    transformations: List[Dict[str, Any]] = []
    key_warnings: List[str] = []
    
    for hua_type in ("化禄", "化权", "化科", "化忌"):
        target_star = hua_table.get(hua_type, "")
        target_idx = star_to_idx.get(target_star, -1)
        target_name = by_index.get(target_idx, {}).get("name", "") if target_idx >= 0 else ""
        fh_type = _classify_feihua(overlay_palace_idx, target_idx)
        
        tags: List[str] = []
        if fh_type != "未排到":
            tags.append(f"{overlay_label}{fh_type}")
        else:
            tags.append(f"{overlay_label}未排到")
        
        # 我宫他宫
        target_is_inner = is_inner_palace(target_name)
        if target_name:
            tags.append("入我宫" if target_is_inner else "入他宫")
        
        # 化忌专属：冲对宫
        chong_palace = ""
        if hua_type == "化忌" and fh_type == FH_FLY_OUT and target_idx >= 0:
            chong_idx = (target_idx + 6) % 12
            chong_palace = by_index.get(chong_idx, {}).get("name", "")
            if chong_palace:
                tags.append(f"{overlay_label}忌冲{chong_palace}")
            # 重要警示：限/流忌冲命宫
            if chong_idx == natal_soul_idx:
                key_warnings.append(
                    f"⚠ {overlay_label}化忌{target_star}冲命宫（{overlay_label}最凶之象）"
                )
        
        # 飞入命宫
        if target_idx == natal_soul_idx and target_idx != overlay_palace_idx:
            tags.append(f"{overlay_label}{hua_type}飞入命宫")
            if hua_type in ("化禄", "化权", "化科"):
                key_warnings.append(
                    f"✦ {overlay_label}{hua_type}{target_star}飞入命宫（{overlay_label}吉象，本身受益）"
                )
            elif hua_type == "化忌":
                key_warnings.append(
                    f"⚠ {overlay_label}化忌{target_star}飞入命宫（{overlay_label}劫数，自身受困）"
                )
        
        # 落点宫的生年四化重叠
        natal_overlap_list: List[str] = []
        if target_idx >= 0:
            target_natal = _palace_stars_with_mutagen(by_index[target_idx])
            for mut_type, stars_list in target_natal.items():
                for star_n in stars_list:
                    natal_overlap_list.append(f"{star_n}·生年化{mut_type}")
        
        # 禄解忌：限/流禄入本命化忌宫
        is_he_won_ji = (
            hua_type == "化禄"
            and natal_ji_idx >= 0
            and target_idx == natal_ji_idx
        )
        if is_he_won_ji:
            tags.append("禄解忌（转机）")
            key_warnings.append(
                f"✦ {overlay_label}化禄{target_star}解本命忌（{overlay_label}有重要转机）"
            )
        
        # 双忌叠加：限/流忌入本命化忌宫
        is_double_ji = (
            hua_type == "化忌"
            and natal_ji_idx >= 0
            and target_idx == natal_ji_idx
            and fh_type != FH_SELF_OUT
        )
        if is_double_ji:
            tags.append("双忌叠加（极凶）")
            key_warnings.append(
                f"⚠ {overlay_label}化忌{target_star}入本命化忌宫（双忌叠加，{overlay_label}此宫极凶）"
            )
        
        # 禄忌交战：限/流忌入本命化禄宫
        is_lu_ji_war = (
            hua_type == "化忌"
            and natal_lu_idx >= 0
            and target_idx == natal_lu_idx
        )
        if is_lu_ji_war:
            tags.append("禄忌交战")
            key_warnings.append(
                f"⚠ {overlay_label}化忌{target_star}冲本命化禄宫（虚禄、{overlay_label}财损）"
            )
        
        # 大限/流年的自化（"限自化"）
        if fh_type == FH_SELF_OUT:
            self_meaning = {
                "化禄": f"{overlay_label}自化禄：好事留不住，财来财往",
                "化权": f"{overlay_label}自化权：过度操控，难成",
                "化科": f"{overlay_label}自化科：名声虚而不实",
                "化忌": f"{overlay_label}自化忌：诸事有始无终，散漫无章",
            }
            interp = self_meaning.get(hua_type, f"{overlay_label}{hua_type}")
            key_warnings.append(f"· {interp}")
        elif fh_type == FH_SELF_IN:
            self_meaning = {
                "化禄": f"{overlay_label}向心自化禄：能量射向对宫{target_name}",
                "化权": f"{overlay_label}向心自化权：主导权让予对宫{target_name}",
                "化科": f"{overlay_label}向心自化科：声名射向对宫{target_name}",
                "化忌": f"{overlay_label}向心自化忌：忌象反射向对宫{target_name}",
            }
            interp = self_meaning.get(hua_type, f"{overlay_label}{hua_type}")
            key_warnings.append(f"· {interp}")
        
        # 一句话断语
        interp = _build_overlay_interpretation(
            overlay_label, hua_type, target_star, target_name,
            fh_type, chong_palace, is_he_won_ji, is_double_ji,
            is_lu_ji_war, target_is_inner,
        )
        
        transformations.append({
            "hua_type":           hua_type,
            "target_star":        target_star,
            "target_palace_idx":  target_idx,
            "target_palace_name": target_name,
            "fh_type":            fh_type,
            "is_inner":           target_is_inner,
            "chong_palace":       chong_palace,
            "is_he_won_ji":       is_he_won_ji,
            "is_double_ji":       is_double_ji,
            "is_lu_ji_war":       is_lu_ji_war,
            "natal_overlap":      natal_overlap_list,
            "tags":               tags,
            "interpretation":     interp,
        })
    
    return {
        "overlay_label":      overlay_label,
        "overlay_stem":       overlay_stem,
        "overlay_palace_idx": overlay_palace_idx,
        "overlay_palace_name": overlay_palace_name,
        "opp_palace_name":    opp_name,
        "transformations":    transformations,
        "key_warnings":       key_warnings,
    }


def _build_overlay_interpretation(
    overlay_label: str,
    hua_type: str,
    target_star: str,
    target_palace_name: str,
    fh_type: str,
    chong_palace: str,
    is_he_won_ji: bool,
    is_double_ji: bool,
    is_lu_ji_war: bool,
    target_is_inner: bool,
) -> str:
    """构造叠合飞化的单条中文断语。"""
    if fh_type == "未排到" or not target_star:
        return f"{overlay_label}{hua_type}（化星{target_star or '?'}未在盘上）"
    
    # 自化分支
    if fh_type == FH_SELF_OUT:
        return f"{target_star}{overlay_label}自化{hua_type[-1]}：{overlay_label}此盘内事多变、留不住"
    if fh_type == FH_SELF_IN:
        return f"{target_star}{overlay_label}向心自化{hua_type[-1]}：能量射向对宫{target_palace_name}"
    
    # 普通飞宫
    wo_ta = "我宫" if target_is_inner else "他宫"
    if hua_type == "化禄":
        if target_is_inner:
            base = f"{target_star}{overlay_label}化禄入【{target_palace_name}】（{wo_ta}）：{overlay_label}此领域受益"
        else:
            base = f"{target_star}{overlay_label}化禄入【{target_palace_name}】（{wo_ta}）：{overlay_label}此期付出/为他人做"
    elif hua_type == "化权":
        base = f"{target_star}{overlay_label}化权入【{target_palace_name}】（{wo_ta}）：{overlay_label}此领域有主导力"
    elif hua_type == "化科":
        base = f"{target_star}{overlay_label}化科入【{target_palace_name}】（{wo_ta}）：{overlay_label}此期有名声/贵人"
    elif hua_type == "化忌":
        chong_str = f"，冲【{chong_palace}】" if chong_palace else ""
        if target_is_inner:
            base = f"{target_star}{overlay_label}化忌入【{target_palace_name}】（{wo_ta}）：{overlay_label}此领域多阻碍{chong_str}"
        else:
            base = f"{target_star}{overlay_label}化忌入【{target_palace_name}】（{wo_ta}）：{overlay_label}此领域损失{chong_str}"
    else:
        base = f"{target_star}{overlay_label}{hua_type}入【{target_palace_name}】"
    
    suffix: List[str] = []
    if is_he_won_ji:
        suffix.append("✦ 禄解忌（转机）")
    if is_double_ji:
        suffix.append("⚠ 双忌叠加（极凶）")
    if is_lu_ji_war:
        suffix.append("⚠ 禄忌交战（虚禄财损）")
    if suffix:
        base += "；" + "；".join(suffix)
    return base


def format_overlay_feihua_for_prompt(overlay_record: Dict[str, Any]) -> str:
    """
    把单层叠合飞化（大限/流年）格式化成 LLM 可读的多行中文文本。
    """
    if not overlay_record or "transformations" not in overlay_record:
        return ""
    
    label = overlay_record.get("overlay_label", "大限")
    stem = overlay_record.get("overlay_stem", "?")
    p_name = overlay_record.get("overlay_palace_name", "?")
    opp = overlay_record.get("opp_palace_name", "?")
    
    lines = [
        f"【{label}盘飞化分析】",
        f"  {label}命宫：【{p_name}】（宫干 {stem}） 对宫：【{opp}】",
    ]
    
    # 关键警示放最上面
    warnings = overlay_record.get("key_warnings", [])
    if warnings:
        lines.append(f"  {label}关键语象：")
        for w in warnings:
            lines.append(f"    {w}")
    
    # 4 条化象详情
    lines.append(f"  {label}四化（{stem}干起化）：")
    for tr in overlay_record["transformations"]:
        lines.append(f"    · {tr.get('interpretation','')}")
    
    return "\n".join(lines)


def analyze_three_plate_concentration(
    natal_palaces: List[Dict[str, Any]],
    decade_overlay: Optional[Dict[str, Any]] = None,
    annual_overlay: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    三盘叠合分析：本命忌 + 大限忌 + 流年忌 汇聚同一宫位 = 三忌冲，极凶。
    
    Returns:
        List[str]: 警示文本列表（如有）
    """
    ji_at_palace: Dict[str, List[str]] = {}
    
    # 本命忌
    for p in natal_palaces:
        mut = _palace_stars_with_mutagen(p)
        if mut["忌"]:
            pn = p.get("name", "")
            ji_at_palace.setdefault(pn, []).append("本命忌")
    
    # 大限忌（飞入哪个宫）
    if decade_overlay and decade_overlay.get("transformations"):
        for tr in decade_overlay["transformations"]:
            if tr.get("hua_type") == "化忌":
                tn = tr.get("target_palace_name", "")
                if tn:
                    ji_at_palace.setdefault(tn, []).append("大限忌")
                # 冲宫也算
                chong = tr.get("chong_palace", "")
                if chong:
                    ji_at_palace.setdefault(chong, []).append("大限忌冲")
    
    # 流年忌
    if annual_overlay and annual_overlay.get("transformations"):
        for tr in annual_overlay["transformations"]:
            if tr.get("hua_type") == "化忌":
                tn = tr.get("target_palace_name", "")
                if tn:
                    ji_at_palace.setdefault(tn, []).append("流年忌")
                chong = tr.get("chong_palace", "")
                if chong:
                    ji_at_palace.setdefault(chong, []).append("流年忌冲")
    
    warnings: List[str] = []
    for palace, sources in ji_at_palace.items():
        # 至少 2 处汇聚才有警示价值
        if len(sources) >= 3:
            warnings.append(
                f"⚠⚠⚠ 【{palace}】三忌汇聚（{ '、'.join(sources) }）→ 此宫事极凶，注意应期"
            )
        elif len(sources) == 2:
            warnings.append(
                f"⚠ 【{palace}】双忌汇聚（{ '、'.join(sources) }）→ 此宫事有阻"
            )
    
    return warnings
