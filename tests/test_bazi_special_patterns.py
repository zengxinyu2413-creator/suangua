"""
Tests for core/bazi/special_patterns.py — B-2 特殊格局深度识别
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bazi.special_patterns import (
    detect_all_special_patterns,
    detect_rilu_guishi,
    detect_guanyin_xiangsheng,
    detect_shishen_zhisha,
    detect_shangguan_jianguan,
    detect_cai_guan_yin_quanju,
    detect_yangren_jiasha,
    detect_zaqi_yueling,
    detect_kuigang_ge,
    detect_tianyi_dugui,
    format_special_patterns_for_prompt,
)


def make_chart(yp, mp, dp, hp):
    """yp = (天干, 地支) 等。会用 CANGGAN 补藏干"""
    from core.constants import CANGGAN
    return {
        "day_master": dp[0],
        "year_pillar":  {"tiangan": yp[0], "dizhi": yp[1], "canggan": CANGGAN.get(yp[1], [])},
        "month_pillar": {"tiangan": mp[0], "dizhi": mp[1], "canggan": CANGGAN.get(mp[1], [])},
        "day_pillar":   {"tiangan": dp[0], "dizhi": dp[1], "canggan": CANGGAN.get(dp[1], [])},
        "hour_pillar":  {"tiangan": hp[0], "dizhi": hp[1], "canggan": CANGGAN.get(hp[1], [])},
    }


def test_rilu_guishi():
    """日禄归时：庚日主时支申"""
    print("=" * 70)
    print("TEST 1: 日禄归时格")
    print("=" * 70)
    chart = make_chart(("壬", "戌"), ("癸", "卯"), ("庚", "辰"), ("甲", "申"))
    r = detect_rilu_guishi(chart)
    assert r["matched"]
    assert "庚" in r["condition"] and "申" in r["condition"]
    print(f"  ✓ {r['name']} 检测：{r['condition']}")
    print()


def test_guanyin_xiangsheng():
    """官印相生：庚金日，有官（丙/丁）+ 印（戊/己）"""
    print("=" * 70)
    print("TEST 2: 官印相生")
    print("=" * 70)
    chart = make_chart(("庚", "午"), ("癸", "未"), ("庚", "辰"), ("己", "卯"))
    r = detect_guanyin_xiangsheng(chart)
    assert r["matched"]
    assert r["auspicious"]
    print(f"  ✓ {r['name']} — {r['condition']}")
    print()


def test_shangguan_jianguan():
    """伤官见官：庚金日，伤官癸 + 正官丁"""
    print("=" * 70)
    print("TEST 3: 伤官见官（凶格）")
    print("=" * 70)
    # 庚日主，癸水为伤官，丁火为正官
    chart = make_chart(("丁", "卯"), ("癸", "卯"), ("庚", "辰"), ("丙", "子"))
    r = detect_shangguan_jianguan(chart)
    assert r["matched"]
    assert not r["auspicious"]
    print(f"  ✓ {r['name']} 凶格检测")
    print()


def test_cai_guan_yin_quanju():
    """财官印三全"""
    print("=" * 70)
    print("TEST 4: 财官印三全")
    print("=" * 70)
    # 1990-7-14 卯时男的命盘
    chart = make_chart(("庚", "午"), ("癸", "未"), ("庚", "辰"), ("己", "卯"))
    r = detect_cai_guan_yin_quanju(chart)
    assert r["matched"]
    assert r["auspicious"]
    print(f"  ✓ {r['name']} — {r['condition']}")
    print()


def test_zaqi_yueling():
    """杂气月令：月支辰戌丑未"""
    print("=" * 70)
    print("TEST 5: 杂气月令格")
    print("=" * 70)
    # 月支未（土库）
    chart = make_chart(("庚", "午"), ("癸", "未"), ("庚", "辰"), ("己", "卯"))
    r = detect_zaqi_yueling(chart)
    assert r["matched"]
    assert "未" in r["condition"]
    print(f"  ✓ {r['name']} — {r['condition']}")
    
    # 月支寅（非库）— 不该匹配
    chart2 = make_chart(("庚", "午"), ("戊", "寅"), ("庚", "辰"), ("己", "卯"))
    r2 = detect_zaqi_yueling(chart2)
    assert not r2["matched"]
    print(f"  ✓ 月支非库时正确返回 not matched")
    print()


def test_kuigang_ge():
    """魁罡格：庚辰/庚戌/壬辰/戊戌 日柱"""
    print("=" * 70)
    print("TEST 6: 魁罡格")
    print("=" * 70)
    # 庚辰日
    chart = make_chart(("庚", "午"), ("癸", "未"), ("庚", "辰"), ("己", "卯"))
    r = detect_kuigang_ge(chart)
    assert r["matched"]
    print(f"  ✓ 庚辰日 → 魁罡格")
    
    # 壬辰日
    chart2 = make_chart(("丁", "卯"), ("癸", "卯"), ("壬", "辰"), ("丙", "午"))
    r2 = detect_kuigang_ge(chart2)
    assert r2["matched"]
    print(f"  ✓ 壬辰日 → 魁罡格")
    
    # 甲子日 — 不该是魁罡
    chart3 = make_chart(("庚", "午"), ("癸", "未"), ("甲", "子"), ("己", "卯"))
    r3 = detect_kuigang_ge(chart3)
    assert not r3["matched"]
    print(f"  ✓ 非魁罡日正确返回 not matched")
    print()


def test_tianyi_dugui():
    """天乙独贵"""
    print("=" * 70)
    print("TEST 7: 天乙独贵")
    print("=" * 70)
    # 庚日主，天乙在丑未；本命有未
    chart = make_chart(("庚", "午"), ("癸", "未"), ("庚", "辰"), ("己", "卯"))
    r = detect_tianyi_dugui(chart)
    assert r["matched"]
    assert "未" in r["evidence"]
    print(f"  ✓ {r['name']} — 庚日主天乙在未")
    print()


def test_full_real_chart():
    """真实命盘整合：1990-7-14 卯时男"""
    print("=" * 70)
    print("TEST 8: 真实命盘 — 1990-7-14 卯时男（庚午癸未庚辰己卯）")
    print("=" * 70)
    chart = make_chart(("庚", "午"), ("癸", "未"), ("庚", "辰"), ("己", "卯"))
    result = detect_all_special_patterns(chart)
    
    assert result["total"] >= 4  # 至少 4 个格局
    
    names = [p["name"] for p in result["matched"]]
    assert "财官印三全" in names
    assert "杂气月令格" in names
    assert "天乙独贵" in names
    assert "魁罡格" in names
    
    print(f"  ✓ 检测出 {result['total']} 个格局")
    print(f"  ✓ 包含：{'、'.join(names)}")
    
    # prompt 格式化
    text = format_special_patterns_for_prompt(result)
    assert "特殊格局深度识别" in text
    print(f"  ✓ prompt 格式化输出长度 {len(text)} chars")
    print()


def test_empty_input():
    """空输入兜底"""
    print("=" * 70)
    print("TEST 9: 空输入兜底")
    print("=" * 70)
    result = detect_all_special_patterns({})
    assert result["total"] == 0
    
    text = format_special_patterns_for_prompt(result)
    assert text == ""
    print(f"  ✓ 空输入返回 0 格局，不报错")
    print()


if __name__ == "__main__":
    test_rilu_guishi()
    test_guanyin_xiangsheng()
    test_shangguan_jianguan()
    test_cai_guan_yin_quanju()
    test_zaqi_yueling()
    test_kuigang_ge()
    test_tianyi_dugui()
    test_full_real_chart()
    test_empty_input()
    print("=" * 70)
    print("ALL B-2 SPECIAL PATTERNS TESTS PASSED")
    print("=" * 70)
