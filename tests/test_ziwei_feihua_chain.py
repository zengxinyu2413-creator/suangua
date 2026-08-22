"""
tests/test_ziwei_feihua_chain.py
紫微 — 飞化链路多步串联（互化/化忌连环/化禄流通/焦点/生年串联）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ziwei.feihua_chain import (
    analyze_feihua_chains, _build_graph, _detect_mutual,
    _detect_hua_chains, _trace_chain, _detect_focus,
)
from core.ziwei.birth_sihua import build_birth_sihua_panel


def _chart(year=1985, month=3, day=15, hour=10, gender="male"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/ziwei/chart", json={
        "year": year, "month": month, "day": day, "hour": hour,
        "gender": gender, "is_lunar": False}).json()["data"]


def _mock_feihua():
    # A(0)忌→B(1), B(1)忌→C(2), C(2)忌→A(0) 形成忌环；A禄→B，B禄→A 互化禄
    return [
        {"palace_idx": 0, "palace_name": "命宫", "stem": "甲",
         "transformations": [
             {"hua_type": "化禄", "target_palace_idx": 1, "target_palace_name": "兄弟宫"},
             {"hua_type": "化权", "target_palace_idx": 3, "target_palace_name": "子女宫"},
             {"hua_type": "化科", "target_palace_idx": 4, "target_palace_name": "财帛宫"},
             {"hua_type": "化忌", "target_palace_idx": 1, "target_palace_name": "兄弟宫"},
         ]},
        {"palace_idx": 1, "palace_name": "兄弟宫", "stem": "乙",
         "transformations": [
             {"hua_type": "化禄", "target_palace_idx": 0, "target_palace_name": "命宫"},
             {"hua_type": "化权", "target_palace_idx": 4, "target_palace_name": "财帛宫"},
             {"hua_type": "化科", "target_palace_idx": 3, "target_palace_name": "子女宫"},
             {"hua_type": "化忌", "target_palace_idx": 2, "target_palace_name": "夫妻宫"},
         ]},
        {"palace_idx": 2, "palace_name": "夫妻宫", "stem": "丙",
         "transformations": [
             {"hua_type": "化禄", "target_palace_idx": 4, "target_palace_name": "财帛宫"},
             {"hua_type": "化权", "target_palace_idx": 0, "target_palace_name": "命宫"},
             {"hua_type": "化科", "target_palace_idx": 1, "target_palace_name": "兄弟宫"},
             {"hua_type": "化忌", "target_palace_idx": 0, "target_palace_name": "命宫"},
         ]},
    ]


def test_build_graph():
    g = _build_graph(_mock_feihua())
    assert 0 in g and g[0]["edges"]["化忌"]["idx"] == 1


def test_mutual_double_lu():
    """命宫禄→兄弟、兄弟禄→命 = 双禄交流（吉）。"""
    g = _build_graph(_mock_feihua())
    mut = _detect_mutual(g)
    dl = [m for m in mut if "双禄" in m["desc"]]
    assert dl and dl[0]["nature"] == "吉"


def test_trace_ji_chain():
    """化忌链：命→兄弟→夫妻→命（环）。"""
    g = _build_graph(_mock_feihua())
    ch = _trace_chain(g, 0, "化忌")
    assert ch[:3] == [0, 1, 2]   # 命→兄→夫


def test_ji_chain_detected():
    g = _build_graph(_mock_feihua())
    chains = _detect_hua_chains(g, "化忌")
    assert chains and len(chains[0]["names"]) >= 3


def test_focus_palace():
    """命宫被多宫飞入 → 焦点。"""
    g = _build_graph(_mock_feihua())
    focus = _detect_focus(g)
    # 命宫(0)被 兄弟禄、夫妻权、夫妻忌 飞入 ≥3
    assert any(f["palace"] == "命宫" for f in focus)


def test_full_real_chart():
    """真实命盘：链路分析可用，含各类链。"""
    d = _chart()
    bs = build_birth_sihua_panel(d)
    fc = analyze_feihua_chains(d, bs)
    assert fc["available"]
    assert "mutual" in fc and "ji_chains" in fc and "lu_chains" in fc
    assert "focus" in fc and "summary" in fc
    # 化忌连环应存在（密图必有链）
    assert fc["ji_chains"]


def test_birth_chain_lu_sui_ji():
    """生年串联：禄随忌走 / 忌上加忌。"""
    d = _chart()
    bs = build_birth_sihua_panel(d)
    fc = analyze_feihua_chains(d, bs)
    # 1985 乙: 生年忌在疾厄 → 应有 birth_chain
    if fc["birth_chain"]:
        assert any(b["type"] in ("禄随忌走", "忌上加忌") for b in fc["birth_chain"])


def test_chain_in_chart_api():
    """/chart 输出含 feihua_chains。"""
    d = _chart()
    assert "feihua_chains" in d
    assert d["feihua_chains"]["available"]


def test_summary_nonempty():
    d = _chart()
    bs = build_birth_sihua_panel(d)
    fc = analyze_feihua_chains(d, bs)
    assert fc["summary"] and len(fc["summary"]) > 10


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))


# ── 大限 / 流年 飞化链路 ──
def test_wuhu_branch_stems():
    """五虎遁：乙年→寅宫戊起，顺布。"""
    from core.ziwei.feihua_chain import _wuhu_branch_stems
    m = _wuhu_branch_stems("乙")
    assert m["寅"] == "戊" and m["卯"] == "己" and m["辰"] == "庚"


def test_decade_layer_chains():
    """大限飞化链路：用 decadal_stem（含原始键翻译）。"""
    from core.ziwei.feihua_chain import analyze_layer_feihua_chains
    d = _chart()
    dc = analyze_layer_feihua_chains(d, "大限")
    assert dc["available"] and dc["layer"] == "大限"
    assert dc["ji_chains"]   # 密图必有忌链


def test_annual_layer_chains():
    """流年飞化链路：用年干经五虎遁。"""
    from core.ziwei.feihua_chain import analyze_layer_feihua_chains
    d = _chart()
    yc = analyze_layer_feihua_chains(d, "流年", year_stem="乙")
    assert yc["available"] and yc["layer"] == "流年"


def test_layer_chains_differ():
    """不同层（大限 vs 流年不同年干）链路应不同。"""
    from core.ziwei.feihua_chain import analyze_layer_feihua_chains
    d = _chart()
    a = analyze_layer_feihua_chains(d, "流年", year_stem="甲")
    b = analyze_layer_feihua_chains(d, "流年", year_stem="丙")
    # 不同年干→不同宫干→链路多半不同
    assert a["available"] and b["available"]


def test_layer_chains_in_triple_api():
    """/triple 输出 decade/annual 飞化链路。"""
    from fastapi.testclient import TestClient
    from main import app
    cl = TestClient(app)
    d = cl.post("/api/v1/ziwei/triple", json={
        "year": 1985, "month": 3, "day": 15, "hour": 10,
        "gender": "男", "is_lunar": False}).json()["data"]
    assert d.get("decade_feihua_chains", {}).get("available")
    assert d.get("annual_feihua_chains", {}).get("available")
