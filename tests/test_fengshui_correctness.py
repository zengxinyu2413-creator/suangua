"""
风水八宅 + 玄空飞星 命理学专业性系统验证
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_eight_mansion_completeness():
    """八宅表完整性 — 每宫 8 游年星齐全不重复"""
    print("=" * 70)
    print("TEST 1: 八宅游年表完整性")
    print("=" * 70)
    from core.fengshui.calculator import EIGHT_MANSION
    EXPECTED = {"伏位", "生气", "天医", "延年", "绝命", "五鬼", "六煞", "祸害"}
    GUA_NAME = {1:"坎",2:"坤",3:"震",4:"巽",6:"乾",7:"兑",8:"艮",9:"离"}
    for gua, layout in EIGHT_MANSION.items():
        stars = list(layout.values())
        # 每星只出现一次
        for s in EXPECTED:
            count = stars.count(s)
            assert count == 1, f"{GUA_NAME[gua]}宅 {s} 出现 {count} 次（应 1 次）"
        # 8 个方位
        assert len(layout) == 8, f"{GUA_NAME[gua]}宅 方位数 {len(layout)} (应 8)"
        print(f"  ✓ {GUA_NAME[gua]}宅 ({gua}): 八游年星完整不重复")
    print()


def test_eight_mansion_fuwei():
    """每宫的本卦方位必为伏位"""
    print("=" * 70)
    print("TEST 2: 本宫为伏位")
    print("=" * 70)
    from core.fengshui.calculator import EIGHT_MANSION
    POS = {1:"北",2:"西南",3:"东",4:"东南",6:"西北",7:"西",8:"东北",9:"南"}
    GUA_NAME = {1:"坎",2:"坤",3:"震",4:"巽",6:"乾",7:"兑",8:"艮",9:"离"}
    for gua, pos in POS.items():
        assert EIGHT_MANSION[gua][pos] == "伏位", \
            f"{GUA_NAME[gua]}宅 在 {pos} 应为伏位"
        print(f"  ✓ {GUA_NAME[gua]}宅 在 {pos} 为伏位")
    print()


def test_eight_mansion_canonical():
    """对照《八宅明镜》经典 — 坎宅四吉位标准"""
    print("=" * 70)
    print("TEST 3: 坎宅四吉对照《八宅明镜》")
    print("=" * 70)
    from core.fengshui.calculator import EIGHT_MANSION
    # 标准：坎宅生气在东南、天医正东、延年正南、伏位正北
    #       绝命西南、五鬼东北、六煞西北、祸害正西
    kanzhai = EIGHT_MANSION[1]
    expected = {"北":"伏位", "南":"延年", "东":"天医", "西":"祸害",
                "东南":"生气", "西北":"六煞", "东北":"五鬼", "西南":"绝命"}
    for d, s in expected.items():
        assert kanzhai[d] == s, f"坎宅 {d} 应为 {s}，实际 {kanzhai[d]}"
    print(f"  ✓ 坎宅 8 方位与《八宅明镜》完全一致")

    # 同时验证乾宅（大游年歌：六天五祸绝延生）
    # 乾(伏位)→坎(六煞)→艮(天医)→震(五鬼)→巽(祸害)→离(绝命)→坤(延年)→兑(生气)
    qianzhai = EIGHT_MANSION[6]
    expected_qian = {"西北":"伏位", "北":"六煞", "东北":"天医", "东":"五鬼",
                     "东南":"祸害", "南":"绝命", "西南":"延年", "西":"生气"}
    for d, s in expected_qian.items():
        assert qianzhai[d] == s, f"乾宅 {d} 应为 {s}，实际 {qianzhai[d]}"
    print(f"  ✓ 乾宅 8 方位符合大游年歌「六天五祸绝延生」")
    print()


def test_ming_gua_calculation():
    """命卦计算 — 6 个已知案例验证"""
    print("=" * 70)
    print("TEST 4: 命卦算法 6 个权威案例")
    print("=" * 70)
    from core.fengshui.calculator import calculate_ming_gua
    cases = [
        (1990, "男", 1, "坎"),
        (1989, "男", 2, "坤"),
        (1985, "男", 6, "乾"),
        (1990, "女", 8, "艮"),
        (2000, "男", 9, "离"),
        (2024, "男", 3, "震"),
    ]
    for year, gender, expected, name in cases:
        actual = calculate_ming_gua(year, gender)
        assert actual == expected, f"{year}{gender}: 算法={actual} 期望={expected}({name})"
        print(f"  ✓ {year} 年 {gender} → {actual} ({name}卦)")
    print()


def test_east_west_four():
    """东四命/西四命分组"""
    print("=" * 70)
    print("TEST 5: 东四/西四命分组")
    print("=" * 70)
    from core.fengshui.calculator import EAST_FOUR_LIFE, WEST_FOUR_LIFE
    # 东四命：坎离震巽 (1 9 3 4)
    assert EAST_FOUR_LIFE == {1, 3, 4, 9}
    # 西四命：乾坤艮兑 (6 2 8 7)
    assert WEST_FOUR_LIFE == {2, 6, 7, 8}
    # 不应有重叠
    assert not (EAST_FOUR_LIFE & WEST_FOUR_LIFE)
    print(f"  ✓ 东四命 = 坎离震巽 {EAST_FOUR_LIFE}")
    print(f"  ✓ 西四命 = 乾坤艮兑 {WEST_FOUR_LIFE}")
    print()


def test_house_gua_sitting():
    """宅卦取坐山派（主流）"""
    print("=" * 70)
    print("TEST 6: 宅卦取坐山（主流派）")
    print("=" * 70)
    from core.fengshui.calculator import get_house_gua
    # 坐北朝南（朝向"南"）应为坎宅 (1)
    assert get_house_gua("南") == 1, "坐北朝南 应为 坎宅(1)"
    print(f"  ✓ 朝南 → 坎宅(1)（坐北）")
    # 坐南朝北 → 离宅 (9)
    assert get_house_gua("北") == 9
    print(f"  ✓ 朝北 → 离宅(9)（坐南）")
    # 坐西朝东 → 兑宅 (7)
    assert get_house_gua("东") == 7
    print(f"  ✓ 朝东 → 兑宅(7)（坐西）")
    
    # 直接传坐山
    assert get_house_gua("北", direction_is_facing=False) == 1
    print(f"  ✓ 坐北 (direction_is_facing=False) → 坎宅(1)")
    print()


def test_annual_center_star():
    """年飞星中宫数 — 权威多年验证"""
    print("=" * 70)
    print("TEST 7: 年飞星中宫数（权威表对照）")
    print("=" * 70)
    from core.fengshui.flying_stars import get_annual_center_star
    # 权威表：1984=七赤、2024=三碧、2025=二黑、2026=一白、2027=九紫
    cases = [
        (1984, 7, "七赤"),
        (1985, 6, "六白"),
        (1990, 1, "一白"),
        (2000, 9, "九紫"),
        (2024, 3, "三碧"),
        (2025, 2, "二黑"),
        (2026, 1, "一白"),
        (2027, 9, "九紫"),
    ]
    for year, expected, name in cases:
        actual = get_annual_center_star(year)
        assert actual == expected, f"{year} 中宫: 算法={actual} 期望={expected}({name})"
        print(f"  ✓ {year} 年中宫 = {actual} ({name})")
    print()


def test_annual_2026_layout():
    """2026 年九宫飞星完整布局（权威对照）"""
    print("=" * 70)
    print("TEST 8: 2026 年九宫飞星布局（权威对照）")
    print("=" * 70)
    from core.fengshui.flying_stars import calculate_annual_flying_stars
    result = calculate_annual_flying_stars(2026)
    expected = {
        "中": 1, "西北": 2, "西": 3, "东北": 4,
        "南": 5, "北": 6, "西南": 7, "东": 8, "东南": 9,
    }
    for d, s in expected.items():
        actual = result["direction_stars"].get(d, {}).get("star_num", 0)
        assert actual == s, f"2026 {d}: 算法={actual} 期望={s}"
        print(f"  ✓ {d}: {s} 星")
    print()


def test_ming_gua_lucky_derived():
    """MING_GUA_LUCKY 与 EIGHT_MANSION 一致"""
    print("=" * 70)
    print("TEST 9: 个人吉位表与八宅表一致")
    print("=" * 70)
    from core.fengshui.calculator import EIGHT_MANSION
    from core.fengshui.flying_stars import MING_GUA_LUCKY
    
    STAR_TO_KEY = {
        "生气":"shengqi", "天医":"tianyi", "延年":"niannian", "伏位":"fuwei",
        "绝命":"jueming", "五鬼":"wugui", "六煞":"liusha", "祸害":"huohai",
    }
    GUA_NAME = {1:"坎",2:"坤",3:"震",4:"巽",6:"乾",7:"兑",8:"艮",9:"离"}
    
    for gua, lucky in MING_GUA_LUCKY.items():
        mansion = EIGHT_MANSION[gua]
        # mansion direction → star
        # lucky key → direction
        for direction, star in mansion.items():
            key = STAR_TO_KEY.get(star)
            if key:
                assert lucky.get(key) == direction, \
                    f"{GUA_NAME[gua]} {star}: lucky 说在 {lucky.get(key)} 但 mansion 在 {direction}"
        print(f"  ✓ {GUA_NAME[gua]}卦: 个人吉位 ↔ 八宅表 完全一致")
    print()


def test_xuankong_basic():
    """玄空山向飞星基础测试"""
    print("=" * 70)
    print("TEST 10: 玄空山向飞星")
    print("=" * 70)
    from core.fengshui.flying_stars import calculate_xuankong_chart
    
    # 九运（2024-2043）旺星为 9
    result = calculate_xuankong_chart("南", year=2026, yun=9)
    assert result["wang_star"] == 9
    assert result["yun"] == 9
    assert result["xiang"] == "南"
    assert "pattern" in result
    print(f"  ✓ 玄空山向算法工作正常（向南 9 运盘）")
    print(f"  · 格局: {result['pattern']}")
    print(f"  · 等级: {result['pattern_level']}")
    print()


def test_house_compat():
    """命宅相配：东四命住东四宅，西四命住西四宅"""
    print("=" * 70)
    print("TEST 11: 命宅相配判定")
    print("=" * 70)
    from core.fengshui.calculator import check_compatibility
    # 1990 男坎命 + 坎宅 (1+1) = 相配
    r = check_compatibility(1, 1)
    assert "相配" in r and "不相配" not in r
    print(f"  ✓ 坎命 + 坎宅 = 相配")
    # 坎命 + 乾宅 = 不相配（东四命 vs 西四宅）
    r2 = check_compatibility(1, 6)
    assert "不相配" in r2
    print(f"  ✓ 坎命(东四) + 乾宅(西四) = 不相配")
    print()


if __name__ == "__main__":
    test_eight_mansion_completeness()
    test_eight_mansion_fuwei()
    test_eight_mansion_canonical()
    test_ming_gua_calculation()
    test_east_west_four()
    test_house_gua_sitting()
    test_annual_center_star()
    test_annual_2026_layout()
    test_ming_gua_lucky_derived()
    test_xuankong_basic()
    test_house_compat()
    print("=" * 70)
    print("ALL 风水专业性 TESTS PASSED")
    print("=" * 70)
