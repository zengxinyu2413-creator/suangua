"""
tests/test_liuyao_hua_bian.py
六爻·动爻化变全谱（回头生克/进退/长生墓绝/空/反伏吟/化六亲）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.hua_bian import analyze_one_hua, analyze_hua_bian


def _types(r):
    return [f["type"] for f in r["facets"]]


def test_hui_tou_sheng():
    """午(火)化卯(木)：木生火 = 回头生（偏吉）。"""
    r = analyze_one_hua("午", "卯")
    assert "回头生" in _types(r)
    assert r["score"] > 0


def test_hui_tou_ke_with_fanyin():
    """午化子：水克火=回头克，且子午冲=反吟 → 大凶。"""
    r = analyze_one_hua("午", "子")
    t = _types(r)
    assert "回头克" in t and "反吟" in t
    assert r["tendency"] == "化变大凶"


def test_jin_shen():
    """寅化卯：进神 + 化比和 + 化帝旺。"""
    r = analyze_one_hua("寅", "卯")
    t = _types(r)
    assert any("进神" in x for x in t)
    assert "化比和" in t


def test_hua_mu():
    """申(金)化丑：金墓于丑 = 化墓。"""
    r = analyze_one_hua("申", "丑")
    assert "化墓" in _types(r)


def test_hua_jue():
    """申(金)化寅：金绝于寅 = 化绝（且寅申冲反吟）。"""
    r = analyze_one_hua("申", "寅")
    t = _types(r)
    assert "化绝" in t and "反吟" in t


def test_fuyin():
    """子化子：同支 = 伏吟。"""
    assert "伏吟" in _types(analyze_one_hua("子", "子"))


def test_hua_kong():
    """化神旬空 → 化空。"""
    r = analyze_one_hua("午", "卯", kong_wang=["卯", "辰"])
    assert "化空" in _types(r)


def test_hua_liuqin_role():
    """化六亲应事：求财化子孙=元神，化兄弟=忌神。"""
    r1 = analyze_one_hua("午", "卯", orig_qin="妻财", changed_qin="子孙", topic="求财")
    f1 = [f for f in r1["facets"] if f["type"] == "化子孙"][0]
    assert "元神" in f1["desc"]
    r2 = analyze_one_hua("午", "卯", orig_qin="妻财", changed_qin="兄弟", topic="求财")
    f2 = [f for f in r2["facets"] if f["type"] == "化兄弟"][0]
    assert "忌神" in f2["desc"]


def test_full_text_present():
    """单爻化变须有整合成文断 + 总倾向。"""
    r = analyze_one_hua("午", "卯", orig_qin="官鬼", changed_qin="妻财", topic="求财")
    assert r["full_text"] and r["tendency"]
    assert "总断" in r["full_text"]


def test_analyze_hua_bian_chart():
    """全卦：仅统计发动之爻，安静爻不计。"""
    yaos = [
        {"is_changing": True, "branch": "午", "changed_branch": "卯",
         "liu_qin": "官鬼", "changed_liu_qin": "妻财", "position": 4, "line": "四"},
        {"is_changing": False, "branch": "子"},
        {"is_changing": True, "branch": "申", "changed_branch": "寅",
         "liu_qin": "兄弟", "changed_liu_qin": "妻财", "position": 5, "line": "五"},
    ]
    r = analyze_hua_bian(yaos, kong_wang=["辰", "巳"], topic="求财")
    assert r["count"] == 2
    assert len(r["moving_lines"]) == 2
    assert r["summary"]


def test_all_static():
    """六爻安静：不论化变。"""
    yaos = [{"is_changing": False, "branch": "子"}] * 6
    r = analyze_hua_bian(yaos)
    assert r["count"] == 0
    assert "安静" in r["summary"]


def test_bad_branch():
    assert analyze_one_hua("X", "卯")["success"] is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
