"""六爻 — 综合总断（总汇合参）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_master_present_and_structured():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    d = c.post("/api/v1/liuyao/divine",
               json={"question": "求财能成否", "method": "time", "query_time": "2026-01-02T10:00:00"}).json()["data"]
    ms = d.get("master_synthesis", {})
    assert ms.get("available")
    assert ms["overall_quality"] in ("吉", "中", "凶")
    dims = {dv["dim"] for dv in ms["dimension_verdicts"]}
    # 五维：用神/世应/动爻/卦型/应期
    assert "用神" in dims and "卦型" in dims
    assert ms["integrated_paragraphs"] and ms["master_advice"]


def test_yongshen_fallback():
    """用神为空时回退至应期/主题之用神。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    d = c.post("/api/v1/liuyao/divine",
               json={"question": "求财能成否", "method": "time", "query_time": "2026-01-02T10:00:00"}).json()["data"]
    ms = d["master_synthesis"]
    # 求财用神应为妻财（即便未上卦）
    assert ms["yong_shen"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
