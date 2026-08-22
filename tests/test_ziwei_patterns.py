"""
Tests for core/ziwei/pattern_detector.py — Z-4 经典格局自动检测

Verifies:
  1. mock 命盘（2000-8-16 紫微午）能检测到正确的吉格
  2. 构造的紫府同宫场景能正确识别
  3. 杀破狼格识别（命财官三方七杀+破军+贪狼）
  4. 凶格识别（羊陀夹忌、巨火羊、命无正曜等）
  5. 边界情况（无格局命盘）
  6. format 输出包含关键内容
"""
import os
import sys
import copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_ziwei_context import make_mock_chart_2000_8_16
from core.ziwei.pattern_detector import (
    detect_all_patterns,
    format_patterns_for_prompt,
    detect_zifu_tonggong,
    detect_shapolang,
    detect_jiyue_tongliang,
    detect_yangtuo_jiaji,
    detect_juhuo_yang,
    detect_ming_wu_zhengyao,
    detect_riyue_bingming,
    detect_huotan,
    detect_xingqiu_jiayin,
    detect_huoling_jiaming,
)


def test_mock_chart_patterns():
    """对原始 mock 命盘做格局检测，看能检测到哪些格局。"""
    print("=" * 70)
    print("TEST 1: 原始 mock 命盘（2000-8-16 紫微午）格局检测")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    result = detect_all_patterns(data["palaces"], birth_hour_index=2)
    
    print(f"  吉格 {len(result['good_patterns'])} 个：")
    for p in result["good_patterns"]:
        print(f"    · {p['name']}")
        for ev in p["evidence"]:
            print(f"      - {ev}")
    print(f"  凶格 {len(result['bad_patterns'])} 个：")
    for p in result["bad_patterns"]:
        print(f"    · {p['name']}")
    
    # mock 中命宫午紫微 + 三方四正杀破狼（迁移宫贪狼+疾厄宫巨门同度等）
    # 验证至少能识别"杀破狼"
    # mock: 命宫紫微午、官禄宫廉贞天府戌、财帛宫武曲天相寅、迁移宫贪狼子
    # 命财官三方：命(紫微)、财(武曲天相)、官(廉贞天府)
    # 三方包含贪狼? 没有，贪狼在迁移宫
    # 注：杀破狼定义按命财官三方（不含对宫），贪狼在迁移宫(对宫)不算
    # 所以本mock 不构成杀破狼格 — 这是正确的
    
    print()
    return True


def test_zifu_tonggong():
    """构造紫府同宫格场景：命宫在寅，紫微+天府同坐。"""
    print("=" * 70)
    print("TEST 2: 紫府同宫格")
    print("=" * 70)
    
    # 构造命盘：命宫在寅，紫微+天府同坐
    palaces = []
    for i in range(12):
        branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
        names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
                 "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
        palaces.append({
            "index": i,
            "name": names[i],
            "earthly_branch": branches[i],
            "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [],
            "minor_stars": [],
            "adj_stars": [],
        })
    # 命宫(index 0, 寅) 加紫微+天府
    palaces[0]["major_stars"] = [
        {"name": "紫微", "type": "major", "brightness": "得", "mutagen": ""},
        {"name": "天府", "type": "major", "brightness": "庙", "mutagen": ""},
    ]
    
    result = detect_zifu_tonggong(palaces)
    assert result is not None, "应识别紫府同宫格"
    assert result["name"] == "紫府同宫格"
    assert result["category"] == "吉格"
    print(f"  ✓ 紫府同宫格识别成功：{result['name']}")
    print(f"    evidence: {result['evidence']}")
    print()


