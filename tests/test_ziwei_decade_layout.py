"""
Tests for core/ziwei/chart.py — compute_decade_palaces_layout / compute_annual_palaces_layout

Z-7: 大限十二宫重排
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ziwei.chart import (
    compute_decade_palaces_layout,
    compute_annual_palaces_layout,
    DECADE_PALACE_NAMES,
    DECADE_PALACE_SHORT,
)


def test_decade_palaces_layout_basic():
    """大限命宫在 idx=5，验证 12 宫重排正确（逆时针）"""
    print("=" * 70)
    print("TEST 1: 大限十二宫基础重排（大限命宫 idx=5）")
    print("=" * 70)
    layout = compute_decade_palaces_layout(5)
    
    # 应有 12 项
    assert len(layout) == 12
    # 大限命宫
    assert layout[5]["name"] == "大限命宫"
    assert layout[5]["short"] == "大-命"
    assert layout[5]["offset"] == 0
    # 大限兄弟（命宫 -1，逆时针 idx 减）
    assert layout[4]["name"] == "大限兄弟"
    # 大限夫妻 (-2)
    assert layout[3]["name"] == "大限夫妻"
    # 大限子女 (-3)
    assert layout[2]["name"] == "大限子女"
    # 大限财帛 (-4)
    assert layout[1]["name"] == "大限财帛"
    # 大限疾厄 (-5)
    assert layout[0]["name"] == "大限疾厄"
    # 大限迁移 (-6，对宫)
    assert layout[11]["name"] == "大限迁移"
    # 大限交友 (-7)
    assert layout[10]["name"] == "大限交友"
    # 大限官禄 (-8)
    assert layout[9]["name"] == "大限官禄"
    # 大限田宅 (-9)
    assert layout[8]["name"] == "大限田宅"
    # 大限福德 (-10)
    assert layout[7]["name"] == "大限福德"
    # 大限父母 (-11)
    assert layout[6]["name"] == "大限父母"
    
    print("  ✓ 12 宫完整重排，逆时针 idx 递减正确")
    print()


def test_decade_layout_at_origin():
    """大限命宫在 idx=0，跨越边界（应循环到 idx=11）"""
    print("=" * 70)
    print("TEST 2: 大限命宫在 idx=0（循环边界）")
    print("=" * 70)
    layout = compute_decade_palaces_layout(0)
    
    assert layout[0]["name"] == "大限命宫"
    # 兄弟应在 idx=-1 即 11
    assert layout[11]["name"] == "大限兄弟"
    # 夫妻 idx=10
    assert layout[10]["name"] == "大限夫妻"
    # 父母 idx=1
    assert layout[1]["name"] == "大限父母"
    
    print("  ✓ idx 循环正确")
    print()


def test_decade_layout_at_eleven():
    """大限命宫在 idx=11"""
    print("=" * 70)
    print("TEST 3: 大限命宫在 idx=11")
    print("=" * 70)
    layout = compute_decade_palaces_layout(11)
    
    assert layout[11]["name"] == "大限命宫"
    assert layout[10]["name"] == "大限兄弟"
    assert layout[0]["name"] == "大限父母"  # 11 - 11 = 0
    
    print("  ✓ idx=11 时层 layout 正确")
    print()


def test_decade_palaces_complete_coverage():
    """验证任意起点都能覆盖全部 12 个 natal_idx，且 12 个宫名不重复"""
    print("=" * 70)
    print("TEST 4: 12 个 natal_idx 全部覆盖 + 12 宫名不重复")
    print("=" * 70)
    for start in range(12):
        layout = compute_decade_palaces_layout(start)
        # 覆盖
        assert set(layout.keys()) == set(range(12))
        # 不重复
        names = [info["name"] for info in layout.values()]
        assert len(set(names)) == 12, f"start={start} 有重复"
        assert len(set([info["offset"] for info in layout.values()])) == 12, "offset 重复"
    print("  ✓ 所有 12 种起点都通过覆盖+不重复验证")
    print()


def test_annual_palaces_layout():
    """流年 layout 同样逻辑"""
    print("=" * 70)
    print("TEST 5: 流年十二宫重排")
    print("=" * 70)
    layout = compute_annual_palaces_layout(7)
    
    assert layout[7]["name"] == "流年命宫"
    assert layout[7]["short"] == "年-命"
    assert layout[6]["name"] == "流年兄弟"
    assert layout[1]["name"] == "流年迁移"  # 7 - 6 = 1
    
    # 12 个不重复
    names = [info["name"] for info in layout.values()]
    assert len(set(names)) == 12
    
    print("  ✓ 流年十二宫重排正确")
    print()


def test_decade_opposite_palace():
    """大限命宫和大限迁移宫永远是对宫（地支冲）"""
    print("=" * 70)
    print("TEST 6: 大限命宫与大限迁移宫永远对冲（idx 相差 6）")
    print("=" * 70)
    for start in range(12):
        layout = compute_decade_palaces_layout(start)
        # 找命和迁
        cmd_idx = None
        qian_idx = None
        for nidx, info in layout.items():
            if info["name"] == "大限命宫":  cmd_idx = nidx
            if info["name"] == "大限迁移":  qian_idx = nidx
        assert abs(cmd_idx - qian_idx) == 6 or abs(cmd_idx - qian_idx) == 6, \
            f"start={start}: 命={cmd_idx} 迁={qian_idx} 不是对冲"
    print("  ✓ 所有 12 种起点的命-迁皆对冲")
    print()


def test_decade_palaces_with_real_chart():
    """用真实命盘验证（1990 五月廿二 卯时男，35 岁大限）"""
    print("=" * 70)
    print("TEST 7: 真实命盘 — 1990 农历五月廿二卯时男，35 岁大限")
    print("=" * 70)
    
    try:
        from core.ziwei.chart import build_ziwei_chart, get_decade_palace
        decade = get_decade_palace('1990-7-14', 3, '男', 35)
        if decade is None:
            print("  · 跳过：get_decade_palace 返回 None（iztro 未装或失败）")
            return
        
        # 已经在 decade 里
        assert "palaces_layout" in decade
        layout = decade["palaces_layout"]
        assert len(layout) == 12
        
        # 大限命宫 idx=5（田宅宫，按上一步的验证）
        dec_cmd_idx = decade["palace_idx"]
        assert layout[dec_cmd_idx]["name"] == "大限命宫"
        
        print(f"  · 大限命宫在本命 idx={dec_cmd_idx} ({decade['palace_name']})")
        print(f"  · 大限迁移 = 本命 idx={(dec_cmd_idx + 6) % 12}")
        print(f"  ✓ 真实数据 layout 正确")
    except ImportError:
        print("  · 跳过：iztro_py 未装")
    print()


if __name__ == "__main__":
    test_decade_palaces_layout_basic()
    test_decade_layout_at_origin()
    test_decade_layout_at_eleven()
    test_decade_palaces_complete_coverage()
    test_annual_palaces_layout()
    test_decade_opposite_palace()
    test_decade_palaces_with_real_chart()
    print("=" * 70)
    print("ALL DECADE LAYOUT TESTS PASSED")
    print("=" * 70)
