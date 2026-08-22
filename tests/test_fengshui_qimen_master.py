"""玄空/阳宅/奇门 — 综合总汇"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _c():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


def test_xuankong_master():
    d = _c().post("/api/v1/fengshui/xuankong",
                  json={"sitting_mountain": "子", "year": 2026, "birth_year": 1990, "gender": "male"}).json()["data"]
    ms = d.get("master_synthesis", {})
    assert ms.get("available")
    dims = {dv["dim"] for dv in ms["dimension_verdicts"]}
    assert "山向格局" in dims and "命卦宜居" in dims
    assert ms["integrated_paragraphs"] and ms["master_advice"]


def test_yangzhai_master_occupant_flip():
    c = _c()
    dong = c.post("/api/v1/fengshui/yangzhai_sanyao",
                  json={"men": "坎", "zhu": "巽", "zao": "震", "birth_year": 1990, "gender": "male"}).json()["data"]
    xi = c.post("/api/v1/fengshui/yangzhai_sanyao",
                json={"men": "坎", "zhu": "巽", "zao": "震", "birth_year": 1976, "gender": "male"}).json()["data"]
    # 同宅，坎命相配 vs 乾命相背 → 命卦相配维度吉凶不同
    md = next(dv for dv in dong["master_synthesis"]["dimension_verdicts"] if dv["dim"] == "命卦相配")
    mx = next(dv for dv in xi["master_synthesis"]["dimension_verdicts"] if dv["dim"] == "命卦相配")
    assert md["quality"] == "吉" and mx["quality"] == "凶"


def test_qimen_master_purpose_sensitive():
    c = _c()
    cai = c.post("/api/v1/qimen/layout",
                 json={"year": 2026, "month": 6, "day": 24, "hour": 14, "minute": 0, "purpose": "求财"}).json()["data"]
    ms = cai.get("master_synthesis", {})
    assert ms.get("available")
    assert any(dv["dim"] == "用神落宫" for dv in ms["dimension_verdicts"])
    assert ms["ju"] and ms["master_advice"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
