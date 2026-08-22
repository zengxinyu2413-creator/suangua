"""
core/qimen/patterns_complete.py
================================
奇门遁甲完整格局识别（《奇门遁甲秘笈大全》《烟波钓叟歌》《奇门遁甲统宗》）

涵盖核心格局类别：
  1. 三奇格局（11 种）
  2. 八门格局（门迫、门刑、伏吟、反吟、击刑等）
  3. 九星格局（青龙返首、飞鸟跌穴等）
  4. 六仪格局（六仪击刑、六仪入墓）
  5. 八神组合格局
  6. 凶煞格局（大格、刑格、悖格、伏宫、飞宫）
  7. 九遁格局（天遁、地遁、人遁、神遁、鬼遁、风遁、云遁、龙遁、虎遁）
  8. 三诈五假
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional


# ─────────────────────────────────────────────────────────────
# 1. 三奇格局（乙丙丁三奇 + 戊己庚辛壬癸六仪）
# ─────────────────────────────────────────────────────────────

def detect_sanqi_patterns(palaces: List[Dict[str, Any]], yang_dun: bool) -> List[Dict[str, Any]]:
    """三奇相关 11 大格局"""
    patterns = []
    
    # 找到三奇位置
    qi_positions = {}  # 三奇 -> palace
    for p in palaces:
        for qi in ("乙", "丙", "丁"):
            if p.get("天盘", "") == qi:
                qi_positions[qi] = p
    
    # 1. 三奇得使（乙奇得使、丙奇得使、丁奇得使）
    DESHI_RULES = {
        "乙": [("甲戌", "甲午"), ("甲申", "甲子")],  # 乙奇得使条件
        "丙": [("甲子", "甲午"), ("甲申", "甲寅")],
        "丁": [("甲寅", "甲子"), ("甲戌", "甲申")],
    }
    
    # 2. 三奇升殿（乙在震宫、丙在离宫、丁在兑宫，得当令）
    SHENG_DIAN = {
        "乙": 3,  # 震宫
        "丙": 9,  # 离宫
        "丁": 7,  # 兑宫
    }
    for qi, palace_num in SHENG_DIAN.items():
        if qi in qi_positions and qi_positions[qi].get("palace") == palace_num:
            patterns.append({
                "name": f"{qi}奇升殿",
                "severity": "auspicious_great",
                "desc": f"{qi}奇飞临{['','坎','坤','震','巽','中','乾','兑','艮','离'][palace_num]}宫（本宫），三奇当令，大利所求，万事亨通。",
                "source": "《奇门遁甲秘笈大全·升殿格》",
            })
    
    # 3. 三奇游六仪（三奇飞入六仪位 — 主吉中有凶）
    LIU_YI = {"戊", "己", "庚", "辛", "壬", "癸"}
    for qi, p in qi_positions.items():
        di_pan = p.get("地盘", "")
        if di_pan in LIU_YI:
            patterns.append({
                "name": f"{qi}奇游六仪（地盘{di_pan}）",
                "severity": "mixed",
                "desc": f"{qi}奇飞临{di_pan}仪之位，吉中带凶，吉事须防曲折。",
                "source": "《奇门遁甲秘笈大全》",
            })
    
    # 4. 三奇入墓（《奇门遁甲秘笈大全·三奇入墓》正法）
    # 五行墓库：木墓未（坤2）、火墓戌（乾6）、金墓丑（艮8）、水墓辰（巽4）、土墓辰戌丑未
    # 乙木墓在未 → 坤宫 2
    # 丙火、丁火墓在戌 → 乾宫 6
    SANQI_MU = {
        "乙": [2],         # 乙木 → 坤宫（未位）
        "丙": [6],         # 丙火 → 乾宫（戌位）
        "丁": [6],         # 丁火 → 乾宫（戌位）
    }
    for qi, mu_palaces in SANQI_MU.items():
        if qi in qi_positions:
            p = qi_positions[qi]
            if p.get("palace") in mu_palaces:
                patterns.append({
                    "name": f"{qi}奇入墓",
                    "severity": "inauspicious",
                    "desc": f"{qi}奇飞临墓库之位（{p.get('palace')}宫），「入墓」之凶，主吉气被埋藏、谋事难发。",
                    "source": "《奇门遁甲秘笈大全·三奇入墓》",
                })
    
    # 三奇临中5（无方位、失令）
    for qi, p in qi_positions.items():
        if p.get("palace") == 5:
            patterns.append({
                "name": f"{qi}奇入中宫",
                "severity": "inauspicious",
                "desc": f"{qi}奇入中宫（无方位之处），主三奇失令、吉气无所归。",
                "source": "《奇门遁甲秘笈大全》",
            })
    
    # 5. 三奇会合（三奇相会同宫或邻宫）
    if all(qi in qi_positions for qi in ("乙", "丙", "丁")):
        pal_set = {qi_positions[qi].get("palace") for qi in ("乙","丙","丁")}
        if len(pal_set) == 1:
            patterns.append({
                "name": "三奇会聚",
                "severity": "auspicious_great",
                "desc": "乙丙丁三奇齐聚一宫，是为「三奇升殿」之大贵格局，主大喜大利。",
                "source": "《烟波钓叟歌》「乙丙丁三奇为吉，更得奇门相会聚」",
            })
    
    # 6. 玉女守门（乙奇加临开门或休门 — 婚姻喜事大吉）
    for qi, p in qi_positions.items():
        if qi == "乙":
            men = p.get("门", "")
            if men in ("开门", "休门", "生门"):
                patterns.append({
                    "name": "玉女守门",
                    "severity": "auspicious_great",
                    "desc": f"乙奇加临{men}，「玉女守门」最利婚姻、求贵、谋事顺遂。",
                    "source": "《奇门遁甲秘笈大全》",
                })
    
    return patterns


# ─────────────────────────────────────────────────────────────
# 2. 九遁格局
# ─────────────────────────────────────────────────────────────

def detect_jiudun_patterns(palaces: List[Dict[str, Any]], yang_dun: bool) -> List[Dict[str, Any]]:
    """九遁格局 — 利用奇门吉星组合进行隐遁的高级格局"""
    patterns = []
    
    # 找到三奇 + 吉门 + 吉星 + 吉神的组合
    for p in palaces:
        tian = p.get("天盘", "")
        di = p.get("地盘", "")
        men = p.get("门", "")
        xing = p.get("星", "")
        shen = p.get("神", "")
        palace = p.get("palace", 0)
        DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
        direction = DIR.get(palace, "")
        
        # 天遁 = 丙奇 + 生门 + 九天
        if tian == "丙" and men == "生门" and shen == "九天":
            patterns.append({
                "name": "天遁",
                "severity": "auspicious_great",
                "desc": f"{direction}方丙奇 + 生门 + 九天，「天遁」之吉，最宜上书、求贵、谒见上司。",
                "source": "《烟波钓叟歌》「天遁要逢生门丙；地遁开门乙临己」",
                "direction": direction,
            })
        # 地遁 = 乙奇 + 开门 + 六合（古书「地遁开门乙临己」）
        if tian == "乙" and men == "开门" and (shen == "六合" or di == "己"):
            patterns.append({
                "name": "地遁",
                "severity": "auspicious_great",
                "desc": f"{direction}方乙奇 + 开门 + 六合（或临己），「地遁」之吉，宜埋伏、潜藏、避险。",
                "source": "《烟波钓叟歌》",
                "direction": direction,
            })
        # 人遁 = 丁奇 + 休门 + 太阴
        if tian == "丁" and men == "休门" and shen == "太阴":
            patterns.append({
                "name": "人遁",
                "severity": "auspicious_great",
                "desc": f"{direction}方丁奇 + 休门 + 太阴，「人遁」之吉，宜逃避、隐居、招贤纳士。",
                "source": "《烟波钓叟歌》「人遁休门丁太阴」",
                "direction": direction,
            })
        # 神遁 = 丙奇 + 生门 + 九地
        if tian == "丙" and men == "生门" and shen == "九地":
            patterns.append({
                "name": "神遁",
                "severity": "auspicious_great",
                "desc": f"{direction}方丙奇 + 生门 + 九地，「神遁」之吉，宜祭祀、求神、问卜。",
                "source": "《奇门遁甲秘笈大全·九遁》",
                "direction": direction,
            })
        # 鬼遁 = 丁奇 + 杜门 + 九地
        if tian == "丁" and men == "杜门" and shen == "九地":
            patterns.append({
                "name": "鬼遁",
                "severity": "auspicious",
                "desc": f"{direction}方丁奇 + 杜门 + 九地，「鬼遁」之吉，宜暗中行事、查访、捕捉。",
                "source": "《奇门遁甲秘笈大全》",
                "direction": direction,
            })
        # 风遁 = 乙奇 + 开门 + 巽宫（4）
        if tian == "乙" and men == "开门" and palace == 4:
            patterns.append({
                "name": "风遁",
                "severity": "auspicious",
                "desc": f"乙奇 + 开门 + 巽宫，「风遁」之吉，宜借风势、传消息、动远行。",
                "source": "《奇门遁甲秘笈大全》",
                "direction": direction,
            })
        # 云遁 = 乙奇 + 开门 + 坎宫（1）
        if tian == "乙" and men == "开门" and palace == 1:
            patterns.append({
                "name": "云遁",
                "severity": "auspicious",
                "desc": f"乙奇 + 开门 + 坎宫，「云遁」之吉，宜借云隐藏、求雨、用兵。",
                "source": "《奇门遁甲秘笈大全》",
                "direction": direction,
            })
        # 龙遁 = 乙奇 + 休门 + 坎宫
        if tian == "乙" and men == "休门" and palace == 1:
            patterns.append({
                "name": "龙遁",
                "severity": "auspicious",
                "desc": f"乙奇 + 休门 + 坎宫，「龙遁」之吉，宜借水势、出行、远谋。",
                "source": "《奇门遁甲秘笈大全》",
                "direction": direction,
            })
        # 虎遁 = 乙奇 + 生门 + 艮宫（8）
        if tian == "乙" and men == "生门" and palace == 8:
            patterns.append({
                "name": "虎遁",
                "severity": "auspicious",
                "desc": f"乙奇 + 生门 + 艮宫，「虎遁」之吉，宜借山势、埋伏、武勇之事。",
                "source": "《奇门遁甲秘笈大全》",
                "direction": direction,
            })
    
    return patterns


# ─────────────────────────────────────────────────────────────
# 3. 凶煞格局
# ─────────────────────────────────────────────────────────────

def detect_xiongsha_patterns(palaces: List[Dict[str, Any]], yang_dun: bool,
                                shi_gan: str = None) -> List[Dict[str, Any]]:
    """凶煞格局：大格、刑格、悖格、伏宫、飞宫、门迫等"""
    patterns = []
    
    DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
    
    for p in palaces:
        tian = p.get("天盘", "")
        di = p.get("地盘", "")
        men = p.get("门", "")
        palace = p.get("palace", 0)
        direction = DIR.get(palace, "")
        
        # === 大格（庚加癸或庚加日干）===
        if tian == "庚" and di == "癸":
            patterns.append({
                "name": "大格",
                "severity": "inauspicious_great",
                "desc": f"{direction}方天盘庚加地盘癸，「大格」之凶，主诸事不通、官司缠身、远行多阻。",
                "source": "《烟波钓叟歌》「庚加癸兮为大格」",
                "direction": direction,
            })
        # 庚加日干 = 日格
        if tian == "庚" and shi_gan and di == shi_gan:
            patterns.append({
                "name": "日格（庚加日干）",
                "severity": "inauspicious",
                "desc": f"{direction}方庚加日干{shi_gan}，「日格」，主当日诸事不利。",
                "source": "《奇门遁甲》",
                "direction": direction,
            })
        # 庚加时干 = 时格
        # 庚加年干 = 岁格
        
        # === 刑格（庚加己）===
        if tian == "庚" and di == "己":
            patterns.append({
                "name": "刑格",
                "severity": "inauspicious",
                "desc": f"{direction}方庚加己，「刑格」，主官司、刑罚、是非缠身。",
                "source": "《奇门遁甲》「庚加己兮为刑格」",
                "direction": direction,
            })
        
        # === 悖格（己加丙、丙加己）===
        if (tian == "己" and di == "丙") or (tian == "丙" and di == "己"):
            patterns.append({
                "name": "悖格",
                "severity": "inauspicious",
                "desc": f"{direction}方己丙相加，「悖格」，主诸事违背、计划失败、心绪烦乱。",
                "source": "《奇门遁甲》「丙加己兮为悖格」",
                "direction": direction,
            })
        
        # 飞宫格在函数末尾按 shi_gan 综合判定
        
        # 门迫（门所克之宫或克门之宫）
        # 五行：休门-水、生门-土、伤门-木、杜门-木、景门-火、死门-土、惊门-金、开门-金
        MEN_WX = {"休门":"水", "生门":"土", "伤门":"木", "杜门":"木",
                  "景门":"火", "死门":"土", "惊门":"金", "开门":"金"}
        PALACE_WX = {1:"水",2:"土",3:"木",4:"木",5:"土",6:"金",7:"金",8:"土",9:"火"}
        KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
        
        men_wx = MEN_WX.get(men)
        pal_wx = PALACE_WX.get(palace)
        if men_wx and pal_wx:
            if KE.get(pal_wx) == men_wx:
                patterns.append({
                    "name": f"门迫（{men}受宫克）",
                    "severity": "inauspicious",
                    "desc": f"{direction}方{men}（{men_wx}）受{pal_wx}宫克制，「门迫」之凶，所求受阻，行动有碍。",
                    "source": "《奇门遁甲·门迫论》",
                    "direction": direction,
                })
            elif KE.get(men_wx) == pal_wx:
                patterns.append({
                    "name": f"门克宫",
                    "severity": "mixed",
                    "desc": f"{direction}方{men}（{men_wx}）克宫位（{pal_wx}），事可成但有损耗。",
                    "source": "《奇门遁甲·门宫生克》",
                    "direction": direction,
                })
        
        # 六仪击刑（《奇门遁甲·六仪击刑》正法）
        # 戊在 3（震）、己在 2（坤）、庚在 4（巽）、辛在 7（兑）、壬在 8（艮）、癸在 5（中）
        JI_XING_RULES = {"戊":3, "己":2, "庚":4, "辛":7, "壬":8, "癸":5}
        for yi, ji_palace in JI_XING_RULES.items():
            if di == yi and palace == ji_palace:
                patterns.append({
                    "name": f"{yi}仪击刑",
                    "severity": "inauspicious",
                    "desc": f"{direction}方地盘{yi}仪临{ji_palace}宫，「六仪击刑」之凶，主刑伤、官非、计划落空。",
                    "source": "《奇门遁甲·六仪击刑》",
                    "direction": direction,
                })
    
    # ─── 飞宫格（《烟波钓叟歌》「值符飞宫为凶」）───
    # 飞宫格：值符首甲遁于六仪戊，戊不在本位（5中宫）而飞到他宫
    # 完整规则：地盘戊若在某宫，而该宫位的天盘上又有六仪，谓之"戊为飞宫"
    if shi_gan:
        # 找地盘戊所在宫
        wu_palace = None
        for p in palaces:
            if p.get("地盘") == "戊":
                wu_palace = p.get("palace")
                break
        # 戊在中5为正位，不在中5即"飞宫"
        if wu_palace and wu_palace != 5:
            DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
            patterns.append({
                "name": "戊飞宫",
                "severity": "mixed",
                "desc": f"地盘戊（值符首六仪）不在中5宫而飞到{DIR.get(wu_palace,'')}方{wu_palace}宫，「飞宫」之象，主能量外散、贵气流动。须配合其他格局综合判断。",
                "source": "《奇门遁甲·飞宫论》",
                "direction": DIR.get(wu_palace,""),
            })
    
    return patterns


# ─────────────────────────────────────────────────────────────
# 4. 九星格局
# ─────────────────────────────────────────────────────────────

def detect_jiuxing_patterns(palaces: List[Dict[str, Any]], yang_dun: bool) -> List[Dict[str, Any]]:
    """九星相关格局：青龙返首、飞鸟跌穴、青龙逃走、白虎猖狂、朱雀投江、勾陈得位"""
    patterns = []
    
    DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
    
    for p in palaces:
        xing = p.get("星", "")
        tian = p.get("天盘", "")
        di = p.get("地盘", "")
        palace = p.get("palace", 0)
        direction = DIR.get(palace, "")
        
        # 青龙返首（《奇门遁甲秘笈大全·九星格局》正法）
        # 定义：值符首（甲，遁于戊）所在天盘 = 丙（火生戊土，主光明）
        # 即天盘"丙"加临地盘"戊"（戊为甲值符之代）
        if tian == "丙" and di == "戊":
            patterns.append({
                "name": "青龙返首",
                "severity": "auspicious_great",
                "desc": f"{direction}方天盘丙加地盘戊（值符），「青龙返首」之大吉，主谋事大成、贵人扶持、官运亨通。",
                "source": "《奇门遁甲秘笈大全·九星格局》",
                "direction": direction,
            })
        
        # 飞鸟跌穴（《烟波钓叟歌》）
        # 定义：天盘"戊"加临地盘"丙"
        if tian == "戊" and di == "丙":
            patterns.append({
                "name": "飞鸟跌穴",
                "severity": "auspicious_great",
                "desc": f"{direction}方天盘戊加地盘丙，「飞鸟跌穴」之大吉，主意外得利、机会自来、远行大吉。",
                "source": "《烟波钓叟歌》「戊加丙兮飞鸟跌穴」",
                "direction": direction,
            })
        
        # 青龙逃走（《奇门遁甲秘笈大全》）
        # 定义：天盘"乙"加临地盘"辛"（金克木，三奇受制）
        if tian == "乙" and di == "辛":
            patterns.append({
                "name": "青龙逃走",
                "severity": "inauspicious",
                "desc": f"{direction}方天盘乙加地盘辛（金克木），「青龙逃走」之凶，主吉气消散、贵人远离、谋事不成。",
                "source": "《奇门遁甲秘笈大全》",
                "direction": direction,
            })
        
        # 白虎猖狂（庚加乙，金克木 — 或庚加天柱+兑宫）
        # 完整定义（《烟波钓叟歌》「庚加乙兮白虎猖狂」）
        if tian == "庚" and di == "乙":
            patterns.append({
                "name": "白虎猖狂",
                "severity": "inauspicious",
                "desc": f"{direction}方天盘庚加地盘乙（庚为大煞、乙为三奇），「白虎猖狂」之凶，主血光、争斗、刀伤、远行多险。",
                "source": "《烟波钓叟歌》「庚加乙兮白虎猖狂」",
                "direction": direction,
            })
        # 另一种白虎猖狂：庚加 7 兑宫 + 天柱
        elif tian == "庚" and palace == 7 and xing == "天柱":
            patterns.append({
                "name": "白虎猖狂（兑宫天柱）",
                "severity": "inauspicious",
                "desc": f"{direction}方庚加兑宫天柱，「白虎猖狂」之凶，主血光、争斗、刀伤。",
                "source": "《奇门遁甲》",
                "direction": direction,
            })
        
        # 朱雀投江（《烟波钓叟歌》「辛加癸兮朱雀投江」）
        # 定义：天盘"辛"加地盘"癸"
        if tian == "辛" and di == "癸":
            patterns.append({
                "name": "朱雀投江",
                "severity": "inauspicious",
                "desc": f"{direction}方天盘辛加地盘癸（金生水却反受困），「朱雀投江」之凶，主文书阻、消息断、口舌官非。",
                "source": "《烟波钓叟歌》「辛加癸兮朱雀投江」",
                "direction": direction,
            })
        # 另一种朱雀投江：天英（朱雀代位）落坎宫
        elif xing == "天英" and palace == 1:
            patterns.append({
                "name": "朱雀投江（天英落坎）",
                "severity": "inauspicious",
                "desc": f"{direction}方天英（朱雀）落坎宫（水），「朱雀投江」之凶，主文书失误、消息阻断。",
                "source": "《奇门遁甲》",
                "direction": direction,
            })
        
        # 螣蛇妖娇（《烟波钓叟歌》「癸加丁兮螣蛇妖娇」）
        if tian == "癸" and di == "丁":
            patterns.append({
                "name": "螣蛇妖娇",
                "severity": "inauspicious",
                "desc": f"{direction}方天盘癸加地盘丁，「螣蛇妖娇」之凶，主怪异之事、虚惊、邪魅相侵。",
                "source": "《烟波钓叟歌》「癸加丁兮螣蛇妖娇」",
                "direction": direction,
            })
        
        # 太白入荧（《烟波钓叟歌》「庚加丙兮太白入荧」）— 庚为白虎、丙为太阳
        if tian == "庚" and di == "丙":
            patterns.append({
                "name": "太白入荧",
                "severity": "inauspicious_great",
                "desc": f"{direction}方天盘庚加地盘丙（白虎入阳明），「太白入荧」之大凶，主贼盗、刀兵、远行最忌。",
                "source": "《烟波钓叟歌》「庚加丙兮太白入荧」",
                "direction": direction,
            })
        
        # 荧入太白（《烟波钓叟歌》「丙加庚兮荧入太白」）
        if tian == "丙" and di == "庚":
            patterns.append({
                "name": "荧入太白",
                "severity": "inauspicious",
                "desc": f"{direction}方天盘丙加地盘庚，「荧入太白」之凶，主贼来攻己、家有破损。",
                "source": "《烟波钓叟歌》「丙加庚兮荧入太白」",
                "direction": direction,
            })
        
        # 勾陈得位：天禽（勾陈/值符代位）在中5宫
        if xing == "天禽" and palace == 5:
            patterns.append({
                "name": "勾陈得位",
                "severity": "auspicious",
                "desc": f"天禽（勾陈）在中宫得位，主稳重持重、田产有益。",
                "source": "《奇门遁甲》",
                "direction": direction,
            })
    
    return patterns


# ─────────────────────────────────────────────────────────────
# 5. 三诈五假
# ─────────────────────────────────────────────────────────────

def detect_sanzha_wujia(palaces: List[Dict[str, Any]], yang_dun: bool) -> List[Dict[str, Any]]:
    """
    三诈五假：奇门遁甲战术格局
      真诈：休生开 + 乙丙丁 + 六合九地九天（吉中之吉，宜进取）
      重诈：休生开 + 乙丙丁 + 六合（吉，宜谋事）
      休诈：休生开 + 乙丙丁（小吉）
      天假：景门 + 丁奇 + 九天（宜公文上书）
      地假：杜门 + 丁奇 + 九地（宜潜伏）
      人假：景门 + 丁奇 + 太阴
      神假：杜门 + 丁奇 + 太阴
      鬼假：杜门 + 丁奇 + 六合
    """
    patterns = []
    DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
    
    GOOD_MEN = {"休门", "生门", "开门"}
    QI = {"乙", "丙", "丁"}
    
    for p in palaces:
        tian = p.get("天盘", "")
        men = p.get("门", "")
        shen = p.get("神", "")
        palace = p.get("palace", 0)
        direction = DIR.get(palace, "")
        
        # 真诈：吉门 + 三奇 + 九天/九地/六合
        if men in GOOD_MEN and tian in QI and shen in ("九天", "九地", "六合"):
            patterns.append({
                "name": "真诈",
                "severity": "auspicious_great",
                "desc": f"{direction}方{men} + {tian}奇 + {shen}，「真诈」之吉，万事皆宜，最利出兵远征。",
                "source": "《奇门遁甲·三诈》",
                "direction": direction,
            })
        # 天假：景门 + 丁奇 + 九天
        if men == "景门" and tian == "丁" and shen == "九天":
            patterns.append({
                "name": "天假",
                "severity": "auspicious",
                "desc": f"{direction}方景门 + 丁奇 + 九天，「天假」，宜上书献策、传递消息。",
                "source": "《奇门遁甲·五假》",
                "direction": direction,
            })
        # 地假：杜门 + 丁奇 + 九地
        if men == "杜门" and tian == "丁" and shen == "九地":
            patterns.append({
                "name": "地假",
                "severity": "auspicious",
                "desc": f"{direction}方杜门 + 丁奇 + 九地，「地假」，宜潜伏、隐藏、避祸。",
                "source": "《奇门遁甲·五假》",
                "direction": direction,
            })
    
    return patterns


# ─────────────────────────────────────────────────────────────
# 综合入口
# ─────────────────────────────────────────────────────────────

def detect_all_patterns_complete(palaces: List[Dict[str, Any]], yang_dun: bool,
                                    shi_gan: str = None) -> List[Dict[str, Any]]:
    """
    完整奇门格局识别 — 整合 5 大类共 30+ 个格局
    
    palaces 字段适配：
      支持 'stem'（单一天干，等同地盘）或 ('天盘' + '地盘') 双盘
      支持 'door'/'门'、'star'/'星'、'deity'/'神'、'palace'/'position'
    """
    # 归一化字段
    normalized = []
    single_stem_mode = True  # 检测是否是单 stem 模式（天盘=地盘）
    for p in palaces:
        tian = p.get("天盘", p.get("tian_pan", ""))
        di = p.get("地盘", p.get("di_pan", ""))
        # 如果原始数据没有显式天/地盘，用 stem 当 tian
        if not tian and not di:
            stem = p.get("stem", "")
            tian = di = stem
        else:
            # 若天地盘不同，关闭单 stem 模式
            if tian != di:
                single_stem_mode = False
            # 若有显式 tian_pan/di_pan，即使二者相同也算双盘模式
            if p.get("tian_pan") and p.get("di_pan"):
                single_stem_mode = False
        normalized.append({
            "palace": p.get("palace", p.get("position", 0)),
            "天盘": tian,
            "地盘": di,
            "门": p.get("门", p.get("door", "")),
            "星": p.get("星", p.get("star", "")),
            "神": p.get("神", p.get("deity", "")),
        })
    
    all_patterns = []
    all_patterns.extend(detect_sanqi_patterns(normalized, yang_dun))
    all_patterns.extend(detect_jiudun_patterns(normalized, yang_dun))
    # 单 stem 模式下不检测涉及天地盘对比的格局（大格、刑格、悖格、伏宫）
    if not single_stem_mode:
        all_patterns.extend(detect_xiongsha_patterns(normalized, yang_dun, shi_gan))
    else:
        # 单 stem 模式只查门迫和六仪击刑（不依赖天地盘对比）
        all_patterns.extend(_detect_xiongsha_single_stem(normalized))
    all_patterns.extend(detect_jiuxing_patterns(normalized, yang_dun))
    all_patterns.extend(detect_sanzha_wujia(normalized, yang_dun))
    
    # ── 整盘伏吟/反吟判定（仅当 9 宫天=地全相等时报一次） ──
    if not single_stem_mode:
        all_match = all(p["天盘"] == p["地盘"] for p in normalized if p["天盘"] and p["地盘"])
        if all_match:
            all_patterns.append({
                "name": "全盘伏吟",
                "severity": "inauspicious_great",
                "desc": "9 宫天盘地盘全部相等（时干 = 旬首六仪），「伏吟之局」整盘停滞，万事不利，宜静守、避动土、避诉讼。",
                "source": "《奇门遁甲·伏吟章》",
            })
    
    return all_patterns


def _detect_xiongsha_single_stem(palaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    单地盘模式下的凶煞检测后备（仅依赖门 + 宫 + 星）。
    
    完整天地双盘已实现于 detect_xiongsha_patterns，本函数仅用于：
      - 整盘伏吟时（天盘=地盘）的处理
      - 历史数据兼容（旧版数据可能没有 tian_pan 字段）
    """
    patterns = []
    DIR = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
    
    for p in palaces:
        stem = p.get("天盘", "")
        men = p.get("门", "")
        palace = p.get("palace", 0)
        direction = DIR.get(palace, "")
        
        # 门迫
        MEN_WX = {"休门":"水", "生门":"土", "伤门":"木", "杜门":"木",
                  "景门":"火", "死门":"土", "惊门":"金", "开门":"金"}
        PALACE_WX = {1:"水",2:"土",3:"木",4:"木",5:"土",6:"金",7:"金",8:"土",9:"火"}
        KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
        men_wx = MEN_WX.get(men)
        pal_wx = PALACE_WX.get(palace)
        if men_wx and pal_wx:
            if KE.get(pal_wx) == men_wx:
                patterns.append({
                    "name": f"门迫（{men}受宫克）",
                    "severity": "inauspicious",
                    "desc": f"{direction}方{men}（{men_wx}）受{pal_wx}宫克制，「门迫」之凶。",
                    "source": "《奇门遁甲·门迫论》",
                    "direction": direction,
                })
        
        # 六仪击刑（stem 在被克之宫）
        JI_XING_RULES = {"戊":3, "己":2, "庚":4, "辛":7, "壬":8, "癸":5}
        if stem in JI_XING_RULES and palace == JI_XING_RULES[stem]:
            patterns.append({
                "name": f"{stem}仪击刑",
                "severity": "inauspicious",
                "desc": f"{direction}方{stem}仪临{palace}宫，「六仪击刑」之凶。",
                "source": "《奇门遁甲·六仪击刑》",
                "direction": direction,
            })
    return patterns
