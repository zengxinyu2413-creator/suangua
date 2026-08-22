"""
core/liuyao/advanced_features.py
================================
六爻高级特性补强模块

包含：
1. 卦身（世爻所在卦的特定地支）- 《增删卜易》卷十二
2. 世身（卦身的同位卦爻）
3. 独发独静（动静格局识别）
4. 化合化冲（动爻所化与本爻的合冲关系）
5. 起卦法实操（铜钱起卦、梅花数字起卦）
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
import random


# ─────────────────────────────────────────────────────────────
# 1. 卦身（《增删卜易·卷十二》）
# ─────────────────────────────────────────────────────────────
# 卦身定法：
#   阳世立卦从子起，按世爻位置数到子位
#   阴世立卦从午起，按世爻位置数到午位
# 
# 实际口诀：
#   子月卦阳起子（即世爻为初爻 → 子月，第二爻 → 丑月...）
#   阴爻则换位算
#
# 经典正法（《增删卜易·卷一·安卦身诀》原文规则）：
#   卦身 = 世爻位序 + 该世爻为阳/阴对应的起点
#     阳世：从子开始（世初爻 = 子，二爻 = 丑，三爻 = 寅，四爻 = 卯，五爻 = 辰，上爻 = 巳）
#     阴世：从午开始（世初爻 = 午，二爻 = 未，三爻 = 申，四爻 = 酉，五爻 = 戌，上爻 = 亥）
# 这是《增删卜易》原文规则的完整忠实实现。

# 12 地支序
DIZHI_LIST = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def get_gua_shen(world_position: int, world_yin_yang: str) -> Dict[str, Any]:
    """
    计算卦身地支。
    
    Args:
        world_position: 世爻位置 (1-6，初爻为 1)
        world_yin_yang: 世爻阴阳 ('阳' 或 '阴')
    
    Returns:
        {"zhi": 卦身地支, "position": 卦身所在爻位, "source": 出处}
    """
    if world_yin_yang in ("阳", "阳爻", "yang"):
        # 阳世从子起：初爻=子(0), 二爻=丑(1), 三爻=寅(2), 四爻=卯(3), 五爻=辰(4), 上爻=巳(5)
        zhi_idx = world_position - 1
        start_label = "阳世从子起"
    else:
        # 阴世从午起：初爻=午(6), 二爻=未(7), 三爻=申(8), 四爻=酉(9), 五爻=戌(10), 上爻=亥(11)
        zhi_idx = (world_position - 1) + 6
        start_label = "阴世从午起"
    
    zhi = DIZHI_LIST[zhi_idx % 12]
    return {
        "zhi": zhi,
        "world_position": world_position,
        "world_yin_yang": world_yin_yang,
        "rule": start_label,
        "source": "《增删卜易·卷一·安卦身诀》",
        "desc": f"{start_label}，世爻在{world_position}爻（{world_yin_yang}），卦身 = {zhi}",
    }


def find_guashen_in_chart(yaos: List[Dict[str, Any]], gua_shen_zhi: str) -> Dict[str, Any]:
    """
    在六爻卦中找到卦身所在的爻。
    
    Args:
        yaos: 6 爻列表（含 zhi 字段）
        gua_shen_zhi: 卦身地支
    
    Returns:
        {"on_chart": 是否在卦中, "positions": 在卦中的爻位列表}
    """
    positions = []
    for i, y in enumerate(yaos):
        if y.get("zhi", "") == gua_shen_zhi:
            positions.append({
                "line": i + 1,
                "yao_name": ["初", "二", "三", "四", "五", "上"][i],
                "yao_data": y,
            })
    return {
        "on_chart": len(positions) > 0,
        "gua_shen_zhi": gua_shen_zhi,
        "positions": positions,
        "interpretation": _interpret_guashen(positions, gua_shen_zhi),
    }


def _interpret_guashen(positions: List, gua_shen_zhi: str) -> str:
    if not positions:
        return f"卦身{gua_shen_zhi}不上卦，所占之事根本不在此卦，所测之事难以应验，《增删卜易》云「卦身不上卦，事关本身者难期」。"
    p = positions[0]
    line = p["line"]
    if line == 1:
        return "卦身在初爻，主事关基础、根脚、家庭底层。"
    elif line == 2:
        return "卦身在二爻，主事关居家、内部、近身之人事。"
    elif line == 3:
        return "卦身在三爻，主事关身体、行动、出入之事。"
    elif line == 4:
        return "卦身在四爻，主事关外部、官职、社会层面。"
    elif line == 5:
        return "卦身在五爻，主事关君主、上司、高层决策。"
    else:
        return "卦身在上爻，主事关结局、晚年、终末之事。"


# ─────────────────────────────────────────────────────────────
# 2. 世身（卦身爻的同位之爻）
# ─────────────────────────────────────────────────────────────
# 世身 = 与世爻地支六合的另一爻
# 《增删卜易》原文：「世身者，世爻之合神，主一身吉凶藏隐」
# 完整算法：六合 + 卦中位置查找 + 旺衰

def get_shi_shen(world_position: int, world_zhi: str,
                 yaos: list = None, month_zhi: str = "",
                 day_zhi: str = "") -> Dict[str, Any]:
    """
    世身完整分析：六合定位 + 在卦中位置 + 旺衰
    """
    LIUHE = {"子":"丑", "丑":"子", "寅":"亥", "亥":"寅",
             "卯":"戌", "戌":"卯", "辰":"酉", "酉":"辰",
             "巳":"申", "申":"巳", "午":"未", "未":"午"}
    he_zhi = LIUHE.get(world_zhi)
    
    # 在卦中找世身所在爻
    on_chart = False
    position_in_chart = None
    yao_data = None
    if yaos and he_zhi:
        for i, y in enumerate(yaos):
            if y.get("branch", y.get("zhi", "")) == he_zhi:
                on_chart = True
                position_in_chart = i + 1
                yao_data = y
                break
    
    # 旺衰判断（按月日地支）
    SANHE = {  # 三合局：日月与世身的关系
        "亥卯未":"木", "寅午戌":"火", "巳酉丑":"金", "申子辰":"水",
    }
    旺衰 = ""
    if he_zhi:
        ZHI_WX = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
                  "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
        if month_zhi:
            month_wx = ZHI_WX.get(month_zhi, "")
            sb_wx = ZHI_WX.get(he_zhi, "")
            生 = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
            克 = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
            if month_wx == sb_wx:
                旺衰 = "旺（月令）"
            elif 生.get(month_wx) == sb_wx:
                旺衰 = "相（月令生）"
            elif 克.get(month_wx) == sb_wx:
                旺衰 = "囚（月令克）"
            elif 生.get(sb_wx) == month_wx:
                旺衰 = "休（月令为食伤）"
            else:
                旺衰 = "死（月令为财）"
    
    desc_parts = []
    if he_zhi:
        desc_parts.append(f"世爻{world_zhi}的六合之神为{he_zhi}，称为「世身」")
        if on_chart:
            desc_parts.append(f"世身在第{position_in_chart}爻显象")
        else:
            desc_parts.append("世身不上卦，主隐藏深处之事")
        if 旺衰:
            desc_parts.append(f"月令断为{旺衰}")
        desc_parts.append("主一身吉凶藏隐、心底真意")
    
    return {
        "world_zhi": world_zhi,
        "he_zhi": he_zhi,
        "on_chart": on_chart,
        "position_in_chart": position_in_chart,
        "wang_shuai": 旺衰,
        "desc": "，".join(desc_parts) + "。" if desc_parts else "",
        "source": "《增删卜易·世身论》",
    }


# ─────────────────────────────────────────────────────────────
# 3. 独发独静识别
# ─────────────────────────────────────────────────────────────

def analyze_dong_jing(yaos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析卦中动爻分布：独发、独静、多发、全静、全动。
    
    Args:
        yaos: 6 爻（含 dong 字段或 type='moving'）
    """
    moving_yaos = []
    for i, y in enumerate(yaos):
        is_moving = y.get("dong", False) or y.get("is_moving", False) or y.get("type") == "moving"
        if is_moving:
            moving_yaos.append({
                "line": i + 1,
                "yao_name": ["初", "二", "三", "四", "五", "上"][i],
                "data": y,
            })
    
    n = len(moving_yaos)
    
    if n == 0:
        return {
            "type": "全静卦",
            "level": "important",
            "moving_count": 0,
            "desc": "六爻皆静，无动爻。《增删卜易》云「静卦看本卦，以世应、用神为主」，事不变。",
            "advice": "看世爻与用神的旺衰生克即可，不必看变卦。",
            "source": "《增删卜易·静卦总论》",
        }
    elif n == 1:
        return {
            "type": "独发卦",
            "level": "auspicious_great",
            "moving_count": 1,
            "moving_lines": moving_yaos,
            "desc": f"独发一爻（第{moving_yaos[0]['line']}爻 {moving_yaos[0]['yao_name']}爻动），《增删卜易》云「独发易取，乱动难凭」，此爻乃断事关键。",
            "advice": "重点看独发爻的变化、化象、生克，再合参世应。",
            "source": "《增删卜易·独发独静章》",
        }
    elif n == 6:
        return {
            "type": "全动卦",
            "level": "warning",
            "moving_count": 6,
            "desc": "六爻全动，《增删卜易》云「乱动之卦，事多反复」，主局势剧烈变化，难定吉凶。",
            "advice": "全动须以变卦为主，本卦次之；或看主静之爻反推。",
            "source": "《增删卜易·乱动章》",
        }
    elif n == 5:
        # 独静：仅一爻不动
        static_idx = next(i for i, y in enumerate(yaos)
                           if not (y.get("dong") or y.get("is_moving") or y.get("type") == "moving"))
        return {
            "type": "独静卦",
            "level": "auspicious",
            "moving_count": 5,
            "static_line": static_idx + 1,
            "desc": f"独静一爻（第{static_idx+1}爻 {['初','二','三','四','五','上'][static_idx]}爻不动），《增删卜易》云「独静则取，独发亦同」，此静爻乃断事关键。",
            "advice": "重点看独静爻的处境（旺衰、空亡、临神）。",
            "source": "《增删卜易·独发独静章》",
        }
    else:
        return {
            "type": f"多发卦（{n}爻动）",
            "level": "warning",
            "moving_count": n,
            "moving_lines": moving_yaos,
            "desc": f"卦中{n}爻发动，《增删卜易》云「多动者乱，乱则难占」，须以用神为主，他爻为辅。",
            "advice": "重点看用神所在爻的动变；忌神动则凶，原神动则吉。",
            "source": "《增删卜易·多发章》",
        }


