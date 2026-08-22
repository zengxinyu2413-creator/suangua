"""八字 — 全功能激活 + 总汇合参（每问启动全部功能并汇总）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _chart():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/bazi/chart",
                  json={"year": 1990, "month": 5, "day": 22, "hour": 8,
                        "gender": "male", "is_lunar": False}).json()["data"]


def test_all_life_aspects_activated():
    """一次查询须激活全部专域（事业/财/婚/健康），非孤儿。"""
    d = _chart()
    la = d.get("life_aspects", {})
    for dom in ("career", "wealth", "health", "marriage"):
        assert dom in la, f"{dom} 未激活"


def test_master_synthesis_aggregates():
    """总汇须含单点速览 + 组合段落 + 总评总建议。"""
    d = _chart()
    ms = d.get("master_synthesis", {})
    assert ms.get("available")
    assert ms["overall_quality"] in ("吉", "中", "凶")
    # 单点：各域速览
    domains = {dv["domain"] for dv in ms["dimension_verdicts"]}
    assert {"事业", "财运", "婚姻", "健康"} <= domains
    # 组合：连贯段落
    assert len(ms["integrated_paragraphs"]) >= 2
    # 汇总：总建议
    assert ms["master_advice"]


def test_master_includes_temporal():
    """总汇须叠入后天运程。"""
    d = _chart()
    ms = d["master_synthesis"]
    assert any("运" in p for p in ms["integrated_paragraphs"])
    assert any(dv["domain"] == "运程" for dv in ms["dimension_verdicts"])


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
