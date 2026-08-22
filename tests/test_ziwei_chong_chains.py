"""
Tests for core/ziwei/chong_analysis.py — Z-8 冲宫连锁深度分析。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ziwei.chong_analysis import (
    interpret_single_chong_event,
    get_chong_multilayer_semantics,
    collect_chong_events_from_feihua_records,
    analyze_chong_chains,
    format_chong_chains_for_prompt,
    PALACE_TO_PERSON,
    PALACE_THEME_SHORT,
    HUA_IMPACT_LEVEL,
)


def test_palace_to_person():
    """所有 12 宫都应有人物映射"""
    print("=" * 70)
    print("TEST 1: 宫位 → 人物映射")
    print("=" * 70)
    expected = ["命宫","兄弟宫","夫妻宫","子女宫","财帛宫","疾厄宫",
                "迁移宫","交友宫","官禄宫","田宅宫","福德宫","父母宫"]
    for p in expected:
        assert p in PALACE_TO_PERSON, f"{p} 缺失"
        assert p in PALACE_THEME_SHORT, f"{p} 主题缺失"
    print(f"  ✓ 12 宫人物映射完整")
    print(f"  ✓ 12 宫主题缩写完整")
    print()


def test_interpret_single_event():
    print("=" * 70)
    print("TEST 2: 单事件解读")
    print("=" * 70)
    
    # 普通飞宫冲
    event = {
        "from_palace":  "疾厄宫",
        "hua_type":     "化忌",
        "star":         "巨门",
        "target_palace": "迁移宫",
        "chong_palace": "命宫",
        "layer":        "natal",
        "fh_type":      "普通飞宫",
    }
    s = interpret_single_chong_event(event)
    assert "本命疾厄宫" in s
    assert "化忌" in s and "巨门" in s
    assert "命宫" in s and "本人" in s
    print(f"  ✓ 普通飞宫: {s}")

    # 自化冲
    event2 = {
        "from_palace":  "夫妻宫",
        "hua_type":     "化忌",
        "star":         "天同",
        "target_palace": "夫妻宫",
        "chong_palace": "官禄宫",
        "layer":        "decade",
        "fh_type":      "离心自化",
    }
    s2 = interpret_single_chong_event(event2)
    assert "大限" in s2
    assert "自化忌" in s2
    assert "事业" in s2  # 官禄宫的主题
    print(f"  ✓ 自化冲: {s2}")
    print()


def test_multilayer_semantics():
    print("=" * 70)
    print("TEST 3: 多层语义解读")
    print("=" * 70)
    
    palaces_by_idx = {
        2: {"name": "命宫"},
        5: {"name": "田宅宫"},
        8: {"name": "迁移宫"},
    }
    decade_layout = {
        2: {"name": "大限子女", "short": "大-子", "offset": 3},
        5: {"name": "大限命宫", "short": "大-命", "offset": 0},
        8: {"name": "大限官禄", "short": "大-官", "offset": 8},
    }
    annual_layout = {
        2: {"name": "流年夫妻", "short": "年-夫", "offset": 2},
    }

    # 命宫被冲（chong_natal_idx=2）
    ml = get_chong_multilayer_semantics(2, palaces_by_idx, decade_layout, annual_layout)
    assert ml["natal"]["palace_name"] == "命宫"
    assert ml["natal"]["theme"] == "本人"
    assert ml["decade"]["palace_name"] == "大限子女宫"
    assert ml["decade"]["theme"] == "子女"
    assert ml["annual"]["palace_name"] == "流年夫妻宫"
    assert ml["annual"]["theme"] == "配偶"
    print(f"  ✓ 三层语义查询正确")
    print(f"    · natal:  {ml['natal']}")
    print(f"    · decade: {ml['decade']}")
    print(f"    · annual: {ml['annual']}")
    print()


def test_collect_events():
    print("=" * 70)
    print("TEST 4: 从 records 提取 chong 事件")
    print("=" * 70)
    
    records = [
        {
            "palace_name": "疾厄宫", "palace_idx": 5,
            "transformations": [
                {"hua_type":"化忌","target_star":"巨门",
                 "target_palace_name":"迁移宫","target_palace_idx":8,
                 "chong_palace":"命宫","fh_type":"普通飞宫"},
                {"hua_type":"化禄","target_star":"天同",
                 "target_palace_name":"福德宫","target_palace_idx":4,
                 "chong_palace":"","fh_type":"普通飞宫"},  # 无冲
            ],
        },
        {
            "palace_name": "命宫", "palace_idx": 2,
            "transformations": [
                {"hua_type":"化忌","target_star":"廉贞",
                 "target_palace_name":"子女宫","target_palace_idx":11,
                 "chong_palace":"田宅宫","fh_type":"普通飞宫"},
            ],
        },
    ]
    
    events = collect_chong_events_from_feihua_records(records, layer="natal", only_ji=True)
    assert len(events) == 2  # 两个化忌冲
    # 应按 impact_level 排序，但都是化忌(4)，看顺序保持
    chong_targets = [e["chong_palace"] for e in events]
    assert "命宫" in chong_targets
    assert "田宅宫" in chong_targets
    print(f"  ✓ 提取 2 个化忌冲事件")
    print()


def test_collect_events_include_all_hua():
    """only_ji=False 时所有冲都收集"""
    print("=" * 70)
    print("TEST 5: only_ji=False 收集所有化")
    print("=" * 70)
    
    records = [{
        "palace_name": "命宫", "palace_idx": 2,
        "transformations": [
            {"hua_type":"化忌","target_star":"X","target_palace_name":"A",
             "target_palace_idx":1,"chong_palace":"B","fh_type":""},
            {"hua_type":"化权","target_star":"Y","target_palace_name":"C",
             "target_palace_idx":3,"chong_palace":"D","fh_type":""},
            {"hua_type":"化禄","target_star":"Z","target_palace_name":"E",
             "target_palace_idx":5,"chong_palace":"F","fh_type":""},
        ],
    }]
    events = collect_chong_events_from_feihua_records(records, only_ji=False)
    assert len(events) == 3
    # 应按 impact_level 排序，化忌在最前
    assert events[0]["hua_type"] == "化忌"
    print(f"  ✓ 全 3 类化都收集，化忌排第一")
    print()


def test_analyze_chong_chains_natal_only():
    """仅本命层分析"""
    print("=" * 70)
    print("TEST 6: 本命层 chong_chains")
    print("=" * 70)
    
    try:
        from core.ziwei.chart import build_ziwei_chart
        from core.ziwei.feihua_advanced import analyze_palace_feihua
        chart = build_ziwei_chart('1990-7-14', 3, '男')
        palaces = chart['palaces']
        records = analyze_palace_feihua(palaces)
        
        chains = analyze_chong_chains(palaces, records)
        assert chains["total"] > 0
        assert "events" in chains and len(chains["events"]) > 0
        assert "top_warnings" in chains
        assert "key_palaces_hit" in chains
        
        # 每个事件应有 multilayer 字段
        for e in chains["events"]:
            assert "multilayer" in e
            assert "natal" in e["multilayer"]
        
        print(f"  ✓ 真实命盘 chong_chains: {chains['total']} 个事件")
        print(f"  ✓ {len(chains['key_palaces_hit'])} 个宫被冲")
    except ImportError:
        print("  · 跳过：iztro_py 未装")
    print()


def test_analyze_chong_chains_three_layer():
    """三层完整分析"""
    print("=" * 70)
    print("TEST 7: 三层 chong_chains（本命+大限+流年）")
    print("=" * 70)
    
    try:
        from core.ziwei.chart import (
            build_ziwei_chart, get_decade_palace,
            compute_decade_palaces_layout, compute_annual_palaces_layout,
        )
        from core.ziwei.feihua_advanced import (
            analyze_palace_feihua, analyze_overlay_feihua,
        )
        from core.constants import TIANGAN, DIZHI

        chart = build_ziwei_chart('1990-7-14', 3, '男')
        palaces = chart['palaces']
        records = analyze_palace_feihua(palaces)

        decade = get_decade_palace('1990-7-14', 3, '男', 35)
        decade_record = analyze_overlay_feihua(
            palaces, decade['stem'], decade['palace_idx'], '大限'
        )
        decade_layout = compute_decade_palaces_layout(decade['palace_idx'])

        year = 2026
        year_stem = TIANGAN[(year-1984)%10]
        year_branch = DIZHI[(year-1984)%12]
        annual_idx = next(p['index'] for p in palaces if p['earthly_branch']==year_branch)
        annual_record = analyze_overlay_feihua(palaces, year_stem, annual_idx, f'流年{year}')
        annual_layout = compute_annual_palaces_layout(annual_idx)

        chains = analyze_chong_chains(
            palaces, records,
            decade_overlay_record=decade_record,
            annual_overlay_record=annual_record,
            decade_layout=decade_layout,
            annual_layout=annual_layout,
        )

        # 三层都应有 events
        layers_seen = set(e["layer"] for e in chains["events"])
        assert "natal" in layers_seen
        # decade/annual 可能没冲，但 layout 应当让 multilayer 含 decade 和 annual
        e0 = chains["events"][0]
        assert "natal" in e0["multilayer"]
        # 若 decade_layout 提供，应当多层有 decade
        if decade_layout:
            assert "decade" in e0["multilayer"]
        
        print(f"  ✓ 三层 chong_chains: {chains['total']} 事件")
        print(f"  ✓ 涉及层: {layers_seen}")
        print(f"  ✓ 警示 {len(chains['top_warnings'])} 条")
    except ImportError:
        print("  · 跳过：iztro_py 未装")
    print()


def test_format_for_prompt():
    print("=" * 70)
    print("TEST 8: prompt 格式化")
    print("=" * 70)
    
    try:
        from core.ziwei.chart import build_ziwei_chart
        from core.ziwei.feihua_advanced import analyze_palace_feihua
        chart = build_ziwei_chart('1990-7-14', 3, '男')
        records = analyze_palace_feihua(chart['palaces'])
        chains = analyze_chong_chains(chart['palaces'], records)
        text = format_chong_chains_for_prompt(chains)
        
        assert "冲宫连锁警示" in text
        assert "本命层冲宫" in text
        print(f"  ✓ prompt 长度: {len(text)} chars")
        print(f"  ✓ 含关键 section 标题")
        # 看前几行
        for line in text.split('\n')[:8]:
            print(f"  | {line}")
    except ImportError:
        print("  · 跳过：iztro_py 未装")
    print()


def test_empty_input():
    print("=" * 70)
    print("TEST 9: 空输入兜底")
    print("=" * 70)
    
    chains = analyze_chong_chains([], [])
    assert chains["total"] == 0
    assert chains["events"] == []
    
    text = format_chong_chains_for_prompt(chains)
    assert text == ""  # 0 个事件返回空字符串
    print(f"  ✓ 空 records 不报错且返回空 prompt")
    print()


if __name__ == "__main__":
    test_palace_to_person()
    test_interpret_single_event()
    test_multilayer_semantics()
    test_collect_events()
    test_collect_events_include_all_hua()
    test_analyze_chong_chains_natal_only()
    test_analyze_chong_chains_three_layer()
    test_format_for_prompt()
    test_empty_input()
    print("=" * 70)
    print("ALL CHONG CHAINS TESTS PASSED")
    print("=" * 70)
