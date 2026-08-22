"""
core/ziwei/brightness.py
=========================
紫微斗数主星亮度评级与命格高低评分引擎（Z-3）。

iztro_py 已经为每颗主星给出 brightness 字段（庙/旺/得/利/平/不/陷七级中文之一），
但 Z-1/Z-2 中我们只是把它"显示"了出来，并没有让 LLM 在论命时**用好**这个维度。

本模块的职责：
  1. 亮度等级 → 分数映射（用于命格评分）
  2. 亮度等级 → 标准命理学含义（"庙吉星极吉、凶星不凶"等七级断语）
  3. 14 主星各自的庙陷敏感度（不敏感的 5 颗 vs 敏感的 9 颗）
  4. 主星 × 庙陷的具体落点断语（如太阳在子陷 = 父亲不利、夜生人尤剧）
  5. 命格高低自动评分（命宫+三方四正 4 主星平均分）→ 上格/中格/下格/破格

设计原则：
  · 不用静态表替代 iztro 的 brightness 字段（iztro 已经计算好了）
  · 只补充"评分 / 评级 / 断语"这一层，作为论命的语义层
  · 命格判定是建议，不是绝对 — 实际命格高低还需结合四化/煞星/格局
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# 1. 七级亮度分数与命理学含义
# ─────────────────────────────────────────────────────────────

# 标准七级（来源：紫微斗数全书 / 令东来 / 神机阁 多源校对）
# 分数：+3(庙) +2(旺) +1(得) 0(利) -1(平) -2(不) -3(陷)
BRIGHTNESS_SCORE: Dict[str, int] = {
    "庙": 3,    # 星最明，得数最强
    "旺": 2,    # 星次明，得数次强
    "得": 1,    # 星光明，得数适度（又叫"得地"）
    "利": 0,    # 星尚明，得数渐弱（又叫"利益"）
    "平": -1,   # 星光已低，得数已弱（又叫"和平"）
    "不": -2,   # 星光已暗，得数最弱（又叫"不得地"）
    "陷": -3,   # 星无光，无数可得（又叫"落陷"）
    "":   0,    # 空亮度（不敏感星或未排到）
}

# 七级亮度的命理学含义（标准断语）
BRIGHTNESS_MEANING: Dict[str, str] = {
    "庙": "星最明，吉星极吉，凶星不凶。组合好基本不畏煞星",
    "旺": "星次明，吉星吉，凶星不凶。能充分发挥优势",
    "得": "星光明，吉星仍吉，凶星不凶。优点明显",
    "利": "星尚明，吉星尚吉，凶星渐凶。优势渐弱",
    "平": "星光已低，吉星力微，凶星肆凶。怕煞，敏感",
    "不": "星光已暗，吉星无力，凶星愈凶。优势难显",
    "陷": "星无光，吉星无用，凶星最凶。遇煞更凶",
}


# ─────────────────────────────────────────────────────────────
# 2. 14 主星的庙陷敏感度
# ─────────────────────────────────────────────────────────────

# 不受亮度影响的 5 颗主星 — 紫府武杀破
# 这些星不论亮度如何，特质相对固定（紫天府特质稳定，杀破狼武曲煞气固定）
# 论命时这 5 颗的亮度可以"基本理解为庙旺"
BRIGHTNESS_INSENSITIVE: set = {
    "紫微", "天府", "武曲", "七杀", "破军"
}

# 受亮度影响显著的 9 颗主星 — 机日月同梁巨贪相廉
# 这些星亮度变化对论命影响极大，必须重点关注
BRIGHTNESS_SENSITIVE: set = {
    "天机", "太阳", "太阴", "天同", "天梁",
    "巨门", "贪狼", "天相", "廉贞"
}


# ─────────────────────────────────────────────────────────────
# 3. 主星 × 落陷的针对性断语（重点星陷地警示）
# ─────────────────────────────────────────────────────────────

# 这些断语是命理师必看的"陷地警示"，覆盖最影响论命的几种组合
# 格式：(星名, 落陷宫位地支 list) → 警示文
STAR_AT_FALLEN_BRANCH_WARNINGS: Dict[Tuple[str, str], str] = {
    # 太阳 — 陷地辛劳，父星不利，男命克父
    ("太阳", "子"): "太阳子宫落陷：日生人事业辛苦先勤后惰，夜生人更剧；父亲缘薄，男命克父、女命克夫倾向",
    ("太阳", "亥"): "太阳亥宫落陷：黑夜之日，光辉不显；男性六亲缘薄，事业多奔波而少成",
    ("太阳", "戌"): "太阳戌宫落陷：晚景之日，志大才疏；夜生人精神鼓荡，白天易困倦",
    ("太阳", "酉"): "太阳酉宫落陷：日落之象，先盛后衰；中年后事业受挫",
    ("太阳", "申"): "太阳申宫落陷：西斜之日，先勤后惰，名声虚而不实",
    
    # 太阴 — 陷地母星不利，女命刑克
    ("太阴", "卯"): "太阴卯宫落陷：白日之月，光辉被夺；女命不利母，男命妻迟",
    ("太阴", "辰"): "太阴辰宫落陷：月入墓地，情感受抑；夫妻缘薄",
    ("太阴", "巳"): "太阴巳宫落陷：火地之月，受燥烤；情绪敏感，易神经衰弱",
    ("太阴", "午"): "太阴午宫落陷：日午之月最弱；女命不利母、夫，男命妻有阻碍",
    
    # 天机 — 陷地多思无用，决策失误
    ("天机", "丑"): "天机丑宫落陷：智星入墓，多虑而少决；决策易失误",
    ("天机", "未"): "天机未宫落陷：同上，思虑过度而无成",
    ("天机", "辰"): "天机辰宫落陷（部分流派）：心机过重，难成大局",
    ("天机", "戌"): "天机戌宫落陷（部分流派）：智巧失用，谋而不得",
    
    # 天同 — 陷地福分受损
    ("天同", "丑"): "天同丑宫落陷：福星入墓，享乐无门；多小疾小病",
    ("天同", "未"): "天同未宫落陷：同上",
    ("天同", "午"): "天同午宫不得地：太过于安逸而缺进取，福分有限",
    
    # 巨门 — 陷地口舌是非加剧
    ("巨门", "子"): "巨门子宫落陷（部分流派列为庙）：石中隐玉格的对宫；口才虚耗多",
    ("巨门", "辰"): "巨门辰宫落陷：暗星入墓，是非满身；唯辛年生人化禄反吉",
    ("巨门", "戌"): "巨门戌宫落陷：同上",
    ("巨门", "卯"): "巨门卯宫陷地：与天机同度多浮荡（巨机居卯异化）",
    
    # 贪狼 — 陷地桃花减但失原性
    ("贪狼", "辰"): "贪狼辰宫落陷：木墓之地，桃花减而不失浪荡",
    ("贪狼", "戌"): "贪狼戌宫落陷：同上",
    
    # 天相 — 陷地辅佐力减
    ("天相", "卯"): "天相卯宫落陷：印鉴失用，难辅佐",
    ("天相", "酉"): "天相酉宫落陷：同上",
    
    # 廉贞 — 陷地易官非
    ("廉贞", "巳"): "廉贞巳宫落陷：囚星入火地，易官非桃花劫",
    ("廉贞", "亥"): "廉贞亥宫落陷：囚星入水乡，反主头脑冷静，但情绪压抑",
    
    # 天梁 — 陷地孤克
    ("天梁", "申"): "天梁申宫落陷：荫星无力，孤克之象重",
    ("天梁", "酉"): "天梁酉宫落陷：同上",
    
    # 紫府武杀破 — 这 5 颗不敏感，但极端组合时也有提示
    # 这里不列，让"不敏感"提示自然处理
}

# 主星 × 庙旺的吉象提示
STAR_AT_MIAOWANG_BLESSINGS: Dict[Tuple[str, str], str] = {
    # 紫微在午 — 帝座最尊
    ("紫微", "午"): "紫微午宫入庙：帝座之地，权威最盛；最适合掌权位",
    ("紫微", "子"): "紫微子宫入庙：北斗主星归位，名利双收",
    
    # 太阳在午 — 日丽中天
    ("太阳", "午"): "太阳午宫入庙：日丽中天格，男命大贵；女命旺夫益子",
    ("太阳", "辰"): "太阳辰宫入庙：旭日东升，事业蒸蒸日上",
    ("太阳", "巳"): "太阳巳宫入庙：旭日东升，少年得志",
    ("太阳", "卯"): "太阳卯宫入庙：日照雷门格，富贵声扬",
    
    # 太阴 — 月朗天门、月生沧海
    ("太阴", "亥"): "太阴亥宫入庙：月朗天门格，富贵之命；女命尤吉",
    ("太阴", "子"): "太阴子宫入庙：水澄桂萼格，秀气逼人",
    ("太阴", "戌"): "太阴戌宫入庙：月生沧海，得名得利",
    ("太阴", "酉"): "太阴酉宫入庙：月明寒潭，名扬于外",
    
    # 巨门 — 石中隐玉
    ("巨门", "子"): "巨门子宫（部分庙派）：石中隐玉格，因辞惊众",
    ("巨门", "午"): "巨门午宫：石中隐玉格的午宫版本",
    ("巨门", "辰"): "巨门辰宫陷地，但辛年生人化禄反为奇格",
    
    # 武曲 — 财星
    ("武曲", "辰"): "武曲辰宫入庙：财星归库格，主大富",
    ("武曲", "戌"): "武曲戌宫入庙：同上",
    ("武曲", "丑"): "武曲丑宫入庙：金气之地，主有横财",
    ("武曲", "未"): "武曲未宫入庙：同上",
    
    # 天府 — 库星
    ("天府", "戌"): "天府戌宫入庙：库星归位，主稳重而富",
    
    # 七杀 — 庙旺化煞为权
    ("七杀", "寅"): "七杀寅宫入庙：化杀为权格，威权显赫",
    ("七杀", "申"): "七杀申宫入庙：同上",
    
    # 破军 — 庙旺除旧布新
    ("破军", "子"): "破军子宫入庙：英星入庙格，主大富大贵",
    ("破军", "午"): "破军午宫入庙：同上",
    
    # 天机 — 庙旺则智慧高
    ("天机", "卯"): "天机卯宫入庙：智星明亮，机谋多得",
    ("天机", "酉"): "天机酉宫入庙：同上",
    
    # 天梁 — 庙旺则贵气
    ("天梁", "子"): "天梁子宫入庙：荫星明亮，贵人多，名声好",
    ("天梁", "午"): "天梁午宫入庙：同上",
    ("天梁", "寅"): "天梁寅宫入庙：长寿之象，贵气重",
    
    # 天相 — 庙旺则辅佐有功
    ("天相", "辰"): "天相辰宫入庙：印鉴之地，文职显贵",
    ("天相", "戌"): "天相戌宫入庙：同上",
    
    # 天同 — 庙旺则福寿双全
    ("天同", "卯"): "天同卯宫入庙：福星明亮，一生安乐",
    ("天同", "亥"): "天同亥宫入庙：水乡福地，性情温和有福",
    ("天同", "戌"): "天同戌宫入庙：福寿之地（丁年生人化忌反吉异变格）",
    
    # 贪狼 — 庙旺则才华
    ("贪狼", "寅"): "贪狼寅宫入庙：火铃同度更佳；多才多艺",
    ("贪狼", "申"): "贪狼申宫入庙：同上",
    
    # 廉贞 — 庙旺则文武双全
    ("廉贞", "寅"): "廉贞寅宫入庙：清白上格，富贵双全",
    ("廉贞", "申"): "廉贞申宫入庙：同上",
}


# ─────────────────────────────────────────────────────────────
# 4. 主要查询函数
# ─────────────────────────────────────────────────────────────

def get_brightness_score(brightness: str) -> int:
    """亮度等级 → 分数 (-3 ~ +3)。空值返回 0。"""
    return BRIGHTNESS_SCORE.get(brightness, 0)


def get_brightness_meaning(brightness: str) -> str:
    """亮度等级 → 标准命理学含义。"""
    return BRIGHTNESS_MEANING.get(brightness, "")


def is_brightness_sensitive(star_name: str) -> bool:
    """该主星是否对亮度敏感（机日月同梁巨贪相廉 = 是；紫府武杀破 = 否）。"""
    return star_name in BRIGHTNESS_SENSITIVE


def get_star_branch_note(star_name: str, branch: str) -> str:
    """
    查询主星在特定地支的针对性命理断语。
    
    优先级：庙旺吉象 → 落陷警示 → 空字符串
    
    Args:
        star_name: 主星中文名（如"太阳"）
        branch:    地支中文（如"午"）
    
    Returns:
        断语字符串。若该组合无特殊断语则返回空。
    """
    if not star_name or not branch:
        return ""
    # 先查吉象
    blessing = STAR_AT_MIAOWANG_BLESSINGS.get((star_name, branch))
    if blessing:
        return blessing
    # 再查警示
    warning = STAR_AT_FALLEN_BRANCH_WARNINGS.get((star_name, branch))
    if warning:
        return warning
    return ""


# ─────────────────────────────────────────────────────────────
# 5. 命格高低自动评分
# ─────────────────────────────────────────────────────────────

def compute_palace_score(palace: Dict[str, Any]) -> Dict[str, Any]:
    """
    对一个宫位做"主星亮度评分"。
    
    扫描该宫位所有 14 主星，按亮度打分；
    对煞星扣分（落陷煞星比庙旺煞星更凶）；
    返回综合数据。
    
    Returns:
        {
          "palace_name":   str,
          "branch":        str,
          "major_count":   int,         # 14 主星数
          "major_stars":   [str, ...],  # 主星名列表
          "raw_score":     float,       # 主星亮度总分
          "average":       float,       # 平均亮度（按主星数）
          "rating":        "上格"/"中格"/"下格"/"破格"/"空宫",
          "explanation":   str,         # 评级说明
          "star_notes":    [str, ...],  # 各主星的具体断语
        }
    """
    from core.ziwei.feihua_advanced import _palace_stars_with_mutagen  # 复用 mutagen 提取
    
    # 收集 14 主星
    FOURTEEN_MAJOR = {
        "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
        "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
    }
    
    palace_name = palace.get("name", "")
    branch = palace.get("earthly_branch", "")
    
    main_stars: List[Dict[str, Any]] = []
    for s in (palace.get("major_stars") or []):
        if isinstance(s, dict):
            nm = s.get("name", "")
            if nm in FOURTEEN_MAJOR:
                main_stars.append(s)
    
    if not main_stars:
        return {
            "palace_name":   palace_name,
            "branch":        branch,
            "major_count":   0,
            "major_stars":   [],
            "raw_score":     0.0,
            "average":       0.0,
            "rating":        "空宫",
            "explanation":   "空宫，需借对宫主星论命",
            "star_notes":    [],
        }
    
    # 算分
    total_score = 0.0
    star_names: List[str] = []
    star_notes: List[str] = []
    for s in main_stars:
        nm = s.get("name", "")
        b = s.get("brightness", "")
        score = get_brightness_score(b)
        # 不敏感星：分数权重稍微调整
        # 不敏感星按 +1 计算（避免无谓加分），敏感星按真实分
        if nm in BRIGHTNESS_INSENSITIVE:
            adj_score = max(1, score)  # 至少 +1
        else:
            adj_score = score
        total_score += adj_score
        star_names.append(nm)
        
        # 该星在该宫的针对性断语
        note = get_star_branch_note(nm, branch)
        if note:
            star_notes.append(note)
    
    avg = total_score / len(main_stars) if main_stars else 0.0
    
    # 评级
    if avg >= 2.0:
        rating = "上格"
        explanation = "主星庙旺、亮度高，先天格局极佳"
    elif avg >= 0.5:
        rating = "中上格"
        explanation = "主星明亮，先天格局较好"
    elif avg >= -0.5:
        rating = "中格"
        explanation = "主星亮度中庸，需观四化煞星综合论"
    elif avg >= -2.0:
        rating = "中下格"
        explanation = "主星亮度偏弱，需吉星辅佐方显贵气"
    else:
        rating = "下格"
        explanation = "主星落陷，先天格局受挫，多劳少成；需大吉化解"
    
    return {
        "palace_name":   palace_name,
        "branch":        branch,
        "major_count":   len(main_stars),
        "major_stars":   star_names,
        "raw_score":     total_score,
        "average":       round(avg, 2),
        "rating":        rating,
        "explanation":   explanation,
        "star_notes":    star_notes,
    }


def compute_mingge_overall_rating(
    soul_palace: Optional[Dict[str, Any]],
    san_fang_si_zheng: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    综合命宫 + 三方四正 4 宫的主星亮度，给出整体命格评级。
    
    Args:
        soul_palace:       命宫 palace dict
        san_fang_si_zheng: 三方四正 4 宫 palace dict list（含命宫）
    
    Returns:
        {
          "overall_rating":   "上格"/"中上格"/"中格"/"中下格"/"下格"/"破格",
          "average_score":    float,
          "soul_palace_score": dict (compute_palace_score 输出),
          "sfsz_scores":      [dict, ...],
          "summary":          str,
          "key_observations": [str, ...],   # 关键观察（庙旺/落陷的主星）
        }
    """
    if not soul_palace:
        return {
            "overall_rating": "未知",
            "average_score":  0.0,
            "soul_palace_score": None,
            "sfsz_scores":    [],
            "summary":        "命宫信息缺失，无法评级",
            "key_observations": [],
        }
    
    soul_score = compute_palace_score(soul_palace)
    sfsz_scores = [compute_palace_score(p) for p in san_fang_si_zheng]
    
    # 算 4 宫平均（含命宫）
    total = sum(s["raw_score"] for s in sfsz_scores)
    total_major_count = sum(s["major_count"] for s in sfsz_scores)
    avg = total / total_major_count if total_major_count > 0 else 0.0
    
    # 命宫给双倍权重（毕竟命宫最重要）
    weighted_total = soul_score["raw_score"] * 2 + sum(s["raw_score"] for s in sfsz_scores if s != soul_score)
    weighted_count = soul_score["major_count"] * 2 + sum(
        s["major_count"] for s in sfsz_scores if s != soul_score
    )
    weighted_avg = weighted_total / weighted_count if weighted_count > 0 else 0.0
    
    # 加权评级
    if weighted_avg >= 2.0:
        rating = "上格"
        summary = "命宫与三方四正主星普遍庙旺，先天命格优异，事业财官皆有基础"
    elif weighted_avg >= 0.8:
        rating = "中上格"
        summary = "主星明亮，先天命格良好，运程顺遂；煞星过多则减"
    elif weighted_avg >= -0.5:
        rating = "中格"
        summary = "主星亮度中庸，命格平实；需四化吉、辅星扶持方有突破"
    elif weighted_avg >= -2.0:
        rating = "中下格"
        summary = "主星亮度偏弱，先天命格受限；需后天努力、化解煞气"
    else:
        rating = "下格"
        summary = "主星普遍落陷，先天格局受挫；宜守不宜攻，更需谨防煞星引发劫数"
    
    # 关键观察
    observations: List[str] = []
    # 命宫主星状态
    if soul_score["major_count"] > 0:
        observations.append(
            f"命宫{ '/'.join(soul_score['major_stars']) }评级 [{soul_score['rating']}]（平均亮度 {soul_score['average']}）"
        )
    else:
        observations.append("命宫空宫 — 借对宫论命")
    
    # 庙旺主星统计（按亮度细分，《紫微斗数全书》庙旺利平不陷分级）
    # brightness 字段：'庙','旺','地','利','平','陷','不'
    BRIGHT_LEVELS = {"庙", "旺", "得"}      # 亮
    FALLEN_LEVELS = {"陷", "不", "落"}       # 暗
    
    bright_in_sfsz: List[str] = []
    fallen_in_sfsz: List[str] = []
    
    # 遍历 SFSZ 各宫，从原始 palace 的 major_stars 中读取 brightness
    all_palaces = ([soul_palace] if soul_palace else []) + (san_fang_si_zheng or [])
    for palace in all_palaces:
        for s in palace.get("major_stars", []) or []:
            if isinstance(s, dict):
                nm = s.get("name", "")
                b = s.get("brightness", "")
                if b in BRIGHT_LEVELS and nm not in bright_in_sfsz:
                    bright_in_sfsz.append(nm)
                elif b in FALLEN_LEVELS and nm not in fallen_in_sfsz:
                    fallen_in_sfsz.append(nm)
    
    # 收集所有星断语（去重）
    all_star_notes_set = set()
    for s_score in sfsz_scores:
        for note in s_score["star_notes"]:
            all_star_notes_set.add(note)
    
    return {
        "overall_rating":   rating,
        "average_score":    round(weighted_avg, 2),
        "soul_palace_score": soul_score,
        "sfsz_scores":      sfsz_scores,
        "summary":          summary,
        "key_observations": observations,
        "star_notes":       sorted(all_star_notes_set),
        # 庙旺/失陷主星统计
        "bright_in_sfsz":   bright_in_sfsz,
        "fallen_in_sfsz":   fallen_in_sfsz,
    }


