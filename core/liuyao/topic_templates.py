"""
core/liuyao/topic_templates.py
==============================
六爻·十四类占事专用断语模板。

综合断卦（zonghe_duan）出通用吉凶，本模块据占事之别，套各类专用断语——
求财看财爻与子孙（原神）、求官看官鬼与父母（印）、婚姻看世应与间爻媒、
求医看子孙（医药）与官鬼（病符）、官司看世应强弱与父母（理状）……
使「吉」「凶」之断落到该事之具体关窍，并随卦中关键六亲之动静空旺细化。

复用 zonghe_duan 之 conclusion / roles / 用神状态，与断卦同源，不另取用神。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional


def _role(zonghe: Dict[str, Any], name: str) -> Dict[str, Any]:
    return (zonghe.get("roles", {}) or {}).get(name, {}) or {}


def _find_qin(yaos: List[Dict], qin: str) -> Optional[Dict]:
    cand = [y for y in yaos if y.get("liu_qin") == qin]
    if not cand:
        return None
    return next((y for y in cand if y.get("is_changing")), None) or cand[0]


def _state_tag(yao: Optional[Dict]) -> str:
    if not yao:
        return "不上卦"
    tags = []
    if yao.get("is_changing"):
        tags.append("发动")
    if yao.get("kong_wang"):
        tags.append("空亡")
    st = yao.get("strength", {})
    if isinstance(st, dict) and st.get("label"):
        tags.append(st["label"])
    return "·".join(tags) if tags else "静守"


# 各占事之专用断语模板
#   yong: 用神说明；ji/xiong/zhong: 按吉凶极性之主断；watch: 需察之六亲
_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "求财": {
        "yong": "妻财为用神、子孙为原神（财源）、兄弟为忌神（劫财）。",
        "ji": "财爻得地、子孙生扶，财源不竭，所求之财可得，宜把握求取。",
        "xiong": "财爻无力或兄弟劫夺，求财多阻、防破耗，宜守不宜贪进。",
        "zhong": "财气平平、得失参半，小求可遂、大谋须待时。",
        "watch": [("妻财", "财爻"), ("子孙", "财源"), ("兄弟", "劫财之忌")],
    },
    "求官仕途": {
        "yong": "官鬼为用神（官职功名）、父母为原神（文书印绶）、子孙为忌神（伤官克官）。",
        "ji": "官星旺相、父母生扶，功名有望、升迁可期，宜积极进取。",
        "xiong": "官星无力或子孙动克，仕途多阻、谋职费力，须待官旺之运。",
        "zhong": "官运中平，须文书（父母）得力、贵人扶持方成。",
        "watch": [("官鬼", "官星"), ("父母", "文书印绶"), ("子孙", "克官之忌")],
    },
    "考试功名": {
        "yong": "父母为用神（文书成绩）、官鬼为原神（功名）、妻财为忌神（财动克文书）。",
        "ji": "父母文书旺相、官鬼相生，考运佳、榜上有名，宜全力以赴。",
        "xiong": "父母受克或财动伤文书，考运不利、临场失常，宜稳扎根基勿轻敌。",
        "zhong": "成绩中游，须临场稳定、文书（父母）不受冲克方可中。",
        "watch": [("父母", "文书成绩"), ("官鬼", "功名之原神"), ("妻财", "克文书之忌")],
    },
    "婚姻感情": {
        "yong": "男占以妻财为用神（妻）、女占以官鬼为用神（夫），世为己、应为彼，间爻为媒。",
        "ji": "用神得地、世应相生相合，姻缘可成、两情和美，宜促成之。",
        "xiong": "用神受克或世应相冲相克，缘分多舛、好事难谐，强求反伤。",
        "zhong": "缘分半成、须媒人（间爻）得力、世应相和方易就。",
        "watch": [("妻财", "妻星"), ("官鬼", "夫星"), ("子孙", "子嗣/欢悦")],
    },
    "求医疾病": {
        "yong": "占病以官鬼为病符、子孙为医药（用神/原神）、父母为医院文书。世爻为病人。",
        "ji": "子孙（医药）旺相制官鬼（病符），病有良方、可愈，宜及时就医。",
        "xiong": "病符官鬼旺动而子孙受制，病势缠绵、医药无功，须慎防迁延。",
        "zhong": "病情反复，须医药（子孙）得力、病符（官鬼）受制方转安。",
        "watch": [("子孙", "医药"), ("官鬼", "病符"), ("父母", "医院文书")],
    },
    "出行远行": {
        "yong": "以世爻为出行人，父母为行装舟车、妻财为盘缠、子孙为顺利之神、官鬼为险阻。",
        "ji": "世爻得地、子孙旺相，出行平安顺遂、所图可得，宜启程。",
        "xiong": "世爻受克或官鬼动阻，途中多险阻、不利远行，宜缓行或改期。",
        "zhong": "行程平稳中带波折，宜择吉日、备而后行。",
        "watch": [("子孙", "顺利之神"), ("官鬼", "险阻"), ("妻财", "盘缠")],
    },
    "官司诉讼": {
        "yong": "世为我、应为对方，父母为状词理据，官鬼为官府/刑，子孙为解神（和解了讼）。",
        "ji": "世旺克应、子孙发动解讼，我方有理得胜、或得和解了结，宜据理而争。",
        "xiong": "应旺克世或官鬼动克世，我方理屈势弱、防败防刑，宜求和勿强争。",
        "zhong": "胜负未明、缠讼难了，须看子孙（解神）与父母（理状）之力。",
        "watch": [("子孙", "解神"), ("官鬼", "官刑"), ("父母", "状词理据")],
    },
    "求子嗣": {
        "yong": "子孙为用神（子嗣），妻财为原神（生子孙），父母为忌神（克子孙）。",
        "ji": "子孙旺相、妻财生扶，子嗣有望、宜把握求嗣之机。",
        "xiong": "子孙受克或父母动克，求子多阻、须调养待时。",
        "zhong": "子嗣之缘中平，须子孙不空不破、妻财得力方成。",
        "watch": [("子孙", "子嗣"), ("妻财", "生子之原神"), ("父母", "克子之忌")],
    },
    "找人行人": {
        "yong": "以应爻（或所寻者类神）为用神，看其旺衰动静与马星。",
        "ji": "用神旺动而向世、或临驿马，行人将归、可得音信，近期有望。",
        "xiong": "用神空破墓绝或背世而去，人难寻、归期渺茫，须待出空冲动之时。",
        "zhong": "归与不归未定，须看用神动静、逢冲逢合之期。",
        "watch": [("官鬼", "灾阻"), ("子孙", "平安")],
    },
    "失物寻物": {
        "yong": "以妻财（财物）为用神，玄武所临为盗方，看用神存亡与藏所。",
        "ji": "财爻不空不破、伏而可寻，失物可复，宜往用神之方寻觅。",
        "xiong": "财爻空亡墓绝或逢冲散，物已远去难复，寻之多劳。",
        "zhong": "失物或可寻、或难复，须看财爻存亡与逢冲填实之时。",
        "watch": [("妻财", "财物"), ("兄弟", "劫夺")],
    },
    "家宅风水": {
        "yong": "父母为宅舍、妻财为家财、子孙为人丁香火、官鬼为忧患、兄弟为破耗。",
        "ji": "父母（宅）安、子孙（丁）旺、财（妻财）足，家宅兴旺、人财两旺，宜安居。",
        "xiong": "官鬼动扰或父母受冲，宅有忧患、人口不安，须化解修整。",
        "zhong": "家宅平稳中有小忧，宜安父母（宅基）、旺子孙（人丁）。",
        "watch": [("父母", "宅舍"), ("子孙", "人丁"), ("官鬼", "忧患")],
    },
    "天气占候": {
        "yong": "父母为雨、子孙为日月晴明、官鬼为云雾雷电、妻财为晴、兄弟为风。",
        "ji": "子孙（晴明）旺相、妻财得地，天气晴好可期。",
        "xiong": "父母（雨）旺动或官鬼（雷云）发动，主风雨阴晦。",
        "zhong": "阴晴不定，须看父母（雨）与子孙（晴）之消长。",
        "watch": [("父母", "雨"), ("子孙", "晴"), ("兄弟", "风"), ("官鬼", "雷云")],
    },
    "综合": {
        "yong": "无专占之事，以世爻为用神，总观一卦之吉凶向背。",
        "ji": "世爻得地、卦气向我，诸事顺遂、可把握时机进取。",
        "xiong": "世爻无力或卦气背我，诸事多阻，宜守静待时。",
        "zhong": "卦气中平、吉凶相参，随事而断、待应期消息。",
        "watch": [],
    },
}


def build_topic_verdict(topic: str, zonghe: Dict[str, Any],
                        yaos: List[Dict]) -> Dict[str, Any]:
    """据占事类型 + 综合断卦极性，产出专用断语。"""
    tpl = _TEMPLATES.get(topic) or _TEMPLATES["综合"]
    if not zonghe or not zonghe.get("available"):
        return {"available": False}

    if zonghe.get("fu_shen"):
        return {
            "available": True, "topic": topic,
            "yong_desc": tpl["yong"],
            "verdict": f"{tpl['yong']}然用神不上卦、伏而未现——其事隐伏未发，目下未可遽断，待用神出伏之时再观。",
            "watch_points": [],
        }

    conclusion = zonghe.get("conclusion", "中")
    pol = "吉" if "吉" in conclusion and "中" not in conclusion else \
          "凶" if "凶" in conclusion and "中" not in conclusion else "中"
    main = tpl["ji"] if pol == "吉" else tpl["xiong"] if pol == "凶" else tpl["zhong"]

    # 关键六亲看点
    watch_points: List[str] = []
    for qin, label in tpl.get("watch", []):
        y = _find_qin(yaos, qin)
        watch_points.append(f"{label}（{qin}）：{_state_tag(y)}")

    verdict = f"{tpl['yong']}本卦综断为【{conclusion}】——{main}"

    return {
        "available": True, "topic": topic,
        "yong_desc": tpl["yong"],
        "polarity": pol,
        "verdict": verdict,
        "watch_points": watch_points,
    }