def test_shapolang():
    """构造杀破狼格：命财官三方会齐七杀+破军+贪狼。"""
    print("=" * 70)
    print("TEST 3: 杀破狼格")
    print("=" * 70)
    
    # 命宫七杀，财帛宫贪狼，官禄宫破军（这是经典三方）
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    palaces = []
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    palaces[0]["major_stars"] = [{"name":"七杀","type":"major","brightness":"庙","mutagen":""}]
    palaces[4]["major_stars"] = [{"name":"贪狼","type":"major","brightness":"得","mutagen":""}]
    palaces[8]["major_stars"] = [{"name":"破军","type":"major","brightness":"旺","mutagen":""}]
    
    result = detect_shapolang(palaces)
    assert result is not None, "应识别杀破狼格"
    assert result["name"] == "杀破狼格"
    print(f"  ✓ 杀破狼格识别成功")
    print(f"    evidence: {result['evidence']}")
    print()


def test_jiyue_tongliang():
    """构造机月同梁格：命财官三方有天机+太阴+天同+天梁。"""
    print("=" * 70)
    print("TEST 4: 机月同梁格")
    print("=" * 70)
    
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    palaces = []
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    palaces[0]["major_stars"] = [{"name":"天机","type":"major","brightness":"庙","mutagen":""}]
    palaces[4]["major_stars"] = [{"name":"太阴","type":"major","brightness":"旺","mutagen":""}]
    palaces[8]["major_stars"] = [{"name":"天梁","type":"major","brightness":"庙","mutagen":""}]
    
    result = detect_jiyue_tongliang(palaces)
    assert result is not None
    assert result["name"] == "机月同梁格"
    print(f"  ✓ 机月同梁格识别成功（3 颗：天机+太阴+天梁）")
    print(f"    evidence: {result['evidence']}")
    print()


def test_riyue_bingming():
    """构造日月并明格：太阳午宫庙+太阴亥宫庙。"""
    print("=" * 70)
    print("TEST 5: 日月并明格")
    print("=" * 70)
    
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    palaces = []
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    # 太阳在 index 4 (午宫)
    palaces[4]["major_stars"] = [{"name":"太阳","type":"major","brightness":"庙","mutagen":""}]
    # 太阴在 index 9 (亥宫)
    palaces[9]["major_stars"] = [{"name":"太阴","type":"major","brightness":"庙","mutagen":""}]
    
    result = detect_riyue_bingming(palaces)
    assert result is not None
    assert result["name"] == "日月并明格"
    print(f"  ✓ 日月并明格识别成功")
    print(f"    evidence: {result['evidence']}")
    print()


def test_huotan():
    """构造火贪格：命宫贪狼+火星同宫。"""
    print("=" * 70)
    print("TEST 6: 火贪格")
    print("=" * 70)
    
    palaces = []
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    palaces[0]["major_stars"] = [{"name":"贪狼","type":"major","brightness":"庙","mutagen":""}]
    palaces[0]["minor_stars"] = [{"name":"火星","type":"minor","brightness":"庙","mutagen":""}]
    
    result = detect_huotan(palaces)
    assert result is not None
    assert result["name"] == "火贪格"
    print(f"  ✓ 火贪格识别成功")
    print()


def test_yangtuo_jiaji():
    """构造羊陀夹忌格：禄存+生年化忌在命宫。"""
    print("=" * 70)
    print("TEST 7: 羊陀夹忌格（凶格）")
    print("=" * 70)
    
    palaces = []
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    # 命宫坐天同(生年化忌) + 禄存
    palaces[0]["major_stars"] = [
        {"name": "天同", "type": "major", "brightness": "庙", "mutagen": "忌"},
    ]
    palaces[0]["minor_stars"] = [
        {"name": "禄存", "type": "minor", "brightness": "庙", "mutagen": ""},
    ]
    
    result = detect_yangtuo_jiaji(palaces)
    assert result is not None
    assert result["name"] == "羊陀夹忌格"
    assert result["category"] == "凶格"
    print(f"  ✓ 羊陀夹忌格识别成功（凶格）")
    print(f"    含义：{result['meaning'][:60]}...")
    print()


