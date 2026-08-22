"""
core/fengshui/xuankong_advanced.py
===================================
玄空飞星高级理论模块

包含：
1. **零神 / 正神**（每运的正神方位 + 零神方位）— 玄空挨星的核心原则
2. **反吟 / 伏吟**（运盘与山盘/向盘同数 = 反伏吟，凶煞）
3. **流年紫白与本盘叠加**（实战流年应期）
4. **正确的七星打劫**（区分真打劫离宫 vs 假打劫坎宫）
5. **收山出煞**（坐山见山、向方见水的形理判定）
6. **替卦 / 起星**（兼向 ≥ 3° 用替卦法）
7. **太岁刑冲坐山**（年支与坐山的关系）
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional


# ─────────────────────────────────────────────────────────────
# 1. 零神 / 正神
# ─────────────────────────────────────────────────────────────
# 玄空挨星法核心原则之一：
#   - **正神**：当令之运的洛书数所在方位，宜实（见山、建筑、靠山）
#   - **零神**：与正神相对（运数 + 零神数 = 10）的方位，宜虚（见水、空地、开门）
#   - **照神**：正神之左右辅佐（一卦三山中其他两山）
#
# 「正神百步始成龙，水短便遭凶」——《青囊奥语》
# 「正神正位装，拨水入零堂」——《天玉经》
#
# 即：正神方宜见山实方旺丁，零神方宜见水开门旺财。
# 反之（正神见水、零神见山）则为「上山下水」之凶象。

ZHENG_LING_SHEN: Dict[int, Dict[str, Any]] = {
    1: {  # 一运
        "zhengshen_num": 1, "zhengshen_dir": "北", "zhengshen_gua": "坎",
        "lingshen_num": 9, "lingshen_dir": "南", "lingshen_gua": "离",
        "desc": "一运坐北朝南或坐南朝北最为合理，北方实（山）南方虚（水）则丁财两旺。",
    },
    2: {
        "zhengshen_num": 2, "zhengshen_dir": "西南", "zhengshen_gua": "坤",
        "lingshen_num": 8, "lingshen_dir": "东北", "lingshen_gua": "艮",
        "desc": "二运西南宜见山，东北宜见水。",
    },
    3: {
        "zhengshen_num": 3, "zhengshen_dir": "东", "zhengshen_gua": "震",
        "lingshen_num": 7, "lingshen_dir": "西", "lingshen_gua": "兑",
        "desc": "三运东方宜见山，西方宜见水。",
    },
    4: {
        "zhengshen_num": 4, "zhengshen_dir": "东南", "zhengshen_gua": "巽",
        "lingshen_num": 6, "lingshen_dir": "西北", "lingshen_gua": "乾",
        "desc": "四运东南宜见山，西北宜见水。",
    },
    5: {  # 五黄无方位，前十年寄艮（8），后十年寄坤（2）
        "zhengshen_num": 5, "zhengshen_dir": "中（前十年寄艮，后十年寄坤）",
        "zhengshen_gua": "中宫",
        "lingshen_num": 5, "lingshen_dir": "中",
        "lingshen_gua": "中宫",
        "desc": "五运中宫无定位，前十年视同二运（坐西南），后十年视同八运（坐东北）。",
    },
    6: {
        "zhengshen_num": 6, "zhengshen_dir": "西北", "zhengshen_gua": "乾",
        "lingshen_num": 4, "lingshen_dir": "东南", "lingshen_gua": "巽",
        "desc": "六运西北宜见山，东南宜见水。",
    },
    7: {
        "zhengshen_num": 7, "zhengshen_dir": "西", "zhengshen_gua": "兑",
        "lingshen_num": 3, "lingshen_dir": "东", "lingshen_gua": "震",
        "desc": "七运西方宜见山，东方宜见水。",
    },
    8: {
        "zhengshen_num": 8, "zhengshen_dir": "东北", "zhengshen_gua": "艮",
        "lingshen_num": 2, "lingshen_dir": "西南", "lingshen_gua": "坤",
        "desc": "八运东北宜见山，西南宜见水（拨水入零堂）。",
    },
    9: {  # 当前九运 2024-2043
        "zhengshen_num": 9, "zhengshen_dir": "南", "zhengshen_gua": "离",
        "lingshen_num": 1, "lingshen_dir": "北", "lingshen_gua": "坎",
        "desc": "九运（2024-2043）南方为正神宜见山，北方为零神宜见水（拨水入零堂主大旺财）。",
    },
}


def get_zheng_ling_shen(yun: int) -> Dict[str, Any]:
    """返回某运的正神零神方位。"""
    return ZHENG_LING_SHEN.get(yun, {})


def analyze_zheng_ling_layout(yun: int, sitting_gua: str, facing_gua: str,
                                has_water_at_facing: bool = None,
                                has_mountain_at_sitting: bool = None) -> Dict[str, Any]:
    """
    分析房屋坐向与零正神的关系。
    
    返回评级：
    - perfect: 正神方坐山有山，零神方朝向见水（旺山旺向之正神局）
    - good: 部分符合
    - bad: 完全相反（正神见水、零神见山，犯「上山下水」）
    """
    info = get_zheng_ling_shen(yun)
    if not info:
        return {}
    
    zs = info["zhengshen_gua"]
    ls = info["lingshen_gua"]
    
    is_sitting_zs = (sitting_gua == zs)
    is_facing_ls = (facing_gua == ls)
    is_sitting_ls = (sitting_gua == ls)
    is_facing_zs = (facing_gua == zs)
    
    if is_sitting_zs and is_facing_ls:
        verdict = "perfect"
        desc = f"坐{sitting_gua}（{zs}=正神）朝{facing_gua}（{ls}=零神），正神坐山旺丁、零神向首旺财，乃《天玉经》「正神正位装，拨水入零堂」最佳格局。"
    elif is_sitting_ls and is_facing_zs:
        verdict = "very_bad"
        desc = f"坐{sitting_gua}（{ls}=零神）朝{facing_gua}（{zs}=正神），正神见水、零神见山，犯「上山下水」之大凶。"
    elif is_sitting_zs or is_facing_ls:
        verdict = "good"
        desc = f"部分合零正：坐山{'正神' if is_sitting_zs else '辅位'}，向首{'零神' if is_facing_ls else '辅位'}。尚可。"
    elif is_sitting_ls or is_facing_zs:
        verdict = "bad"
        desc = f"部分犯反位：{'坐山见零神' if is_sitting_ls else '向首见正神'}，丁财一损。"
    else:
        verdict = "neutral"
        desc = f"坐向为辅位（{sitting_gua}/{facing_gua}），非正神亦非零神，宜配合形势综合判断。"
    
    return {
        "yun": yun,
        "zhengshen": info,
        "verdict": verdict,
        "is_sitting_zhengshen": is_sitting_zs,
        "is_facing_lingshen": is_facing_ls,
        "desc": desc,
        "advice": _get_zheng_ling_advice(verdict, info),
    }


def _get_zheng_ling_advice(verdict: str, info: Dict) -> List[str]:
    advice = []
    zs_dir = info["zhengshen_dir"]
    ls_dir = info["lingshen_dir"]
    if verdict == "perfect":
        advice = [
            f"{zs_dir}方（正神）宜见山或实物（如靠山墙、家具），加固丁口",
            f"{ls_dir}方（零神）宜开阔、见水（鱼缸、流水），加强财气",
            "此局当令期间丁财两旺，应抓紧装修布局以纳吉气",
        ]
    elif verdict == "very_bad":
        advice = [
            f"⚠ 坐向反位，犯「上山下水」之大凶",
            f"{ls_dir}方（实际坐山方）应去除高耸物、改为见水",
            f"{zs_dir}方（实际朝向）应增加实物靠山",
            "或考虑改门换向，方能转凶为吉",
        ]
    else:
        advice = [
            f"参考：{zs_dir}方为正神，宜实（见山）",
            f"参考：{ls_dir}方为零神，宜虚（见水）",
            "依实际格局微调家具摆设以靠近最佳布局",
        ]
    return advice


# ─────────────────────────────────────────────────────────────
# 2. 反吟 / 伏吟
# ─────────────────────────────────────────────────────────────
# 玄空大忌之一！
#   - **伏吟**：山盘或向盘的入中星 = 运盘的入中星（即两盘的中宫数相同）
#     主静止不动、家运停滞、丁财两不旺
#   - **反吟**：山盘或向盘的入中星 + 运盘的入中星 = 10（对宫数）
#     主反复无常、家运起伏激烈、易有凶事
# 反伏吟既无生气又无变化，主家败、停滞、丧丁等。

def detect_fan_fu_yin(yun: int, mountain_chart_center: int, facing_chart_center: int) -> Dict[str, Any]:
    """
    检测山盘 / 向盘的反吟伏吟。
    
    Args:
        yun: 当令运数
        mountain_chart_center: 山盘入中星
        facing_chart_center: 向盘入中星
    """
    patterns = []
    
    if mountain_chart_center == yun:
        patterns.append({
            "type": "山盘伏吟",
            "level": "inauspicious",
            "desc": f"山盘入中{mountain_chart_center} = 运盘入中{yun}，犯「山盘伏吟」。主家中人口停滞、丁口衰退、健康不振。",
            "source": "《沈氏玄空学》「伏吟之局，灾祸频频」",
        })
    if facing_chart_center == yun:
        patterns.append({
            "type": "向盘伏吟",
            "level": "inauspicious",
            "desc": f"向盘入中{facing_chart_center} = 运盘入中{yun}，犯「向盘伏吟」。主财气停滞、家业难发。",
            "source": "《沈氏玄空学》",
        })
    if mountain_chart_center + yun == 10:
        patterns.append({
            "type": "山盘反吟",
            "level": "inauspicious_great",
            "desc": f"山盘入中{mountain_chart_center} + 运盘入中{yun} = 10，犯「山盘反吟」。主家口反复多变、丁口不安、出入意外。",
            "source": "《地理辨正·天玉经》「反吟伏吟泪淋淋」",
        })
    if facing_chart_center + yun == 10:
        patterns.append({
            "type": "向盘反吟",
            "level": "inauspicious_great",
            "desc": f"向盘入中{facing_chart_center} + 运盘入中{yun} = 10，犯「向盘反吟」。主财气大起大落、家业难守。",
            "source": "《地理辨正》",
        })
    
    return {
        "has_fan_fu_yin": len(patterns) > 0,
        "patterns": patterns,
        "remedy": "犯反伏吟者，须以挂铜钱、五帝钱镇压；或在该宫位放静物（水晶球）化解" if patterns else None,
    }


# ─────────────────────────────────────────────────────────────
# 3. 流年紫白与本盘叠加
# ─────────────────────────────────────────────────────────────

def get_annual_zibai_center(year: int) -> int:
    """
    流年紫白入中宫星数。
    
    规则（《沈氏玄空学》三元紫白）：
      1984 甲子 = 七赤入中
      每年中宫数 - 1，1↔9 循环
    """
    offset = year - 1984
    center = ((7 - offset - 1) % 9) + 1
    return center


def calculate_annual_flying(year: int) -> Dict[int, int]:
    """计算流年紫白九宫飞星（始终阳顺飞）。"""
    center = get_annual_zibai_center(year)
    palace_to_star = {}
    YANG_SEQ = [5, 6, 7, 8, 9, 1, 2, 3, 4]  # 顺飞序
    for i, palace in enumerate(YANG_SEQ):
        star = ((center - 1 + i) % 9) + 1
        palace_to_star[palace] = star
    return palace_to_star


# ─────────────────────────────────────────────────────────────
# 3b. 流月紫白
# ─────────────────────────────────────────────────────────────
# 《沈氏玄空学·月紫白》起例口诀：
#   子午卯酉年正月起八白
#   寅申巳亥年正月起二黑
#   辰戌丑未年正月起五黄
# 然后每月减一（逆推），1↔9 循环。

def get_monthly_zibai_center(year: int, month: int) -> int:
    """
    流月紫白入中宫星数。
    
    Args:
        year: 阴历年（用于确定年地支）
        month: 农历月份 (1-12)
    """
    # 年地支
    zhi_list = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    offset = (year - 1984) % 12
    year_zhi = zhi_list[offset]
    
    # 正月起例
    if year_zhi in ("子", "午", "卯", "酉"):
        first_month_center = 8
    elif year_zhi in ("寅", "申", "巳", "亥"):
        first_month_center = 2
    else:  # 辰戌丑未
        first_month_center = 5
    
    # 每月减 1（逆推）
    center = ((first_month_center - (month - 1) - 1) % 9) + 1
    if center == 0:
        center = 9
    return center


def calculate_monthly_flying(year: int, month: int) -> Dict[int, int]:
    """计算流月紫白九宫飞星（始终阳顺飞）。"""
    center = get_monthly_zibai_center(year, month)
    palace_to_star = {}
    YANG_SEQ = [5, 6, 7, 8, 9, 1, 2, 3, 4]
    for i, palace in enumerate(YANG_SEQ):
        star = ((center - 1 + i) % 9) + 1
        palace_to_star[palace] = star
    return palace_to_star


def overlay_monthly_on_annual(year: int, month: int) -> Dict[int, Dict[str, int]]:
    """
    流月与流年叠加，得出某月的双重时间影响。
    
    Returns: {pos: {annual, monthly}}
    """
    annual = calculate_annual_flying(year)
    monthly = calculate_monthly_flying(year, month)
    DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
    return {
        pos: {
            "annual": annual[pos],
            "monthly": monthly[pos],
            "direction": DIR[pos],
        }
        for pos in range(1, 10)
    }


def detect_monthly_warnings(year: int, month: int) -> List[Dict[str, Any]]:
    """检测某月的紫白凶位（结合流年+流月）。"""
    overlaid = overlay_monthly_on_annual(year, month)
    warnings = []
    for pos, stars in overlaid.items():
        annual = stars["annual"]
        monthly = stars["monthly"]
        direction = stars["direction"]
        
        # 流月五黄叠加流年五黄 = 大凶
        if annual == 5 and monthly == 5:
            warnings.append({
                "direction": direction, "level": "inauspicious_great",
                "year": year, "month": month,
                "title": f"{year}-{month}月 流月五黄叠加流年五黄到{direction}方",
                "desc": "双重五黄煞气！绝对禁止此月此方位动土修造、装修、搬迁。",
                "remedy": "本月避免接近该方位，挂铜葫芦",
            })
        # 流月五黄单飞
        elif monthly == 5:
            warnings.append({
                "direction": direction, "level": "inauspicious",
                "year": year, "month": month,
                "title": f"{year}-{month}月 流月五黄飞临{direction}方",
                "desc": "本月此方位忌动土修造。",
                "remedy": "暂避接近，放铜质化煞物",
            })
        # 流月二黑叠加流年二黑
        elif annual == 2 and monthly == 2:
            warnings.append({
                "direction": direction, "level": "inauspicious",
                "year": year, "month": month,
                "title": f"{year}-{month}月 流月二黑叠加病符到{direction}方",
                "desc": "本月此方位主疾病加重，老人小孩尤避久居。",
                "remedy": "放铜葫芦化病气",
            })
    return warnings


def overlay_annual_on_base(base_combined: Dict[int, Dict[str, int]], year: int) -> Dict[int, Dict[str, int]]:
    """
    将流年紫白叠加到本盘飞星上。
    
    Args:
        base_combined: 本盘 {luoshu_pos: {yun, mountain, facing}}
        year: 流年
    
    Returns:
        {luoshu_pos: {yun, mountain, facing, annual, ...}}
    """
    annual_chart = calculate_annual_flying(year)
    overlaid = {}
    for pos, stars in base_combined.items():
        overlaid[pos] = {
            **stars,
            "annual": annual_chart[pos],
        }
    return overlaid


def detect_annual_warnings(overlaid: Dict[int, Dict[str, int]], year: int) -> List[Dict[str, Any]]:
    """
    检测流年与本盘叠加的危险组合：
    - 流年五黄到本盘当令位 → 当年凶
    - 流年二黑（病符）到本盘山星位 → 当年丁口不利
    - 流年三碧到本盘吉位 → 当年是非
    """
    DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
    warnings = []
    for pos, stars in overlaid.items():
        annual = stars["annual"]
        mtn = stars["mountain"]
        fac = stars["facing"]
        direction = DIR[pos]
        
        # 流年五黄
        if annual == 5:
            warnings.append({
                "direction": direction, "level": "inauspicious_great",
                "year": year,
                "title": f"{year}年五黄飞临{direction}方",
                "desc": f"流年五黄到此宫（本盘山{mtn}向{fac}），此年此方位绝对不可动土、修造、开门、装修。",
                "remedy": "放六帝钱、铜葫芦、铜风铃化煞",
            })
        # 流年二黑病符
        elif annual == 2:
            warnings.append({
                "direction": direction, "level": "inauspicious",
                "year": year,
                "title": f"{year}年二黑病符飞临{direction}方",
                "desc": f"流年病符到此宫，主家人健康不利，老人小孩尤忌久居。",
                "remedy": "放铜葫芦、铜钟化病气",
            })
        # 流年三碧蚩尤
        elif annual == 3:
            warnings.append({
                "direction": direction, "level": "inauspicious",
                "year": year,
                "title": f"{year}年三碧是非飞临{direction}方",
                "desc": "流年口舌之星，主官非、争讼、是非。",
                "remedy": "放红色物品化解（火克木）",
            })
        # 流年八白财星
        elif annual == 8:
            warnings.append({
                "direction": direction, "level": "auspicious",
                "year": year,
                "title": f"{year}年八白财星飞临{direction}方",
                "desc": "流年财星到此，宜在此方位放招财物品（貔貅、聚宝盆、流水）。",
                "remedy": "招财物品 + 鱼缸（如本盘也为吉位）",
            })
        # 流年九紫喜庆星（九运当令）
        elif annual == 9:
            warnings.append({
                "direction": direction, "level": "auspicious",
                "year": year,
                "title": f"{year}年九紫喜庆飞临{direction}方",
                "desc": "流年喜庆星到此，主升迁、婚嫁、添丁、喜事。",
                "remedy": "宜放紫红色装饰、灯具",
            })
    
    return warnings


# ─────────────────────────────────────────────────────────────
# 4. 七星打劫的精确判定（区分真打劫 vs 假打劫）
# ─────────────────────────────────────────────────────────────
# 《青囊奥语》《天玉经》之秘传。
# 
# 真打劫只有两种：
#   - 离宫打劫：向首在「南（离）」时，南-中-北三宫向星成 147/258/369
#   - 坎宫打劫：向首在「北（坎）」时，北-中-南三宫向星成 147/258/369
# 
# 其他方位的三宫成 147/258/369 称为「假打劫」，威力次之。
# 严格区分是判断真假打劫的关键。

def detect_qixing_dajie_precise(combined: Dict[int, Dict[str, int]], facing_gua: str) -> Dict[str, Any]:
    """
    精确判定七星打劫：真打劫 / 假打劫 / 无。
    
    Args:
        combined: 本盘九宫
        facing_gua: 向首所属卦（决定是否为真打劫）
    """
    # 向盘星按方位提取
    DIR_TO_POS = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
    by_dir = {DIR_TO_POS[pos]: stars["facing"] for pos, stars in combined.items()}
    
    THREE_GENERAL = [{1,4,7}, {2,5,8}, {3,6,9}]
    
    # 离宫真打劫：南-中-北
    south_center_north = sorted([by_dir["南"], by_dir["中"], by_dir["北"]])
    set_scn = set(south_center_north)
    if set_scn in THREE_GENERAL:
        return {
            "type": "离宫真打劫",
            "is_real": True,
            "level": "auspicious_great",
            "stars": south_center_north,
            "directions": "南-中-北",
            "desc": f"离宫真打劫！南中北三宫向星成 {''.join(map(str,south_center_north))} 之局，乃玄空至贵格局，主三元不败、富贵绵长。",
            "source": "《天玉经》「南北八神共一卦」+《青囊奥语》「七星打劫」",
            "condition": f"向首在{facing_gua}卦，符合离宫之位" if facing_gua == "离" else f"向首在{facing_gua}（不在离宫），稍减威力",
        }
    
    # 坎宫真打劫：北-中-南（实际与离宫同向，但向首在坎位时论）
    if facing_gua == "坎" and set_scn in THREE_GENERAL:
        return {
            "type": "坎宫真打劫",
            "is_real": True,
            "level": "auspicious_great",
            "stars": south_center_north,
            "directions": "北-中-南",
            "desc": "坎宫真打劫！北中南三宫向星成三般卦，向首在坎，吉象大成。",
            "source": "《天玉经》《青囊奥语》",
        }
    
    # 假打劫修正：艮坤(2-5-8)向星恒成三般卦——此乃飞星「中宫线必差3」之数学必然
    # （顺逆飞中宫5与坤2、艮8恒差±3），非真格局，96/96 命盘皆「中」。旧版以 OTHER_TRIPLETS
    # 检 艮坤/震兑/巽乾，仅艮坤恒中、震兑巽乾恒不中，故每盘皆误报「艮坤假打劫·吉」并虚加 +1 分。
    # 正法七星打劫专论离-坎(南中北 1-5-9)线，已在上方判真打劫；此线不成三般即「无打劫」。
    return {"type": "无", "is_real": False, "level": "neutral", "desc": "无七星打劫格局（本盘向星未成离宫/坎宫打劫之局）。"}


# ─────────────────────────────────────────────────────────────
# 5. 收山出煞（形理配合）
# ─────────────────────────────────────────────────────────────

def analyze_shoushan_chusha(combined: Dict, sitting_luoshu: int, facing_luoshu: int,
                              current_yun: int) -> Dict[str, Any]:
    """
    收山出煞分析：
      - 当令山星到坐位见山 = 收山旺丁
      - 当令向星到向位见水 = 出煞旺财
      - 衰星到旺位反凶
    """
    sitting_mtn = combined[sitting_luoshu]["mountain"]
    sitting_fac = combined[sitting_luoshu]["facing"]
    facing_mtn = combined[facing_luoshu]["mountain"]
    facing_fac = combined[facing_luoshu]["facing"]
    
    items = []
    
    # 坐山方
    if sitting_mtn == current_yun:
        items.append({
            "type": "收山", "level": "auspicious_great",
            "desc": f"坐山方山星 {sitting_mtn} = 当令星，宜坐方见山实物（靠山墙、家具）以「收山旺丁」",
            "advice": "保持坐山方厚实有靠，忌动土凿空",
        })
    if sitting_fac == current_yun:
        items.append({
            "type": "向星到坐", "level": "mixed",
            "desc": f"坐山方向星 {sitting_fac} = 当令星，宜坐方见小水（鱼缸）而非大水",
            "advice": "可在坐方放小型流水或鱼缸",
        })
    
    # 向首方
    if facing_fac == current_yun:
        items.append({
            "type": "出煞", "level": "auspicious_great",
            "desc": f"向首方向星 {facing_fac} = 当令星，宜向方见水或开门以「出煞旺财」",
            "advice": "向首宜见水、低洼、街道、明堂开阔",
        })
    if facing_mtn == current_yun:
        items.append({
            "type": "山星到向", "level": "mixed",
            "desc": f"向首方山星 {facing_mtn} = 当令星，宜向方见小山而非大水",
            "advice": "向方宜见适当远山或建筑，忌纯水路冲射",
        })
    
    return {
        "items": items,
        "summary": "收山出煞" if items else "形理无特殊配合需求",
    }


# ─────────────────────────────────────────────────────────────
# 6. 替卦（兼向起星法）
# ─────────────────────────────────────────────────────────────
# 当坐向偏离正中线 ≥ 3° 但 < 6° 时，用替卦法（起星）排盘。
# 即山星 / 向星的入中星不取运星，改取「替星」。

# 替星表（兼向用，《沈氏玄空学·卷二·替卦口诀》正法）
# 替星口诀（沈氏正传）：
#   子癸并甲申，贪狼一路行。     → 子癸甲申 替贪狼 1
#   壬卯乙未坤，五位为巨门。     → 壬卯乙未坤 替巨门 2
#   乾亥辰巽巳，连戌武曲名。     → 乾亥辰巽巳戌 替武曲 6
#   酉辛丑艮丙，天上是破军。     → 酉辛丑艮丙 替破军 7
#   寅午庚丁上，右弼四星临。     → 寅午庚丁 替右弼 9
#   （未出现于上述口诀者，本宫不替）
TI_STAR_TABLE: Dict[str, int] = {
    # 贪狼 1：子、癸、甲、申
    "子": 1, "癸": 1, "甲": 1, "申": 1,
    # 巨门 2：壬、卯、乙、未、坤
    "壬": 2, "卯": 2, "乙": 2, "未": 2, "坤": 2,
    # 武曲 6：乾、亥、辰、巽、巳、戌
    "乾": 6, "亥": 6, "辰": 6, "巽": 6, "巳": 6, "戌": 6,
    # 破军 7：酉、辛、丑、艮、丙
    "酉": 7, "辛": 7, "丑": 7, "艮": 7, "丙": 7,
    # 右弼 9：寅、午、庚、丁
    "寅": 9, "午": 9, "庚": 9, "丁": 9,
}


def get_ti_star(mountain_name: str) -> int:
    """获取某山的替星（兼向用）。"""
    return TI_STAR_TABLE.get(mountain_name, 5)


def calculate_chart_type(degree: float, mountain_name: str) -> Dict[str, Any]:
    """
    根据坐山精确度数判定下卦/起星：
      - |deg - 山中心| < 3°：下卦（用运星入中）
      - 3° ≤ |deg - 山中心| < 6°：起星（用替星入中）
      - ≥ 6°：兼线太过，立向有误，须重新立向
    """
    # 计算山的中心度数（每山 15°）
    from core.fengshui.xuankong import TWENTY_FOUR_MOUNTAINS
    
    mtn = next((m for m in TWENTY_FOUR_MOUNTAINS if m["name"] == mountain_name), None)
    if not mtn:
        return {"type": "unknown", "valid": False}
    
    start = mtn["start"]
    end = mtn["end"]
    # 中心度数处理 0/360 跨越
    if start < end:
        center = (start + end) / 2
    else:
        center = ((start + end + 360) / 2) % 360
    
    # 度数差（最短角距离）
    diff = abs(degree - center)
    if diff > 180:
        diff = 360 - diff
    
    if diff < 3:
        return {"type": "下卦", "valid": True, "diff": diff,
                "desc": "正向（下卦），用运盘入中星起飞，最为标准。",
                "method": "use_yun_star"}
    elif diff < 6:
        return {"type": "起星（替卦）", "valid": True, "diff": diff,
                "desc": "兼向（起星），偏离中线 3-6°，须用替星法。",
                "method": "use_ti_star",
                "ti_star": get_ti_star(mountain_name)}
    else:
        return {"type": "兼线过度", "valid": False, "diff": diff,
                "desc": f"偏离中线 {diff:.1f}°，超过 6° 兼线，立向有误，须重新校准。",
                "method": "invalid"}


# ─────────────────────────────────────────────────────────────
# 7. 太岁刑冲坐山
# ─────────────────────────────────────────────────────────────

# 12 地支冲表
ZHI_CHONG = {"子":"午","丑":"未","寅":"申","卯":"酉","辰":"戌","巳":"亥",
             "午":"子","未":"丑","申":"寅","酉":"卯","戌":"辰","亥":"巳"}
# 三刑
ZHI_XING = {"寅":"巳", "巳":"申", "申":"寅",  # 无恩之刑
            "丑":"戌", "戌":"未", "未":"丑",  # 持势之刑
            "子":"卯", "卯":"子",  # 无礼之刑
            "辰":"辰", "午":"午", "酉":"酉", "亥":"亥"}  # 自刑

# 年份 → 干支（简易表，每 12 年循环）
def year_to_zhi(year: int) -> str:
    """年份转地支"""
    zhi_list = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    # 1984 = 甲子年
    offset = (year - 1984) % 12
    return zhi_list[offset]


def detect_taisui_conflict(year: int, sitting_mountain: str) -> Dict[str, Any]:
    """
    检测太岁刑冲坐山。
    
    若坐山地支 = 当年太岁，称「占太岁」（凶）
    若坐山地支冲太岁，称「冲太岁」（大凶）
    若坐山地支刑太岁，称「刑太岁」（凶）
    """
    taisui = year_to_zhi(year)
    
    # 仅地支山才有刑冲（壬甲丙庚是天干不论太岁）
    if sitting_mountain not in ZHI_CHONG:
        return {"has_conflict": False, "taisui": taisui}
    
    if sitting_mountain == taisui:
        return {
            "has_conflict": True, "taisui": taisui,
            "type": "占太岁",
            "level": "inauspicious",
            "desc": f"{year}年太岁{taisui}与坐山{sitting_mountain}同位，「占太岁」，主家有不安、宜静不宜动，忌大兴土木。",
            "remedy": "放化太岁锦囊、犯太岁符化解",
        }
    if ZHI_CHONG[sitting_mountain] == taisui:
        return {
            "has_conflict": True, "taisui": taisui,
            "type": "冲太岁",
            "level": "inauspicious_great",
            "desc": f"{year}年太岁{taisui}冲坐山{sitting_mountain}，「冲太岁」（岁破方），主大破、官非、健康损、家口不安。",
            "remedy": "绝对忌在坐山方动土、装修；佩戴太岁符；冲太岁年宜静守",
        }
    if ZHI_XING.get(sitting_mountain) == taisui:
        return {
            "has_conflict": True, "taisui": taisui,
            "type": "刑太岁",
            "level": "inauspicious",
            "desc": f"{year}年太岁{taisui}刑坐山{sitting_mountain}，「刑太岁」，主家中口舌、官非、是非缠身。",
            "remedy": "化解口舌符、避免诉讼",
        }
    
    return {"has_conflict": False, "taisui": taisui, "desc": f"{year}年太岁{taisui}与坐山{sitting_mountain}无刑冲，平安。"}


# ─────────────────────────────────────────────────────────────
# 8. 金龙四诀（《青囊奥语》「先看金龙动不动」）
# ─────────────────────────────────────────────────────────────
# 金龙四诀（蒋大鸿《地理辨正注》核心秘传之一）：
#   1. 看金龙——金龙者，当令之水。看水从何来何去，是否合元运
#   2. 一卦三山——24 山每三山一组（同卦），坐立同卦为「同元一气」
#   3. 阴阳交媾——坐山与朝向阴阳须互补（一阴一阳为正）
#   4. 父母三般卦——天父地母交媾，最贵之局
#
# 金龙诀的核心问：是否合「龙水交汇」？
# 龙 = 山势（高处/坐山方）
# 水 = 朝向（低处/明堂方）
# 当令山星到坐方有山实为「龙真」
# 当令向星到向方有水开阔为「水的」
# 两者皆备 = 龙真水的，富贵长久

def analyze_jinlong_juejue(combined: Dict[int, Dict[str, int]],
                              sitting_luoshu: int,
                              facing_luoshu: int,
                              current_yun: int,
                              sitting_yin_yang: str,
                              facing_yin_yang: str,
                              sitting_gua: str,
                              facing_gua: str) -> Dict[str, Any]:
    """
    金龙四诀完整分析（《青囊奥语》核心）
    """
    # 一、看金龙（当令水之去向）
    facing_dir_star = combined[facing_luoshu]["facing"]
    sitting_mtn_star = combined[sitting_luoshu]["mountain"]
    
    jin_long_dong = (sitting_mtn_star == current_yun) and (facing_dir_star == current_yun)
    
    # 二、一卦三山（坐向同元一气）
    GUA_GROUP = {
        "壬": "坎", "子": "坎", "癸": "坎",
        "丑": "艮", "艮": "艮", "寅": "艮",
        "甲": "震", "卯": "震", "乙": "震",
        "辰": "巽", "巽": "巽", "巳": "巽",
        "丙": "离", "午": "离", "丁": "离",
        "未": "坤", "坤": "坤", "申": "坤",
        "庚": "兑", "酉": "兑", "辛": "兑",
        "戌": "乾", "乾": "乾", "亥": "乾",
    }
    # 坐向都是一卦三山中的某山
    
    # 三、阴阳交媾
    yin_yang_jiao_gou = sitting_yin_yang != facing_yin_yang
    
    # 四、父母三般卦（天父地母同元）
    # 父母三般卦：1-4-7（坎巽兑）、2-5-8（坤中艮）、3-6-9（震乾离）
    # 已在 detect_special_patterns 中检测
    
    # 综合金龙诀评级
    items = []
    
    if jin_long_dong:
        items.append({
            "name": "金龙动（龙真水的）",
            "status": "auspicious_great",
            "desc": f"当令山星{current_yun}到坐方、向星{current_yun}到向方，「金龙动」之大吉，主丁财两旺、富贵长久。",
            "source": "《青囊奥语》「先看金龙动不动」",
        })
    else:
        items.append({
            "name": "金龙静",
            "status": "inauspicious" if not (sitting_mtn_star == current_yun or facing_dir_star == current_yun) else "mixed",
            "desc": "当令山向星未到位，金龙不动，气运迟滞。需配合形势化解。",
            "source": "《青囊奥语》",
        })
    
    if yin_yang_jiao_gou:
        items.append({
            "name": "阴阳交媾",
            "status": "auspicious",
            "desc": f"坐山{sitting_yin_yang}、向首{facing_yin_yang}，一阴一阳，阴阳得配，主生发。",
            "source": "《青囊奥语》「阴阳相见，福禄永贞」",
        })
    else:
        items.append({
            "name": "孤阴/孤阳",
            "status": "inauspicious",
            "desc": f"坐山向首皆为{sitting_yin_yang}，「孤阴不生、独阳不长」，主阴阳失调。",
            "source": "《青囊奥语》",
        })
    
    # 综合评级
    auspicious_count = sum(1 for it in items if it["status"].startswith("auspicious"))
    if auspicious_count == 2:
        verdict = "金龙四诀全合，蒋大鸿真传上吉之局"
        verdict_level = "auspicious_great"
    elif auspicious_count == 1:
        verdict = "金龙四诀部分合，须配合其他理气补救"
        verdict_level = "mixed"
    else:
        verdict = "金龙四诀失合，需重立向或化解"
        verdict_level = "inauspicious"
    
    return {
        "verdict": verdict,
        "verdict_level": verdict_level,
        "items": items,
        "jin_long_dong": jin_long_dong,
        "yin_yang_jiao_gou": yin_yang_jiao_gou,
        "source": "《青囊奥语》《地理辨正注》（蒋大鸿真传）",
    }


# ─────────────────────────────────────────────────────────────
# 流年方位辅参（文昌/病符/五黄/财位/是非/太岁/三煞）
#   用于阳宅三要等静态盘之「宅静时动」动态方位提示。
# ─────────────────────────────────────────────────────────────
_PALACE_DIR = {1: "正北", 2: "西南", 3: "正东", 4: "东南",
               5: "中宫", 6: "西北", 7: "正西", 8: "东北", 9: "正南"}
_ZHI_DIR = {"子": "正北", "丑": "东北", "寅": "东北", "卯": "正东",
            "辰": "东南", "巳": "东南", "午": "正南", "未": "西南",
            "申": "西南", "酉": "正西", "戌": "西北", "亥": "西北"}
_ZHI = "子丑寅卯辰巳午未申酉戌亥"


def get_annual_directions(year: int) -> dict:
    """流年方位辅参：据年紫白飞星 + 年支，定文昌/病符/五黄/财位/是非/喜庆/太岁/三煞之方。

    宅之门主灶为静（终身不易），然流年九星加临各方，吉凶之气一年一换，
    择吉用事（如安文昌助学、避五黄病符）须合此流年方位——是为静盘之动态辅参。
    """
    p2s = calculate_annual_flying(year)        # {宫:星}
    s2p = {star: pal for pal, star in p2s.items()}

    def _dir(star):
        return _PALACE_DIR.get(s2p.get(star), "")

    # 年支与三煞
    zhi = _ZHI[(year - 4) % 12]
    taisui = _ZHI_DIR.get(zhi, "")
    # 岁破 = 对冲（年支 +6）
    suipo = _ZHI_DIR.get(_ZHI[(_ZHI.index(zhi) + 6) % 12], "")
    # 三煞（三合局对冲方）
    if zhi in "申子辰":
        sansha = "正南"
    elif zhi in "寅午戌":
        sansha = "正北"
    elif zhi in "巳酉丑":
        sansha = "正东"
    else:                      # 亥卯未
        sansha = "正西"

    return {
        "year": year,
        "wenchang":  {"star": "四绿文昌", "dir": _dir(4), "use": "宜置书桌/文昌塔，助学业考试功名"},
        "caiwei":    {"star": "八白财星", "dir": _dir(8), "use": "宜动/开门/置保险柜，催财帛"},
        "xiqing":    {"star": "九紫喜庆", "dir": _dir(9), "use": "主婚喜添丁，宜喜事用此方"},
        "bingfu":    {"star": "二黑病符", "dir": _dir(2), "use": "忌动土久居，主疾病，宜静、置铜器化"},
        "wuhuang":   {"star": "五黄廉贞", "dir": _dir(5), "use": "大凶！忌动土修造，主灾病，宜静置金属化"},
        "shifei":    {"star": "三碧是非", "dir": _dir(3), "use": "主口舌官非，忌争吵，宜静"},
        "taisui":    {"dir": taisui, "use": f"{zhi}年太岁方，忌动土兴工，犯之主灾"},
        "suipo":     {"dir": suipo, "use": "岁破方（冲太岁），忌动土"},
        "sansha":    {"dir": sansha, "use": "三煞方，忌动土坐向，宜静"},
    }


def get_monthly_directions(year: int, month: int) -> dict:
    """流月方位辅参：流月紫白飞星定某月文昌/财位/病符/五黄等方；
    并标流月凶星叠流年凶星之方（双五黄/双病符 = 该月该方大凶，尤忌动土）。

    流年为「年之气」、流月为「月之气」——叠加方为该月最凶/最吉之向，
    择日择方精确到月，是静宅流年辅参之再细化。
    """
    m_fly = calculate_monthly_flying(year, month)      # {宫:星}
    a_fly = calculate_annual_flying(year)
    m_s2p = {s: p for p, s in m_fly.items()}
    a_s2p = {s: p for p, s in a_fly.items()}

    def _mdir(star):
        return _PALACE_DIR.get(m_s2p.get(star), "")

    # 叠加：流月凶星方 == 流年同凶星方 → 双星叠临
    def _overlap(star):
        return m_s2p.get(star) == a_s2p.get(star)

    overlaps = []
    if _overlap(5):
        overlaps.append(f"{_mdir(5)}（双五黄叠临·大凶，万勿动土修造）")
    if _overlap(2):
        overlaps.append(f"{_mdir(2)}（双病符叠临·主重病，忌久居动土）")
    if _overlap(3):
        overlaps.append(f"{_mdir(3)}（双三碧叠临·主官非口舌）")

    return {
        "year": year, "month": month,
        "wenchang": {"star": "四绿文昌", "dir": _mdir(4), "use": "本月宜此方读书办文"},
        "caiwei":   {"star": "八白财星", "dir": _mdir(8), "use": "本月催财动此方"},
        "xiqing":   {"star": "九紫喜庆", "dir": _mdir(9), "use": "本月喜事用此方"},
        "bingfu":   {"star": "二黑病符", "dir": _mdir(2), "use": "本月忌此方动土久居"},
        "wuhuang":  {"star": "五黄廉贞", "dir": _mdir(5), "use": "本月大凶方，忌动土"},
        "shifei":   {"star": "三碧是非", "dir": _mdir(3), "use": "本月忌此方争吵"},
        "overlaps": overlaps,                 # 流月叠流年凶星之方（最凶）
    }


# ─────────────────────────────────────────────────────────────
# 流时紫白（时家紫白·时白）——《沈氏玄空学·时白诀》
#   阳遁（冬至后→夏至前）顺行、阴遁（夏至后→冬至前）逆行；
#   日支三元定子时入中：子午卯酉日子时一白(阳)/九紫(阴)、
#   辰戌丑未日四绿/六白、寅申巳亥日七赤/三碧；逐时顺/逆推。
# ─────────────────────────────────────────────────────────────
_YANG_DUN_TERMS = {"冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
                   "春分", "清明", "谷雨", "立夏", "小满", "芒种"}
_ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"


def _is_yang_dun_zibai(dt) -> bool:
    """紫白阳遁/阴遁：冬至→夏至前为阳遁(顺)，夏至→冬至前为阴遁(逆)。"""
    from core.calendar.solar_terms import current_solar_term
    term = current_solar_term(dt) or ""
    return term in _YANG_DUN_TERMS


def get_hourly_zibai_center(dt) -> int:
    """流时紫白入中星。dt 须含时刻（hour）。"""
    from core.calendar.solar_terms import day_ganzhi_at
    yang = _is_yang_dun_zibai(dt)
    day_gz = day_ganzhi_at(dt)
    day_zhi = day_gz[1] if len(day_gz) >= 2 else "子"
    # 日支三元 → 子时入中
    if day_zhi in "子午卯酉":
        zi_center = 1 if yang else 9
    elif day_zhi in "辰戌丑未":
        zi_center = 4 if yang else 6
    else:                       # 寅申巳亥
        zi_center = 7 if yang else 3
    # 时辰 index（子=0…亥=11）
    from core.constants import hour_to_dizhi
    hour_zhi = hour_to_dizhi(dt.hour)
    h_idx = _ZHI_ORDER.index(hour_zhi)
    if yang:
        center = ((zi_center - 1 + h_idx) % 9) + 1
    else:
        center = ((zi_center - 1 - h_idx) % 9) + 1
    return center


def calculate_hourly_flying(dt) -> dict:
    """流时紫白九宫飞星（阳顺飞布，与年月同例）。返回 {宫:星}。"""
    center = get_hourly_zibai_center(dt)
    YANG_SEQ = [5, 6, 7, 8, 9, 1, 2, 3, 4]
    return {pal: ((center - 1 + i) % 9) + 1 for i, pal in enumerate(YANG_SEQ)}


def get_hourly_directions(dt) -> dict:
    """流时方位辅参：流时紫白定此时辰文昌/财位/五黄/病符方，精确择时择方。"""
    h_fly = calculate_hourly_flying(dt)
    s2p = {s: p for p, s in h_fly.items()}

    def _d(star):
        return _PALACE_DIR.get(s2p.get(star), "")

    from core.constants import hour_to_dizhi
    return {
        "hour_zhi": hour_to_dizhi(dt.hour),
        "center": get_hourly_zibai_center(dt),
        "wenchang": {"star": "四绿文昌", "dir": _d(4)},
        "caiwei":   {"star": "八白财星", "dir": _d(8)},
        "wuhuang":  {"star": "五黄廉贞", "dir": _d(5)},
        "bingfu":   {"star": "二黑病符", "dir": _d(2)},
    }


# ─────────────────────────────────────────────────────────────
# 流日紫白（日家紫白·三元日白）——《协纪辨方书·卷十一》
#   阳遁(冬至→夏至)顺行、阴遁(夏至→冬至)逆行；三元各以甲子日(符头)起锚星：
#   冬至一白·雨水七赤·谷雨四绿（阳三元）；夏至九紫·处暑三碧·霜降六白（阴三元）。
#   符头取离锚点节气最近之甲子日，自符头逐日顺/逆推。
# ─────────────────────────────────────────────────────────────
# (节气, 锚星, 是否阳遁)
_DAY_ANCHORS = [
    ("冬至", 1, True), ("雨水", 7, True), ("谷雨", 4, True),
    ("夏至", 9, False), ("处暑", 3, False), ("霜降", 6, False),
]


def _ganzhi_index_of(dt) -> int:
    """该日干支在六十甲子中的序号（甲子=0）。"""
    from core.calendar.ganzhi import _REF_DATE, _REF_DAY_IDX
    from datetime import date as _date
    d = dt.date() if hasattr(dt, "date") else dt
    return (_REF_DAY_IDX + (d - _REF_DATE).days) % 60


def _nearest_jiazi(anchor_dt):
    """离 anchor_dt 最近之甲子日（符头）。"""
    from datetime import timedelta
    idx = _ganzhi_index_of(anchor_dt)
    # 前一个甲子在 idx 天前，后一个在 (60-idx) 天后；取近者
    back = idx
    fwd = (60 - idx) % 60
    if fwd == 0:
        return anchor_dt
    if back <= fwd:
        return anchor_dt - timedelta(days=back)
    return anchor_dt + timedelta(days=fwd)


def get_daily_zibai_center(dt) -> int:
    """流日紫白入中星（三元日白法）。dt 为日期/时刻。"""
    from core.calendar.solar_terms import _get_solarterm_dt
    from datetime import timedelta
    d = dt
    # 收集本年及前后一年之六锚点 (符头日, 锚星, 阳遁)，取符头≤d 且最近者
    cands = []
    for yy in (d.year - 1, d.year, d.year + 1):
        for term, star, yang in _DAY_ANCHORS:
            try:
                tdt = _get_solarterm_dt(yy, term)
            except Exception:
                tdt = None
            if not tdt:
                continue
            futou = _nearest_jiazi(tdt)
            cands.append((futou, star, yang))
    # 符头日期 ≤ d 之最近者为当前元
    valid = [c for c in cands if (c[0].date() if hasattr(c[0], "date") else c[0]) <= (d.date() if hasattr(d, "date") else d)]
    if not valid:
        valid = cands
    futou, star, yang = max(valid, key=lambda c: (c[0].date() if hasattr(c[0], "date") else c[0]))
    days = ((d.date() if hasattr(d, "date") else d) - (futou.date() if hasattr(futou, "date") else futou)).days
    if yang:
        center = ((star - 1 + days) % 9) + 1
    else:
        center = ((star - 1 - days) % 9) + 1
    return center


def calculate_daily_flying(dt) -> dict:
    """流日紫白九宫飞星（阳顺飞布）。返回 {宫:星}。"""
    center = get_daily_zibai_center(dt)
    YANG_SEQ = [5, 6, 7, 8, 9, 1, 2, 3, 4]
    return {pal: ((center - 1 + i) % 9) + 1 for i, pal in enumerate(YANG_SEQ)}


def get_daily_directions(dt) -> dict:
    """流日方位辅参：流日紫白定某日文昌/财位/五黄/病符方。"""
    fly = calculate_daily_flying(dt)
    s2p = {s: p for p, s in fly.items()}

    def _d(star):
        return _PALACE_DIR.get(s2p.get(star), "")
    return {
        "center": get_daily_zibai_center(dt),
        "wenchang": {"star": "四绿文昌", "dir": _d(4)},
        "caiwei":   {"star": "八白财星", "dir": _d(8)},
        "wuhuang":  {"star": "五黄廉贞", "dir": _d(5)},
        "bingfu":   {"star": "二黑病符", "dir": _d(2)},
    }
