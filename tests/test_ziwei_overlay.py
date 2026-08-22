"""
Tests for the overlay (大限/流年) feihua integration (Task 3).

Verifies:
  1. analyze_overlay_feihua 正确处理大限四化
  2. 流年禄/忌检测正确
  3. 大限化忌冲命宫等关键警示能被检测
  4. 三盘叠合 — 本命忌+大限忌+流年忌汇聚检测
  5. context_builder 能读取 data["_overlay"] 并生成对应 prompt 段
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_ziwei_context import make_mock_chart_2000_8_16
from core.ziwei.feihua_advanced import (
    analyze_overlay_feihua,
    format_overlay_feihua_for_prompt,
    analyze_three_plate_concentration,
    FH_FLY_OUT, FH_SELF_OUT, FH_SELF_IN,
)
from core.ziwei.context_builder import build_ziwei_context


# ─────────────────────────────────────────────────────────────
# 测试 1: 大限四化的基础分类
# ─────────────────────────────────────────────────────────────

def test_decade_basic():
    print("=" * 70)
    print("TEST 1: 大限四化基本飞化分类")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    
    # 假设当前 35 岁大限 — 简单选个干，让验证更直接
    # 大限命宫宫干假设是庚（与生年同干就特别有意思）
    # 选大限命宫 = 命宫(index 4)，宫干壬。但壬已经是命宫宫干，重复无意义
    # 我们模拟一个不一样的大限命宫
    # 假设大限走到田宅宫(index 7, 宫干乙)
    # 乙四化：禄天机、权天梁、科紫微、忌太阴
    # 这里：
    #   天机在父母宫(5) → index 5 != 7 != 1(对宫子女) → 普通飞宫
    #   天梁在子女宫(1) → index 1 != 7 != 1。其实1是田宅(7)的对宫吗？(7+6)%12=1, 是的！→ 向心自化
    #   紫微在命宫(4) → 普通飞宫
    #   太阴在交友宫(9) → 普通飞宫
    
    record = analyze_overlay_feihua(
        palaces=palaces,
        overlay_stem="乙",
        overlay_palace_idx=7,  # 田宅宫
        overlay_label="大限",
    )
    
    assert record["overlay_palace_name"] == "田宅宫"
    assert record["opp_palace_name"] == "子女宫"
    
    by_hua = {tr["hua_type"]: tr for tr in record["transformations"]}
    
    assert by_hua["化禄"]["target_star"] == "天机"
    assert by_hua["化禄"]["target_palace_name"] == "父母宫"
    assert by_hua["化禄"]["fh_type"] == FH_FLY_OUT
    print(f"  ✓ 大限田宅(乙)化禄天机 → 普通飞宫入父母宫 ✓")
    
    assert by_hua["化权"]["target_star"] == "天梁"
    assert by_hua["化权"]["target_palace_name"] == "子女宫"
    assert by_hua["化权"]["fh_type"] == FH_SELF_IN  # 天梁在子女宫=田宅对宫
    print(f"  ✓ 大限田宅(乙)化权天梁 → 向心自化（化星落对宫子女） ✓")
    
    assert by_hua["化忌"]["target_star"] == "太阴"
    assert by_hua["化忌"]["target_palace_name"] == "交友宫"
    assert by_hua["化忌"]["fh_type"] == FH_FLY_OUT
    # 交友宫对宫是兄弟宫
    assert by_hua["化忌"]["chong_palace"] == "兄弟宫"
    print(f"  ✓ 大限田宅(乙)化忌太阴 → 普通飞宫入交友，冲兄弟 ✓")
    print()


# ─────────────────────────────────────────────────────────────
# 测试 2: 大限化忌冲命宫警示
# ─────────────────────────────────────────────────────────────

def test_decade_chong_soul():
    print("=" * 70)
    print("TEST 2: 大限化忌冲命宫的关键警示")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    # 命宫 index = 4。要让大限化忌冲命宫，
    # 大限化忌应飞入 (4+6)%12=10=迁移宫
    # 哪些干→忌的星在迁移宫(贪狼)？癸干→化忌贪狼
    # 假设大限走到父母宫(index 5, 宫干癸)
    # 癸四化：禄破军、权巨门、科太阴、忌贪狼
    #   贪狼在迁移宫(10) → 5 != 10 也 != 11(父母对宫疾厄). 10 是普通飞宫
    #   贪狼在迁移宫，(10+6)%12=4=命宫 → 化忌冲命宫
    
    record = analyze_overlay_feihua(
        palaces=palaces,
        overlay_stem="癸",
        overlay_palace_idx=5,  # 父母宫
        overlay_label="大限",
    )
    
    by_hua = {tr["hua_type"]: tr for tr in record["transformations"]}
    
    assert by_hua["化忌"]["target_star"] == "贪狼"
    assert by_hua["化忌"]["target_palace_name"] == "迁移宫"
    assert by_hua["化忌"]["chong_palace"] == "命宫"
    print(f"  ✓ 大限父母(癸)化忌贪狼飞入迁移，冲命宫 ✓")
    
    # key_warnings 应该包含"冲命宫"
    warnings_str = " | ".join(record["key_warnings"])
    assert "冲命宫" in warnings_str, f"key_warnings 缺'冲命宫': {warnings_str}"
    print(f"  ✓ 关键警示包含'冲命宫': {warnings_str[:80]}... ✓")
    print()


# ─────────────────────────────────────────────────────────────
# 测试 3: 大限禄解忌
# ─────────────────────────────────────────────────────────────

def test_decade_lu_jie_ji():
    print("=" * 70)
    print("TEST 3: 大限禄解本命忌")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    # 本命化忌天同在疾厄宫(11)
    # 大限化禄=天同 → 丙干
    # 假设大限走到夫妻宫(index 2, 改干丙)
    
    record = analyze_overlay_feihua(
        palaces=palaces,
        overlay_stem="丙",
        overlay_palace_idx=2,
        overlay_label="大限",
    )
    
    by_hua = {tr["hua_type"]: tr for tr in record["transformations"]}
    
    assert by_hua["化禄"]["target_star"] == "天同"
    assert by_hua["化禄"]["target_palace_name"] == "疾厄宫"
    assert by_hua["化禄"]["is_he_won_ji"] == True
    print(f"  ✓ 大限化禄天同入疾厄(本命忌宫) → 禄解忌 ✓")
    
    warnings_str = " | ".join(record["key_warnings"])
    assert "禄解" in warnings_str or "转机" in warnings_str
    print(f"  ✓ 关键警示包含转机: ✓")
    print()


# ─────────────────────────────────────────────────────────────
# 测试 4: 流年飞化（同样套用 analyze_overlay_feihua）
# ─────────────────────────────────────────────────────────────

def test_annual_overlay():
    print("=" * 70)
    print("TEST 4: 流年飞化")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    # 流年用太岁干。比如 2026 年 = 丙午年，丙干
    # 流年命宫的 index 可用本命命宫 idx=4
    
    record = analyze_overlay_feihua(
        palaces=palaces,
        overlay_stem="丙",
        overlay_palace_idx=4,  # 用本命命宫
        overlay_label="流年2026",
    )
    
    # 丙四化：禄天同、权天机、科文昌、忌廉贞
    by_hua = {tr["hua_type"]: tr for tr in record["transformations"]}
    
    assert by_hua["化禄"]["target_star"] == "天同"
    # 天同在疾厄宫(11)
    # 流年禄入疾厄 → 化禄入本命化忌宫 → 流年禄解忌！
    assert by_hua["化禄"]["is_he_won_ji"] == True
    print(f"  ✓ 流年2026丙化禄天同入疾厄(本命忌宫) → 流年禄解忌 ✓")
    
    # 流年化忌廉贞在官禄宫(8) → 飞入官禄
    assert by_hua["化忌"]["target_star"] == "廉贞"
    assert by_hua["化忌"]["target_palace_name"] == "官禄宫"
    print(f"  ✓ 流年2026丙化忌廉贞入官禄 ✓")
    print()


# ─────────────────────────────────────────────────────────────
# 测试 5: 三盘叠合 — 本命+大限+流年忌汇聚
# ─────────────────────────────────────────────────────────────

def test_three_plate_concentration():
    print("=" * 70)
    print("TEST 5: 三盘叠合 — 忌汇聚检测")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    
    # 本命化忌：天同在疾厄宫(11)
    # 大限选个让化忌也进疾厄的，比如丙干（丙忌廉贞？不对，丙忌廉贞，廉贞在官禄不在疾厄）
    # 庚干→化忌天同，在疾厄。同干（夫妻宫干庚）
    # 大限走夫妻宫，宫干庚 → 大限化忌天同入疾厄 → 双忌叠加
    decade_overlay = analyze_overlay_feihua(palaces, "庚", 2, "大限")
    
    # 流年再来个忌进疾厄的：庚年 → 化忌天同；丁年 → 化忌巨门(在疾厄宫也是)
    # 丁化忌巨门，巨门在疾厄宫(11) → 流年忌入疾厄
    annual_overlay = analyze_overlay_feihua(palaces, "丁", 4, "流年")
    
    warnings = analyze_three_plate_concentration(
        natal_palaces=palaces,
        decade_overlay=decade_overlay,
        annual_overlay=annual_overlay,
    )
    
    # 应该有"疾厄宫三忌汇聚"
    found = False
    for w in warnings:
        if "疾厄宫" in w and ("三忌" in w or "本命忌" in w):
            found = True
            print(f"  ✓ 检测到疾厄宫忌汇聚: {w}")
            break
    assert found, f"未检测到疾厄宫忌汇聚: {warnings}"
    print()


# ─────────────────────────────────────────────────────────────
# 测试 6: format_overlay_feihua_for_prompt 输出可读性
# ─────────────────────────────────────────────────────────────

def test_format_output():
    print("=" * 70)
    print("TEST 6: 叠合飞化格式化输出")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    record = analyze_overlay_feihua(palaces, "癸", 5, "大限")
    output = format_overlay_feihua_for_prompt(record)
    
    must_have = [
        "大限盘飞化分析",
        "大限命宫",
        "父母宫",        # overlay 命宫
        "对宫",
        "大限四化",
        "癸",            # 大限干
        "贪狼",          # 癸化忌
        "化忌",
    ]
    missing = [k for k in must_have if k not in output]
    if missing:
        print(f"  ✗ 缺失关键词: {missing}")
        print("--- output ---")
        print(output)
        return False
    print(f"  ✓ 所有 {len(must_have)} 个关键词都出现")
    print(f"  · 输出长度: {len(output)} chars")
    print()
    print("--- 样例 ---")
    print(output)
    print()
    return True


# ─────────────────────────────────────────────────────────────
# 测试 7: context_builder 集成 — _overlay 字段被读取
# ─────────────────────────────────────────────────────────────

def test_context_builder_overlay():
    print("=" * 70)
    print("TEST 7: context_builder 读取 _overlay 集成测试")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    
    # 模拟前端注入的 _overlay
    data["_overlay"] = {
        "layer": "triple",
        "decade": None,  # 三盘叠合不用 decade endpoint
        "triple": {
            "decade_info": {
                "palace_idx": 5,
                "palace_name": "父母宫",
                "stem": "癸",
                "age_range": [14, 23],
            },
            "decade_feihua": [],  # 旧字段，新逻辑不依赖
            "annual_feihua": [],  # 旧字段，新逻辑不依赖
            "combined_warnings": [],
            "age": 26,
            "current_year": 2026,
        }
    }
    
    output = build_ziwei_context(data)
    
    must_have = [
        "当前用户视图",      # 标签
        "三盘叠合",
        "大限盘飞化分析",    # 大限段
        "父母宫",
        "癸",
        "流年2026盘飞化分析",  # 流年段（labelled as "流年2026"）
        "年龄",              # age_range
    ]
    missing = [k for k in must_have if k not in output]
    if missing:
        print(f"  ✗ 缺失关键词: {missing}")
        idx_overlay = output.find("当前用户视图")
        if idx_overlay >= 0:
            print(f"--- overlay 段 ---")
            print(output[idx_overlay:idx_overlay+2000])
        return False
    print(f"  ✓ 所有 {len(must_have)} 个关键词都出现")
    print(f"  · 输出总长度: {len(output)} chars (vs 无 overlay 时 ~5200 chars)")
    print()
    return True


# ─────────────────────────────────────────────────────────────
# 测试 8: 只有 decade 没有 triple 时，能正常工作
# ─────────────────────────────────────────────────────────────

def test_context_builder_decade_only():
    print("=" * 70)
    print("TEST 8: 只有 decade（用户在 decade 视图）的情况")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    data["_overlay"] = {
        "layer": "decade",
        "decade": {
            "decade": {
                "palace_idx": 5,
                "palace_name": "父母宫",
                "stem": "癸",
                "age_range": [14, 23],
            },
            "feihua": [],
        },
        "triple": None,
    }
    
    output = build_ziwei_context(data)
    
    assert "大限盘飞化分析" in output, "应包含大限段"
    assert "大限视图" in output, "应识别 layer=decade"
    # 没有流年段
    assert "流年" not in output or "流年" not in output[output.find("【数据范围】"):], "不应有流年段"
    print(f"  ✓ decade-only 视图正确处理 ✓")
    print()


# ─────────────────────────────────────────────────────────────
# 测试 9: 完全没有 _overlay 时，行为与之前一致（向后兼容）
# ─────────────────────────────────────────────────────────────

def test_context_builder_no_overlay():
    print("=" * 70)
    print("TEST 9: 没有 _overlay 字段（向后兼容）")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    # 不注入 _overlay
    output = build_ziwei_context(data)
    
    # 应该没有大限/流年段
    assert "大限盘飞化分析" not in output
    assert "流年" not in output or "流年" not in output.split("【数据范围】")[0]
    # 应该有"未调用大限/流年"的提示
    assert "前端未调用" in output
    print(f"  ✓ 无 overlay 时未引入大限/流年段，保持向后兼容 ✓")
    print()


if __name__ == "__main__":
    test_decade_basic()
    test_decade_chong_soul()
    test_decade_lu_jie_ji()
    test_annual_overlay()
    test_three_plate_concentration()
    ok6 = test_format_output()
    ok7 = test_context_builder_overlay()
    test_context_builder_decade_only()
    test_context_builder_no_overlay()
    print()
    print("=" * 70)
    if ok6 and ok7:
        print("ALL OVERLAY TESTS PASSED")
    else:
        print("SOME OVERLAY TESTS FAILED")
    print("=" * 70)