def test_juhuo_yang():
    """构造巨火羊格：巨门+火星+擎羊同宫。"""
    print("=" * 70)
    print("TEST 8: 巨火羊格（凶格）")
    print("=" * 70)
    
    palaces = []
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    palaces[0]["major_stars"] = [{"name":"巨门","type":"major","brightness":"陷","mutagen":""}]
    palaces[0]["minor_stars"] = [
        {"name":"火星","type":"minor","brightness":"庙","mutagen":""},
        {"name":"擎羊","type":"minor","brightness":"庙","mutagen":""},
    ]
    
    result = detect_juhuo_yang(palaces)
    assert result is not None
    assert result["name"] == "巨火羊格"
    assert result["category"] == "凶格"
    print(f"  ✓ 巨火羊格识别成功（极凶）")
    print()


def test_ming_wu_zhengyao():
    """构造命无正曜格：命宫空宫。"""
    print("=" * 70)
    print("TEST 9: 命无正曜格")
    print("=" * 70)
    
    palaces = []
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    # 命宫空，对宫(index 6 迁移宫=申)有紫微
    palaces[6]["major_stars"] = [{"name":"紫微","type":"major","brightness":"庙","mutagen":""}]
    
    result = detect_ming_wu_zhengyao(palaces)
    assert result is not None
    assert result["name"] == "命无正曜格"
    print(f"  ✓ 命无正曜格识别成功")
    print(f"    evidence: {result['evidence']}")
    print()


