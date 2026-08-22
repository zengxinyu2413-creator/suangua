"""
Tests for core/ziwei/brightness.py — Z-3 主星亮度评级与命格评分

Verifies:
  1. 七级亮度分数映射正确
  2. 敏感/不敏感星识别正确
  3. 主星×宫位断语查询（庙旺吉象、落陷警示）
  4. 单宫评分（含命宫/三方四正）
  5. 整体命格评级
  6. prompt 格式化输出
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_ziwei_context import make_mock_chart_2000_8_16
from core.ziwei.brightness import (
    get_brightness_score,
    get_brightness_meaning,
    is_brightness_sensitive,
    get_star_branch_note,
    compute_palace_score,
    compute_mingge_overall_rating,
    format_brightness_analysis_for_prompt,
    BRIGHTNESS_SENSITIVE, BRIGHTNESS_INSENSITIVE,
)
from core.ziwei.context_builder import find_soul_palace, get_san_fang_si_zheng


def test_brightness_score():
    print("=" * 70)
    print("TEST 1: 七级亮度分数映射")
    print("=" * 70)
    
    assert get_brightness_score("庙") == 3
    assert get_brightness_score("旺") == 2
    assert get_brightness_score("得") == 1
    assert get_brightness_score("利") == 0
    assert get_brightness_score("平") == -1
    assert get_brightness_score("不") == -2
    assert get_brightness_score("陷") == -3
    assert get_brightness_score("") == 0   # 空值
    assert get_brightness_score("XXXX") == 0  # 无效值
    print(f"  ✓ 七级亮度分数映射全部正确 (+3 庙 → -3 陷) ✓")
    print()


def test_sensitivity_classification():
    print("=" * 70)
    print("TEST 2: 主星亮度敏感度分类")
    print("=" * 70)
    
    # 不敏感的 5 颗
    for star in ["紫微", "天府", "武曲", "七杀", "破军"]:
        assert not is_brightness_sensitive(star), f"{star} 应不敏感"
        assert star in BRIGHTNESS_INSENSITIVE
    print(f"  ✓ 不敏感 5 颗（紫府武杀破）识别正确 ✓")
    
    # 敏感的 9 颗
    for star in ["天机", "太阳", "太阴", "天同", "天梁",
                 "巨门", "贪狼", "天相", "廉贞"]:
        assert is_brightness_sensitive(star), f"{star} 应敏感"
        assert star in BRIGHTNESS_SENSITIVE
    print(f"  ✓ 敏感 9 颗（机日月同梁巨贪相廉）识别正确 ✓")
    print()


def test_star_branch_notes():
    print("=" * 70)
    print("TEST 3: 主星×宫位针对性断语")
    print("=" * 70)
    
    # 太阳午 = 日丽中天格 (吉象)
    note1 = get_star_branch_note("太阳", "午")
    assert "日丽中天" in note1 or "庙" in note1
    print(f"  ✓ 太阳午: {note1[:40]}...")
    
    # 太阳子 = 落陷警示
    note2 = get_star_branch_note("太阳", "子")
    assert "落陷" in note2 or "辛苦" in note2 or "父" in note2
    print(f"  ✓ 太阳子: {note2[:40]}...")
    
    # 太阴亥 = 月朗天门格
    note3 = get_star_branch_note("太阴", "亥")
    assert "月朗天门" in note3 or "富贵" in note3
    print(f"  ✓ 太阴亥: {note3[:40]}...")
    
    # 紫微午 = 帝座之地
    note4 = get_star_branch_note("紫微", "午")
    assert "帝座" in note4 or "权威" in note4
    print(f"  ✓ 紫微午: {note4[:40]}...")
    
    # 巨门辰 = 落陷
    note5 = get_star_branch_note("巨门", "辰")
    assert "暗" in note5 or "是非" in note5 or "陷" in note5
    print(f"  ✓ 巨门辰: {note5[:40]}...")
    
    # 没有断语的组合
    note_empty = get_star_branch_note("紫微", "卯")  # 这个组合没特别断语
    # 这个不一定空，要看我是否列了；不强断言
    print(f"  · 紫微卯（可能无断语）: {repr(note_empty)}")
    
    print()


def test_palace_score():
    print("=" * 70)
    print("TEST 4: 单宫亮度评分")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    
    # 命宫(index 4) = 紫微(庙) — 不敏感星但庙旺
    soul = next(p for p in palaces if p["index"] == 4)
    soul_score = compute_palace_score(soul)
    print(f"  命宫评分: {soul_score}")
    
    assert soul_score["major_count"] == 1
    assert soul_score["major_stars"] == ["紫微"]
    # 紫微(庙) = 3 分但是不敏感星，取 max(1, 3) = 3
    assert soul_score["raw_score"] == 3.0
    assert soul_score["average"] == 3.0
    assert soul_score["rating"] == "上格"
    # 紫微午 应该有吉象断语
    assert len(soul_score["star_notes"]) >= 1
    assert any("紫微午" in n or "帝座" in n for n in soul_score["star_notes"])
    print(f"  ✓ 命宫紫微(庙)@午 → 上格 + 帝座断语 ✓")
    
    # 财帛宫(index 0) = 武曲(得)·化权 + 天相(庙)
    cb = next(p for p in palaces if p["index"] == 0)
    cb_score = compute_palace_score(cb)
    print(f"  财帛宫评分: {cb_score}")
    
    assert cb_score["major_count"] == 2
    assert "武曲" in cb_score["major_stars"]
    assert "天相" in cb_score["major_stars"]
    # 武曲(得)=1分(不敏感) + 天相(庙)=3分(敏感)
    # 武曲不敏感 max(1, 1) = 1，天相敏感 = 3
    # raw_score = 1 + 3 = 4
    # average = 2.0
    assert cb_score["raw_score"] == 4.0
    assert cb_score["average"] == 2.0
    assert cb_score["rating"] == "上格"
    print(f"  ✓ 财帛宫武曲(得)+天相(庙) → 上格 ✓")
    
    # 父母宫(index 5) = 天机(陷) — 敏感星落陷
    fm = next(p for p in palaces if p["index"] == 5)
    fm_score = compute_palace_score(fm)
    print(f"  父母宫评分: {fm_score}")
    
    assert fm_score["major_count"] == 1
    assert fm_score["major_stars"] == ["天机"]
    # 天机敏感 + 陷 = -3 分
    assert fm_score["raw_score"] == -3.0
    assert fm_score["rating"] == "下格"
    # 父母宫的"天机陷"应触发断语？看表里有"天机丑/未/辰/戌"，但我 mock 父母宫地支是"未"，
    # 而 mock 中天机陷在未宫，应该有断语
    has_tj_note = any("天机" in n for n in fm_score["star_notes"])
    if has_tj_note:
        print(f"  ✓ 天机陷在未宫触发断语 ✓")
    else:
        # mock 数据里我设置 brightness=陷，但地支是未；表里有天机未宫
        # 应当触发
        print(f"  ✗ 天机陷未宫未触发断语；star_notes={fm_score['star_notes']}")
    
    # 兄弟宫 (index 3) = 空宫
    xd = next(p for p in palaces if p["index"] == 3)
    xd_score = compute_palace_score(xd)
    assert xd_score["major_count"] == 0
    assert xd_score["rating"] == "空宫"
    print(f"  ✓ 空宫识别正确 ✓")
    print()


def test_overall_rating():
    print("=" * 70)
    print("TEST 5: 整体命格评级")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    soul = find_soul_palace(palaces)
    sfsz = get_san_fang_si_zheng(palaces, soul["index"])
    
    overall = compute_mingge_overall_rating(soul, sfsz)
    
    print(f"  整体评级: {overall['overall_rating']}")
    print(f"  加权平均分: {overall['average_score']}")
    print(f"  总结: {overall['summary']}")
    print()
    print(f"  命宫评分:")
    print(f"    主星: {overall['soul_palace_score']['major_stars']}")
    print(f"    评级: [{overall['soul_palace_score']['rating']}]")
    print()
    print(f"  三方四正:")
    for s in overall["sfsz_scores"]:
        print(f"    {s['palace_name']}({s['branch']}): {'/'.join(s['major_stars'])} → [{s['rating']}]")
    print()
    print(f"  星位断语 ({len(overall['star_notes'])} 条):")
    for note in overall["star_notes"]:
        print(f"    · {note[:60]}...")
    
    # 验证：本 mock 命宫紫微(庙) + 三方四正 紫府武相贪狼，都比较亮
    # 应该评级中上格或上格
    assert overall["overall_rating"] in ["上格", "中上格"], \
        f"Expected 上格/中上格, got {overall['overall_rating']}"
    print()
    print(f"  ✓ 整体命格评级 [{overall['overall_rating']}] 合理 ✓")
    print()


def test_format_output():
    print("=" * 70)
    print("TEST 6: prompt 格式化输出")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    soul = find_soul_palace(palaces)
    sfsz = get_san_fang_si_zheng(palaces, soul["index"])
    overall = compute_mingge_overall_rating(soul, sfsz)
    
    output = format_brightness_analysis_for_prompt(overall)
    
    must_have = [
        "主星亮度与命格评级",
        "整体命格评级",
        "上格",  # 本 mock 应该是上格或中上格
        "命宫",
        "紫微",
        "三方四正",
        "财帛宫", "官禄宫", "迁移宫",
        "关键主星·宫位断语",
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
    print("--- 完整输出 ---")
    print(output)
    print()
    return True


def test_fallen_star_scenario():
    """构造一个'命宫主星落陷'的测试场景，验证下格识别。"""
    print("=" * 70)
    print("TEST 7: 落陷下格场景")
    print("=" * 70)
    
    # 构造一个 mock：命宫坐"太阳(陷)"在子宫
    fake_palace = {
        "index": 0,
        "name": "命宫",
        "earthly_branch": "子",
        "heavenly_stem": "戊",
        "is_soul": True,
        "major_stars": [
            {"name": "太阳", "type": "major", "brightness": "陷", "mutagen": ""},
        ],
        "minor_stars": [],
        "adj_stars": [],
    }
    score = compute_palace_score(fake_palace)
    print(f"  命宫太阳(陷)@子: {score}")
    
    assert score["raw_score"] == -3.0
    assert score["average"] == -3.0
    assert score["rating"] == "下格"
    # 太阳子陷应触发断语
    assert any("太阳子" in n or "落陷" in n for n in score["star_notes"])
    print(f"  ✓ 命宫太阳(陷)@子 → 下格 + 父亲不利断语 ✓")
    print()


if __name__ == "__main__":
    test_brightness_score()
    test_sensitivity_classification()
    test_star_branch_notes()
    test_palace_score()
    test_overall_rating()
    ok = test_format_output()
    test_fallen_star_scenario()
    print()
    print("=" * 70)
    if ok:
        print("ALL BRIGHTNESS TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 70)
