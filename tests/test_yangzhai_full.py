"""阳宅 — 命卦匹配(人宅相配) + 六件套"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.fengshui.yangzhai_mingua import analyze_mingua_match
from core.fengshui.yangzhai_overview import synthesize_overview
from core.fengshui.yangzhai_synthesis import synthesize_zhaixiang
from core.fengshui.yangzhai_perspectives import build_perspectives
from core.fengshui.yangzhai_audit import audit_consistency


def _house(birth_year=None, gender=None):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"men": "坎", "zhu": "巽", "zao": "震"}
    if birth_year:
        body["birth_year"] = birth_year
        body["gender"] = gender
    return c.post("/api/v1/fengshui/yangzhai_sanyao", json=body).json()["data"]


def test_mingua_match_occupant_aware():
    """同宅不同主人：坎命(东四)吉、乾命(西四)凶。"""
    dong = _house(1990, "male")   # 坎命东四
    xi = _house(1976, "male")     # 乾命西四
    md, mx = dong["mingua_match"], xi["mingua_match"]
    assert md["compatible"] and md["match_quality"] == "吉"
    assert (not mx["compatible"]) and mx["match_quality"] == "凶"


def test_overview_quality_flips_by_occupant():
    """同一上吉之宅，质量随主人翻转。"""
    dong = synthesize_overview(_house(1990, "male"))
    xi = synthesize_overview(_house(1976, "male"))
    assert dong["quality"] == "吉" and xi["quality"] == "凶"


def test_synthesis_mingua_weight():
    s_dong = synthesize_zhaixiang(_house(1990, "male"))
    s_xi = synthesize_zhaixiang(_house(1976, "male"))
    # 同内格，人宅不配应显著拉低综合力
    assert s_dong["composite_score"] > s_xi["composite_score"]
    assert any("人宅相配" in f["module"] for f in s_dong["factors"])


def test_audit_catches_grade_vs_person():
    a = audit_consistency(_house(1976, "male"))   # 内格吉但人宅不配
    assert "grade_vs_person" in {f["id"] for f in a["findings"]}


def test_perspectives_no_orphans():
    p = build_perspectives(_house(1990, "male"))
    ids = {l["id"] for l in p["lenses"]}
    assert ids == {"sanyao", "renzhai", "chundu", "youxing", "liushi", "louceng"}
    for needed in ["命卦", "八星详解", "路井灶厕碓磨畜栏", "穿宫九星"]:
        assert needed in p["coverage"]


def test_six_piece_in_api():
    d = _house(1990, "male")
    assert all(k in d for k in ("mingua_match", "overview", "zhaixiang_synthesis", "perspectives", "consistency_audit"))


def test_works_without_occupant():
    d = _house()
    assert d["overview"]["available"] and not d["overview"]["has_person"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
