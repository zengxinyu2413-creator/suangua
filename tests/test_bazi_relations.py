"""
Tests for core/bazi/relations.py — B-1 地支刑冲合害自动检测引擎。

覆盖：六合、三合、半合、三会、六冲、三刑、互刑、自刑、相害、相破，
+ 大运/流年应期触发。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bazi.relations import (
    analyze_all_relations,
    analyze_dayun_liunian_trigger,
    format_relations_for_prompt,
    detect_liu_he, detect_san_he, detect_san_hui,
    detect_liu_chong, detect_xing, detect_hai, detect_po,
    LIU_HE, SAN_HE, LIU_CHONG,
)


def make_chart(y, m, d, h):
    """构造一个迷你 chart 用于测试，只填四柱地支"""
    return {
        "year_pillar":  {"tiangan": "庚", "dizhi": y},
        "month_pillar": {"tiangan": "癸", "dizhi": m},
        "day_pillar":   {"tiangan": "庚", "dizhi": d},
        "hour_pillar":  {"tiangan": "己", "dizhi": h},
    }


def test_liu_he():
    """六合：午未、子丑、寅亥"""
    print("=" * 70)
    print("TEST 1: 六合检测")
    print("=" * 70)
    
    # 午未六合
    chart = make_chart("午", "未", "辰", "卯")
    he = detect_liu_he([
        ("year_pillar", "午"), ("month_pillar", "未"),
        ("day_pillar", "辰"), ("hour_pillar", "卯"),
    ])
    assert len(he) == 1
    assert he[0]["type"] == "六合"
    assert "土" == he[0]["wuxing"]
    print(f"  ✓ 午未六合化土 — {he[0]['interpretation']}")

    # 子丑六合
    chart2 = make_chart("子", "丑", "辰", "戌")
    he2 = detect_liu_he([
        ("year_pillar", "子"), ("month_pillar", "丑"),
        ("day_pillar", "辰"), ("hour_pillar", "戌"),
    ])
    assert len(he2) >= 1
    assert any(e["branches"] in [["子","丑"],["丑","子"]] for e in he2)
    print(f"  ✓ 子丑六合检测")
    print()


def test_san_he_complete():
    """完整三合局：申子辰水"""
    print("=" * 70)
    print("TEST 2: 三合局检测（完整三支）")
    print("=" * 70)
    
    branches = [
        ("year_pillar", "申"), ("month_pillar", "子"),
        ("day_pillar", "辰"), ("hour_pillar", "寅"),
    ]
    he = detect_san_he(branches)
    
    triples = [e for e in he if e["type"] == "三合局"]
    assert len(triples) == 1
    assert triples[0]["wuxing"] == "水"
    print(f"  ✓ 申子辰三合水局 — {triples[0]['interpretation']}")

    # 寅午戌三合火
    branches2 = [
        ("year_pillar", "寅"), ("month_pillar", "午"),
        ("day_pillar", "戌"), ("hour_pillar", "亥"),
    ]
    he2 = detect_san_he(branches2)
    triples2 = [e for e in he2 if e["type"] == "三合局"]
    assert triples2[0]["wuxing"] == "火"
    print(f"  ✓ 寅午戌三合火局")
    print()


def test_san_he_half():
    """半三合：只有两支"""
    print("=" * 70)
    print("TEST 3: 半三合检测")
    print("=" * 70)
    
    # 申子半合水（无辰）
    branches = [
        ("year_pillar", "申"), ("month_pillar", "子"),
        ("day_pillar", "卯"), ("hour_pillar", "未"),
    ]
    he = detect_san_he(branches)
    # 应包含 申子半合 和 卯未半合木
    half_events = [e for e in he if e["type"] == "半三合"]
    assert len(half_events) >= 1
    wuxings = [e["wuxing"] for e in half_events]
    print(f"  ✓ 检测到 {len(half_events)} 个半合：五行 {wuxings}")
    print()


def test_san_he_no_dup_with_full():
    """完整三合不重复报半合"""
    print("=" * 70)
    print("TEST 4: 完整三合不应同时报半合")
    print("=" * 70)
    
    branches = [
        ("year_pillar", "申"), ("month_pillar", "子"),
        ("day_pillar", "辰"), ("hour_pillar", "丑"),
    ]
    he = detect_san_he(branches)
    # 申子辰是完整三合水，不应再报 申子/子辰 半合
    half_events = [e for e in he if e["type"] == "半三合"]
    # 半合事件不应包含申/子/辰的组合
    for e in half_events:
        assert set(e["branches"]) - {"申", "子", "辰"} != set(), \
            f"完整三合中的支不应再报半合：{e}"
    print(f"  ✓ 完整三合中的支不会重复报半合")
    print()


def test_san_hui():
    """三会方"""
    print("=" * 70)
    print("TEST 5: 三会方检测")
    print("=" * 70)
    
    branches = [
        ("year_pillar", "寅"), ("month_pillar", "卯"),
        ("day_pillar", "辰"), ("hour_pillar", "丑"),
    ]
    he = detect_san_hui(branches)
    assert len(he) == 1
    assert he[0]["wuxing"] == "木"
    print(f"  ✓ 寅卯辰三会东方木 — {he[0]['interpretation']}")
    print()


def test_liu_chong():
    """六冲"""
    print("=" * 70)
    print("TEST 6: 六冲检测")
    print("=" * 70)
    
    # 子午冲
    branches = [
        ("year_pillar", "子"), ("month_pillar", "未"),
        ("day_pillar", "午"), ("hour_pillar", "戌"),
    ]
    chongs = detect_liu_chong(branches)
    assert len(chongs) >= 1
    # 至少有子午冲
    has_ziwu = any(set(c["branches"]) == {"子", "午"} for c in chongs)
    assert has_ziwu
    print(f"  ✓ 子午冲检测")

    # 日月冲：寅申冲（日柱寅、月柱申）
    branches2 = [
        ("year_pillar", "辰"), ("month_pillar", "申"),
        ("day_pillar", "寅"), ("hour_pillar", "戌"),
    ]
    chongs2 = detect_liu_chong(branches2)
    ym_chong = [c for c in chongs2 if "日月相冲" in c.get("key", "")]
    assert len(ym_chong) >= 1
    print(f"  ✓ 日月相冲位置识别 — {ym_chong[0]['key']}")
    print()


def test_xing():
    """三刑/互刑/自刑"""
    print("=" * 70)
    print("TEST 7: 相刑检测")
    print("=" * 70)
    
    # 寅巳申三刑
    branches = [
        ("year_pillar", "寅"), ("month_pillar", "巳"),
        ("day_pillar", "申"), ("hour_pillar", "辰"),
    ]
    xing = detect_xing(branches)
    san_xing = [e for e in xing if e["type"] == "三刑"]
    assert len(san_xing) >= 1
    print(f"  ✓ 寅巳申三刑（无恩之刑）— {san_xing[0]['interpretation']}")

    # 子卯互刑
    branches2 = [
        ("year_pillar", "子"), ("month_pillar", "卯"),
        ("day_pillar", "辰"), ("hour_pillar", "戌"),
    ]
    xing2 = detect_xing(branches2)
    hu_xing = [e for e in xing2 if e["type"] == "互刑"]
    assert len(hu_xing) >= 1
    print(f"  ✓ 子卯互刑（无礼之刑）")

    # 辰辰自刑
    branches3 = [
        ("year_pillar", "辰"), ("month_pillar", "申"),
        ("day_pillar", "辰"), ("hour_pillar", "戌"),
    ]
    xing3 = detect_xing(branches3)
    self_xing = [e for e in xing3 if e["type"] == "自刑"]
    assert len(self_xing) >= 1
    assert self_xing[0]["branches"][0] == "辰"
    print(f"  ✓ 辰辰自刑")
    print()


def test_hai():
    """相害"""
    print("=" * 70)
    print("TEST 8: 相害检测")
    print("=" * 70)
    
    # 卯辰相害
    branches = [
        ("year_pillar", "卯"), ("month_pillar", "辰"),
        ("day_pillar", "未"), ("hour_pillar", "戌"),
    ]
    hai = detect_hai(branches)
    has_mao_chen = any(set(e["branches"]) == {"卯", "辰"} for e in hai)
    assert has_mao_chen
    print(f"  ✓ 卯辰相害")
    print()


def test_full_analysis_real_chart():
    """真实命盘整合：1990-7-14 卯时男（庚午癸未庚辰己卯）"""
    print("=" * 70)
    print("TEST 9: 完整分析 — 1990-7-14 卯时男")
    print("=" * 70)
    
    chart = {
        "year_pillar":  {"tiangan": "庚", "dizhi": "午"},
        "month_pillar": {"tiangan": "癸", "dizhi": "未"},
        "day_pillar":   {"tiangan": "庚", "dizhi": "辰"},
        "hour_pillar":  {"tiangan": "己", "dizhi": "卯"},
    }
    result = analyze_all_relations(chart)
    
    # 应有：午未六合、未卯半合木、辰卯相害
    assert result["summary"]["total_he"] >= 2  # 六合 + 半合
    assert result["summary"]["total_hai"] >= 1
    assert result["summary"]["total_chong"] == 0
    
    # 检查具体语义
    he_branches = [tuple(sorted(e["branches"])) for e in result["he"]]
    assert ("午", "未") in he_branches or ("未", "午") in he_branches
    
    text = format_relations_for_prompt(result)
    assert "午未六合化土" in text or "午与月柱未六合化土" in text
    assert "卯相害" in text or "辰" in text
    print(f"  ✓ 真实命盘检测出：六合×1、半合×1、相害×1")
    print(f"  ✓ prompt 格式化输出长度 {len(text)} chars")
    print()


def test_dayun_trigger():
    """大运流年应期触发"""
    print("=" * 70)
    print("TEST 10: 大运/流年应期触发")
    print("=" * 70)
    
    chart = {
        "year_pillar":  {"tiangan": "庚", "dizhi": "午"},
        "month_pillar": {"tiangan": "癸", "dizhi": "未"},
        "day_pillar":   {"tiangan": "庚", "dizhi": "辰"},
        "hour_pillar":  {"tiangan": "己", "dizhi": "卯"},
    }
    
    # 大运子，应冲本命午（年柱）
    triggers = analyze_dayun_liunian_trigger(chart, "子", "大运")
    chongs = [t for t in triggers if t["type"] == "冲"]
    assert len(chongs) >= 1
    assert "午" in chongs[0]["target"]
    print(f"  ✓ 大运子冲年柱午 — {chongs[0]['interpretation']}")
    
    # 流年酉，应与辰六合化金
    triggers2 = analyze_dayun_liunian_trigger(chart, "酉", "流年2029")
    hes = [t for t in triggers2 if t["type"] == "合"]
    assert len(hes) >= 1
    print(f"  ✓ 流年酉合本命辰 — {hes[0]['interpretation']}")
    print()


def test_no_dup_po_when_he_or_chong():
    """六合或六冲优先，破不重复报"""
    print("=" * 70)
    print("TEST 11: 巳申/寅亥既合也破，应只报合不报破")
    print("=" * 70)
    
    branches = [
        ("year_pillar", "巳"), ("month_pillar", "申"),
        ("day_pillar", "丑"), ("hour_pillar", "酉"),
    ]
    po = detect_po(branches)
    # 巳申既是合（六合）也是破，应跳过破
    sishen_po = [e for e in po if set(e["branches"]) == {"巳", "申"}]
    assert len(sishen_po) == 0, "巳申已构成六合，相破应跳过"
    print(f"  ✓ 巳申已构成六合，相破被正确跳过")
    print()


def test_empty_chart():
    """空命盘不报错"""
    print("=" * 70)
    print("TEST 12: 空输入兜底")
    print("=" * 70)
    
    result = analyze_all_relations({})
    assert result["summary"]["total_he"] == 0
    text = format_relations_for_prompt(result)
    assert "无明显刑冲合害" in text
    print(f"  ✓ 空输入返回 0 关系，不报错")
    print()


if __name__ == "__main__":
    test_liu_he()
    test_san_he_complete()
    test_san_he_half()
    test_san_he_no_dup_with_full()
    test_san_hui()
    test_liu_chong()
    test_xing()
    test_hai()
    test_full_analysis_real_chart()
    test_dayun_trigger()
    test_no_dup_po_when_he_or_chong()
    test_empty_chart()
    print("=" * 70)
    print("ALL B-1 RELATIONS TESTS PASSED")
    print("=" * 70)
