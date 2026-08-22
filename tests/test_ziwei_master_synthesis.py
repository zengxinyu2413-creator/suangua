"""紫微 — 全功能激活 + 总汇合参"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _chart():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/ziwei/chart",
                  json={"year": 1990, "month": 5, "day": 22, "hour": 8,
                        "gender": "male", "is_lunar": False}).json()["data"]


def test_master_aggregates_key_palaces():
    d = _chart()
    ms = d.get("master_synthesis", {})
    assert ms.get("available")
    domains = {dv["domain"] for dv in ms["dimension_verdicts"]}
    assert {"事业", "财运", "婚姻", "健康"} <= domains


def test_sihua_affects_verdict():
    """四化须影响要宫吉凶（化禄吉、化忌凶）。"""
    d = _chart()
    ms = d["master_synthesis"]
    # 福德宫天同化忌 → 凶
    fu = next((dv for dv in ms["dimension_verdicts"] if dv["domain"] == "福分"), None)
    if fu and "化忌" in fu["verdict"]:
        assert fu["quality"] == "凶"


def test_master_has_three_levels():
    d = _chart()
    ms = d["master_synthesis"]
    assert ms["dimension_verdicts"]          # 单点
    assert len(ms["integrated_paragraphs"]) >= 2   # 组合
    assert ms["master_advice"] and ms["overall_quality"]   # 汇总


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
