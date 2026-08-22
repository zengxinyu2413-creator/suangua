"""
core/liuyao/hua_bian.py
=======================
六爻·动爻化变全谱（逐爻成文断）——把"动爻变出"之一切关系熔于一炉：

  1. 化五行关系：回头生 / 回头克 / 化比和 / 化泄气 / 化克出
  2. 进退神    ：化进神（向前益壮）/ 化退神（退缩反复）
  3. 化十二长生：化长生·帝旺（得气）/ 化墓（事入墓须冲开）/ 化绝（气绝事败）/
                 化胎养·沐浴死病衰（各有纤旨）
  4. 化空亡    ：化神旬空——化而不实，待出空填实方应
  5. 反吟·伏吟 ：自化六冲为反吟（翻覆反复、得而复失）；
                 自化同支为伏吟（呻吟不前、旧事重提）
  6. 化六亲    ：化出之六亲对所占之事之吉凶（接 zhuang_gua 五神体系：
                 化出用神/元神为喜，化出忌神/仇神为忌）

  复用 relations.py 的十二长生与进退神、zhuang_gua 的五神用神体系，
  与排盘、装卦库完全同源；本module只做"动爻"层之整合成文，不另立基元。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.constants import DIZHI_WUXING, WUXING_SHENG, WUXING_KE
from core.liuyao.relations import get_changsheng_status, check_jin_tui_shen
from core.liuyao.zhuang_gua import _five_roles, _yong_for, _ROLE_VERDICT, TOPIC_LABEL
from core.liuyao.najia import LIU_QIN_MEANINGS

_POS_NAMES = ["初", "二", "三", "四", "五", "上"]

# 六冲
_LIU_CHONG: Dict[str, str] = {
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}

# 化十二长生的纤旨与吉凶倾向
_CHANGSHENG_NOTE: Dict[str, Dict[str, str]] = {
    "长生": {"q": "吉", "d": "化长生，化神反育本爻，得气而日渐生旺，事得长养、绵延有继。"},
    "帝旺": {"q": "吉", "d": "化帝旺，气势至盛，本爻化而极旺，事主鼎盛（然旺极防衰）。"},
    "临官": {"q": "吉", "d": "化临官（禄），化而得位，事顺职遂、渐入佳境。"},
    "冠带": {"q": "小吉", "d": "化冠带，渐成之象，事方兴而未盛，宜进。"},
    "沐浴": {"q": "平", "d": "化沐浴（败地），主反复未定、或有桃花暧昧、淘洗之扰。"},
    "养": {"q": "小吉", "d": "化养，蓄养待时，事须培育、未可遽求。"},
    "胎": {"q": "平", "d": "化胎，事在萌芽孕育，朦胧未成，须待时日。"},
    "衰": {"q": "平", "d": "化衰，气始转退，事过盛而趋平，宜守不宜进。"},
    "病": {"q": "凶", "d": "化病，化神使本爻染病，事多滞碍、力不从心。"},
    "死": {"q": "凶", "d": "化死，化神使本爻入死地，事象僵绝、生机已微。"},
    "墓": {"q": "凶", "d": "化墓，本爻动化入墓——事被收藏闭塞、暗昧难明，须待冲开墓库之日方应。"},
    "绝": {"q": "大凶", "d": "化绝，化神使本爻气绝于此，事到尽头、根断难续，最为不吉。"},
}


def _wx_relation_note(orig_wx: str, changed_wx: str) -> Dict[str, str]:
    """化神 vs 本爻 五行关系。"""
    if not orig_wx or not changed_wx:
        return {"rel": "", "q": "", "d": ""}
    if WUXING_SHENG.get(changed_wx) == orig_wx:
        return {"rel": "回头生", "q": "吉",
                "d": f"化神{changed_wx}反生本爻{orig_wx}——回头生，本爻得力大增；"
                     f"用神逢之事必成、忌神逢之凶愈坚。"}
    if WUXING_KE.get(changed_wx) == orig_wx:
        return {"rel": "回头克", "q": "凶",
                "d": f"化神{changed_wx}反克本爻{orig_wx}——回头克，本爻被反伤；"
                     f"用神逢之事必败、忌神逢之反受制（化解）。"}
    if changed_wx == orig_wx:
        return {"rel": "化比和", "q": "中",
                "d": "化神与本爻同气——化比和，扶持有力；逢伏吟则呻吟反复。"}
    if WUXING_SHENG.get(orig_wx) == changed_wx:
        return {"rel": "化泄气", "q": "凶",
                "d": f"本爻{orig_wx}生化神{changed_wx}——化泄气，本爻能量外泄而渐弱。"}
    if WUXING_KE.get(orig_wx) == changed_wx:
        return {"rel": "化克出", "q": "中",
                "d": f"本爻{orig_wx}克化神{changed_wx}——化克出，用神化克他为喜（去病），忌神化克他为凶。"}
    return {"rel": "", "q": "", "d": ""}


def analyze_one_hua(orig_branch: str, changed_branch: str,
                    orig_qin: str = "", changed_qin: str = "",
                    kong_wang: Optional[List[str]] = None,
                    topic: str = "", gender: str = "male") -> Dict[str, Any]:
    """单一动爻之化变全谱断。"""
    kong_wang = kong_wang or []
    orig_wx = DIZHI_WUXING.get(orig_branch, "")
    changed_wx = DIZHI_WUXING.get(changed_branch, "")
    if not orig_wx or not changed_wx:
        return {"success": False, "error": "地支无效"}

    facets: List[Dict[str, str]] = []

    # 1. 五行关系
    wxr = _wx_relation_note(orig_wx, changed_wx)
    if wxr["rel"]:
        facets.append({"type": wxr["rel"], "quality": wxr["q"], "desc": wxr["d"]})

    # 2. 进退神
    jt = check_jin_tui_shen(orig_branch, changed_branch)
    if jt.get("type"):
        facets.append({"type": f"化{jt['type']}", "quality": "吉" if jt["type"] == "进神" else "凶",
                       "desc": jt.get("interpretation", "")})

    # 3. 反吟 / 伏吟（自化）
    if changed_branch == orig_branch:
        facets.append({"type": "伏吟", "quality": "凶",
                       "desc": "动化同支为伏吟——主呻吟不前、旧事重提、迁延反复、痛苦呻吟。"})
    elif _LIU_CHONG.get(orig_branch) == changed_branch:
        facets.append({"type": "反吟", "quality": "凶",
                       "desc": "动化六冲为反吟——主翻覆反复、事得而复失、去而又来、悔吝不安。"})

    # 4. 化十二长生（本爻五行 在 化神地支 之长生态）
    cs = get_changsheng_status(orig_wx, changed_branch)
    cs_status = cs.get("status", "")
    if cs_status in _CHANGSHENG_NOTE:
        note = _CHANGSHENG_NOTE[cs_status]
        facets.append({"type": f"化{cs_status}", "quality": note["q"], "desc": note["d"]})

    # 5. 化空亡
    if changed_branch in kong_wang:
        facets.append({"type": "化空", "quality": "凶",
                       "desc": "化神旬空——化而不实，所化之吉凶皆虚悬，待化神出空、填实之日方见应验。"})

    # 6. 化六亲应事
    qin_facet = None
    if changed_qin:
        qm = LIU_QIN_MEANINGS.get(changed_qin, {})
        base = f"动化{changed_qin}（{qm.get('meaning','')}）"
        role_txt = ""
        yong = _yong_for(topic, gender) if topic else None
        if yong:
            roles = _five_roles(yong)
            role = roles.get(changed_qin)
            if role:
                rv = _ROLE_VERDICT[role]
                role_txt = (f"——于{TOPIC_LABEL.get(topic, topic)}，化出之{changed_qin}为{role}"
                            f"（{rv['q']}），{rv['d']}")
        qin_facet = {"type": f"化{changed_qin}", "changed_liu_qin": changed_qin,
                     "quality": "—", "desc": base + (role_txt or "。")}
        facets.append(qin_facet)

    # ── 总倾向（吉凶计分）──
    qmap = {"大吉": 3, "吉": 2, "小吉": 1, "中": 0, "平": 0, "凶": -2, "大凶": -3, "—": 0, "": 0}
    score = sum(qmap.get(f.get("quality", ""), 0) for f in facets)
    if score >= 3:
        tendency = "化变大吉"
    elif score >= 1:
        tendency = "化变偏吉"
    elif score <= -3:
        tendency = "化变大凶"
    elif score <= -1:
        tendency = "化变偏凶"
    else:
        tendency = "化变吉凶参半"

    qin_part = f"（{orig_qin}化{changed_qin}）" if (orig_qin and changed_qin) else ""
    full_text = (
        f"{orig_branch}{orig_wx}动化{changed_branch}{changed_wx}{qin_part}："
        + "　".join(f["desc"] for f in facets)
        + f"　【总断】{tendency}。"
    )

    return {
        "success": True,
        "orig_branch": orig_branch, "orig_wuxing": orig_wx, "orig_liu_qin": orig_qin,
        "changed_branch": changed_branch, "changed_wuxing": changed_wx,
        "changed_liu_qin": changed_qin,
        "facets": facets,
        "tendency": tendency,
        "score": score,
        "full_text": full_text,
    }


def analyze_hua_bian(yaos: List[Dict[str, Any]],
                     kong_wang: Optional[List[str]] = None,
                     topic: str = "", gender: str = "male") -> Dict[str, Any]:
    """
    全卦动爻化变断：逐一分析每个动爻之化变全谱。
    yaos 须为 najia 注解后之爻（含 branch / changed_branch / liu_qin / changed_liu_qin / is_changing）。
    """
    kong_wang = kong_wang or []
    moving: List[Dict[str, Any]] = []
    for y in yaos:
        if not y.get("is_changing"):
            continue
        ob = y.get("branch", "")
        cb = y.get("changed_branch", "")
        if not ob or not cb:
            continue
        one = analyze_one_hua(
            ob, cb,
            orig_qin=y.get("liu_qin", ""),
            changed_qin=y.get("changed_liu_qin", ""),
            kong_wang=kong_wang, topic=topic, gender=gender,
        )
        if one.get("success"):
            pos = y.get("position", 0)
            one["position"] = pos
            one["name"] = _POS_NAMES[pos - 1] if 1 <= pos <= 6 else y.get("line", "")
            moving.append(one)

    if not moving:
        return {"success": True, "count": 0, "moving_lines": [],
                "summary": "六爻安静无动，不论化变，以本卦静断。"}

    ji = [m for m in moving if m["score"] > 0]
    xiong = [m for m in moving if m["score"] < 0]
    summary = (
        f"共 {len(moving)} 爻发动。"
        + (f"化吉者 {len(ji)} 爻；" if ji else "")
        + (f"化凶者 {len(xiong)} 爻；" if xiong else "")
        + "动爻化变以回头生·化进神·化长生为喜，回头克·化退神·化墓绝·化空·反伏吟为忌；"
        + "用神化喜则事成，忌神化喜反坚其凶。"
    )
    return {
        "success": True,
        "count": len(moving),
        "moving_lines": moving,
        "summary": summary,
    }
