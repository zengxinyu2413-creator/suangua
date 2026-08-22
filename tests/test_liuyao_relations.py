"""
Tests for core/liuyao/relations.py — L-1 六爻关系深度分析
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.relations import (
    identify_yuanshen_jishen_choushen,
    find_lines_by_wuxing,
    check_jin_tui_shen,
    analyze_changed_line_relation,
    analyze_line_strength_detail,
    get_changsheng_status,
    analyze_liuyao_deep_relations,
    format_liuyao_relations_for_prompt,
)


def test_yuanshen_jishen_choushen():
    """用神金 → 原神土、忌神火、仇神木"""
    print("=" * 70)
    print("TEST 1: 原神/忌神/仇神判定")
    print("=" * 70)
    r = identify_yuanshen_jishen_choushen("金")
    assert r["用神_wx"] == "金"
    assert r["原神_wx"] == "土"  # 土生金
    assert r["忌神_wx"] == "火"  # 火克金
    assert r["仇神_wx"] == "木"  # 木生火
    assert r["食神_wx"] == "水"  # 金生水
    print(f"  ✓ 用神金 → 原神{r['原神_wx']} / 忌神{r['忌神_wx']} / 仇神{r['仇神_wx']}")
    
    # 用神木 → 原神水、忌神金、仇神土
    r2 = identify_yuanshen_jishen_choushen("木")
    assert r2["原神_wx"] == "水"
    assert r2["忌神_wx"] == "金"
    assert r2["仇神_wx"] == "土"
    print(f"  ✓ 用神木 → 原神{r2['原神_wx']} / 忌神{r2['忌神_wx']} / 仇神{r2['仇神_wx']}")
    print()


def test_changsheng():
    """十二长生：金长生在巳"""
    print("=" * 70)
    print("TEST 2: 十二长生状态")
    print("=" * 70)
    # 金长生在巳
    r = get_changsheng_status("金", "巳")
    assert r["status"] == "长生"
    print(f"  ✓ 金在巳 → 长生 (力量+{r['force']})")
    
    # 金帝旺在酉（长生巳 + 4 = 酉）
    r2 = get_changsheng_status("金", "酉")
    assert r2["status"] == "帝旺"
    print(f"  ✓ 金在酉 → 帝旺 (力量+{r2['force']})")
    
    # 金墓在丑（长生巳 + 8 = 丑）
    r3 = get_changsheng_status("金", "丑")
    assert r3["status"] == "墓"
    print(f"  ✓ 金在丑 → 墓 (力量{r3['force']})")
    
    # 木长生在亥
    r4 = get_changsheng_status("木", "亥")
    assert r4["status"] == "长生"
    print(f"  ✓ 木在亥 → 长生")
    print()


def test_jin_tui_shen():
    """进退神"""
    print("=" * 70)
    print("TEST 3: 进神/退神")
    print("=" * 70)
    # 寅 → 卯（木进神）
    r = check_jin_tui_shen("寅", "卯")
    assert r["type"] == "进神"
    print(f"  ✓ 寅→卯 进神")
    
    # 卯 → 寅（退神）
    r2 = check_jin_tui_shen("卯", "寅")
    assert r2["type"] == "退神"
    print(f"  ✓ 卯→寅 退神")
    
    # 申 → 酉 进神
    r3 = check_jin_tui_shen("申", "酉")
    assert r3["type"] == "进神"
    print(f"  ✓ 申→酉 进神")
    
    # 子 → 卯 既不进也不退（跨五行）
    r4 = check_jin_tui_shen("子", "卯")
    assert r4["type"] == ""
    print(f"  ✓ 跨五行非进退神")
    print()


def test_changed_line_relation():
    """爻动后回头生/回头克"""
    print("=" * 70)
    print("TEST 4: 爻动 → 变爻关系")
    print("=" * 70)
    # 寅木动化亥水：水生木 = 回头生
    orig = {"branch": "寅"}
    changed = {"branch": "亥"}
    r = analyze_changed_line_relation(orig, changed)
    assert r["relation"] == "回头生"
    print(f"  ✓ 寅木→亥水 = 回头生")
    
    # 寅木动化酉金：金克木 = 回头克
    orig2 = {"branch": "寅"}
    changed2 = {"branch": "酉"}
    r2 = analyze_changed_line_relation(orig2, changed2)
    assert r2["relation"] == "回头克"
    print(f"  ✓ 寅木→酉金 = 回头克")
    
    # 寅木动化午火：木生火 = 化泄
    orig3 = {"branch": "寅"}
    changed3 = {"branch": "午"}
    r3 = analyze_changed_line_relation(orig3, changed3)
    assert r3["relation"] == "化泄"
    print(f"  ✓ 寅木→午火 = 化泄")
    print()


def test_line_strength():
    """爻力量评估"""
    print("=" * 70)
    print("TEST 5: 月日辰旺衰评估")
    print("=" * 70)
    # 金爻在巳月 + 酉日 → 月长生 + 日帝旺 = 极旺
    line = {"branch": "酉"}
    r = analyze_line_strength_detail(line, month_zhi="巳", day_zhi="酉")
    print(f"  · 金酉爻 月{r['month_chs']['status']}/日{r['day_chs']['status']}: {r['overall']}")
    assert r["overall"] in ("极旺", "旺相")
    print(f"  ✓ 金爻在巳月酉日 → {r['overall']}")
    
    # 木爻在申月 + 申日 → 月绝 + 日绝 = 无气
    line2 = {"branch": "卯"}
    r2 = analyze_line_strength_detail(line2, month_zhi="申", day_zhi="申")
    print(f"  · 木卯爻 月{r2['month_chs']['status']}/日{r2['day_chs']['status']}: {r2['overall']}")
    assert r2["overall"] in ("无气", "休囚")
    print(f"  ✓ 木爻在申月申日 → {r2['overall']}")
    
    # 月破检查：午爻遇子月 = 月破
    line3 = {"branch": "午"}
    r3 = analyze_line_strength_detail(line3, month_zhi="子", day_zhi="未")
    assert r3["is_yuepo"] == True
    print(f"  ✓ 午爻遇子月 → 月破")
    print()


def test_find_lines_by_wuxing():
    """按五行找爻"""
    print("=" * 70)
    print("TEST 6: 按五行查找爻")
    print("=" * 70)
    yaos = [
        {"branch": "卯", "liu_qin": "父母"},  # 木
        {"branch": "巳", "liu_qin": "兄弟"},  # 火
        {"branch": "未", "liu_qin": "子孙"},  # 土
        {"branch": "酉", "liu_qin": "妻财"},  # 金
        {"branch": "亥", "liu_qin": "官鬼"},  # 水
        {"branch": "丑", "liu_qin": "子孙"},  # 土
    ]
    # 找土爻
    found = find_lines_by_wuxing(yaos, "土")
    assert len(found) == 2
    branches = [x["branch"] for x in found]
    assert "未" in branches and "丑" in branches
    print(f"  ✓ 找土爻：{branches}")
    
    # 找金爻
    found2 = find_lines_by_wuxing(yaos, "金")
    assert len(found2) == 1
    assert found2[0]["branch"] == "酉"
    print(f"  ✓ 找金爻：{found2[0]['branch']}")
    print()


def test_full_analysis():
    """完整分析"""
    print("=" * 70)
    print("TEST 7: 完整六爻关系分析")
    print("=" * 70)
    yaos = [
        {"branch": "卯", "liu_qin": "父母", "is_changing": False},
        {"branch": "巳", "liu_qin": "兄弟", "is_changing": False},
        {"branch": "未", "liu_qin": "子孙", "is_changing": True},
        {"branch": "酉", "liu_qin": "妻财", "is_changing": False},
        {"branch": "亥", "liu_qin": "官鬼", "is_changing": False},
        {"branch": "丑", "liu_qin": "子孙", "is_changing": False},
    ]
    # 男占婚姻：用神妻财
    yong_info = {"liuqin": "妻财"}
    result = analyze_liuyao_deep_relations(
        yaos, yong_shen_info=yong_info,
        month_zhi="巳", day_zhi="申",
    )
    
    assert result["yong_yuan_ji_chou"]["用神_wx"] == "金"
    assert len(result["key_lines"]["用神_lines"]) == 1
    assert len(result["key_lines"]["原神_lines"]) == 2  # 未+丑
    assert len(result["key_lines"]["忌神_lines"]) == 1  # 巳
    
    print(f"  ✓ 用神妻财金：第 4 爻")
    print(f"  ✓ 原神土：{len(result['key_lines']['原神_lines'])} 处（未/丑）")
    print(f"  ✓ 忌神火：{len(result['key_lines']['忌神_lines'])} 处（巳）")
    
    text = format_liuyao_relations_for_prompt(result)
    assert "六爻关系深度分析" in text
    assert "用神=金" in text
    print(f"  ✓ prompt 输出长度 {len(text)} chars")
    print()


def test_empty_input():
    """空输入兜底"""
    print("=" * 70)
    print("TEST 8: 空输入兜底")
    print("=" * 70)
    result = analyze_liuyao_deep_relations([])
    assert result["yong_yuan_ji_chou"] == {} or not result["yong_yuan_ji_chou"]
    text = format_liuyao_relations_for_prompt(result)
    assert len(text) > 0  # 至少有标题
    print(f"  ✓ 空输入不报错")
    print()


if __name__ == "__main__":
    test_yuanshen_jishen_choushen()
    test_changsheng()
    test_jin_tui_shen()
    test_changed_line_relation()
    test_line_strength()
    test_find_lines_by_wuxing()
    test_full_analysis()
    test_empty_input()
    print("=" * 70)
    print("ALL L-1 LIUYAO RELATIONS TESTS PASSED")
    print("=" * 70)
