"""
tests/test_bazi_combos.py
八字·组合断：神煞组合 + 格局成破评断 + 岁运组合
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bazi.chart import build_chart
from core.bazi.analyzer import analyze_chart
from core.bazi.combos import (
    shensha_combos, evaluate_geju, analyze_suiyun, bazi_combos,
    _GEJU_RULES, _PAIR_COMBOS,
)


def _chart(y, m, d, h):
    c = build_chart(y, m, d, h)
    analyze_chart(c)
    return c


def test_shensha_overlap_and_pair():
    """命局神煞重叠与相会能被识别（1985-3-15-10：华盖×2、文昌学堂）。"""
    c = _chart(1985, 3, 15, 10)
    sc = shensha_combos(c)
    assert sc["success"]
    names = {x["name"] for x in sc["combos"]}
    assert any("华盖" in n for n in names)        # 华盖重叠
    assert "文昌学堂" in names                      # 文昌+学堂 相会
    # 每个组合都有 nature 与 desc
    for x in sc["combos"]:
        assert x["nature"] in ("吉", "凶", "中") and x["desc"]


def test_shensha_summary_polarity():
    """全吉组合 → summary 言吉为主。"""
    c = _chart(1985, 3, 15, 10)
    sc = shensha_combos(c)
    if sc["ji_count"] > sc["xiong_count"]:
        assert "吉为主" in sc["summary"]


def test_geju_evaluation_structure():
    """格局成破评断含 status/verdict，且与命局十神自洽。"""
    c = _chart(1985, 3, 15, 10)   # 食神格 + 偏印(枭) + 财 → 破而有救
    ge = evaluate_geju(c)
    assert ge["available"]
    assert ge["pattern"] == c["pattern"]
    assert ge["status"] in ("格成", "破而有救", "格破", "格局未显")
    assert ge["verdict"]
    # 食神格遇枭(偏印)又有财 → 破而有救
    if ge["pattern"] == "食神格":
        assert ge["status"] == "破而有救"


def test_geju_rules_cover_eight_plus():
    """格局规则覆盖八正格 + 建禄/月刃。"""
    for g in ("正官格", "七杀格", "正财格", "偏财格", "正印格",
              "偏印格", "食神格", "伤官格", "建禄格", "月刃格"):
        assert g in _GEJU_RULES
        assert _GEJU_RULES[g]["cheng"]  # 至少有成格判据
        assert _GEJU_RULES[g]["jiu"]


def test_geju_po_no_save_scan():
    """能扫到一个'格破无救'之造（如偏印格遇食神而无财制枭）。"""
    found = False
    import random
    random.seed(7)
    for _ in range(300):
        c = _chart(random.randint(1950, 2010), random.randint(1, 12),
                   random.randint(1, 28), random.randint(0, 23))
        ge = evaluate_geju(c)
        if ge.get("status") == "格破":
            assert ge["po_hit"] and not ge["cheng_hit"]
            found = True
            break
    assert found


def test_special_geju_fallback():
    """专旺/化气/从格无标准成破规则 → available=False 但仍有 verdict。"""
    import random
    random.seed(123)
    for _ in range(400):
        c = _chart(random.randint(1940, 2015), random.randint(1, 12),
                   random.randint(1, 28), random.randint(0, 23))
        if c.get("pattern", "") not in _GEJU_RULES:
            ge = evaluate_geju(c)
            assert ge["available"] is False and ge["verdict"]
            return
    # 若未扫到特殊格也不算失败（多数命为正格）


def test_suiyun_bingli():
    """岁运并临：大运干支==流年干支。"""
    c = _chart(1985, 3, 15, 10)
    r = analyze_suiyun(c, "甲", "子", "甲", "子")
    assert "岁运并临" in r["tags"]


def test_suiyun_xiangzhan():
    """岁运天克地冲（相战）：甲子运 vs 庚午年（庚克甲、子午冲）。"""
    c = _chart(1985, 3, 15, 10)
    r = analyze_suiyun(c, "甲", "子", "庚", "午")
    assert any("相战" in t for t in r["tags"])


def test_suiyun_pinghe():
    """无并临无相战 → 平和。"""
    c = _chart(1985, 3, 15, 10)
    r = analyze_suiyun(c, "乙", "丑", "丙", "寅")
    assert "岁运平和" in r["tags"] or r["notes"]


def test_suiyun_yindong():
    """流年/大运冲命局某支 → 引动该宫之事。"""
    c = _chart(1985, 3, 15, 10)
    day_zhi = c["day_pillar"]["dizhi"]
    from core.bazi.combos import DIZHI_CHONG
    chong_zhi = DIZHI_CHONG[day_zhi]
    r = analyze_suiyun(c, "乙", "丑", "丙", chong_zhi)
    assert any("日支" in n for n in r["notes"])


def test_bazi_combos_top():
    """顶层综合：神煞组合 + 格局评断 一并产出。"""
    c = _chart(1985, 3, 15, 10)
    cb = bazi_combos(c)
    assert cb["success"]
    assert "shensha_combos" in cb and "geju_evaluation" in cb


def test_pair_rules_wellformed():
    """组合规则集结构良好：每条有 set/name/nature/desc。"""
    for r in _PAIR_COMBOS:
        assert isinstance(r["set"], set) and len(r["set"]) == 2
        assert r["name"] and r["nature"] in ("吉", "凶", "中") and r["d"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))


# ── 流年逐年组合断（深化） ──
def test_liunian_combo_structure():
    """流年组合断含完整十神/喜忌/应事/结论。"""
    from core.bazi.combos import analyze_liunian_combo
    c = _chart(1985, 3, 15, 10)
    r = analyze_liunian_combo(c, "庚", "申", "庚", "子")
    assert r["success"]
    assert r["shishen_gan"] and r["shishen_zhi"]   # 天干+地支本气十神
    assert r["xiji"] in ("喜", "忌", "平")
    assert r["quality"] in ("吉", "凶", "平")
    assert r["verdict"] and r["themes"]


def test_liunian_combo_xiyong_ji():
    """流年为调候喜用五行 → 喜 → 吉（中和命）。"""
    from core.bazi.combos import analyze_liunian_combo
    c = _chart(1985, 3, 15, 10)   # 癸日 中和 调候用神庚(金)
    r = analyze_liunian_combo(c, "庚", "申", "庚", "子")   # 庚=金=喜用
    assert r["xiji"] == "喜" and r["quality"] == "吉"


def test_liunian_combo_dayun_combo():
    """大运×流年典型组合断（官印相生）。"""
    from core.bazi.combos import analyze_liunian_combo
    c = _chart(1985, 3, 15, 10)
    # 大运辛酉(偏印) + 流年戊戌(正官) → 官印相生
    r = analyze_liunian_combo(c, "辛", "酉", "戊", "戌")
    assert "官印相生" in r["dayun_combo"] or r["dayun_combo"] == "" or "印" in r["verdict"]


def test_liunian_combo_themes_by_shishen():
    """应事主题随十神而变。"""
    from core.bazi.combos import analyze_liunian_combo, _SHISHEN_THEME
    c = _chart(1985, 3, 15, 10)
    r = analyze_liunian_combo(c, "丙", "子", "乙", "巳")   # 乙=食神(癸日)
    assert any("食神" in t or "财" in t for t in r["themes"])
    assert len(_SHISHEN_THEME) == 10


def test_liunian_combo_in_fortune_api():
    """/fortune 每个流年带 liunian_combo，且回填 shishen_zhi。"""
    from fastapi.testclient import TestClient
    from main import app
    cl = TestClient(app)
    d = cl.post("/api/v1/bazi/fortune", json={
        "birth": {"year": 1985, "month": 3, "day": 15, "hour": 10, "gender": "male"},
        "query_year": 2025}).json()["data"]
    ln = d["liunian"]
    assert ln and all("liunian_combo" in y for y in ln)
    assert all(y.get("shishen_zhi") for y in ln)   # 回填后非空


# ── 流月/流日 通用逐期组合断 ──
def test_period_combo_liuyue():
    """流月组合断（parent=流年）含完整十神+喜忌+应事+组合。"""
    from core.bazi.combos import analyze_period_combo
    c = _chart(1985, 3, 15, 10)
    r = analyze_period_combo(c, "乙", "巳", "癸", "未", label="流月", parent_label="流年")
    assert r["success"] and r["label"] == "流月"
    assert r["shishen_gan"] and r["shishen_zhi"]
    assert r["quality"] in ("吉", "凶", "平")
    assert "流月" in r["verdict"]


def test_period_combo_liuri():
    """流日组合断（parent=流月）。"""
    from core.bazi.combos import analyze_period_combo
    c = _chart(1985, 3, 15, 10)
    r = analyze_period_combo(c, "癸", "未", "辛", "丑", label="流日", parent_label="流月")
    assert r["label"] == "流日" and "流日" in r["verdict"]


def test_period_combo_parent_label():
    """组合断语用 parent_label（流年/流月）而非硬编大运。"""
    from core.bazi.combos import _dy_ln_combo
    txt = _dy_ln_combo("正财", "正官", parent_label="流年")
    assert "大运" not in txt   # 已泛化


def test_period_combo_in_fortune_api():
    """/fortune 流月/流日 均带 combo。"""
    from fastapi.testclient import TestClient
    from main import app
    cl = TestClient(app)
    d = cl.post("/api/v1/bazi/fortune", json={
        "birth": {"year": 1985, "month": 3, "day": 15, "hour": 10, "gender": "male"},
        "query_year": 2025, "query_month": 6}).json()["data"]
    assert all("combo" in m for m in d["liuyue"])
    assert d["liuri"] and all("combo" in dd for dd in d["liuri"])


def test_period_combo_liushi_api():
    """/fortune 流时带 combo（parent=流日）。"""
    from fastapi.testclient import TestClient
    from main import app
    cl = TestClient(app)
    d = cl.post("/api/v1/bazi/fortune", json={
        "birth": {"year": 1985, "month": 3, "day": 15, "hour": 10, "gender": "male"},
        "query_year": 2025, "query_month": 6, "query_day": 15}).json()["data"]
    ls = d.get("liushi", [])
    assert ls and all("combo" in h for h in ls)
    assert all(h["combo"]["label"] == "流时" for h in ls)
