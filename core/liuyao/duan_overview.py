"""
core/liuyao/duan_overview.py
============================
六爻·断卦总览（综合断卦 × 应期联动）——「何事 · 吉凶 · 何时应」一体之断。

综合断卦（zonghe_duan）定吉凶之「然否」，应期（yingqi）定应验之「何时」，
二者本各自为政。本模块以吉凶之极性，重述应期落点之义：
  · 用神入墓，吉则「冲墓开库而事成」，凶则「墓开而祸发」；
  · 用神逢空，吉则「填实出空而事真」，凶则「出空之时凶显」；
  · 用神受引动之日，吉则吉事应此、凶则凶事应此。
合为一段总览，使占断有结论、有时点、有所循。

复用 zonghe_duan 之结论链与 yingqi 之 primary 落点，不另算用神。
"""
from __future__ import annotations
from typing import Dict, Any, Optional


def _polarity(conclusion: str) -> str:
    if "中" in conclusion:        # 「中（吉凶参半）」含吉凶二字，须先判
        return "中"
    if "吉" in conclusion:
        return "吉"
    if "凶" in conclusion:
        return "凶"
    return "中"


def _reframe_yingqi(primary: Optional[Dict[str, Any]], pol: str) -> str:
    """以吉凶极性重述应期落点。"""
    if not primary:
        return "未来百日内无明确应期落点，事态恐拖延，须以应月、应年论之。"
    date = primary.get("date", "")
    gz = primary.get("ganzhi", "")
    scope = primary.get("scope", "日")
    days = primary.get("days_ahead", "")
    typ = primary.get("type", "")
    when = f"{date}（{gz}{scope}，第{days}日）"

    # 据应期类型 + 吉凶极性 重述
    if "墓" in typ:
        if pol == "吉":
            return f"用神入墓、气闭未发，待{when}冲开墓库，用神出墓得用，吉事应此而成。"
        if pol == "凶":
            return f"用神入墓、气结难解，至{when}冲墓，墓开而患发，凶事应此而显。"
        return f"用神入墓，待{when}冲墓开库，事机始动。"
    if "空" in typ or "填实" in typ:
        if pol == "吉":
            return f"用神逢空、虚而未实，待{when}填实出空，事乃落实而成。"
        if pol == "凶":
            return f"用神逢空、凶暂未临，至{when}出空填实，凶事方真。"
        return f"用神逢空，待{when}填实出空，虚实方定。"
    if "合" in typ:
        if pol == "吉":
            return f"用神发动待合，至{when}合住用神，事机收束而成，吉应此时。"
        return f"用神发动待合，至{when}合而绊住，事于此时见分晓。"
    # 逢值/逢冲/回头 等：通用引动
    if pol == "吉":
        return f"至{when}用神得力引动（{typ}），吉事应此，可把握行事。"
    if pol == "凶":
        return f"至{when}用神受引动（{typ}），凶事应此，宜预为之备、避其锋。"
    return f"应期落于{when}（{typ}），吉凶于此时见分晓。"


def build_duan_overview(zonghe: Dict[str, Any], yingqi: Dict[str, Any],
                        topic: str = "", question: str = "") -> Dict[str, Any]:
    """合成「何事·吉凶·何时应」总览。"""
    if not zonghe or not zonghe.get("available"):
        return {"available": False}

    # 用神伏藏：无吉凶结论，亦无应期
    if zonghe.get("fu_shen"):
        return {
            "available": True,
            "shi": topic or "所占之事",
            "polarity": "待", "conclusion": "待时",
            "yingqi_text": "用神伏而不现，须待伏神得提拔出伏之时方有应。",
            "overview": f"【{topic or '所占'}】用神不上卦、伏而未现——其事隐伏未发，"
                        f"目下未可遽断，待用神出伏引拔之时再观消息。",
        }

    conclusion = zonghe.get("conclusion", "中")
    conf = zonghe.get("confidence", "中")
    pol = _polarity(conclusion)
    yong_liuqin = zonghe.get("yong_liuqin", "") or zonghe.get("yong_shen", "")
    reasons = zonghe.get("reasoning", [])
    key_reason = reasons[0] if reasons else ""

    primary = (yingqi or {}).get("primary")
    yingqi_text = _reframe_yingqi(primary, pol)
    tempo = (yingqi or {}).get("tempo", "")

    # ── 总览成段 ──
    shi = topic or "所占之事"
    overview = (
        f"【{shi}】以{yong_liuqin or '用神'}为用神。{key_reason}"
        f"综断为【{conclusion}】（信心{conf}）。{yingqi_text}"
        + (f"（{tempo}）" if tempo else "")
    )

    return {
        "available": True,
        "shi": shi,
        "yong_liuqin": yong_liuqin,
        "polarity": pol,
        "conclusion": conclusion,
        "confidence": conf,
        "key_reason": key_reason,
        "yingqi_text": yingqi_text,
        "primary_date": (primary or {}).get("date", ""),
        "primary_ganzhi": (primary or {}).get("ganzhi", ""),
        "overview": overview,
    }