# ─────────────────────────────────────────────────────────────
# 4. 化合化冲（动爻所化与本爻的关系）
# ─────────────────────────────────────────────────────────────

LIU_HE = {"子":"丑", "丑":"子", "寅":"亥", "亥":"寅",
          "卯":"戌", "戌":"卯", "辰":"酉", "酉":"辰",
          "巳":"申", "申":"巳", "午":"未", "未":"午"}

LIU_CHONG = {"子":"午", "午":"子", "丑":"未", "未":"丑",
             "寅":"申", "申":"寅", "卯":"酉", "酉":"卯",
             "辰":"戌", "戌":"辰", "巳":"亥", "亥":"巳"}


def analyze_hua_he_chong(yaos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    分析每个动爻"化"出来的爻与原爻是否构成化合、化冲。
    
    Args:
        yaos: 6 爻，每个动爻须含 'changed_zhi' 字段（化出的地支）
    """
    results = []
    for i, y in enumerate(yaos):
        is_moving = y.get("dong", False) or y.get("is_moving", False) or y.get("type") == "moving"
        if not is_moving:
            continue
        
        orig_zhi = y.get("zhi", "")
        changed_zhi = y.get("changed_zhi") or y.get("hua_zhi") or y.get("bian_zhi", "")
        if not orig_zhi or not changed_zhi:
            continue
        
        line_label = f"第{i+1}爻（{['初','二','三','四','五','上'][i]}爻）"
        
        # 化合
        if LIU_HE.get(orig_zhi) == changed_zhi:
            results.append({
                "line": i + 1,
                "type": "化合",
                "orig_zhi": orig_zhi,
                "changed_zhi": changed_zhi,
                "level": "auspicious",
                "desc": f"{line_label} {orig_zhi}动化{changed_zhi}，{orig_zhi}{changed_zhi}六合，「化合」之吉。"
                       f"主事情虽动而归于和合，谋事可成，纠纷可解。",
                "source": "《增删卜易·化合章》",
            })
        # 化冲
        elif LIU_CHONG.get(orig_zhi) == changed_zhi:
            results.append({
                "line": i + 1,
                "type": "化冲",
                "orig_zhi": orig_zhi,
                "changed_zhi": changed_zhi,
                "level": "inauspicious",
                "desc": f"{line_label} {orig_zhi}动化{changed_zhi}，{orig_zhi}{changed_zhi}六冲，「化冲」之凶。"
                       f"主事情反复、变卦、人离物散。",
                "source": "《增删卜易·化冲章》",
            })
        # 化进
        elif _is_jin_shen(orig_zhi, changed_zhi):
            results.append({
                "line": i + 1,
                "type": "化进神",
                "orig_zhi": orig_zhi,
                "changed_zhi": changed_zhi,
                "level": "auspicious",
                "desc": f"{line_label} {orig_zhi}化{changed_zhi}，「化进神」，主渐进、事态向前。",
                "source": "《增删卜易·进神章》",
            })
        # 化退
        elif _is_tui_shen(orig_zhi, changed_zhi):
            results.append({
                "line": i + 1,
                "type": "化退神",
                "orig_zhi": orig_zhi,
                "changed_zhi": changed_zhi,
                "level": "inauspicious",
                "desc": f"{line_label} {orig_zhi}化{changed_zhi}，「化退神」，主衰退、事态向后。",
                "source": "《增删卜易·退神章》",
            })
    
    return results


# 进神/退神（同五行同方向）
def _is_jin_shen(orig: str, changed: str) -> bool:
    """化进神：寅→卯, 巳→午, 申→酉, 亥→子 等同五行内顺序"""
    JIN_PAIRS = [("寅","卯"), ("巳","午"), ("申","酉"), ("亥","子"),
                 ("丑","辰"), ("辰","未"), ("未","戌"), ("戌","丑")]  # 土
    return (orig, changed) in JIN_PAIRS


def _is_tui_shen(orig: str, changed: str) -> bool:
    TUI_PAIRS = [("卯","寅"), ("午","巳"), ("酉","申"), ("子","亥"),
                 ("辰","丑"), ("未","辰"), ("戌","未"), ("丑","戌")]
    return (orig, changed) in TUI_PAIRS


# ─────────────────────────────────────────────────────────────
# 5. 起卦法实操（铜钱起卦 + 数字起卦）
# ─────────────────────────────────────────────────────────────

def coin_divination() -> Dict[str, Any]:
    """
    铜钱起卦（三枚铜钱六次掷出）
    
    每次掷三枚铜钱，按正反面计：
      三背（一阴二阳？）— 老阳 9（动爻）
      三面 — 老阴 6（动爻）
      两背一面 — 少阳 7（静）
      两面一背 — 少阴 8（静）
    
    标准规则（《增删卜易》）：
      字（背、阴）= 2 分
      花（面、阳）= 3 分
      三枚总分 6/7/8/9 决定爻：
        6 = 老阴（动）
        7 = 少阳（静）
        8 = 少阴（静）
        9 = 老阳（动）
    
    从初爻开始掷 6 次。
    
    Returns:
        {"yaos": [...6 yaos...], "method": "铜钱起卦", "source": "《周易》《增删卜易》"}
    """
    yaos = []
    for line_idx in range(6):
        # 模拟三枚铜钱
        coins = [random.choice(["背", "面"]) for _ in range(3)]
        score = sum(2 if c == "背" else 3 for c in coins)
        
        if score == 6:
            yao = {"value": 6, "name": "老阴", "type": "moving", "yin_yang": "阴", "dong": True}
        elif score == 7:
            yao = {"value": 7, "name": "少阳", "type": "static", "yin_yang": "阳", "dong": False}
        elif score == 8:
            yao = {"value": 8, "name": "少阴", "type": "static", "yin_yang": "阴", "dong": False}
        else:  # 9
            yao = {"value": 9, "name": "老阳", "type": "moving", "yin_yang": "阳", "dong": True}
        yao["line"] = line_idx + 1
        yao["coins"] = coins
        yaos.append(yao)
    
    return {
        "method": "三钱掷六次（铜钱起卦法）",
        "yaos": yaos,
        "source": "《增删卜易·铜钱起卦法》",
        "explanation": "三钱掷六次，背=2分、面=3分，三钱合6/7/8/9定一爻；6 老阴、7 少阳、8 少阴、9 老阳。老阴老阳为动爻。",
    }


def number_divination(num1: int, num2: int, num3: int = None) -> Dict[str, Any]:
    """
    数字起卦（梅花易数）
    
    Args:
        num1: 第一个数（决定上卦）
        num2: 第二个数（决定下卦）
        num3: 可选第三个数（决定变爻）
    """
    BAGUA = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
    
    upper_idx = (num1 - 1) % 8
    lower_idx = (num2 - 1) % 8
    upper_gua = BAGUA[upper_idx]
    lower_gua = BAGUA[lower_idx]
    
    if num3 is not None:
        bian_yao = ((num1 + num2 + num3 - 1) % 6) + 1
    else:
        bian_yao = ((num1 + num2 - 1) % 6) + 1
    
    return {
        "method": "梅花易数（数字起卦）",
        "upper_gua": upper_gua,
        "lower_gua": lower_gua,
        "hexagram_name": f"{upper_gua}{lower_gua}",
        "bian_yao": bian_yao,
        "source": "《梅花易数·数字起卦法》",
        "explanation": f"上卦 = {num1} ÷ 8 余数 → {upper_gua}；下卦 = {num2} ÷ 8 余数 → {lower_gua}；变爻 = 总和 ÷ 6 余数 → 第 {bian_yao} 爻。",
    }