# ─────────────────────────────────────────────────────────────
# 6. Prompt 格式化
# ─────────────────────────────────────────────────────────────

def format_brightness_analysis_for_prompt(
    overall: Dict[str, Any],
) -> str:
    """
    把命格评分结果格式化成 LLM prompt 可读文本。
    """
    if not overall or overall.get("overall_rating") == "未知":
        return ""
    
    lines: List[str] = []
    lines.append("【主星亮度与命格评级】（基于命宫+三方四正主星亮度，自动评分）")
    
    # 总评
    lines.append(
        f"  ◆ 整体命格评级：【{overall['overall_rating']}】"
        f"（加权平均亮度分 {overall['average_score']:+.2f}，"
        f"-3=陷 / 0=利 / +3=庙）"
    )
    lines.append(f"  · {overall['summary']}")
    
    # 命宫详情
    soul = overall.get("soul_palace_score") or {}
    if soul and soul.get("major_count", 0) > 0:
        lines.append(
            f"  ◆ 命宫【{soul['palace_name']}（{soul['branch']}）】"
            f"主星：{ '/'.join(soul['major_stars']) }，"
            f"评级 [{soul['rating']}]（平均 {soul['average']:+.2f}）"
        )
        lines.append(f"  · {soul['explanation']}")
    
    # 三方四正每宫
    lines.append("  ◆ 三方四正各宫亮度评级：")
    for s in overall.get("sfsz_scores", []):
        if s["major_count"] > 0:
            lines.append(
                f"    · {s['palace_name']}（{s['branch']}）："
                f"{'/'.join(s['major_stars'])} → "
                f"[{s['rating']}]（{s['average']:+.2f}）"
            )
        else:
            lines.append(f"    · {s['palace_name']}（{s['branch']}）：空宫")
    
    # 关键主星断语
    star_notes = overall.get("star_notes", [])
    if star_notes:
        lines.append("  ◆ 关键主星·宫位断语：")
        for note in star_notes[:8]:  # 限制 8 条避免太长
            lines.append(f"    · {note}")
        if len(star_notes) > 8:
            lines.append(f"    · ……（还有 {len(star_notes)-8} 条断语未展示）")
    
    # 评级体系说明
    lines.append("")
    lines.append("  说明：")
    lines.append("    · 紫府武杀破 5 颗星不敏感，按基础分计算（最低+1）")
    lines.append("    · 机日月同梁巨贪相廉 9 颗星敏感，按真实亮度计算")
    lines.append("    · 命宫亮度权重为其他宫的 2 倍")
    lines.append("    · 评级仅为先天格局参考，最终命格需结合四化、煞星、格局综合论")
    
    return "\n".join(lines)
