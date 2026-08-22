"""
core/ziwei/context_builder.py
==============================
紫微斗数 LLM 上下文构造器。

把 build_ziwei_chart() 输出的完整命盘数据，结构化成 LLM prompt 所需的
高密度文本。设计目标：

  1. 信息完整 — 主星+亮度+生年四化、辅星、煞星、宫干、长生十二神、大限年龄
     全部进 prompt；不再让 LLM 凭训练印象补完缺失字段。
  2. 命理学层级清晰 — 先列基础信息，再列命宫详情，再列三方四正，
     再列生年四化与来因宫，最后列十二宫概况与大限。
  3. 输入校验 — 容忍 iztro_py 不同版本字段缺失或英文 raw key。
  4. 派别声明 — 明确标注当前使用中州派四化（iztro 默认）。

调用方：api/agent.py 中 _build_interpret_prompt 的 ziwei 分支。
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple

# ─────────────────────────────────────────────────────────────
# 常量定义
# ─────────────────────────────────────────────────────────────

# 紫微斗数 14 主星，用于判断"宫位是否空宫"
FOURTEEN_MAJOR: Set[str] = {
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
    "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
}

# 六煞星 — 论命凶象的核心来源
SIX_SHA: Set[str] = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}

# 六吉星 — 辅佐主星成格的核心
SIX_JI: Set[str] = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺"}

# 桃花星 — 论感情/桃花的标志
TAO_HUA: Set[str] = {"红鸾", "天喜", "天姚", "咸池", "沐浴"}

# 财禄星 — 论财气的辅助
LU_MA: Set[str] = {"禄存", "天马"}

# 三方四正偏移：本宫 / +4(三合一) / +8(三合二) / +6(对宫)
SAN_FANG_SI_ZHENG_OFFSETS: Tuple[int, int, int, int] = (0, 4, 8, 6)


# 命主/身主映射 — 命理学传统表
# 命主按命宫地支取
MING_ZHU_BY_BRANCH: Dict[str, str] = {
    "子": "贪狼", "丑": "巨门", "寅": "禄存", "卯": "文曲",
    "辰": "廉贞", "巳": "武曲", "午": "破军", "未": "武曲",
    "申": "廉贞", "酉": "文曲", "戌": "禄存", "亥": "巨门",
}
# 身主按生年地支取
SHEN_ZHU_BY_YEAR_BRANCH: Dict[str, str] = {
    "子": "火星", "丑": "天相", "寅": "天梁", "卯": "天同",
    "辰": "文昌", "巳": "天机", "午": "火星", "未": "天相",
    "申": "天梁", "酉": "天同", "戌": "文昌", "亥": "天机",
}

# 来因宫断语（生年化忌所落宫位）— 飞星派核心
LAIYIN_LIFE_THEME: Dict[str, str] = {
    "命宫":   "人生重心在自我探索与个人发展，常有执念于「自我证明」",
    "兄弟宫": "与手足关系是人生主线，或因兄弟朋友而生事",
    "夫妻宫": "感情婚姻是人生核心议题，注定有情感纠葛或迟婚",
    "子女宫": "子女、性、合伙是人生主轴",
    "财帛宫": "一生为财所驱或为财所困，钱财是核心命题",
    "疾厄宫": "健康、情绪、身心状态是人生主线，需多注意",
    "迁移宫": "宜外地发展，在外比在家有缘；在家则反复",
    "交友宫": "朋友关系决定人生走向，多受朋友/同事/下属影响",
    "官禄宫": "事业成就是人生主线，不务正业必有挫折",
    "田宅宫": "房产、家业、家庭是人生重心",
    "福德宫": "精神层面与思维方式是人生核心，多思虑、宗教缘",
    "父母宫": "与父母长辈缘深或缘薄，受其深远影响",
}


# ─────────────────────────────────────────────────────────────
# 安全提取辅助
# ─────────────────────────────────────────────────────────────

def _star_name(s: Any) -> str:
    """从星曜对象（dict 或 str）安全提取名字。"""
    if isinstance(s, dict):
        return s.get("name", "")
    return str(s) if s else ""


def _star_brightness(s: Any) -> str:
    """从星曜对象提取亮度（庙/旺/得/利/平/不/陷），可能为空。"""
    if isinstance(s, dict):
        b = s.get("brightness", "")
        return b if b else ""
    return ""


def _star_mutagen(s: Any) -> str:
    """从星曜对象提取生年四化标记（禄/权/科/忌），可能为空。"""
    if isinstance(s, dict):
        m = s.get("mutagen", "")
        return m if m else ""
    return ""


def _format_star(s: Any) -> str:
    """格式化单颗星，例 '紫微(庙)·化权'。"""
    name = _star_name(s)
    if not name:
        return ""
    brightness = _star_brightness(s)
    mutagen = _star_mutagen(s)
    parts = [name]
    if brightness:
        parts.append(f"({brightness})")
    if mutagen:
        parts.append(f"·化{mutagen}")
    return "".join(parts)


def _safe_get_palaces(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从 chart data 中安全取 palaces 列表。"""
    palaces = data.get("palaces") or []
    if not isinstance(palaces, list):
        return []
    return palaces


def _safe_get_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """从 chart data 中安全取 metadata。"""
    m = data.get("metadata") or {}
    return m if isinstance(m, dict) else {}


# ─────────────────────────────────────────────────────────────
# 关键宫位定位（修复 agent.py 旧 bug：soul_palace_index 永远 0）
# ─────────────────────────────────────────────────────────────

