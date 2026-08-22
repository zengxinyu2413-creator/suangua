"""
core/bazi/tiaohou_yongshen.py
==============================
调候用神完整表 (10 干 × 12 月) + 子平真诠 8 格局成败救应

源出处：
  - 《穷通宝鉴》（明·余春台）— 调候用神之根本
  - 《子平真诠》（清·沈孝瞻）— 格局成败救应之根本
  - 任铁樵《滴天髓阐微》— 综合断验
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional


# ─────────────────────────────────────────────────────────────
# 1. 调候用神表（《穷通宝鉴》核心）
# 每个日干 × 12 月的最佳调候用神组合
# ─────────────────────────────────────────────────────────────

TIAOHOU_TABLE: Dict[str, Dict[str, Dict[str, Any]]] = {
    "甲": {
        "寅": {"primary":"丙", "secondary":"癸", "desc":"正月甲木初春寒气未退，丙火解冻为急，癸水滋润为次。",
                "advice":"丙癸两透，富贵双全；丙透癸藏，名贵显达；癸透丙藏，文人雅士。"},
        "卯": {"primary":"庚", "secondary":"丙", "secondary2":"丁", "desc":"二月甲木阳壮木渴，庚金劈甲引丁助火生发。",
                "advice":"庚透丁透，富贵之命；庚藏丁明，文章秀气。"},
        "辰": {"primary":"庚", "secondary":"壬", "desc":"三月甲木气退，土厚而气泄，庚金劈甲，壬水生扶。",
                "advice":"庚壬两透，少年登科；庚透壬藏，富中取贵。"},
        "巳": {"primary":"癸", "secondary":"丁", "secondary2":"庚", "desc":"四月甲木气退火炎，癸水救焚为急。",
                "advice":"癸丁庚三透，大富大贵；癸透有救，但忌火多木焚。"},
        "午": {"primary":"癸", "secondary":"丁", "secondary2":"庚", "desc":"五月甲木丁旺，木性虚焦，癸水为急。",
                "advice":"癸水不可缺，缺则贫贱；癸丁齐透，富贵双全。"},
        "未": {"primary":"癸", "secondary":"丁", "secondary2":"庚", "desc":"六月甲木根枯叶燥，三伏生寒，癸丁庚配。",
                "advice":"癸丁庚三透为上格；癸水独透亦富。"},
        "申": {"primary":"庚", "secondary":"丁", "secondary2":"壬", "desc":"七月甲木已凉，金气当令，庚金劈甲引丁。",
                "advice":"庚丁两透，威武刚毅；丁火配甲，富贵显达。"},
        "酉": {"primary":"庚", "secondary":"丁", "secondary2":"丙", "desc":"八月甲木气衰，丁火制庚，丙火暖身。",
                "advice":"丁庚两透，富贵之兆；缺丁则平庸。"},
        "戌": {"primary":"庚", "secondary":"甲", "secondary2":"丁", "desc":"九月甲木气衰土厚，庚金为用，甲木比助。",
                "advice":"庚甲齐透为吉；土厚埋金则寒。"},
        "亥": {"primary":"庚", "secondary":"丁", "secondary2":"丙", "desc":"十月甲木寒气欲冷，丁火为暖，庚为辅。",
                "advice":"丁庚两透，名利双收；丙火为帮扶。"},
        "子": {"primary":"丁", "secondary":"丙", "secondary2":"庚", "desc":"十一月甲木寒冻，丁丙为急，庚金劈甲。",
                "advice":"丁丙两透，富贵显赫；缺丁则寒孤。"},
        "丑": {"primary":"丁", "secondary":"丙", "secondary2":"庚", "desc":"十二月甲木天寒地冻，丁丙不可缺。",
                "advice":"丁丙庚三透，文武全才；丙丁两透，文章显贵。"},
    },
    "乙": {
        "寅": {"primary":"丙", "secondary":"癸", "desc":"正月乙木嫩芽初生，喜丙火向阳，癸水滋润。",
                "advice":"丙癸两透为上格，主聪明文秀。"},
        "卯": {"primary":"丙", "secondary":"癸", "desc":"二月乙木旺盛，丙火向阳，癸水生扶。",
                "advice":"丙透癸藏，富贵荣华。"},
        "辰": {"primary":"癸", "secondary":"丙", "secondary2":"戊", "desc":"三月乙木气退，土厚需戊，水润需癸。",
                "advice":"癸丙两透为吉。"},
        "巳": {"primary":"癸", "desc":"四月乙木气盛火炎，癸水救焚为急。",
                "advice":"癸水必不可少；缺则枯萎。"},
        "午": {"primary":"癸", "secondary":"丙", "desc":"五月乙木丁旺木焦，癸水为急。",
                "advice":"癸水透干，富贵无疑。"},
        "未": {"primary":"癸", "secondary":"丙", "desc":"六月乙木根燥，癸水滋润为重。",
                "advice":"癸丙两透，福寿双全。"},
        "申": {"primary":"丙", "secondary":"癸", "secondary2":"己", "desc":"七月乙木气凉，丙火为暖，癸水为润。",
                "advice":"丙癸己三透，富贵显达。"},
        "酉": {"primary":"丙", "secondary":"癸", "desc":"八月乙木气衰，丙火为急，癸水次之。",
                "advice":"丙透癸藏，文章显贵。"},
        "戌": {"primary":"癸", "secondary":"辛", "desc":"九月乙木气退，土厚需辛劈土，癸水滋润。",
                "advice":"癸辛两透，富中取贵。"},
        "亥": {"primary":"丙", "secondary":"戊", "desc":"十月乙木寒湿，丙火为暖，戊土制水。",
                "advice":"丙戊两透，富贵双全。"},
        "子": {"primary":"丙", "desc":"十一月乙木严寒，丙火不可缺。",
                "advice":"丙火透干，否则寒孤。"},
        "丑": {"primary":"丙", "desc":"十二月乙木天寒地冻，丙火为急。",
                "advice":"丙火透干为上格。"},
    },
    "丙": {
        "寅": {"primary":"壬", "secondary":"庚", "desc":"正月丙火初出，喜壬水辅佐，庚金为辅。",
                "advice":"壬庚两透，名贵双全。"},
        "卯": {"primary":"壬", "secondary":"己", "desc":"二月丙火气旺，壬水克丙最佳。",
                "advice":"壬水透干，名贵之命。"},
        "辰": {"primary":"壬", "secondary":"甲", "desc":"三月丙火气壮土厚，壬水甲木通关。",
                "advice":"壬甲两透为吉。"},
        "巳": {"primary":"壬", "secondary":"庚", "secondary2":"癸", "desc":"四月丙火建禄，壬水救焚为急。",
                "advice":"壬水透干，富贵双全；缺壬则枯。"},
        "午": {"primary":"壬", "secondary":"庚", "desc":"五月丙火炎上，壬水救焚为唯一调候。",
                "advice":"壬水透干为状元宰相之命；缺壬必平庸。"},
        "未": {"primary":"壬", "secondary":"庚", "desc":"六月丙火退气，壬水滋润为本。",
                "advice":"壬水透干，富贵无疑。"},
        "申": {"primary":"壬", "secondary":"戊", "desc":"七月丙火气衰，壬水为佐，戊土制水。",
                "advice":"壬戊两透，文武双全。"},
        "酉": {"primary":"壬", "secondary":"癸", "desc":"八月丙火气衰，壬癸调候。",
                "advice":"壬透癸藏，富贵之命。"},
        "戌": {"primary":"甲", "secondary":"壬", "desc":"九月丙火气衰土厚，甲木疏土，壬水滋润。",
                "advice":"甲壬两透，名贵显达。"},
        "亥": {"primary":"甲", "secondary":"戊", "secondary2":"壬", "desc":"十月丙火气绝，甲木生扶为急。",
                "advice":"甲透戊辅，富贵双全。"},
        "子": {"primary":"壬", "secondary":"戊", "secondary2":"己", "desc":"十一月丙火寒弱，壬水为忌，戊土制水。",
                "advice":"戊土透干为吉。"},
        "丑": {"primary":"壬", "secondary":"甲", "desc":"十二月丙火气绝，甲木为助。",
                "advice":"甲壬齐透，文章秀气。"},
    },
    "丁": {
        "寅": {"primary":"庚", "secondary":"甲", "desc":"正月丁火，庚金劈甲引丁。",
                "advice":"庚甲两透为上格。"},
        "卯": {"primary":"庚", "secondary":"甲", "desc":"二月丁火，仍喜庚甲。",
                "advice":"庚甲齐透，富贵之命。"},
        "辰": {"primary":"甲", "secondary":"庚", "desc":"三月丁火气退土厚，甲木疏土，庚为辅。",
                "advice":"甲庚两透，文章显贵。"},
        "巳": {"primary":"甲", "secondary":"庚", "desc":"四月丁火建禄，甲木为助，庚为辅。",
                "advice":"甲庚两透为上格。"},
        "午": {"primary":"壬", "secondary":"癸", "secondary2":"庚", "desc":"五月丁火炎上，壬癸救焚。",
                "advice":"壬水透干，富贵无疑。"},
        "未": {"primary":"甲", "secondary":"壬", "secondary2":"庚", "desc":"六月丁火退气，甲木为助。",
                "advice":"甲透壬庚辅，富贵之命。"},
        "申": {"primary":"甲", "secondary":"庚", "secondary2":"丙", "desc":"七月丁火气衰，甲木为助。",
                "advice":"甲庚两透，文武双全。"},
        "酉": {"primary":"甲", "secondary":"庚", "secondary2":"丙", "desc":"八月丁火气衰，甲为助，丙为暖。",
                "advice":"甲透丙辅，富贵之命。"},
        "戌": {"primary":"甲", "secondary":"庚", "secondary2":"戊", "desc":"九月丁火气退，甲庚为辅。",
                "advice":"甲庚两透，名贵显达。"},
        "亥": {"primary":"甲", "secondary":"庚", "desc":"十月丁火气绝，甲木为助为急。",
                "advice":"甲庚两透，富贵双全。"},
        "子": {"primary":"甲", "secondary":"庚", "desc":"十一月丁火寒弱，甲庚为急。",
                "advice":"甲庚两透为上格。"},
        "丑": {"primary":"甲", "secondary":"庚", "desc":"十二月丁火气绝，甲庚为最。",
                "advice":"甲庚两透，富贵无疑。"},
    },
    "戊": {
        "寅": {"primary":"丙", "secondary":"甲", "secondary2":"癸", "desc":"正月戊土初春仍寒，丙火为暖，甲木疏土。",
                "advice":"丙甲齐透，富贵双全。"},
        "卯": {"primary":"丙", "secondary":"甲", "secondary2":"癸", "desc":"二月戊土，丙火为暖，甲木疏土。",
                "advice":"丙甲透干，名贵之命。"},
        "辰": {"primary":"甲", "secondary":"丙", "secondary2":"癸", "desc":"三月戊土气盛，甲疏丙暖癸润。",
                "advice":"甲丙癸三透为上格。"},
        "巳": {"primary":"甲", "secondary":"丙", "secondary2":"癸", "desc":"四月戊土建禄，甲木为助，癸水为润。",
                "advice":"甲透丙暖癸润，富贵无疑。"},
        "午": {"primary":"壬", "secondary":"甲", "secondary2":"丙", "desc":"五月戊土火旺，壬水为润，甲木疏土。",
                "advice":"壬甲两透，富贵显达。"},
        "未": {"primary":"癸", "secondary":"甲", "secondary2":"丙", "desc":"六月戊土湿土需调候，癸水为润。",
                "advice":"癸甲两透，富中取贵。"},
        "申": {"primary":"丙", "secondary":"甲", "secondary2":"癸", "desc":"七月戊土气衰，丙火甲木为助。",
                "advice":"丙甲两透为上格。"},
        "酉": {"primary":"丙", "secondary":"癸", "desc":"八月戊土气衰，丙火癸水调候。",
                "advice":"丙癸两透，文章显贵。"},
        "戌": {"primary":"甲", "secondary":"丙", "secondary2":"癸", "desc":"九月戊土气退土厚，甲木疏土为急。",
                "advice":"甲丙癸三透，富贵无疑。"},
        "亥": {"primary":"甲", "secondary":"丙", "desc":"十月戊土寒湿，丙火为暖，甲木为助。",
                "advice":"甲丙两透，富贵显达。"},
        "子": {"primary":"丙", "secondary":"甲", "desc":"十一月戊土严寒，丙火为唯一调候。",
                "advice":"丙火透干，否则寒孤。"},
        "丑": {"primary":"丙", "secondary":"甲", "desc":"十二月戊土天寒地冻，丙火为急。",
                "advice":"丙火透干，富贵显达。"},
    },
    "己": {
        "寅": {"primary":"丙", "secondary":"庚", "secondary2":"甲", "desc":"正月己土寒湿，丙火为暖。",
                "advice":"丙火透干为上格。"},
        "卯": {"primary":"甲", "secondary":"癸", "secondary2":"丙", "desc":"二月己土气盛，甲木为正官，癸水为润。",
                "advice":"甲癸两透，富贵之命。"},
        "辰": {"primary":"丙", "secondary":"癸", "secondary2":"甲", "desc":"三月己土，丙火为暖，癸水为润。",
                "advice":"丙癸两透，名贵显达。"},
        "巳": {"primary":"癸", "secondary":"丙", "secondary2":"甲", "desc":"四月己土火旺，癸水为急。",
                "advice":"癸水透干，否则枯萎。"},
        "午": {"primary":"癸", "secondary":"丙", "desc":"五月己土火炎，癸水救焚。",
                "advice":"癸水必不可少。"},
        "未": {"primary":"癸", "secondary":"丙", "desc":"六月己土湿土，癸水为润。",
                "advice":"癸水透干，富贵无疑。"},
        "申": {"primary":"丙", "secondary":"癸", "desc":"七月己土气衰，丙火为暖，癸为润。",
                "advice":"丙癸两透，文章显贵。"},
        "酉": {"primary":"丙", "secondary":"癸", "desc":"八月己土气衰，丙癸为调候。",
                "advice":"丙癸两透为上格。"},
        "戌": {"primary":"甲", "secondary":"丙", "secondary2":"癸", "desc":"九月己土气退，甲木疏土为急。",
                "advice":"甲丙两透，富贵显达。"},
        "亥": {"primary":"丙", "secondary":"甲", "desc":"十月己土寒湿，丙火为唯一调候。",
                "advice":"丙火透干，否则寒孤。"},
        "子": {"primary":"丙", "secondary":"甲", "desc":"十一月己土严寒，丙火为急。",
                "advice":"丙火透干为上格。"},
        "丑": {"primary":"丙", "secondary":"甲", "desc":"十二月己土天寒，丙火为暖。",
                "advice":"丙火透干，富贵显达。"},
    },
    "庚": {
        "寅": {"primary":"丙", "secondary":"甲", "secondary2":"壬", "desc":"正月庚金气寒，丙火为暖，甲木为助。",
                "advice":"丙甲两透，富贵双全。"},
        "卯": {"primary":"丁", "secondary":"甲", "secondary2":"庚", "desc":"二月庚金气盛，丁火为炼。",
                "advice":"丁透甲辅，富贵显达。"},
        "辰": {"primary":"甲", "secondary":"丁", "secondary2":"壬", "desc":"三月庚金气壮土厚，甲木疏土，丁火炼金。",
                "advice":"甲丁两透为吉。"},
        "巳": {"primary":"壬", "secondary":"戊", "secondary2":"丙", "desc":"四月庚金长生火地，壬水为润，戊土制水。",
                "advice":"壬戊两透，富贵之命。"},
        "午": {"primary":"壬", "secondary":"癸", "desc":"五月庚金火炎，壬水救之。",
                "advice":"壬水透干，富贵无疑。"},
        "未": {"primary":"丁", "secondary":"甲", "secondary2":"癸", "desc":"六月庚金气衰，丁火炼之。",
                "advice":"丁甲两透为上格。"},
        "申": {"primary":"丁", "secondary":"甲", "desc":"七月庚金建禄，丁火炼之，甲木为助。",
                "advice":"丁甲两透，富贵显达。"},
        "酉": {"primary":"丁", "secondary":"甲", "secondary2":"丙", "desc":"八月庚金气盛，丁火为炼。",
                "advice":"丁透甲辅，富贵之命。"},
        "戌": {"primary":"甲", "secondary":"丁", "secondary2":"壬", "desc":"九月庚金气退土厚，甲木疏土。",
                "advice":"甲丁两透，名贵显达。"},
        "亥": {"primary":"丁", "secondary":"甲", "secondary2":"丙", "desc":"十月庚金气寒，丁丙为暖。",
                "advice":"丁丙齐透，富贵双全。"},
        "子": {"primary":"丁", "secondary":"甲", "secondary2":"丙", "desc":"十一月庚金严寒，丁火为急。",
                "advice":"丁火透干，否则寒孤。"},
        "丑": {"primary":"丙", "secondary":"丁", "secondary2":"甲", "desc":"十二月庚金天寒，丙丁为暖。",
                "advice":"丙丁齐透，富贵显达。"},
    },
    "辛": {
        "寅": {"primary":"己", "secondary":"壬", "secondary2":"庚", "desc":"正月辛金气寒，己土生扶。",
                "advice":"己壬两透为上格。"},
        "卯": {"primary":"壬", "secondary":"甲", "desc":"二月辛金气衰，壬水洗淘。",
                "advice":"壬水透干，富贵之命。"},
        "辰": {"primary":"壬", "secondary":"甲", "desc":"三月辛金气盛，壬水洗淘。",
                "advice":"壬甲两透，富贵无疑。"},
        "巳": {"primary":"壬", "secondary":"癸", "secondary2":"甲", "desc":"四月辛金火旺，壬癸为润。",
                "advice":"壬癸两透，富贵显达。"},
        "午": {"primary":"壬", "secondary":"癸", "desc":"五月辛金火炎，壬水为急。",
                "advice":"壬水透干，富贵无疑。"},
        "未": {"primary":"壬", "secondary":"庚", "secondary2":"甲", "desc":"六月辛金湿土埋金，壬水洗淘。",
                "advice":"壬水透干为吉。"},
        "申": {"primary":"壬", "secondary":"甲", "desc":"七月辛金气壮，壬水洗淘。",
                "advice":"壬水透干为上格。"},
        "酉": {"primary":"壬", "secondary":"甲", "desc":"八月辛金气旺，壬水洗淘。",
                "advice":"壬水透干，富贵之命。"},
        "戌": {"primary":"壬", "secondary":"甲", "desc":"九月辛金气退，壬水洗淘，甲木辅之。",
                "advice":"壬甲两透为吉。"},
        "亥": {"primary":"壬", "secondary":"丙", "desc":"十月辛金气寒，壬水洗淘，丙火为暖。",
                "advice":"壬丙两透，富贵双全。"},
        "子": {"primary":"丙", "secondary":"戊", "secondary2":"壬", "desc":"十一月辛金严寒，丙火为急。",
                "advice":"丙火透干，否则寒孤。"},
        "丑": {"primary":"丙", "secondary":"壬", "secondary2":"戊", "desc":"十二月辛金天寒，丙火为暖。",
                "advice":"丙火透干，富贵显达。"},
    },
    "壬": {
        "寅": {"primary":"庚", "secondary":"丙", "secondary2":"戊", "desc":"正月壬水气退，庚金生扶。",
                "advice":"庚丙两透，富贵双全。"},
        "卯": {"primary":"庚", "secondary":"戊", "secondary2":"辛", "desc":"二月壬水气泄，庚金生扶。",
                "advice":"庚戊两透，名贵显达。"},
        "辰": {"primary":"甲", "secondary":"庚", "desc":"三月壬水气壮土厚，甲木疏土。",
                "advice":"甲庚两透，富贵之命。"},
        "巳": {"primary":"壬", "secondary":"庚", "secondary2":"癸", "desc":"四月壬水绝地，比劫为助。",
                "advice":"壬癸庚透，富贵显达。"},
        "午": {"primary":"癸", "secondary":"庚", "secondary2":"辛", "desc":"五月壬水气衰火旺，癸庚为助。",
                "advice":"癸庚两透，富贵无疑。"},
        "未": {"primary":"辛", "secondary":"甲", "secondary2":"庚", "desc":"六月壬水气退，辛金生扶。",
                "advice":"辛甲两透为上格。"},
        "申": {"primary":"戊", "secondary":"丁", "desc":"七月壬水长生，戊土制水，丁火为暖。",
                "advice":"戊丁两透，富贵之命。"},
        "酉": {"primary":"甲", "secondary":"庚", "desc":"八月壬水气旺金生，甲木泄秀。",
                "advice":"甲庚两透，富贵无疑。"},
        "戌": {"primary":"甲", "secondary":"丙", "desc":"九月壬水气退土厚，甲木疏土，丙火为暖。",
                "advice":"甲丙两透，富贵双全。"},
        "亥": {"primary":"戊", "secondary":"丙", "secondary2":"庚", "desc":"十月壬水建禄，戊土制水，丙火为暖。",
                "advice":"戊丙两透，富贵显达。"},
        "子": {"primary":"戊", "secondary":"丙", "desc":"十一月壬水羊刃，戊土制水为急。",
                "advice":"戊土透干为吉。"},
        "丑": {"primary":"丙", "secondary":"丁", "secondary2":"甲", "desc":"十二月壬水天寒，丙丁为暖。",
                "advice":"丙丁齐透，富贵之命。"},
    },
    "癸": {
        "寅": {"primary":"辛", "secondary":"丙", "desc":"正月癸水气泄，辛金生扶。",
                "advice":"辛丙两透，富贵双全。"},
        "卯": {"primary":"庚", "secondary":"辛", "desc":"二月癸水气泄，庚辛生扶。",
                "advice":"庚辛两透，富贵之命。"},
        "辰": {"primary":"丙", "secondary":"辛", "secondary2":"甲", "desc":"三月癸水气壮土厚，丙火为暖。",
                "advice":"丙辛两透，名贵显达。"},
        "巳": {"primary":"辛", "secondary":"庚", "secondary2":"壬", "desc":"四月癸水绝地，辛庚为助。",
                "advice":"辛庚两透，富贵无疑。"},
        "午": {"primary":"庚", "secondary":"壬", "secondary2":"癸", "desc":"五月癸水气衰，庚壬为助。",
                "advice":"庚壬两透，富贵显达。"},
        "未": {"primary":"庚", "secondary":"辛", "secondary2":"壬", "desc":"六月癸水气退，庚辛壬皆吉。",
                "advice":"庚辛两透为上格。"},
        "申": {"primary":"丁", "secondary":"甲", "desc":"七月癸水气盛，丁火为暖，甲木泄秀。",
                "advice":"丁甲两透，富贵双全。"},
        "酉": {"primary":"辛", "secondary":"丙", "desc":"八月癸水气旺金生，辛金为根，丙火为暖。",
                "advice":"辛丙两透，富贵之命。"},
        "戌": {"primary":"辛", "secondary":"甲", "secondary2":"壬", "desc":"九月癸水气退土厚，辛金为根。",
                "advice":"辛甲两透为吉。"},
        "亥": {"primary":"庚", "secondary":"辛", "secondary2":"戊", "desc":"十月癸水气壮，庚辛为辅。",
                "advice":"庚辛两透，富贵显达。"},
        "子": {"primary":"丙", "secondary":"辛", "desc":"十一月癸水严寒，丙火为唯一调候。",
                "advice":"丙火透干，否则寒孤。"},
        "丑": {"primary":"丙", "secondary":"丁", "desc":"十二月癸水天寒，丙丁为暖。",
                "advice":"丙丁齐透，富贵显达。"},
    },
}


def get_tiaohou_yongshen(day_master: str, month_zhi: str) -> Dict[str, Any]:
    """
    根据日主和月支，返回调候用神组合。
    """
    return TIAOHOU_TABLE.get(day_master, {}).get(month_zhi, {
        "primary": "", "desc": "暂未收录此组合的调候用神",
        "advice": "请参考《穷通宝鉴》对应章节",
    })


def analyze_tiaohou_in_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析命盘中的调候用神是否到位。
    """
    dm = chart["day_master"]
    month_zhi = chart["month_pillar"]["dizhi"]
    
    yongshen = get_tiaohou_yongshen(dm, month_zhi)
    if not yongshen.get("primary"):
        return {"available": False, "desc": "暂无此日主月支的调候资料"}
    
    # 收集命盘所有天干
    all_gans = []
    for pk in ["year_pillar", "month_pillar", "day_pillar", "hour_pillar"]:
        all_gans.append(chart[pk]["tiangan"])
        all_gans.extend(chart[pk].get("canggan", []))
    
    primary = yongshen.get("primary", "")
    secondary = yongshen.get("secondary", "")
    secondary2 = yongshen.get("secondary2", "")
    
    has_primary = primary in all_gans
    has_secondary = secondary in all_gans if secondary else None
    has_secondary2 = secondary2 in all_gans if secondary2 else None
    
    # 评级
    if has_primary and (has_secondary is None or has_secondary):
        grade = "调候到位"
        level = "auspicious_great"
        verdict = f"命盘见调候主用神{primary}" + (f"及辅用神{secondary}" if secondary else "") + "，调候大利。"
    elif has_primary:
        grade = "调候部分到位"
        level = "auspicious"
        verdict = f"命盘见主用神{primary}，但缺辅用神{secondary or ''}{secondary2 or ''}，调候未尽完美。"
    else:
        grade = "调候失司"
        level = "inauspicious"
        verdict = f"命盘缺主用神{primary}，调候失司，须借助大运补救。"
    
    return {
        "available": True,
        "day_master": dm,
        "month_zhi": month_zhi,
        "primary": primary,
        "secondary": secondary,
        "secondary2": secondary2,
        "primary_in_chart": has_primary,
        "secondary_in_chart": has_secondary,
        "secondary2_in_chart": has_secondary2,
        "grade": grade,
        "level": level,
        "verdict": verdict,
        "desc": yongshen.get("desc", ""),
        "advice": yongshen.get("advice", ""),
        "source": "《穷通宝鉴》",
    }


