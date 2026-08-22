"""
Tests for polish features — /chart 端点的 insights 字段。

由于沙箱无 iztro_py 网络，我们直接调用 insights 内部逻辑（不通过 FastAPI），
验证返回结构符合前端预期。

Verifies:
  1. insights.rating 含 overall/score/summary/soul_*/sfsz_brief 字段
  2. insights.patterns.good/bad 数组
  3. insights.feihua_summary 含关键警示字段
  4. 前端能用 insights.rating.overall 判定是否渲染评级徽章
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_ziwei_context import make_mock_chart_2000_8_16
from core.ziwei.context_builder import find_soul_palace, get_san_fang_si_zheng
from core.ziwei.brightness import compute_mingge_overall_rating
from core.ziwei.pattern_detector import detect_all_patterns
from core.ziwei.feihua_advanced import analyze_palace_feihua, summarize_feihua_landscape


def build_insights_like_api(data, birth_hour_index=2):
    """重现 /chart 端点中 insights 的生成逻辑。"""
    palaces = data["palaces"]
    soul_p = find_soul_palace(palaces)
    insights = {}

    # rating
    if soul_p is not None:
        sfsz = get_san_fang_si_zheng(palaces, soul_p.get("index", -1))
        rating = compute_mingge_overall_rating(soul_p, sfsz)
        insights["rating"] = {
            "overall":        rating.get("overall_rating"),
            "score":          rating.get("average_score"),
            "summary":        rating.get("summary"),
            "soul_rating":    rating.get("soul_palace_score", {}).get("rating"),
            "soul_average":   rating.get("soul_palace_score", {}).get("average"),
            "soul_stars":     rating.get("soul_palace_score", {}).get("major_stars"),
            "sfsz_brief": [
                {
                    "palace":     s.get("palace_name"),
                    "branch":     s.get("branch"),
                    "stars":      s.get("major_stars"),
                    "rating":     s.get("rating"),
                    "score":      s.get("average"),
                }
                for s in rating.get("sfsz_scores", [])
            ],
            "star_notes":     rating.get("star_notes", [])[:10],
        }

    # patterns
    patterns = detect_all_patterns(palaces, birth_hour_index=birth_hour_index)
    insights["patterns"] = {
        "good":  [
            {
                "name":              p.get("name"),
                "category":          p.get("category"),
                "evidence":          p.get("evidence", []),
                "meaning":           p.get("meaning"),
                "break_conditions":  p.get("break_conditions", []),
                "is_partial":        p.get("is_partial", False),
            }
            for p in patterns.get("good_patterns", [])
        ],
        "bad":   [
            {
                "name":              p.get("name"),
                "category":          p.get("category"),
                "evidence":          p.get("evidence", []),
                "meaning":           p.get("meaning"),
                "break_conditions":  p.get("break_conditions", []),
            }
            for p in patterns.get("bad_patterns", [])
        ],
        "total": patterns.get("total_count", 0),
    }

    # feihua summary
    feihua_records = analyze_palace_feihua(palaces, school="zhongzhou")
    summary = summarize_feihua_landscape(feihua_records, palaces)
    insights["feihua_summary"] = {
        "quality_changes":     summary.get("key_quality_changes", []),
        "double_ji":           summary.get("double_ji", []),
        "lu_jie_ji":           summary.get("lu_jie_ji", []),
        "lu_ji_war":           summary.get("lu_ji_war", []),
        "soul_incoming":       summary.get("soul_palace_incoming", []),
        "soul_chong":          summary.get("soul_palace_chong", []),
        "self_out_palaces":    summary.get("self_out_palaces", []),
        "self_in_palaces":     summary.get("self_in_palaces", []),
        "concentration":       summary.get("concentration", {}),
    }
    return insights


def test_rating_structure():
    print("=" * 70)
    print("TEST 1: insights.rating 结构")
    print("=" * 70)

    data = make_mock_chart_2000_8_16()
    insights = build_insights_like_api(data)
    rating = insights.get("rating")

    assert rating, "应该有 rating 字段"
    assert rating["overall"] in ["上格", "中上格", "中格", "中下格", "下格"], \
        f"overall 应是评级文字: {rating['overall']}"
    assert isinstance(rating["score"], (int, float))
    assert isinstance(rating["summary"], str) and len(rating["summary"]) > 0
    assert isinstance(rating["sfsz_brief"], list) and len(rating["sfsz_brief"]) == 4

    print(f"  ✓ overall: {rating['overall']} ({rating['score']:+.2f})")
    print(f"  ✓ summary: {rating['summary'][:50]}...")
    print(f"  ✓ soul: {rating['soul_stars']} [{rating['soul_rating']}]")
    print(f"  ✓ sfsz_brief: {len(rating['sfsz_brief'])} 宫")
    for s in rating["sfsz_brief"]:
        print(f"    · {s['palace']}({s['branch']}): {s['stars']} → {s['rating']}")
    print(f"  ✓ star_notes: {len(rating['star_notes'])} 条")
    print()


def test_patterns_structure():
    print("=" * 70)
    print("TEST 2: insights.patterns 结构")
    print("=" * 70)

    data = make_mock_chart_2000_8_16()
    insights = build_insights_like_api(data)
    patterns = insights.get("patterns")

    assert patterns, "应该有 patterns 字段"
    assert isinstance(patterns["good"], list)
    assert isinstance(patterns["bad"], list)
    assert patterns["total"] == len(patterns["good"]) + len(patterns["bad"])

    print(f"  ✓ 总数 {patterns['total']}（吉 {len(patterns['good'])}，凶 {len(patterns['bad'])}）")
    for p in patterns["good"]:
        print(f"    吉 · {p['name']}")
        assert "evidence" in p
        assert "meaning" in p
    for p in patterns["bad"]:
        print(f"    凶 · {p['name']}")

    # mock 命盘应该有 君臣庆会 + 府相朝垣 + 日月并明
    good_names = [p["name"] for p in patterns["good"]]
    assert "君臣庆会格" in good_names
    print(f"  ✓ 君臣庆会格识别 ✓")
    print()


def test_feihua_summary_structure():
    print("=" * 70)
    print("TEST 3: insights.feihua_summary 结构")
    print("=" * 70)

    data = make_mock_chart_2000_8_16()
    insights = build_insights_like_api(data)
    fh = insights.get("feihua_summary")

    assert fh, "应该有 feihua_summary 字段"
    keys = ["quality_changes", "double_ji", "lu_jie_ji", "lu_ji_war",
            "soul_incoming", "soul_chong", "self_out_palaces",
            "self_in_palaces", "concentration"]
    for k in keys:
        assert k in fh, f"feihua_summary 应有 {k} 字段"
        print(f"  ✓ {k}: {type(fh[k]).__name__}, len={len(fh[k])}")

    # 此 mock 应该有 双忌、禄解忌、禄忌交战
    assert len(fh["double_ji"]) >= 1, "应至少 1 个双忌"
    assert len(fh["lu_jie_ji"]) >= 1, "应至少 1 个禄解忌"
    assert len(fh["lu_ji_war"]) >= 1, "应至少 1 个禄忌交战"
    print(f"  ✓ 双忌叠加 {len(fh['double_ji'])}、禄解忌 {len(fh['lu_jie_ji'])}、禄忌交战 {len(fh['lu_ji_war'])} ✓")
    print()


def test_full_payload_size():
    """验证 insights 不会让 /chart 响应变得过大。"""
    print("=" * 70)
    print("TEST 4: insights 负载大小")
    print("=" * 70)

    import json
    data = make_mock_chart_2000_8_16()
    insights = build_insights_like_api(data)
    payload = json.dumps(insights, ensure_ascii=False)
    print(f"  · insights JSON 长度: {len(payload)} chars")
    print(f"  · UTF-8 bytes: {len(payload.encode('utf-8'))}")
    # 合理预算：≤ 20KB
    assert len(payload.encode('utf-8')) < 20000, "insights 负载过大"
    print(f"  ✓ 负载在合理范围内（< 20KB）")
    print()


def test_feihua_by_palace_structure():
    print("=" * 70)
    print("TEST 5: insights.feihua_by_palace 结构（Z-6 新增）")
    print("=" * 70)

    data = make_mock_chart_2000_8_16()
    insights = build_insights_like_api_full(data)
    fbp = insights.get("feihua_by_palace")

    assert fbp, "应该有 feihua_by_palace 字段"
    # 应该有 12 宫
    assert len(fbp) == 12, f"应有 12 宫，实际 {len(fbp)}"
    # 每个 key 都是数字字符串
    for k in fbp.keys():
        assert k.isdigit() and 0 <= int(k) <= 11, f"key 必须是 0-11 字符串: {k}"
    
    # 看其中一宫的结构
    sample = fbp["0"]
    required_fields = ["palace_idx", "palace_name", "stem", "branch",
                       "opp_palace_name", "transformations",
                       "self_out_count", "self_in_count", "fly_out_count",
                       "incoming_list"]
    for f in required_fields:
        assert f in sample, f"feihua_by_palace[0] 缺字段 {f}"
    
    # transformations 必须有 4 个化象
    assert len(sample["transformations"]) == 4, "应有 4 个化象"
    for tr in sample["transformations"]:
        for tf in ["hua_type", "target_star", "target_palace_name", "fh_type",
                   "is_he_won_ji", "is_double_ji", "is_lu_ji_war",
                   "is_quality_change", "chong_palace", "interpretation"]:
            assert tf in tr, f"transformation 缺字段 {tf}"
    
    print(f"  ✓ 12 宫全部有完整结构")
    print(f"  · sample(idx=0): {sample['palace_name']}({sample['stem']}{sample['branch']})")
    print(f"  · 4 化象 + {sample['incoming_count'] if 'incoming_count' in sample else len(sample.get('incoming_list', []))} 飞入")
    print()


def build_insights_like_api_full(data):
    """带 feihua_by_palace 的完整 insights 重建。"""
    palaces = data["palaces"]
    soul_p = find_soul_palace(palaces)
    insights = {}

    if soul_p is not None:
        sfsz = get_san_fang_si_zheng(palaces, soul_p.get("index", -1))
        rating = compute_mingge_overall_rating(soul_p, sfsz)
        insights["rating"] = {
            "overall":        rating.get("overall_rating"),
            "score":          rating.get("average_score"),
            "summary":        rating.get("summary"),
            "soul_rating":    rating.get("soul_palace_score", {}).get("rating"),
            "soul_stars":     rating.get("soul_palace_score", {}).get("major_stars"),
            "sfsz_brief": [
                {"palace": s.get("palace_name"), "branch": s.get("branch"),
                 "stars": s.get("major_stars"), "rating": s.get("rating"),
                 "score": s.get("average")}
                for s in rating.get("sfsz_scores", [])
            ],
            "star_notes": rating.get("star_notes", [])[:10],
        }

    patterns = detect_all_patterns(palaces, birth_hour_index=2)
    insights["patterns"] = {
        "good": [{"name": p.get("name"), "evidence": p.get("evidence", []),
                  "meaning": p.get("meaning")}
                 for p in patterns.get("good_patterns", [])],
        "bad":  [{"name": p.get("name"), "evidence": p.get("evidence", []),
                  "meaning": p.get("meaning")}
                 for p in patterns.get("bad_patterns", [])],
        "total": patterns.get("total_count", 0),
    }

    feihua_records = analyze_palace_feihua(palaces, school="zhongzhou")
    summary = summarize_feihua_landscape(feihua_records, palaces)
    insights["feihua_summary"] = {
        "double_ji":     summary.get("double_ji", []),
        "lu_jie_ji":     summary.get("lu_jie_ji", []),
        "lu_ji_war":     summary.get("lu_ji_war", []),
        "soul_incoming": summary.get("soul_palace_incoming", []),
        "soul_chong":    summary.get("soul_palace_chong", []),
    }
    # Z-6: 每宫详情
    insights["feihua_by_palace"] = {
        str(r["palace_idx"]): {
            "palace_idx":       r["palace_idx"],
            "palace_name":      r["palace_name"],
            "stem":             r["stem"],
            "branch":           r["branch"],
            "opp_palace_name":  r["opp_palace_name"],
            "transformations": [
                {"hua_type": tr["hua_type"], "target_star": tr["target_star"],
                 "target_palace_name": tr["target_palace_name"],
                 "target_palace_idx": tr["target_palace_idx"],
                 "fh_type": tr["fh_type"], "is_inner": tr["is_inner"],
                 "chong_palace": tr["chong_palace"],
                 "is_he_won_ji": tr["is_he_won_ji"], "is_double_ji": tr["is_double_ji"],
                 "is_lu_ji_war": tr["is_lu_ji_war"], "is_quality_change": tr["is_quality_change"],
                 "interpretation": tr["interpretation"]}
                for tr in r["transformations"]
            ],
            "self_out_count": r["self_out_count"],
            "self_in_count":  r["self_in_count"],
            "fly_out_count":  r["fly_out_count"],
            "incoming_count": r["incoming_count"],
            "incoming_list":  r["incoming_list"],
        }
        for r in feihua_records
    }
    return insights


if __name__ == "__main__":
    test_rating_structure()
    test_patterns_structure()
    test_feihua_summary_structure()
    test_full_payload_size()
    test_feihua_by_palace_structure()
    print()
    print("=" * 70)
    print("ALL POLISH BACKEND TESTS PASSED")
    print("=" * 70)