def find_soul_palace(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    定位命宫。优先用 is_soul 标志（build_ziwei_chart 中已设置），
    退而求其次按 name == '命宫' 或 name_raw == 'soulPalace'。
    """
    if not palaces:
        return None
    # 第一优先：is_soul 字段
    for p in palaces:
        if p.get("is_soul"):
            return p
    # 第二优先：name 字段是中文"命宫"
    for p in palaces:
        if p.get("name") == "命宫":
            return p
    # 第三优先：name_raw 为 soulPalace
    for p in palaces:
        if p.get("name_raw") == "soulPalace":
            return p
    return None


def find_body_palace(palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """定位身宫。优先 is_body 字段，退而求其次按 name 字段。"""
    if not palaces:
        return None
    for p in palaces:
        if p.get("is_body"):
            return p
    for p in palaces:
        if p.get("name") == "身宫":
            return p
    return None


def get_san_fang_si_zheng(palaces: List[Dict[str, Any]], anchor_idx: int) -> List[Dict[str, Any]]:
    """
    取 anchor_idx 的三方四正四个宫的完整 palace dict（按 0/+4/+8/+6 偏移）。

    顺序：[本宫, +4三合, +8三合, +6对宫]
    """
    if not palaces or anchor_idx < 0:
        return []
    # 建立 index → palace 的映射，防御 palaces 顺序异常
    by_index: Dict[int, Dict[str, Any]] = {p.get("index", -1): p for p in palaces}
    result = []
    for off in SAN_FANG_SI_ZHENG_OFFSETS:
        target_idx = (anchor_idx + off) % 12
        p = by_index.get(target_idx)
        if p is not None:
            result.append(p)
    return result


# ─────────────────────────────────────────────────────────────
# 生年四化与来因宫
# ─────────────────────────────────────────────────────────────

def collect_natal_sihua(palaces: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    扫描全盘 12 宫，找出所有 mutagen 字段非空的星，
    返回 [{star, hua_type, palace}] 列表（一般 4 条：禄/权/科/忌各一）。

    这是飞星派论命的起点。原 agent.py 完全没用 mutagen 字段。
    """
    result: List[Dict[str, str]] = []
    if not palaces:
        return result
    for p in palaces:
        palace_name = p.get("name", "")
        # 主星+辅星+杂耀 都要扫描，因为生年四化也可能落到辅星上（如壬干左辅化科）
        all_stars = (
            (p.get("major_stars") or [])
            + (p.get("minor_stars") or [])
            + (p.get("adj_stars") or [])
        )
        for s in all_stars:
            m = _star_mutagen(s)
            if m:
                result.append({
                    "star": _star_name(s),
                    "hua_type": f"化{m}",
                    "palace": palace_name,
                    "brightness": _star_brightness(s),
                })
    return result


def find_laiyin_palace(natal_sihua: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    来因宫 = 生年化忌所在的本命宫位。
    飞星派核心：决定此人一生的核心命题方向。
    """
    for item in natal_sihua:
        if item.get("hua_type") == "化忌":
            palace = item.get("palace", "")
            return {
                "palace": palace,
                "ji_star": item.get("star", ""),
                "life_theme": LAIYIN_LIFE_THEME.get(palace, ""),
            }
    return None


# ─────────────────────────────────────────────────────────────
# 命主 / 身主翻译（修复 chart.py 的英文 raw key 残留）
# ─────────────────────────────────────────────────────────────

def resolve_ming_zhu(metadata: Dict[str, Any], soul_palace: Optional[Dict[str, Any]]) -> str:
    """
    解析命主星名（中文）。

    优先级：
      1. metadata.soul_star 已经是中文（iztro_py 默认 zh-CN）→ 直接用
      2. 否则按命宫地支查 MING_ZHU_BY_BRANCH 表
      3. 都失败返回空
    """
    raw = (metadata.get("soul_star") or "").strip()
    # 如果是中文（含 14 主星 + 7 命主可能），直接用
    valid_ming_zhu = set(MING_ZHU_BY_BRANCH.values())
    if raw in valid_ming_zhu:
        return raw
    # 否则尝试从命宫地支推
    if soul_palace:
        branch = soul_palace.get("earthly_branch", "")
        if branch in MING_ZHU_BY_BRANCH:
            return MING_ZHU_BY_BRANCH[branch]
    # 还可以试 metadata.earthly_soul
    earthly_soul = metadata.get("earthly_soul", "")
    if earthly_soul in MING_ZHU_BY_BRANCH:
        return MING_ZHU_BY_BRANCH[earthly_soul]
    return raw  # 兜底返回 raw（可能是英文）


def resolve_shen_zhu(metadata: Dict[str, Any]) -> str:
    """
    解析身主星名（中文）。

    优先级：
      1. metadata.body_star 已是中文 → 直接用
      2. 否则按生年地支查 SHEN_ZHU_BY_YEAR_BRANCH 表
      3. 都失败返回空
    """
    raw = (metadata.get("body_star") or "").strip()
    valid_shen_zhu = set(SHEN_ZHU_BY_YEAR_BRANCH.values())
    if raw in valid_shen_zhu:
        return raw
    # 试从 chinese_date 中取年支：例 "庚辰 甲申 丙午 庚寅"
    chinese_date = metadata.get("chinese_date", "")
    if chinese_date:
        parts = chinese_date.strip().split()
        if parts:
            year_gz = parts[0]
            if len(year_gz) >= 2:
                year_branch = year_gz[-1]
                if year_branch in SHEN_ZHU_BY_YEAR_BRANCH:
                    return SHEN_ZHU_BY_YEAR_BRANCH[year_branch]
    return raw


# ─────────────────────────────────────────────────────────────
# 单个宫位的精细格式化
# ─────────────────────────────────────────────────────────────

def format_palace_detail(palace: Dict[str, Any]) -> str:
    """
    把一个宫位格式化成多行详细文本（用于命宫、身宫等核心宫位）。

    输出示例：
        【命宫（甲午）】身宫同宫
          主星：紫微(庙)·化权、贪狼(平)
          辅星：左辅、文昌(得)
          煞星：擎羊
          桃花：红鸾、天姚
          长生：临官
          大限：6-15岁
    """
    name = palace.get("name", "?宫")
    stem = palace.get("heavenly_stem", "")
    branch = palace.get("earthly_branch", "")
    is_body = palace.get("is_body", False)
    body_tag = "（身宫同宫）" if is_body and palace.get("is_soul") else ""

    major_strs = [_format_star(s) for s in (palace.get("major_stars") or [])]
    major_strs = [x for x in major_strs if x]

    # 辅星 / 煞星 / 桃花 分类整理（扫 minor_stars 和 adj_stars 两处）
    minor_stars = palace.get("minor_stars") or []
    adj_stars = palace.get("adj_stars") or []
    fu_list, sha_list, taohua_list, luma_list, other_minor_list = [], [], [], [], []

    def _classify_star(s, target_lists):
        nm = _star_name(s)
        if not nm:
            return
        formatted = _format_star(s)
        if nm in SIX_SHA:
            target_lists["sha"].append(formatted)
        elif nm in SIX_JI:
            target_lists["fu"].append(formatted)
        elif nm in TAO_HUA:
            target_lists["taohua"].append(formatted)
        elif nm in LU_MA:
            target_lists["luma"].append(formatted)
        else:
            target_lists["other"].append(formatted)

    buckets = {"sha": sha_list, "fu": fu_list, "taohua": taohua_list,
               "luma": luma_list, "other": other_minor_list}
    for s in minor_stars:
        _classify_star(s, buckets)
    # adj_stars 也扫描，主要为了抓桃花星（红鸾天喜）和其它杂耀
    adj_other_list = []
    for s in adj_stars:
        nm = _star_name(s)
        if not nm:
            continue
        if nm in TAO_HUA:
            taohua_list.append(_format_star(s))
        else:
            adj_other_list.append(_format_star(s))

    lines = [f"【{name}（{stem}{branch}）】{body_tag}"]
    lines.append(f"  主星：{'、'.join(major_strs) if major_strs else '空宫（无主星）'}")
    if fu_list:
        lines.append(f"  六吉：{'、'.join(fu_list)}")
    if sha_list:
        lines.append(f"  六煞：{'、'.join(sha_list)} ⚠")
    if luma_list:
        lines.append(f"  禄马：{'、'.join(luma_list)}")
    if taohua_list:
        lines.append(f"  桃花：{'、'.join(taohua_list)}")
    if other_minor_list:
        # 其它辅星只显示前 6 个避免太长
        shown = other_minor_list[:6]
        more = f"…等共{len(other_minor_list)}颗" if len(other_minor_list) > 6 else ""
        lines.append(f"  其它辅星：{'、'.join(shown)}{more}")

    if adj_other_list:
        # 杂耀也限制长度
        shown_adj = adj_other_list[:6]
        more_adj = f"…等共{len(adj_other_list)}颗" if len(adj_other_list) > 6 else ""
        lines.append(f"  杂耀：{'、'.join(shown_adj)}{more_adj}")

    cs12 = palace.get("changsheng12", "")
    if cs12:
        lines.append(f"  长生十二神：{cs12}")
    boshi = palace.get("boshi12", "")
    if boshi:
        lines.append(f"  博士十二神：{boshi}")

    dr = palace.get("decadal_range")
    if dr and isinstance(dr, (list, tuple)) and len(dr) >= 2:
        lines.append(f"  大限：{dr[0]}–{dr[1]}岁")

    return "\n".join(lines)


def format_palace_oneline(palace: Dict[str, Any]) -> str:
    """
    把一个宫位格式化成单行紧凑文本（用于十二宫概览）。

    示例：
        命宫(甲午)：紫微(庙)·化权、贪狼 | 大限6-15
    """
    name = palace.get("name", "?")
    stem = palace.get("heavenly_stem", "")
    branch = palace.get("earthly_branch", "")
    # 主星已经在 _format_star 中带上生年四化标记
    major_strs = [_format_star(s) for s in (palace.get("major_stars") or [])]
    major_strs = [x for x in major_strs if x]
    major_str = "、".join(major_strs) if major_strs else "空宫"

    # 简短显示煞星（让 LLM 知道哪些宫有煞）
    sha_in_minor = [
        _star_name(s) for s in (palace.get("minor_stars") or [])
        if _star_name(s) in SIX_SHA
    ]
    sha_str = f" 煞：{'、'.join(sha_in_minor)}" if sha_in_minor else ""

    # 检查辅星里是否有生年四化（如壬干左辅化科会落到辅星上）
    sihua_in_minor = []
    for s in (palace.get("minor_stars") or []):
        m = _star_mutagen(s)
        if m:
            sihua_in_minor.append(f"{_star_name(s)}·化{m}")
    sihua_str = f" 辅化：{'、'.join(sihua_in_minor)}" if sihua_in_minor else ""

    # 大限年龄
    dr = palace.get("decadal_range")
    dr_str = ""
    if dr and isinstance(dr, (list, tuple)) and len(dr) >= 2:
        dr_str = f" | 大限{dr[0]}-{dr[1]}"

    return f"{name}({stem}{branch})：{major_str}{sha_str}{sihua_str}{dr_str}"


# ─────────────────────────────────────────────────────────────
# 借宫支持（命宫空宫时借对宫）
# ─────────────────────────────────────────────────────────────

def detect_borrowed_palace(soul_palace: Dict[str, Any], palaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    如果命宫空宫（无 14 主星），返回对宫信息供"借宫"看。

    紫微高阶用法：命宫空宫时借迁移宫的主星论命。
    """
    if not soul_palace or not palaces:
        return None
    soul_majors = [_star_name(s) for s in (soul_palace.get("major_stars") or [])]
    soul_majors = [n for n in soul_majors if n in FOURTEEN_MAJOR]
    if soul_majors:
        return None  # 命宫有主星，不需要借
    # 命宫空宫，找对宫（迁移宫）
    soul_idx = soul_palace.get("index", 0)
    opp_idx = (soul_idx + 6) % 12
    by_index = {p.get("index", -1): p for p in palaces}
    opp = by_index.get(opp_idx)
    if not opp:
        return None
    opp_majors = [_format_star(s) for s in (opp.get("major_stars") or [])]
    opp_majors = [x for x in opp_majors if x]
    if not opp_majors:
        return None  # 对宫也空宫
    return {
        "opposite_palace": opp.get("name", ""),
        "opposite_stars": opp_majors,
    }


# ─────────────────────────────────────────────────────────────
# 主入口：build_ziwei_context
# ─────────────────────────────────────────────────────────────

def build_ziwei_context(data: Dict[str, Any]) -> str:
    """
    把 build_ziwei_chart() 输出的完整 data 转成 LLM 高信息密度上下文。

    返回格式化好的多行中文文本（不含 system prompt 部分，
    那部分由 INTERPRET_SYSTEMS['ziwei'] 提供）。

    设计：宁可信息冗余，不可让 LLM 凭训练印象补充缺失字段。
    """
    palaces = _safe_get_palaces(data)
    metadata = _safe_get_metadata(data)

    if not palaces:
        return "【警告】命盘数据不完整，无 palaces 字段。"

    # ── 0. 派别声明（顶部明示） ──
    sections: List[str] = []
    sections.append(
        "【派别声明】当前使用 iztro_py 默认四化表（中州派 / 紫云派体系，与紫微派 ziwei.pub 一致）。"
        "若需切换钦天派或飞星梁派的四化表，请告知。"
    )

    # ── 1. 基础信息 ──
    soul_palace = find_soul_palace(palaces)
    body_palace = find_body_palace(palaces)

    ming_zhu = resolve_ming_zhu(metadata, soul_palace)
    shen_zhu = resolve_shen_zhu(metadata)

    basic_lines = ["【基础信息】"]
    if metadata.get("solar_date"):
        basic_lines.append(f"  阳历：{metadata.get('solar_date','')} {metadata.get('birth_hour_name','')}")
    if metadata.get("lunar_date"):
        basic_lines.append(f"  农历：{metadata.get('lunar_date','')}")
    if metadata.get("chinese_date"):
        basic_lines.append(f"  四柱：{metadata.get('chinese_date','')}")
    if metadata.get("gender"):
        basic_lines.append(f"  性别：{metadata.get('gender','')}")
    if metadata.get("zodiac"):
        basic_lines.append(f"  生肖：{metadata.get('zodiac','')}")
    five_el = metadata.get("five_elements", "")
    if five_el:
        basic_lines.append(f"  五行局：{five_el}")
    if ming_zhu:
        basic_lines.append(f"  命主：{ming_zhu}（先天根器，按命宫地支取）")
    if shen_zhu:
        basic_lines.append(f"  身主：{shen_zhu}（后天造作，按生年地支取）")
    if soul_palace:
        basic_lines.append(
            f"  命宫地支：{soul_palace.get('earthly_branch','')}"
            f"（命宫在第 {soul_palace.get('index','?')} 宫，名「{soul_palace.get('name','')}」）"
        )
    sections.append("\n".join(basic_lines))

    # ── 2. 命宫详情（核心） ──
    if soul_palace:
        sections.append("【命宫详情】（一生格局根基）\n" + format_palace_detail(soul_palace))

        # 借宫提示
        borrowed = detect_borrowed_palace(soul_palace, palaces)
        if borrowed:
            sections.append(
                f"【借宫提示】命宫空宫（无 14 主星），按紫微传统应借对宫"
                f"「{borrowed['opposite_palace']}」之主星论命：{ '、'.join(borrowed['opposite_stars']) }。"
                f"借宫之人，性情多元，需兼看本命与对宫。"
            )

    # ── 3. 身宫详情（若与命宫不同宫） ──
    if body_palace and soul_palace and body_palace.get("index") != soul_palace.get("index"):
        sections.append("【身宫详情】（中年后运势重心）\n" + format_palace_detail(body_palace))
    elif body_palace and soul_palace and body_palace.get("index") == soul_palace.get("index"):
        sections.append("【身宫】身命同宫（子午时生人特征），先天后天合一，性格与追求一致。")

    # ── 4. 三方四正完整 ──
    if soul_palace is not None:
        soul_idx = soul_palace.get("index", -1)
        sfsz = get_san_fang_si_zheng(palaces, soul_idx)
        if sfsz:
            sfsz_lines = ["【命宫三方四正详情】（命迁财官，论一生格局主轴；每宫详列辅煞与四化）"]
            labels = ["本宫", "三合(+4)", "三合(+8)", "对宫(+6)"]
            for i, p in enumerate(sfsz):
                label = labels[i] if i < len(labels) else "?"
                # 三方四正的每个宫都用详细格式
                detail_lines = format_palace_detail(p).split("\n")
                # 在第一行加上 label 标识
                if detail_lines:
                    detail_lines[0] = f"  [{label}] {detail_lines[0]}"
                    # 后续缩进一级
                    for j in range(1, len(detail_lines)):
                        detail_lines[j] = "  " + detail_lines[j]
                sfsz_lines.append("\n".join(detail_lines))
            # 三方四正聚合星耀总览
            all_majors_in_sfsz = []
            for p in sfsz:
                for s in (p.get("major_stars") or []):
                    nm = _star_name(s)
                    if nm in FOURTEEN_MAJOR:
                        all_majors_in_sfsz.append(nm)
            if all_majors_in_sfsz:
                sfsz_lines.append(
                    f"  → 三方四正主星合计：{ '、'.join(all_majors_in_sfsz) }"
                )
            sections.append("\n".join(sfsz_lines))

    # ── 4.5 主星亮度评级 + 命格评分（Z-3） ──
    # 把命宫+三方四正的主星亮度做综合评分，给出"上格/中上/中/中下/下"建议
    # 这是命理评级最直观的"先天格局"维度
    if soul_palace is not None:
        try:
            from core.ziwei.brightness import (
                compute_mingge_overall_rating,
                format_brightness_analysis_for_prompt,
            )
            soul_idx = soul_palace.get("index", -1)
            sfsz_for_score = get_san_fang_si_zheng(palaces, soul_idx)
            overall_rating = compute_mingge_overall_rating(soul_palace, sfsz_for_score)
            brightness_text = format_brightness_analysis_for_prompt(overall_rating)
            if brightness_text:
                sections.append(brightness_text)
        except Exception as e:
            sections.append(
                f"【主星亮度与命格评级】\n  （生成失败：{e}）"
            )

    # ── 4.7 经典格局自动检测（Z-4） ──
    # 自动识别 15 个吉格 + 8 个凶格，命理师论命的核心动作
    try:
        from core.ziwei.pattern_detector import (
            detect_all_patterns,
            format_patterns_for_prompt,
        )
        # 获取出生时辰索引（用于日照雷门格的昼夜判断）
        birth_hour_index = data.get("metadata", {}).get("birth_hour_index")
        if birth_hour_index is None:
            # 从其他字段反推
            bhi = data.get("birth_hour_index")
            if bhi is not None:
                birth_hour_index = bhi
        patterns_result = detect_all_patterns(palaces, birth_hour_index=birth_hour_index)
        patterns_text = format_patterns_for_prompt(patterns_result)
        if patterns_text:
            sections.append(patterns_text)
    except Exception as e:
        sections.append(
            f"【经典格局检测】\n  （生成失败：{e}）"
        )

    # ── 4.8 冲宫连锁深度分析（Z-8） ──
    # 把所有化忌冲宫事件按"被冲宫"汇总，输出多层语义警示
    # 在 overlay 视图下三层全用；本命视图下只用本命层
    try:
        from core.ziwei.chong_analysis import (
            analyze_chong_chains, format_chong_chains_for_prompt
        )
        from core.ziwei.feihua_advanced import analyze_palace_feihua
        natal_records_for_chong = analyze_palace_feihua(palaces, school="zhongzhou")

        # 三盘叠合视图时（_overlay 注入），拿大限/流年数据
        overlay = data.get("_overlay") or {}
        decade_data = overlay.get("decade") or (overlay.get("triple") or {}).get("decade_info")
        triple_data = overlay.get("triple") or {}
        decade_overlay_record = None
        annual_overlay_record = None
        decade_layout = None
        annual_layout = None

        try:
            from core.ziwei.feihua_advanced import analyze_overlay_feihua
            from core.ziwei.chart import (
                compute_decade_palaces_layout, compute_annual_palaces_layout,
            )
            from core.constants import TIANGAN, DIZHI

            if decade_data and isinstance(decade_data, dict):
                stem = decade_data.get("stem")
                pidx = decade_data.get("palace_idx")
                if stem and pidx is not None:
                    decade_overlay_record = analyze_overlay_feihua(
                        palaces, stem, int(pidx), "大限", "zhongzhou"
                    )
                    decade_layout = compute_decade_palaces_layout(int(pidx))

            # 流年（仅 triple）
            current_year = triple_data.get("current_year")
            if current_year:
                year_stem = TIANGAN[(int(current_year) - 1984) % 10]
                year_branch = DIZHI[(int(current_year) - 1984) % 12]
                for p in palaces:
                    if p.get("earthly_branch") == year_branch:
                        annual_overlay_record = analyze_overlay_feihua(
                            palaces, year_stem, p["index"], f"流年{current_year}", "zhongzhou"
                        )
                        annual_layout = compute_annual_palaces_layout(p["index"])
                        break
        except Exception as _e1:
            from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e1)

        chains = analyze_chong_chains(
            palaces, natal_records_for_chong,
            decade_overlay_record=decade_overlay_record,
            annual_overlay_record=annual_overlay_record,
            decade_layout=decade_layout,
            annual_layout=annual_layout,
        )
        chong_text = format_chong_chains_for_prompt(chains)
        if chong_text:
            sections.append(chong_text)
    except Exception as e:
        sections.append(
            f"【冲宫连锁警示】\n  （生成失败：{e}）"
        )

    # ── 5. 生年四化 + 来因宫 ──
    natal_sihua = collect_natal_sihua(palaces)
    if natal_sihua:
        # 排序：禄 → 权 → 科 → 忌
        hua_order = {"化禄": 0, "化权": 1, "化科": 2, "化忌": 3}
        natal_sihua_sorted = sorted(natal_sihua, key=lambda x: hua_order.get(x.get("hua_type",""), 9))
        sihua_lines = ["【生年四化】（一辈子不变的命运基调）"]
        for item in natal_sihua_sorted:
            star = item.get("star", "")
            hua = item.get("hua_type", "")
            palace_name = item.get("palace", "")
            brightness = item.get("brightness", "")
            br_tag = f"({brightness})" if brightness else ""
            sihua_lines.append(f"  {star}{br_tag} {hua} 落在【{palace_name}】")
        sections.append("\n".join(sihua_lines))

        # 来因宫
        laiyin = find_laiyin_palace(natal_sihua)
        if laiyin:
            sections.append(
                f"【来因宫】（飞星派起手第一步：生年化忌所落之宫）\n"
                f"  来因宫：【{laiyin['palace']}】（{laiyin['ji_star']}化忌坐守）\n"
                f"  一生主题：{laiyin['life_theme']}"
            )
    else:
        sections.append(
            "【生年四化】（未在命盘数据中检测到 mutagen 标记）\n"
            "  说明：可能因 iztro_py 版本差异未输出 mutagen 字段；请告诉用户此项缺失。"
        )

    # ── 6. 飞星派飞化分析（Z-2 核心） ──
    # 这是 Z-2 的核心新增：把 12 宫的飞化结构化呈现给 LLM。
    # 含离心自化/向心自化/普通飞宫三类区分、忌冲、双忌、禄解忌、禄忌交战、质能变等语象。
    try:
        from core.ziwei.feihua_advanced import (
            analyze_palace_feihua,
            summarize_feihua_landscape,
            format_feihua_for_prompt,
        )
        feihua_records = analyze_palace_feihua(palaces, school="zhongzhou")
        feihua_summary = summarize_feihua_landscape(feihua_records, palaces)
        feihua_text = format_feihua_for_prompt(
            feihua_records, feihua_summary, school="zhongzhou"
        )
        sections.append(feihua_text)
    except Exception as e:
        sections.append(
            f"【飞星派飞化分析】\n  （生成失败：{e}；本次仅以中州派三合论命，飞化层暂缺）"
        )

    # ── 7. 十二宫概览 ──
    overview_lines = ["【十二宫概览】（紧凑列出全盘）"]
    # 按 index 顺序输出
    sorted_palaces = sorted(palaces, key=lambda p: p.get("index", 99))
    for p in sorted_palaces:
        overview_lines.append("  " + format_palace_oneline(p))
    sections.append("\n".join(overview_lines))

    # ── 7.5 大限/流年叠合飞化（任务 3：overlay 集成） ──
    # 前端若调过 /ziwei/decade 或 /ziwei/triple 端点，会通过 data["_overlay"] 传入。
    # 我们在此使用 Z-2 飞化引擎重新计算（不沿用旧 calculate_decade_feihua）
    overlay = data.get("_overlay")
    current_layer = "natal"
    if overlay and isinstance(overlay, dict):
        current_layer = overlay.get("layer", "natal")
        try:
            from core.ziwei.feihua_advanced import (
                analyze_overlay_feihua,
                format_overlay_feihua_for_prompt,
                analyze_three_plate_concentration,
            )
            decade_overlay_record = None
            annual_overlay_record = None

            # —— 大限 ——
            decade_payload = overlay.get("decade")
            triple_payload = overlay.get("triple")

            # 大限信息可以来自 /decade 或 /triple (两端点都返回 decade_info / decade)
            decade_info = None
            if decade_payload:
                # /decade 返回 {decade: {palace_idx, stem, age_range, palace_name}, feihua: [...]}
                decade_info = decade_payload.get("decade")
            if triple_payload and not decade_info:
                # /triple 返回 {decade_info: {palace_idx, stem, age_range}, ...}
                decade_info = triple_payload.get("decade_info")

            if decade_info and decade_info.get("stem") and decade_info.get("palace_idx") is not None:
                decade_overlay_record = analyze_overlay_feihua(
                    palaces=palaces,
                    overlay_stem=decade_info["stem"],
                    overlay_palace_idx=decade_info["palace_idx"],
                    overlay_label="大限",
                    school="zhongzhou",
                )
                # 附加年龄范围信息
                age_range = decade_info.get("age_range")
                if age_range and len(age_range) >= 2:
                    decade_overlay_record["age_range_text"] = f"{age_range[0]}–{age_range[1]}岁"

            # —— 流年 ——
            if triple_payload:
                annual_fh_raw = triple_payload.get("annual_feihua")
                current_year = triple_payload.get("current_year")
                # 反推流年干（年份 - 1984 % 10 → 天干）
                if current_year:
                    try:
                        from core.constants import TIANGAN
                        year_stem = TIANGAN[(int(current_year) - 1984) % 10]
                    except Exception:
                        year_stem = ""
                    # 流年命宫的 index 不一定等于本命命宫；
                    # 但传统做法是把流年太岁干起化飞入本命，所以 overlay_palace_idx
                    # 用本命命宫即可（用于判断"自化"标识时不严格符合飞星派定义，
                    # 但对于"飞入命宫/冲命宫"等关键警示足够）。
                    soul_p = find_soul_palace(palaces)
                    soul_idx = soul_p.get("index", 0) if soul_p else 0
                    if year_stem:
                        annual_overlay_record = analyze_overlay_feihua(
                            palaces=palaces,
                            overlay_stem=year_stem,
                            overlay_palace_idx=soul_idx,
                            overlay_label=f"流年{current_year}",
                            school="zhongzhou",
                        )
                        annual_overlay_record["year"] = current_year

            # —— 拼装输出 ——
            overlay_sections: List[str] = []
            layer_label = {"natal": "本命盘", "decade": "大限盘", "triple": "三盘叠合"}.get(current_layer, current_layer)
            overlay_sections.append(f"【当前用户视图】{layer_label}（用户在前端选择的视图）")

            if decade_overlay_record:
                age_str = decade_overlay_record.get("age_range_text", "")
                if age_str:
                    overlay_sections.append(
                        format_overlay_feihua_for_prompt(decade_overlay_record)
                        + f"\n  · 大限年龄：{age_str}"
                    )
                else:
                    overlay_sections.append(format_overlay_feihua_for_prompt(decade_overlay_record))

            if annual_overlay_record:
                year_str = annual_overlay_record.get("year", "")
                overlay_sections.append(
                    format_overlay_feihua_for_prompt(annual_overlay_record)
                    + (f"\n  · 流年：{year_str}年" if year_str else "")
                )

            # 三盘叠合（双忌/三忌汇聚）
            three_plate_warnings = analyze_three_plate_concentration(
                natal_palaces=palaces,
                decade_overlay=decade_overlay_record,
                annual_overlay=annual_overlay_record,
            )
            if three_plate_warnings:
                tp_lines = ["【三盘叠合·忌汇聚警示】"]
                for w in three_plate_warnings:
                    tp_lines.append(f"  {w}")
                overlay_sections.append("\n".join(tp_lines))

            if overlay_sections:
                sections.append("\n\n".join(overlay_sections))
        except Exception as e:
            sections.append(
                f"【大限/流年叠合飞化】\n  （生成失败：{e}）"
            )

    # ── 8. 数据完整性提示 ──
    has_decade_info = bool(data.get("decade_info")) or bool(
        overlay and overlay.get("decade") or overlay and overlay.get("triple")
    )
    has_triple = bool(data.get("combined_warnings")) or bool(
        overlay and overlay.get("triple")
    )
    notes = []
    if not has_decade_info:
        notes.append("当前仅本命盘数据（前端未调用 /ziwei/decade 或 /ziwei/triple 端点）；如需大限/流年分析，请提示用户切换三盘叠合视图后再问。")
    else:
        layer_label_msg = {"natal": "本命视图", "decade": "大限视图", "triple": "三盘叠合视图"}.get(current_layer, current_layer)
        notes.append(f"用户当前在【{layer_label_msg}】下提问；回答应优先围绕该层的飞化语象。")
    sections.append("【数据范围】\n  " + ("\n  ".join(notes) if notes else "本命盘 + 大限 + 流年 完整。"))

    return "\n\n".join(sections)


# ─────────────────────────────────────────────────────────────
# 分析任务指令（强制结构化引导）
# ─────────────────────────────────────────────────────────────

ZIWEI_ANALYSIS_INSTRUCTION = """
【分析任务】请严格按以下七步分析，每一步必须明确引用上方命盘数据中的具体字段，禁止凭训练印象补充未提供的星耀或四化：

## 第一步：命格定位（必引用【主星亮度与命格评级】和【经典格局检测】结果）
- **首先引用上方"主星亮度与命格评级"的总评结果**（上格/中上格/中格/中下格/下格），说明此命先天格局
- **接着引用上方"经典格局检测"的结果** — 列出所有自动识别出的吉格和凶格，每个格局的"成格条件"和"含义"都要在分析中用上
- 命宫主星组合（含亮度与生年四化标记）— 引用"主星×宫位断语"中的具体语句
- 三方四正合参：财官迁三宫的主星与亮度评级
- 命主、身主与命宫的关系
- **不能忽略格局**：若检测到经典吉格（如紫府同宫、君臣庆会、杀破狼、机月同梁等），必须明确指出；若检测到凶格（如羊陀夹忌、巨火羊、刑囚夹印等），必须提出警示与化解建议
- **不能忽略亮度评分**：例如太阳在子陷地坐命，即使三方有禄，也不能简单判为上格；要按评分体系给出客观评级

## 第二步：来因宫论核心命题（飞星派起手）
- 来因宫所在 → 一生主题方向
- 来因宫的星耀如何影响此人一生执着点

## 第三步：生年四化论吉凶（一辈子不变的命运基调）
- 化禄星与化禄宫 → 这辈子在哪个领域天然得利
- 化权星与化权宫 → 这辈子在哪个领域有主导力
- 化科星与化科宫 → 这辈子在哪个领域有名声/才华
- 化忌星与化忌宫 → 这辈子在哪个领域注定有阻碍/执念

## 第四步：飞星派飞化语象（用上方【飞星派飞化分析】结果，禁止自己重算）
- **必须引用"全盘关键语象"中已检测出的事项**：质能变 / 双忌叠加 / 禄解忌 / 禄忌交战 / 命宫飞入 / 化忌冲命宫
- 区分三种飞化类型的语义：
  - **离心自化**：本宫能量流出消耗，主"留不住、放弃、自损"
  - **向心自化**：能量射向对宫，对宫受影响（被拖累或得力）
  - **普通飞宫**：跨宫能量流动；化忌还要冲落点对宫
- 关注**飞入命宫**的化象（影响一生格局），以及**化忌冲命宫**（一生有此宫的干扰）
- 解读时必须区分**我宫**（命财官田福疾）与**他宫**（兄夫子迁交父）：
  - 禄入我宫 = 得；禄入他宫 = 给别人/为他人作嫁
  - 忌入我宫 = 自身受困；忌冲我宫 = 损失
- **必须引用上方【冲宫连锁警示】section** — 这是飞星派最精髓的"一冲多义"语象：
  - 同一冲宫事件在**本命/大限/流年三层 layout 下角色不同**时，影响主题随之扩散
  - 例：本命疾厄宫化忌冲命宫，若大限层此命宫=大限子女宫，则该十年健康问题表现为子女牵连
  - 多个化忌冲同一宫位（次数 ≥ 2）= 此宫主题重灾区，必须重点防范
  - 引用具体的"影响主题跨【X/Y/Z】"连锁解读，而非泛泛说"某宫被冲"

## 第五步：煞星分布与凶象警示
- 六煞星（擎羊/陀罗/火星/铃星/地空/地劫）落在哪些宫
- 命宫三方四正是否会煞 → 决定格局是否"破"
- 若煞星与桃花同宫 → 论感情劫；若煞星与财星同宫 → 论破财劫

## 第六步：身宫与中年后运势
- 身宫与命宫的关系（同宫 / 在哪个宫）
- 身宫所主之事 = 此人一生最在意的方向

## 第七步：应期推断与回答用户问题
- **如有【大限盘飞化分析】**：基于大限关键语象（如"大限化忌冲命宫"、"大限禄解忌"）论这十年的吉凶趋势
- **如有【流年盘飞化分析】**：基于流年关键语象论这一年的具体事件
- **如有【三盘叠合·忌汇聚警示】**：三忌汇聚的宫位是本年/本限的"应期窗口"，事必发生
- 若用户提了具体问题：基于以上数据直接回答，**优先用对应层（本命/大限/流年）的飞化语象论吉凶**（如禄入夫妻=感情得意，忌冲夫妻=婚姻有伤）
- 若用户在大限/流年视图下提问：**回答必须围绕该层的飞化**，本命层只作为背景参考
- 若无大限/流年数据：直说"应期判断需切换三盘叠合视图获取大限流年数据"，不要编造
- 若无问题：给出此命的人生大方向建议

## 重要规则
1. 不要使用命盘数据中没有的星耀名（不要"凭印象"补充未列出的辅星煞星）
2. 引用任何星耀必须带上其所在宫位（不要泛泛说"廉贞星"，而要说"财帛宫的廉贞星"）
3. **区分三层四化**：
   - **生年四化**（一辈子不变，已在【生年四化】节列出）
   - **离心/向心自化**（本宫宫干的同宫/对宫飞化，已在【飞星派飞化分析】列出）
   - **普通飞宫**（本宫宫干的跨宫飞化，已在【飞星派飞化分析】列出）
   - **大限/流年飞化**（已在【大限盘飞化分析】/【流年盘飞化分析】列出，如有）
4. **基于视图层回答**：用户当前的视图在【数据范围】中标明（本命视图 / 大限视图 / 三盘叠合视图）。回答应优先围绕该层的语象，不要把所有层的信息平铺直叙。
5. 最后必须有【结论】段落，用通俗直白的语言总结此命格特点与最重要的 1-2 条建议

## 输出格式协议（Z-9 强制结构化）

你的回答**必须严格遵守**以下格式约定，前端会按此协议解析并渲染：

### 一、章节标记
每一步分析用 Markdown 二级标题 (`##`) 开头，原样使用以下章节名（不得改名/删步骤）：

```
## 第一步：命格定位
（内容...）

## 第二步：来因宫论核心命题
（内容...）

## 第三步：生年四化论吉凶
（内容...）

## 第四步：飞星派飞化语象
（内容...）

## 第五步：大限流年应期
（内容...）

## 第六步：用户问题精答
（仅当用户有问题时；无问题则写"无具体问题，省略本步"）

## 第七步：结论与建议
（内容...）
```

### 二、引用溯源标记（核心）
**每条具体判断后必须紧跟引用标签**，让用户能追溯到 prompt 中的原始数据：

格式：` [依据：<section>·<具体项>]`

允许的 section 名（只能用下面这些，不得编造）：
- `主星亮度评级` — 引用【主星亮度与命格评级】section
- `经典格局` — 引用【经典格局检测】section
- `飞星派飞化` — 引用【飞星派飞化分析】section
- `冲宫连锁` — 引用【冲宫连锁警示】section
- `生年四化` — 引用【生年四化】section
- `来因宫` — 引用【来因宫】section
- `三方四正` — 引用【命宫三方四正】section
- `大限盘` — 引用【大限盘飞化分析】section（仅大限/三盘视图）
- `流年盘` — 引用【流年盘飞化分析】section（仅三盘叠合视图）

**示例**（这是正确的写法）：
- 此命整体上格 [依据：主星亮度评级·整体评级上格+2.14]
- 命宫紫微午宫入庙，帝座之地 [依据：主星亮度评级·紫微午宫入庙]
- 触发"君臣庆会"吉格 [依据：经典格局·君臣庆会格]
- 夫妻宫被冲 4 次，配偶相关事项有多重风险 [依据：冲宫连锁·夫妻宫被冲4次]
- 命宫天同化忌冲迁移宫（离心自化） [依据：飞星派飞化·命宫天同离心自化忌]

**禁止**：泛泛说"根据命盘"、"从飞化看"——必须给出具体的 section 名和具体项。

### 三、关键结论加粗
每一步最关键的 1-2 句结论用 **粗体**，让用户一眼抓住要点。

### 四、避免空话
**禁止**写以下空话：
- ❌ "紫微入命主有领导力" — 太泛
- ❌ "此命大富大贵" — 无依据
- ❌ "建议多多努力" — 无操作性
- ❌ "根据古书记载..." — 不引用具体 section

**正确写法**：
- ✓ "紫微在午入庙，帝座之地权威最盛 [依据：主星亮度评级·紫微午宫入庙]，但需有左辅右弼之类的辅星才不致孤君无臣"
- ✓ "本命此格触发'君臣庆会'，但条件'紫微+左辅右弼'必须满足 [依据：经典格局·君臣庆会格]"

### 五、结尾不带任何尾巴
不要写"以上分析仅供参考"、"具体还需结合实际"这种无意义的免责声明 — 前端已经统一展示了。
"""