# ─────────────────────────────────────────────────────────────
# 2. 子平真诠 — 8 格局成败救应
# ─────────────────────────────────────────────────────────────
# 《子平真诠》核心理论：
#   - 每个正格都有"成格"条件 → 主贵
#   - "破格"条件 → 失败
#   - 破格时若有"救应"星 → 反败为贵（更高层次）
#
# 8 大正格：
#   正官、七杀、正印、偏印（枭印）、正财、偏财、食神、伤官
#   建禄格、月刃格 视为外格

GE_JU_CHENG_BAI: Dict[str, Dict[str, Any]] = {
    "正官格": {
        "成格": ["官星纯净不受冲克", "财生官", "印化官", "官不见伤"],
        "破格": ["官星受伤官见冲", "官星被合化", "印重官弱无生", "财官混杂"],
        "救应": [
            ("伤官见官", "印星制伤", "印化伤生身，反成贵格"),
            ("七杀混杂", "去杀留官（合杀）", "去杀留官，清纯之贵"),
            ("官弱无生", "财星生官", "财官两旺，富贵双全"),
        ],
        "desc": "官星为君，最忌伤官冲克。成格主贵，破格主祸，救应反贵。",
    },
    "七杀格": {
        "成格": ["七杀有制（食神制杀）", "杀印相生", "羊刃合杀", "杀化为权"],
        "破格": ["杀重身轻无制", "财生杀攻身", "杀印相战", "群杀攻身无救"],
        "救应": [
            ("身弱杀重", "印星化杀", "杀生印、印生身，反成贵格"),
            ("杀无制", "羊刃合杀", "刃杀合化为权，武贵之命"),
            ("食神制杀过度", "枭印夺食", "枭神救助官星，化险为夷"),
        ],
        "desc": "七杀为攻身之敌，必须制化。成格则贵，破格则凶险，救应则成大贵。",
    },
    "正印格": {
        "成格": ["印星纯净有官杀生", "印不见财破", "印有比劫保护"],
        "破格": ["财星坏印", "印星太过身弱", "印星受冲", "印无源（无官杀生）"],
        "救应": [
            ("财坏印", "比劫制财", "比劫护印，反成贵格"),
            ("印多身重", "财星制印（食伤生财）", "印太过反喜财来制"),
        ],
        "desc": "印星生身为母，最忌财来克。学者文官之命，破格则学业受阻。",
    },
    "偏印格": {
        "成格": ["枭印生身得食神不被夺", "偏印有官杀生", "偏印化为印绶"],
        "破格": ["枭神夺食", "偏印太过", "偏印受财克"],
        "救应": [
            ("枭夺食", "财星制枭", "财生官、官生印、印转化为正用"),
            ("偏印重", "食神有力", "食神泄秀，反成才子之命"),
        ],
        "desc": "枭神性偏，主孤、僧道、技艺。成格主偏门技艺有成。",
    },
    "正财格": {
        "成格": ["财星纯净有食伤生", "财官两旺", "财得比劫制夺"],
        "破格": ["比劫夺财", "财轻身重", "财星受冲", "印重克财"],
        "救应": [
            ("比劫夺财", "食伤通关", "食伤泄比生财，反成富贵"),
            ("印重克财", "官星制印", "官护财，反成贵格"),
        ],
        "desc": "正财为稳定之财，主婚姻、田产。成格主富，破格主婚姻不顺、财来财去。",
    },
    "偏财格": {
        "成格": ["偏财纯净有食伤生", "偏财有官星护", "偏财不被比劫夺"],
        "破格": ["比劫夺财", "偏财被合化", "偏财受冲"],
        "救应": [
            ("比劫夺偏财", "食伤通关", "食伤生财，化解夺财"),
            ("偏财受冲", "官星护财", "官护财，化险为夷"),
        ],
        "desc": "偏财主父亲、外财、偏门之财。成格主豪爽富贵。",
    },
    "食神格": {
        "成格": ["食神纯净有财", "食神生财", "食神制杀"],
        "破格": ["枭神夺食", "食神被合化", "食神受冲"],
        "救应": [
            ("枭神夺食", "财星制枭", "财制枭、食神得用，反成贵格"),
            ("食神制杀过度", "印星化杀", "印化杀转生身，化险为夷"),
        ],
        "desc": "食神温和秀气，主才华、口福。成格主聪慧富贵。",
    },
    "伤官格": {
        "成格": ["伤官佩印", "伤官生财", "伤官配杀（制服）"],
        "破格": ["伤官见官", "伤官无制无化", "伤官被合化"],
        "救应": [
            ("伤官见官", "印星化伤", "印化伤生身，反成贵格"),
            ("伤官无制", "财星泄秀", "财通气、伤化财、富贵双全"),
        ],
        "desc": "伤官聪明而桀骜，最忌见官。成格主才华显达，破格主官非。",
    },
}


def analyze_geju_cheng_bai(chart: Dict[str, Any], pattern_name: str) -> Dict[str, Any]:
    """
    分析格局的成败救应。
    """
    info = GE_JU_CHENG_BAI.get(pattern_name)
    if not info:
        return {"available": False, "pattern": pattern_name}
    
    return {
        "available": True,
        "pattern": pattern_name,
        "成格条件": info["成格"],
        "破格条件": info["破格"],
        "救应模式": [{"破": b, "救": s, "desc": d} for b, s, d in info["救应"]],
        "总论": info["desc"],
        "source": "《子平真诠·成败救应》",
    }
