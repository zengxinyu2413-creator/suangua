"""
core/liuyao/yingqi_calculator.py
================================
六爻应期精算（Backend precise 应期 engine）

依据《增删卜易·应期门》《卜筮正宗·应期总论》《黄金策》等古法，
根据用神所在爻的状态（动/静、旺/衰、空/破、入墓、进退、化生克）
推断应期所对应的地支，并将地支映射为占卦日之后的**具体公历日期**，
供前端「应期日历」精确卡片展示。

设计要点
--------
1. 古法判定产出「候选应期地支 + 古籍依据 + 优先级」。
2. 用 lunar_python 从占卦日起逐日推真太岁干支，将候选地支落到最近的
   未来公历日期（不是朴素 60 甲子循环猜测，避免与真历法偏差）。
3. 输出结构化数据，既给「最可能应期」结论，也给完整候选列表与日历命中。

核心古法口诀
------------
  静者待冲，动者待合。
  旺相速而休囚迟；急事应日时，常事应月，大事应年。
  空者待出空填实、冲空而起；入墓者待冲开墓库之日。
  化进神应于进神之支，化退神须待用神另得生扶。
  化回头生者，冲化神之日事成；化回头克者，冲化神之日见凶。
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple

from core.constants import (
    DIZHI, DIZHI_WUXING, WUXING_SHENG, WUXING_KE,
    LIUHE, LIUCHONG, SANHE_MAP,
)

# ─────────────────────────────────────────────────────────────
# 基础常量
# ─────────────────────────────────────────────────────────────

# 五行墓库（古法：木墓于未、火墓于戌、金墓于丑、水土墓于辰）
TOMB_OF_WUXING: Dict[str, str] = {
    "木": "未", "火": "戌", "金": "丑", "水": "辰", "土": "辰",
}

# 应期类型展示颜色（与前端图例统一）
TYPE_COLOR: Dict[str, str] = {
    "逢冲应期": "#3498db",
    "逢合应期": "#27ae60",
    "三合应期": "#9b59b6",
    "出空填实": "#e67e22",
    "冲空起爻": "#e67e22",
    "冲墓开库": "#c0392b",
    "值用本气": "#16a085",
    "化进神日": "#2980b9",
    "生扶之日": "#16a085",
    "冲化神日": "#8e44ad",
}

_STRONG = ("旺", "相")
_WEAK = ("休", "囚", "死")


# ─────────────────────────────────────────────────────────────
# 干支历法工具（基于 lunar_python，回退到纯 60 甲子循环）
# ─────────────────────────────────────────────────────────────

def _day_ganzhi(d: date) -> str:
    """返回某公历日的日干支，如 '己巳'。统一走历法底座。"""
    from datetime import datetime as _dtm
    from core.calendar.solar_terms import day_ganzhi_at
    return day_ganzhi_at(_dtm(d.year, d.month, d.day))


def _day_zhi(d: date) -> str:
    return _day_ganzhi(d)[-1]


def _month_ganzhi(d: date) -> str:
    from datetime import datetime as _dtm
    from core.calendar.solar_terms import month_ganzhi_at
    gz = month_ganzhi_at(_dtm(d.year, d.month, d.day))
    return gz if gz and not gz.startswith("?") else ""


def _roll_future_dates(
    start: date, target_branch: str, count: int = 2, max_days: int = 120
) -> List[Dict[str, Any]]:
    """
    自占卦日次日起，向后扫描 max_days 天，找出日支 == target_branch 的
    最近 count 个公历日。返回 [{date, ganzhi, day_zhi, days_ahead, scope}]。
    """
    if not target_branch:
        return []
    hits: List[Dict[str, Any]] = []
    for i in range(1, max_days + 1):
        d = start + timedelta(days=i)
        gz = _day_ganzhi(d)
        if gz[-1] == target_branch:
            hits.append({
                "date": d.isoformat(),
                "ganzhi": gz,
                "day_zhi": gz[-1],
                "days_ahead": i,
                "scope": "日",
            })
            if len(hits) >= count:
                break
    return hits


def _roll_future_months(
    start: date, target_branch: str, count: int = 1, max_months: int = 14
) -> List[Dict[str, Any]]:
    """逐月向后找月支 == target_branch 的最近 count 个月（用于「应月」迟应）。"""
    if not target_branch:
        return []
    hits: List[Dict[str, Any]] = []
    seen = set()
    d = start
    for _ in range(max_months * 31):
        d = d + timedelta(days=15)
        mgz = _month_ganzhi(d)
        if not mgz:
            break
        key = mgz
        if mgz[-1] == target_branch and key not in seen:
            seen.add(key)
            hits.append({
                "date": d.replace(day=1).isoformat(),
                "ganzhi": mgz,
                "day_zhi": mgz[-1],
                "days_ahead": (d - start).days,
                "scope": "月",
            })
            if len(hits) >= count:
                break
    return hits


# ─────────────────────────────────────────────────────────────
# 五行 / 地支关系小工具
# ─────────────────────────────────────────────────────────────

def _wx(branch: str) -> str:
    return DIZHI_WUXING.get(branch, "")


def _sheng_me(wx: str) -> str:
    """生我之五行（母）。"""
    for k, v in WUXING_SHENG.items():
        if v == wx:
            return k
    return ""


def _branches_of_wuxing(wx: str) -> List[str]:
    return [b for b, w in DIZHI_WUXING.items() if w == wx]


def _sanhe_partners(branch: str) -> List[str]:
    pair = SANHE_MAP.get(branch)
    if not pair:
        return []
    return [pair[0], pair[1]]


# ─────────────────────────────────────────────────────────────
# 用神状态判定
# ─────────────────────────────────────────────────────────────

def _find_yong_yao(yaos: List[Dict], yong_shen_name: str) -> Optional[Dict]:
    """按用神名（六亲名 / 世爻 / 应爻）定位用神爻。多现时取动爻优先。"""
    if not yong_shen_name:
        return None
    cands: List[Dict] = []
    if yong_shen_name == "世爻":
        cands = [y for y in yaos if y.get("is_world")]
    elif yong_shen_name == "应爻":
        cands = [y for y in yaos if y.get("is_application")]
    else:
        cands = [y for y in yaos if y.get("liu_qin") == yong_shen_name]
    if not cands:
        return None
    # 动爻优先；其次世/应；否则取第一个
    moving = [y for y in cands if y.get("is_changing")]
    if moving:
        return moving[0]
    return cands[0]


def _strength_label(yao: Dict) -> str:
    st = yao.get("strength", {})
    if isinstance(st, dict):
        return st.get("label", "")
    return str(st or "")


def _is_entombed(yong_branch: str, day_zhi: str, changed_branch: str) -> Tuple[bool, str]:
    """
    用神是否入墓。返回 (是否入墓, 墓库支)。
    入日墓：日支为用神五行之墓库；
    化入墓：动爻所化之支为用神五行墓库；
    用神自临墓库支亦视为伏吟入墓（自墓）。
    """
    wx = _wx(yong_branch)
    tomb = TOMB_OF_WUXING.get(wx, "")
    if not tomb:
        return False, ""
    if day_zhi == tomb:
        return True, tomb
    if changed_branch and changed_branch == tomb:
        return True, tomb
    if yong_branch == tomb:
        return True, tomb
    return False, ""


def _jin_tui(yong_branch: str, changed_branch: str) -> str:
    """化进神 / 化退神判定（同五行、序进为进，序退为退）。"""
    if not changed_branch or yong_branch == changed_branch:
        return ""
    if _wx(yong_branch) != _wx(changed_branch):
        return ""
    oi = DIZHI.index(yong_branch)
    ci = DIZHI.index(changed_branch)
    diff = (ci - oi) % 12
    if diff in (1, 2):
        return "进"
    if diff in (10, 11):
        return "退"
    return ""


def _hui_tou(yong_branch: str, changed_branch: str) -> str:
    """化回头生 / 化回头克。返回 '生' | '克' | ''。"""
    if not changed_branch or yong_branch == changed_branch:
        return ""
    yb_wx = _wx(yong_branch)
    cb_wx = _wx(changed_branch)
    if not yb_wx or not cb_wx:
        return ""
    if WUXING_SHENG.get(cb_wx) == yb_wx:
        return "生"
    if WUXING_KE.get(cb_wx) == yb_wx:
        return "克"
    return ""


# ─────────────────────────────────────────────────────────────
# 候选应期生成（古法规则引擎）
# ─────────────────────────────────────────────────────────────

def _make_candidate(branch: str, ctype: str, principle: str, classic: str,
                    priority: int) -> Dict[str, Any]:
    return {
        "branch": branch,
        "type": ctype,
        "principle": principle,
        "classic": classic,
        "priority": priority,
        "color": TYPE_COLOR.get(ctype, "#888"),
    }


def _generate_candidates(
    yong_yao: Dict, day_zhi: str, kong_wang: List[str],
) -> List[Dict[str, Any]]:
    """根据用神状态产出候选应期地支（含古籍依据、优先级）。"""
    yb = yong_yao.get("branch", "")
    if not yb:
        return []
    strength = _strength_label(yong_yao)
    is_kong = bool(yong_yao.get("kong_wang"))
    is_changing = bool(yong_yao.get("is_changing"))
    changed_branch = yong_yao.get("changed_branch", "") or ""

    chong = LIUCHONG.get(yb, "")
    he = LIUHE.get(yb, "")
    cands: List[Dict[str, Any]] = []

    # ── A. 用神旬空：出空填实 / 冲空起爻（最优先，空则事悬而未决）──
    if is_kong:
        # 出空填实：用神本支日（空支之日必在出旬之后，自然填实）
        cands.append(_make_candidate(
            yb, "出空填实",
            f"用神{yong_yao.get('liu_qin','')}爻临{yb}旬空，待出旬逢{yb}日填实而应",
            "《卜筮正宗·应期》", 1,
        ))
        if chong:
            cands.append(_make_candidate(
                chong, "冲空起爻",
                f"旬空逢{chong}日冲空，空而被冲则起，亦为应期",
                "《增删卜易·旬空章》", 2,
            ))
        # 旺空可填实速、衰空真空迟，仅调整优先级文字，不改候选

    # ── B. 用神入墓：冲开墓库 / 值用神之日 ──
    entombed, tomb = _is_entombed(yb, day_zhi, changed_branch)
    if entombed and tomb:
        tomb_chong = LIUCHONG.get(tomb, "")
        if tomb_chong:
            cands.append(_make_candidate(
                tomb_chong, "冲墓开库",
                f"用神{yb}入{tomb}墓，待{tomb_chong}日冲开墓库，用神出墓而应",
                "《增删卜易·墓库章》", 1,
            ))
        cands.append(_make_candidate(
            yb, "值用本气",
            f"用神入墓，亦可于{yb}日值用神本气，引而出之",
            "《黄金策》", 3,
        ))

    # ── C. 用神发动：动者待合 + 进退/回头生克 ──
    if is_changing and not is_kong:
        jt = _jin_tui(yb, changed_branch)
        ht = _hui_tou(yb, changed_branch)

        if jt == "进":
            cands.append(_make_candidate(
                changed_branch, "化进神日",
                f"用神{yb}化进神→{changed_branch}，动而益壮，应于{changed_branch}进神之日",
                "《增删卜易·进退神》", 1,
            ))
        elif jt == "退":
            mother = _sheng_me(_wx(yb))
            for mb in _branches_of_wuxing(mother):
                cands.append(_make_candidate(
                    mb, "生扶之日",
                    f"用神{yb}化退神，气势渐退，须待{mb}日（生扶用神）方应",
                    "《增删卜易·进退神》", 3,
                ))
                break

        if ht == "生":
            cb_chong = LIUCHONG.get(changed_branch, "")
            if cb_chong:
                cands.append(_make_candidate(
                    cb_chong, "冲化神日",
                    f"用神{yb}化回头生（{changed_branch}生本爻），事必成，应于{cb_chong}日冲化神",
                    "《卜筮正宗·化爻》", 1,
                ))
        elif ht == "克":
            cb_chong = LIUCHONG.get(changed_branch, "")
            if cb_chong:
                cands.append(_make_candidate(
                    cb_chong, "冲化神日",
                    f"用神{yb}化回头克（{changed_branch}克本爻），凶，应于{cb_chong}日冲化神见凶",
                    "《卜筮正宗·化爻》", 2,
                ))

        # 一般动爻：逢合之日应（动者待合）+ 值日
        if he:
            cands.append(_make_candidate(
                he, "逢合应期",
                f"用神发动，动者待合，逢{he}日合住用神之日应验",
                "《增删卜易·应期门》", 2,
            ))
        cands.append(_make_candidate(
            yb, "值用本气",
            f"用神动而逢值，{yb}日临用神本气亦可应",
            "《黄金策》", 4,
        ))

    # ── D. 用神安静（不动、不空、不墓）：静者待冲 ──
    if (not is_changing) and (not is_kong) and (not entombed):
        if chong:
            if strength in _STRONG:
                cands.append(_make_candidate(
                    chong, "逢冲应期",
                    f"用神{yb}{strength or '有气'}而静，静者待冲，逢{chong}日冲动（暗动）即应",
                    "《增删卜易·应期门》", 1,
                ))
            else:
                # 衰静：先生扶、后逢冲
                mother = _sheng_me(_wx(yb))
                for mb in _branches_of_wuxing(mother):
                    cands.append(_make_candidate(
                        mb, "生扶之日",
                        f"用神{yb}{strength or '无气'}而静，衰逢冲则散，须先于{mb}日得生扶",
                        "《增删卜易·应期门》", 2,
                    ))
                    break
                cands.append(_make_candidate(
                    chong, "逢冲应期",
                    f"用神得生扶后，再逢{chong}日冲动方应",
                    "《增删卜易·应期门》", 3,
                ))
        # 旺相静爻亦可值本气日应
        if strength in _STRONG:
            cands.append(_make_candidate(
                yb, "值用本气",
                f"用神{strength}相，逢{yb}日值临本气，旬日内可速应",
                "《卜筮正宗》", 3,
            ))

    # ── E. 半三合 → 待补全三合之支 ──
    for pb in _sanhe_partners(yb):
        cands.append(_make_candidate(
            pb, "三合应期",
            f"用神{yb}逢{pb}日，三合成局拱扶用神，亦主应期",
            "《增删卜易·三合局》", 4,
        ))

    # 去重（同 branch+type 合并），保留最高优先级
    dedup: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for c in cands:
        key = (c["branch"], c["type"])
        if key not in dedup or c["priority"] < dedup[key]["priority"]:
            dedup[key] = c
    return list(dedup.values())


# ─────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────

def calculate_yingqi(
    yaos: List[Dict[str, Any]],
    yong_shen_name: str,
    day_zhi: str = "",
    month_zhi: str = "",
    kong_wang: Optional[List[str]] = None,
    divine_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    应期精算主入口。

    参数
    ----
    yaos            : najia 标注后的六爻列表（含 branch / liu_qin / strength /
                      kong_wang / is_changing / changed_branch / is_world ...）
    yong_shen_name  : 用神名（六亲名 / 世爻 / 应爻）
    day_zhi         : 占卦日日支
    month_zhi       : 占卦月令地支
    kong_wang       : 旬空地支列表
    divine_date     : 占卦时刻（缺省为 now）

    返回
    ----
    {
      "available": bool,
      "yong_shen": {...},
      "state_summary": "...",
      "candidates": [ {branch,type,principle,classic,priority,color,dates:[...]} ],
      "calendar_hits": [ {date,ganzhi,day_zhi,days_ahead,scope,type,color,...} ],
      "primary": {...},          # 最可能应期（综合优先级 + 最近）
      "verdict": "...",
    }
    """
    kong_wang = kong_wang or []
    if divine_date is None:
        divine_date = datetime.now()
    base_date = divine_date.date() if isinstance(divine_date, datetime) else divine_date

    yong_yao = _find_yong_yao(yaos, yong_shen_name)
    if not yong_yao or not yong_yao.get("branch"):
        return {
            "available": False,
            "reason": "未能定位用神爻或用神无纳甲地支，无法推算应期",
            "yong_shen_name": yong_shen_name,
        }

    yb = yong_yao.get("branch", "")
    strength = _strength_label(yong_yao)
    is_kong = bool(yong_yao.get("kong_wang"))
    is_changing = bool(yong_yao.get("is_changing"))
    entombed, tomb = _is_entombed(yb, day_zhi, yong_yao.get("changed_branch", "") or "")

    # ── 生成候选并落到具体日期 ──
    candidates = _generate_candidates(yong_yao, day_zhi, kong_wang)
    calendar_hits: List[Dict[str, Any]] = []
    for c in candidates:
        dates = _roll_future_dates(base_date, c["branch"], count=2, max_days=120)
        # 衰弱/大事亦给「应月」参考（仅生扶/逢冲类，取一个月）
        if strength in _WEAK and c["type"] in ("生扶之日", "逢冲应期"):
            dates = dates + _roll_future_months(base_date, c["branch"], count=1)
        c["dates"] = dates
        for d in dates:
            calendar_hits.append({
                **d,
                "branch": c["branch"],
                "type": c["type"],
                "color": c["color"],
                "principle": c["principle"],
                "classic": c["classic"],
                "priority": c["priority"],
            })

    # ── 排序：优先级升序，其次最近 ──
    candidates.sort(key=lambda c: (c["priority"],
                                   c["dates"][0]["days_ahead"] if c.get("dates") else 9999))
    calendar_hits.sort(key=lambda h: (h["priority"], h["days_ahead"]))

    # ── 状态摘要 ──
    flags = []
    if is_changing:
        flags.append("发动")
    else:
        flags.append("安静")
    flags.append(strength or "—")
    if is_kong:
        flags.append("旬空")
    if entombed:
        flags.append(f"入{tomb}墓")
    state_summary = (
        f"用神{yong_yao.get('liu_qin','')}爻 {yb}"
        f"（{_wx(yb)}），{ '、'.join(flags) }"
    )

    # ── 最可能应期（取排序后第一个有落点的候选）──
    primary = None
    for c in candidates:
        if c.get("dates"):
            d0 = c["dates"][0]
            primary = {
                "date": d0["date"],
                "ganzhi": d0["ganzhi"],
                "days_ahead": d0["days_ahead"],
                "scope": d0["scope"],
                "branch": c["branch"],
                "type": c["type"],
                "principle": c["principle"],
                "classic": c["classic"],
                "color": c["color"],
            }
            break

    # ── 结论 ──
    if primary:
        verdict = (
            f"最可能应期：{primary['date']}（{primary['ganzhi']}{primary['scope']}，"
            f"第{primary['days_ahead']}日），{primary['type']}——{primary['principle']}"
        )
    else:
        verdict = "未来 120 日内无明确应期落点，事态恐拖延或须以应月、应年论之。"

    # 缓急判断（提示语）
    if strength in _STRONG and not is_kong:
        tempo = "用神旺相，应期较速，多在旬日（10日）内见验。"
    elif is_kong:
        tempo = "用神旬空，须待出空填实方真，应期偏迟。"
    elif strength in _WEAK:
        tempo = "用神休囚，应期偏迟，须待生扶得力之月日。"
    else:
        tempo = "应期缓急以用神旺衰为准，急事应日时、常事应月、大事应年。"

    return {
        "available": True,
        "yong_shen_name": yong_shen_name,
        "yong_shen": {
            "liu_qin": yong_yao.get("liu_qin", ""),
            "branch": yb,
            "element": _wx(yb),
            "strength": strength,
            "is_kong": is_kong,
            "is_changing": is_changing,
            "entombed": entombed,
            "tomb": tomb,
            "position": yong_yao.get("position", 0),
        },
        "state_summary": state_summary,
        "tempo": tempo,
        "candidates": candidates,
        "calendar_hits": calendar_hits,
        "primary": primary,
        "verdict": verdict,
        "divine_date": base_date.isoformat(),
    }
