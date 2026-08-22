"""
core/fengshui/xuankong_luantou.py
=================================
玄空飞星·九宫多层级峦头形理断（理气配峦头）。

玄空「理气为用、峦头为体」：飞星之吉凶，须配方位之砂水形势方验。
原排盘已有运/山/向三盘叠加（combined）、流年叠盘（overlaid_with_annual）、
双星组合断（palace_judgments），但缺「峦头形理」一层——即每宫之砂水宜忌：
  · 山管人丁、水管财禄。
  · 向星（水星）当令生旺者宜见水（开阔·低·动·路·池），得水则旺财；
    衰死者忌见水（动则退气破财），宜静实。
  · 山星（丁星）当令生旺者宜见山（高·实·靠），得山则旺丁人康；
    衰死者忌高压，宜虚远，或以水化。
  · 五黄·二黑临宫忌动土修造，宜静、宜金泄；逢流年同煞叠临则凶上加凶。

本模块据当运（如九运）判每星之旺·生·退·死·煞，配峦头出每宫之砂水布局断，
并叠流年星论催动，与排盘同源（直接读 chart 之 combined / overlaid_with_annual）。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

# 星之名与本性
STAR_NAME = {1: "一白贪狼", 2: "二黑巨门", 3: "三碧禄存", 4: "四绿文曲",
             5: "五黄廉贞", 6: "六白武曲", 7: "七赤破军", 8: "八白左辅", 9: "九紫右弼"}
STAR_NATURE = {
    1: ("吉", "魁星·官星·桃花，主功名智慧、人缘"),
    2: ("凶", "病符·寡宿，主疾病、肠胃、孤寡"),
    3: ("凶", "蚩尤·是非星，主口舌官非、争斗"),
    4: ("吉", "文昌星，主文章科甲、读书智慧"),
    5: ("大凶", "正关煞·廉贞，主灾病横祸、阻滞，至忌动"),
    6: ("吉", "武曲·权星，主官贵、武职、权威"),
    7: ("凶", "破军·肃杀，当令主偏财、退则主盗劫破耗刀伤"),
    8: ("大吉", "左辅·财星，主富贵、田产、忠厚"),
    9: ("吉", "右弼·喜庆星，主喜事、文明、桃花，当令则极旺"),
}


def _wangshuai(star: int, yun: int) -> Dict[str, str]:
    """据当运判星之旺衰（旺·生·进·退·死煞）。"""
    nxt1 = yun + 1 if yun < 9 else 1
    nxt2 = nxt1 + 1 if nxt1 < 9 else 1
    prev = yun - 1 if yun > 1 else 9
    if star == yun:
        return {"level": "旺", "tag": "当令", "fortune": "吉"}
    if star == nxt1:
        return {"level": "生", "tag": "生气", "fortune": "吉"}
    if star == nxt2:
        return {"level": "进", "tag": "进气", "fortune": "小吉"}
    if star == prev:
        return {"level": "退", "tag": "退气", "fortune": "小凶"}
    # 死煞
    if star == 5:
        return {"level": "煞", "tag": "五黄关煞", "fortune": "大凶"}
    if star == 2:
        return {"level": "死", "tag": "二黑病符", "fortune": "凶"}
    return {"level": "死", "tag": "死气", "fortune": "凶"}


def _is_sheng(level: str) -> bool:
    return level in ("旺", "生", "进")


def analyze_palace_luantou(pal: Dict[str, Any], yun: int) -> Dict[str, Any]:
    """单宫峦头形理：山星·向星之砂水宜忌 + 流年催动。"""
    mountain = pal.get("mountain", 0)   # 山星（丁）
    facing = pal.get("facing", 0)       # 向星（财）
    annual = pal.get("annual")          # 流年星
    direction = pal.get("direction", "")

    m_ws = _wangshuai(mountain, yun)
    f_ws = _wangshuai(facing, yun)

    advice: List[str] = []
    flags: List[Dict[str, str]] = []

    # ── 向星（水/财）砂水宜忌 ──
    if _is_sheng(f_ws["level"]):
        advice.append(f"向星{STAR_NAME.get(facing,'')}（{f_ws['tag']}）当旺——此方宜见水（开阔、低平、路口、水池、动象），得水则旺财禄。")
    else:
        advice.append(f"向星{STAR_NAME.get(facing,'')}（{f_ws['tag']}）已衰——此方忌见水动，宜静实（墙、柜、矮屏），见水反主退财招灾。")

    # ── 山星（山/丁）砂水宜忌 ──
    if _is_sheng(m_ws["level"]):
        advice.append(f"山星{STAR_NAME.get(mountain,'')}（{m_ws['tag']}）当旺——此方宜见山（高实、靠山、楼宇、静），得山则旺丁、人口康健。")
    else:
        advice.append(f"山星{STAR_NAME.get(mountain,'')}（{m_ws['tag']}）已衰——此方忌高压逼塞，衰山宜虚远空旷，或以水化泄。")

    # ── 五黄·二黑临宫 ──
    for star, who in ((mountain, "山星"), (facing, "向星")):
        if star == 5:
            flags.append({"type": "五黄到方", "nature": "大凶",
                          "desc": f"{who}五黄廉贞临{direction}方——至忌动土、修造、开门、安灶，宜静、宜金器（铜铃）泄之。"})
        elif star == 2:
            flags.append({"type": "二黑到方", "nature": "凶",
                          "desc": f"{who}二黑病符临{direction}方——主疾病肠胃，忌动，宜静、宜金泄、忌红黄重物。"})

    # ── 流年叠加催动 ──
    annual_note = ""
    if annual:
        a_ws = _wangshuai(annual, yun)
        if annual == 5:
            annual_note = f"流年五黄入{direction}方——本年此方忌动土兴工，宜静镇。"
            if mountain == 5 or facing == 5:
                annual_note += "且与盘中五黄叠临，凶气大增，务必空净安静。"
            flags.append({"type": "流年五黄", "nature": "大凶", "desc": annual_note})
        elif annual == 2:
            annual_note = f"流年二黑病符入{direction}方——本年此方防疾患，宜金泄、勿久居病人。"
            flags.append({"type": "流年二黑", "nature": "凶", "desc": annual_note})
        elif annual == yun:
            annual_note = f"流年当令{STAR_NAME.get(annual,'')}入{direction}方——本年此方得令催旺，吉上加吉，可开门纳气、催财催贵。"
        elif _is_sheng(a_ws["level"]) and _is_sheng(f_ws["level"]):
            annual_note = f"流年{STAR_NAME.get(annual,'')}（{a_ws['tag']}）会向星旺气——本年此方催财有力。"
        elif _is_sheng(a_ws["level"]) and _is_sheng(m_ws["level"]):
            annual_note = f"流年{STAR_NAME.get(annual,'')}（{a_ws['tag']}）会山星旺气——本年此方利添丁、旺人口。"

    # ── 宫综合定性 ──
    if _is_sheng(f_ws["level"]) or _is_sheng(m_ws["level"]):
        quality = "旺方" if (f_ws["level"] == "旺" or m_ws["level"] == "旺") else "进气方"
    elif any(f["nature"] == "大凶" for f in flags):
        quality = "煞方"
    else:
        quality = "衰方"

    return {
        "direction": direction,
        "mountain_star": mountain, "facing_star": facing, "annual_star": annual,
        "mountain_ws": m_ws, "facing_ws": f_ws,
        "quality": quality,
        "advice": advice,
        "flags": flags,
        "annual_note": annual_note,
        "summary": f"{direction}方【{quality}】：" + "　".join(advice)
                   + (("　" + annual_note) if annual_note else ""),
    }


def enrich_xuankong_luantou(chart: Dict[str, Any]) -> Dict[str, Any]:
    """为整盘九宫补峦头形理层，并汇总旺方/衰方/煞方与砂水总则。"""
    yun_info = chart.get("yun", {})
    yun = yun_info.get("yun") if isinstance(yun_info, dict) else (yun_info or 9)
    src = chart.get("overlaid_with_annual") or chart.get("combined") or {}

    luantou: Dict[Any, Any] = {}
    wang_dirs, shuai_dirs, sha_dirs = [], [], []
    for luoshu, pal in src.items():
        if not isinstance(pal, dict):
            continue
        lt = analyze_palace_luantou(pal, yun)
        luantou[luoshu] = lt
        if lt["quality"] in ("旺方", "进气方"):
            wang_dirs.append(lt["direction"])
        elif lt["quality"] == "煞方":
            sha_dirs.append(lt["direction"])
        else:
            shuai_dirs.append(lt["direction"])

    chart["luantou"] = luantou
    chart["luantou_summary"] = {
        "yun": yun,
        "wang_directions": wang_dirs,
        "shuai_directions": shuai_dirs,
        "sha_directions": sha_dirs,
        "principle": "山管人丁水管财：向星生旺之方宜见水以发财、山星生旺之方宜见山以旺丁；"
                     "衰死之方宜静实化解，五黄二黑之方忌动土、宜金泄。",
        "desc": f"当{STAR_NAME.get(yun,'')[:2] if yun else ''}运。"
                f"旺财旺丁之方：{('、'.join(wang_dirs)) or '无'}；"
                f"衰退宜静之方：{('、'.join(shuai_dirs)) or '无'}；"
                f"五黄二黑煞方（忌动）：{('、'.join(sha_dirs)) or '无'}。",
    }
    return chart
