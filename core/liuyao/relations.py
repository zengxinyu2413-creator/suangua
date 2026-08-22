"""
core/liuyao/relations.py
========================
L-1: 六爻关系深度分析引擎。

补足现有 interpreter.py 缺失的核心维度：
  1. 原神/忌神/仇神自动判定（基于用神五行）
  2. 十二长生状态（地支在月令/日辰的旺衰）
  3. 进神退神细化
  4. 用神对原神/忌神的关系分析
  5. 卦变深度（爻变后的实质影响）

这些是《增删卜易》《卜筮正宗》《野鹤老人占卜全书》核心断卦法的代码化。
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────
# 五行生克
# ─────────────────────────────────────────────────────────────

WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE    = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
WUXING_BEISHENG = {v: k for k, v in WUXING_SHENG.items()}  # 谁生我
WUXING_BEIKE    = {v: k for k, v in WUXING_KE.items()}     # 谁克我

# 地支五行
DIZHI_WUXING = {
    "子": "水", "亥": "水",
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 地支顺序
DIZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"


# ─────────────────────────────────────────────────────────────
# 十二长生表 — 五行长生在哪个地支
# ─────────────────────────────────────────────────────────────
# 金长生在巳，木长生在亥，水长生在申，火长生在寅，土长生在申
WX_CHANGSHENG_START = {
    "金": "巳",
    "木": "亥",
    "水": "申",
    "火": "寅",
    "土": "申",  # 土同水
}

# 十二长生顺序（顺行）
CHANGSHENG_12 = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]


def get_changsheng_status(line_wx: str, target_zhi: str) -> Dict[str, Any]:
    """
    获取爻五行在某地支（日辰或月令）的十二长生状态。
    
    Args:
        line_wx: 爻的五行
        target_zhi: 地支（如日辰、月令）
    """
    start_zhi = WX_CHANGSHENG_START.get(line_wx, "")
    if not start_zhi or not target_zhi:
        return {"status": "", "force": 0}
    
    start_idx = DIZHI_ORDER.index(start_zhi)
    target_idx = DIZHI_ORDER.index(target_zhi)
    offset = (target_idx - start_idx) % 12
    status = CHANGSHENG_12[offset]
    
    # 力量评分（用于综合判断）
    force_map = {
        "长生":  3, "沐浴": -1, "冠带":  2, "临官":  4, "帝旺":  5,
        "衰":   -1, "病":  -2, "死":  -4, "墓":  -3, "绝":  -5,
        "胎":    1, "养":   2,
    }
    return {
        "status": status,
        "force":  force_map.get(status, 0),
        "start":  start_zhi,
        "offset": offset,
    }


# ─────────────────────────────────────────────────────────────
# 1. 原神/忌神/仇神自动判定
# ─────────────────────────────────────────────────────────────

def identify_yuanshen_jishen_choushen(
    yong_shen_wx: str
) -> Dict[str, str]:
    """
    给定用神五行，推出原神/忌神/仇神的五行。
    
    - 原神：生用神的五行（水生木，则水为木的原神）
    - 忌神：克用神的五行（金克木，则金为木的忌神）
    - 仇神：生忌神的五行（土生金，则土为木的仇神）
    - 食神：用神所生（耗用神，不算坏）
    """
    if not yong_shen_wx:
        return {}
    return {
        "用神_wx":  yong_shen_wx,
        "原神_wx":  WUXING_BEISHENG.get(yong_shen_wx, ""),
        "忌神_wx":  WUXING_BEIKE.get(yong_shen_wx, ""),
        "仇神_wx":  WUXING_BEISHENG.get(WUXING_BEIKE.get(yong_shen_wx, ""), ""),
        "食神_wx":  WUXING_SHENG.get(yong_shen_wx, ""),
    }


def find_lines_by_wuxing(yaos: List[Dict], wx: str) -> List[Dict]:
    """从 6 爻中找出指定五行的所有爻"""
    if not wx:
        return []
    out = []
    for i, y in enumerate(yaos):
        line_branch = y.get("branch", "")
        line_wx = DIZHI_WUXING.get(line_branch, "")
        if line_wx == wx:
            out.append({**y, "position": i + 1})
    return out


# ─────────────────────────────────────────────────────────────
# 2. 进神/退神（爻动后变化方向）
# ─────────────────────────────────────────────────────────────

# 进神/退神（《增删卜易·进神退神章》经典定义）
# 经典规则：同五行内地支顺序前进为进神（如寅→卯、巳→午），后退为退神
# 注：进退神主要看地支变化方向，不必涉及天干五合
DIZHI_PROGRESS_GROUPS = [
    ("寅", "卯"),  # 木进神
    ("巳", "午"),  # 火进神
    ("申", "酉"),  # 金进神
    ("亥", "子"),  # 水进神
    ("丑", "辰"),  # 土进神
    ("未", "戌"),  # 土进神
]


def check_jin_tui_shen(orig_zhi: str, changed_zhi: str) -> Dict[str, Any]:
    """
    判断爻动后是进神还是退神。
    
    Returns:
        {
            "type": "进神" | "退神" | "",
            "interpretation": str,
        }
    """
    if not orig_zhi or not changed_zhi or orig_zhi == changed_zhi:
        return {"type": "", "interpretation": ""}
    
    for low, high in DIZHI_PROGRESS_GROUPS:
        if orig_zhi == low and changed_zhi == high:
            return {
                "type": "进神",
                "interpretation": (
                    f"{orig_zhi}动化{changed_zhi}（进神）— 主事物向前发展、力量增强，"
                    "用神进神则吉运推进，忌神进神则灾难逼近"
                ),
            }
        if orig_zhi == high and changed_zhi == low:
            return {
                "type": "退神",
                "interpretation": (
                    f"{orig_zhi}动化{changed_zhi}（退神）— 主事物后退消减，"
                    "用神退神则吉运消退，忌神退神则灾患减轻"
                ),
            }
    return {"type": "", "interpretation": ""}


# ─────────────────────────────────────────────────────────────
# 3. 卦变深度（变卦六亲、回头生克等）
# ─────────────────────────────────────────────────────────────

def analyze_changed_line_relation(
    orig_yao: Dict, changed_yao: Dict
) -> Dict[str, Any]:
    """
    分析爻动化出新爻后的关系（回头生 / 回头克 / 化空 / 化破 等）。
    """
    if not orig_yao or not changed_yao:
        return {}
    
    orig_wx = DIZHI_WUXING.get(orig_yao.get("branch", ""), "")
    changed_wx = DIZHI_WUXING.get(changed_yao.get("branch", ""), "")
    
    if not orig_wx or not changed_wx:
        return {}
    
    result: Dict[str, Any] = {
        "orig_branch":    orig_yao.get("branch", ""),
        "changed_branch": changed_yao.get("branch", ""),
        "orig_wx":        orig_wx,
        "changed_wx":     changed_wx,
        "relation":       "",
        "interpretation": "",
    }
    
    if WUXING_SHENG.get(changed_wx) == orig_wx:
        result["relation"] = "回头生"
        result["interpretation"] = (
            f"{orig_yao.get('branch','')}动化{changed_yao.get('branch','')}"
            f"（{changed_wx}生{orig_wx}）= 回头生 — 主原爻得力，事物增强"
        )
    elif WUXING_KE.get(changed_wx) == orig_wx:
        result["relation"] = "回头克"
        result["interpretation"] = (
            f"{orig_yao.get('branch','')}动化{changed_yao.get('branch','')}"
            f"（{changed_wx}克{orig_wx}）= 回头克 — 主原爻被反伤，凶象"
        )
    elif changed_wx == orig_wx:
        result["relation"] = "化同（伏吟、扶持）"
        result["interpretation"] = (
            f"{orig_yao.get('branch','')}动化{changed_yao.get('branch','')}"
            f"（同五行）— 用神化同主力量加倍，忌神化同主灾难重复"
        )
    elif WUXING_SHENG.get(orig_wx) == changed_wx:
        result["relation"] = "化泄"
        result["interpretation"] = (
            f"{orig_yao.get('branch','')}动化{changed_yao.get('branch','')}"
            f"（{orig_wx}生{changed_wx}）= 化泄 — 原爻能量流出"
        )
    elif WUXING_KE.get(orig_wx) == changed_wx:
        result["relation"] = "化克他"
        result["interpretation"] = (
            f"{orig_yao.get('branch','')}动化{changed_yao.get('branch','')}"
            f"（{orig_wx}克{changed_wx}）= 化克他 — 用神化克他喜，忌神化克他凶"
        )
    
    # 进退神
    jt = check_jin_tui_shen(orig_yao.get("branch", ""), changed_yao.get("branch", ""))
    if jt["type"]:
        result["jin_tui"] = jt
    
    return result


# ─────────────────────────────────────────────────────────────
# 4. 月日辰对爻的旺衰判断（含十二长生）
# ─────────────────────────────────────────────────────────────

def analyze_line_strength_detail(
    line: Dict, month_zhi: str, day_zhi: str
) -> Dict[str, Any]:
    """
    详细分析一爻在月令、日辰的旺衰（含十二长生）。
    """
    line_branch = line.get("branch", "")
    line_wx = DIZHI_WUXING.get(line_branch, "")
    
    result = {
        "branch":    line_branch,
        "wuxing":    line_wx,
        "month_chs": get_changsheng_status(line_wx, month_zhi),
        "day_chs":   get_changsheng_status(line_wx, day_zhi),
    }
    
    # 月破检查（爻被月令相冲）
    chong_map = {
        "子": "午", "午": "子", "丑": "未", "未": "丑",
        "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
        "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
    }
    is_yuepo = chong_map.get(line_branch, "") == month_zhi
    is_ripo  = chong_map.get(line_branch, "") == day_zhi
    
    result["is_yuepo"] = is_yuepo
    result["is_ripo"]  = is_ripo
    
    # 综合力量评分（月+日 + 长生状态）
    score = 0
    score += result["month_chs"]["force"] * 1.5  # 月令权重大
    score += result["day_chs"]["force"]
    if is_yuepo: score -= 3
    if is_ripo:  score -= 2
    
    result["combined_force"] = score
    result["overall"] = (
        "极旺" if score >= 6 else
        "旺相" if score >= 3 else
        "中和" if score >= -1 else
        "休囚" if score >= -4 else "无气"
    )
    
    return result


# ─────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────

def analyze_liuyao_deep_relations(
    yaos: List[Dict],
    changed_yaos: Optional[List[Dict]] = None,
    yong_shen_info: Optional[Dict] = None,
    month_zhi: str = "",
    day_zhi: str = "",
) -> Dict[str, Any]:
    """
    L-1 主入口：六爻关系深度分析。
    
    Args:
        yaos: 本卦 6 爻（含 najia 标注）
        changed_yaos: 变卦 6 爻
        yong_shen_info: {"liuqin": "妻财", "wuxing": "金", ...}
        month_zhi: 月令地支
        day_zhi:   日辰地支
    """
    result: Dict[str, Any] = {
        "yong_yuan_ji_chou": {},
        "key_lines":         {},
        "changing_relations": [],
        "line_details":      [],
        "summary":           [],
    }
    
    # 1. 用神/原神/忌神/仇神 五行判定
    yong_wx = ""
    if yong_shen_info:
        yong_wx = yong_shen_info.get("wuxing") or ""
        if not yong_wx:
            yong_liuqin = yong_shen_info.get("liuqin", "")
            # 从 yaos 中找到第一个该六亲爻，取其五行
            for y in yaos:
                if y.get("liu_qin") == yong_liuqin:
                    yong_wx = DIZHI_WUXING.get(y.get("branch", ""), "")
                    break
    
    if yong_wx:
        result["yong_yuan_ji_chou"] = identify_yuanshen_jishen_choushen(yong_wx)
        
        # 找出每类的具体爻
        result["key_lines"] = {
            "用神_lines": find_lines_by_wuxing(yaos, yong_wx),
            "原神_lines": find_lines_by_wuxing(yaos, result["yong_yuan_ji_chou"]["原神_wx"]),
            "忌神_lines": find_lines_by_wuxing(yaos, result["yong_yuan_ji_chou"]["忌神_wx"]),
            "仇神_lines": find_lines_by_wuxing(yaos, result["yong_yuan_ji_chou"]["仇神_wx"]),
        }
    
    # 2. 每爻在月日的力量评分
    if month_zhi or day_zhi:
        for y in yaos:
            detail = analyze_line_strength_detail(y, month_zhi, day_zhi)
            detail["liu_qin"] = y.get("liu_qin", "")
            result["line_details"].append(detail)
    
    # 3. 动爻 → 变爻关系
    if changed_yaos:
        for i, y in enumerate(yaos):
            if y.get("is_changing") and i < len(changed_yaos):
                rel = analyze_changed_line_relation(y, changed_yaos[i])
                if rel:
                    rel["position"] = i + 1
                    rel["liu_qin"] = y.get("liu_qin", "")
                    result["changing_relations"].append(rel)
    
    # 4. 生成总结
    summary: List[str] = []
    if result["yong_yuan_ji_chou"]:
        yyj = result["yong_yuan_ji_chou"]
        summary.append(
            f"用神{yyj['用神_wx']}、原神{yyj['原神_wx']}（生用神）、"
            f"忌神{yyj['忌神_wx']}（克用神）、仇神{yyj['仇神_wx']}（生忌神）"
        )
    
    if result["key_lines"]:
        kl = result["key_lines"]
        if kl["原神_lines"]:
            posnames = [f"第{l['position']}爻({l['liu_qin']}{l['branch']})" for l in kl["原神_lines"]]
            summary.append(f"原神出现于：{', '.join(posnames)}")
        if kl["忌神_lines"]:
            posnames = [f"第{l['position']}爻({l['liu_qin']}{l['branch']})" for l in kl["忌神_lines"]]
            summary.append(f"⚠ 忌神出现于：{', '.join(posnames)} — 需重点关注其状态")
    
    if result["changing_relations"]:
        for cr in result["changing_relations"]:
            if cr.get("relation") == "回头克":
                summary.append(f"⚠ 第{cr['position']}爻动化回头克：{cr['interpretation']}")
            elif cr.get("relation") == "回头生":
                summary.append(f"✦ 第{cr['position']}爻动化回头生：{cr['interpretation']}")
    
    result["summary"] = summary
    return result


# ─────────────────────────────────────────────────────────────
# Prompt 格式化
# ─────────────────────────────────────────────────────────────

def format_liuyao_relations_for_prompt(result: Dict[str, Any]) -> str:
    """给 LLM 用的中文段"""
    if not result:
        return ""
    
    lines = ["【六爻关系深度分析】（L-1 自动判定）"]
    
    yyj = result.get("yong_yuan_ji_chou", {})
    if yyj:
        lines.append(
            f"  ◆ 四神五行：用神={yyj['用神_wx']} / 原神={yyj['原神_wx']}（生用神）"
            f" / 忌神={yyj['忌神_wx']}（克用神） / 仇神={yyj['仇神_wx']}（生忌神）"
        )
    
    kl = result.get("key_lines", {})
    if kl:
        for label, key in [("用神", "用神_lines"), ("原神", "原神_lines"),
                           ("忌神", "忌神_lines"), ("仇神", "仇神_lines")]:
            ls = kl.get(key, [])
            if ls:
                ps = [f"第{l['position']}爻({l['liu_qin']}{l['branch']})" for l in ls]
                lines.append(f"  ◆ {label}爻位：{', '.join(ps)}")
    
    if result.get("changing_relations"):
        lines.append(f"  ◆ 动爻变化（共 {len(result['changing_relations'])} 处）：")
        for cr in result["changing_relations"]:
            lines.append(f"    · {cr['interpretation']}")
    
    if result.get("line_details"):
        lines.append("  ◆ 六爻力量评估（月令+日辰）：")
        for d in result["line_details"]:
            mc = d['month_chs']
            dc = d['day_chs']
            mark = ""
            if d.get("is_yuepo"): mark += "[月破]"
            if d.get("is_ripo"):  mark += "[日破]"
            lines.append(
                f"    · 第{result['line_details'].index(d)+1}爻 {d.get('liu_qin','')} "
                f"{d['branch']}({d['wuxing']}) "
                f"月{mc['status']}/日{dc['status']} "
                f"→ {d['overall']} {mark}"
            )
    
    if result.get("summary"):
        lines.append("  ◆ 关键提示：")
        for s in result["summary"]:
            lines.append(f"    · {s}")
    
    lines.append("")
    lines.append("  断卦要诀：")
    lines.append("    · 用神旺相又有原神生扶 = 大吉；用神死绝又被忌神克 = 大凶")
    lines.append("    · 忌神动化回头克 = 化解；用神动化回头生 = 大利")
    lines.append("    · 月破日破之爻须等出月或冲填之日方能起作用（应期）")
    
    return "\n".join(lines)