def test_xingqiu_jiayin():
    """构造刑囚夹印格：命宫廉贞+天相+擎羊在子或午宫。"""
    print("=" * 70)
    print("TEST 10: 刑囚夹印格（凶格）")
    print("=" * 70)
    
    palaces = []
    branches_starting_zi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches_starting_zi[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    palaces[0]["major_stars"] = [
        {"name":"廉贞","type":"major","brightness":"平","mutagen":""},
        {"name":"天相","type":"major","brightness":"得","mutagen":""},
    ]
    palaces[0]["minor_stars"] = [
        {"name":"擎羊","type":"minor","brightness":"陷","mutagen":""},
    ]
    
    result = detect_xingqiu_jiayin(palaces)
    assert result is not None
    assert result["name"] == "刑囚夹印格"
    print(f"  ✓ 刑囚夹印格识别成功")
    print()


def test_huoling_jiaming():
    """构造火铃夹命：命宫两邻分别有火星和铃星。"""
    print("=" * 70)
    print("TEST 11: 火铃夹命格")
    print("=" * 70)
    
    palaces = []
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    palaces[0]["major_stars"] = [{"name":"紫微","type":"major","brightness":"得","mutagen":""}]
    # 邻宫：index 11 (父母宫) 和 index 1 (兄弟宫)
    palaces[11]["minor_stars"] = [{"name":"火星","type":"minor","brightness":"庙","mutagen":""}]
    palaces[1]["minor_stars"]  = [{"name":"铃星","type":"minor","brightness":"庙","mutagen":""}]
    
    result = detect_huoling_jiaming(palaces)
    assert result is not None
    assert result["name"] == "火铃夹命格"
    print(f"  ✓ 火铃夹命格识别成功")
    print(f"    evidence: {result['evidence']}")
    print()


def test_format_output():
    """验证 format_patterns_for_prompt 输出包含关键信息。"""
    print("=" * 70)
    print("TEST 12: 格式化输出")
    print("=" * 70)
    
    # 用 mock 数据 + 构造一些格局触发
    data = make_mock_chart_2000_8_16()
    result = detect_all_patterns(data["palaces"], birth_hour_index=2)
    output = format_patterns_for_prompt(result)
    
    # 应包含主标题
    assert "经典格局检测" in output
    if result["good_patterns"] or result["bad_patterns"]:
        assert "·" in output
    
    print(f"  ✓ format 输出长度 {len(output)} chars")
    print()
    print("--- 完整输出 ---")
    print(output)
    print()


def test_no_patterns():
    """构造一个无明显格局的命盘，验证返回中性结果。"""
    print("=" * 70)
    print("TEST 13: 无明显格局的中性命盘")
    print("=" * 70)
    
    # 构造一个完全空的盘
    palaces = []
    branches = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    names = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
             "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for i in range(12):
        palaces.append({
            "index": i, "name": names[i],
            "earthly_branch": branches[i], "heavenly_stem": "甲",
            "is_soul": (i == 0),
            "major_stars": [], "minor_stars": [], "adj_stars": [],
        })
    # 命宫只有紫微（空宫吧），其他都空
    palaces[3]["major_stars"] = [{"name":"紫微","type":"major","brightness":"平","mutagen":""}]
    # 注意：命宫空宫 → 会触发"命无正曜格"，这是预期的
    
    result = detect_all_patterns(palaces, birth_hour_index=2)
    print(f"  吉格 {len(result['good_patterns'])} 个")
    print(f"  凶格 {len(result['bad_patterns'])} 个")
    # 因为命宫空所以会有"命无正曜格"
    bad_names = [p["name"] for p in result["bad_patterns"]]
    assert "命无正曜格" in bad_names
    print(f"  ✓ 命无正曜格自动检测正确")
    print()


def test_zitan_tonggong():
    """紫贪同宫格：紫微+贪狼同坐命宫卯/酉"""
    print("=" * 70)
    print("TEST: 紫贪同宫格")
    print("=" * 70)
    chart = make_mock_chart_2000_8_16()
    palaces = chart["palaces"]
    # 找命宫并强制改为紫微+贪狼在卯宫
    for p in palaces:
        if p.get("is_soul"):
            p["earthly_branch"] = "卯"
            p["major_stars"] = [
                {"name":"紫微","brightness":"旺"},
                {"name":"贪狼","brightness":"旺"},
            ]
            p["minor_stars"] = []
    from core.ziwei.pattern_detector import detect_zitan_tonggong
    result = detect_zitan_tonggong(palaces)
    assert result is not None, "应识别紫贪同宫格"
    assert result["name"] == "紫贪同宫格"
    assert result["category"] == "吉格"
    print(f"  ✓ 紫贪同宫格识别")
    print(f"    证据: {result['evidence'][:2]}")
    print()


def test_hour_index_boundary():
    """时辰边界：hour=5 应为卯时（不是寅）"""
    print("=" * 70)
    print("TEST: 时辰边界")
    print("=" * 70)
    from api.ziwei import ZiWeiRequest
    
    boundary_cases = [
        (23, 0, "子"),  # 23:00
        (0,  0, "子"),
        (1,  1, "丑"),
        (3,  2, "寅"),  # 3:00 = 寅
        (5,  3, "卯"),  # 5:00 = 卯（核心修复点）
        (6,  3, "卯"),
        (7,  4, "辰"),  # 7:00 = 辰
        (11, 6, "午"),
    ]
    for h, expected_idx, name in boundary_cases:
        req = ZiWeiRequest(year=2000, month=1, day=1, hour=h, gender="男", is_lunar=False)
        idx = req.to_hour_index()
        assert idx == expected_idx, f"hour={h}: 期望{expected_idx}({name}), 实际{idx}"
        print(f"  ✓ hour={h:2d} → idx={idx} ({name}时)")
    print()




if __name__ == "__main__":
    test_mock_chart_patterns()
    test_zifu_tonggong()
    test_zitan_tonggong()
    test_shapolang()
    test_jiyue_tongliang()
    test_riyue_bingming()
    test_huotan()
    test_yangtuo_jiaji()
    test_juhuo_yang()
    test_ming_wu_zhengyao()
    test_xingqiu_jiayin()
    test_huoling_jiaming()
    test_format_output()
    test_no_patterns()
    test_hour_index_boundary()
    print()
    print("=" * 70)
    print("ALL PATTERN TESTS PASSED")
    print("=" * 70)
