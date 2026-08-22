"""统一宅报告 — 理气(玄空)×形法(阳宅) 合断"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.fengshui.house_report import build_unified_house_report


def test_combines_liqi_and_xingfa():
    r = build_unified_house_report("子", 2026, "坎", "巽", "震", birth_year=1990, gender="male")
    assert r["available"]
    assert r["liqi_verdict"] and r["xingfa_grade"]
    assert len(r["cross_items"]) == 3
    # 门主灶各含理气×形法
    for it in r["cross_items"]:
        assert it["liqi"] in ("旺", "衰", "平") and it["xingfa"] in ("吉", "凶", "平")


def test_occupant_flips_unified():
    """同房：坎命(东四)吉 vs 乾命(西四)凶。"""
    dong = build_unified_house_report("子", 2026, "坎", "巽", "震", birth_year=1990, gender="male")
    xi = build_unified_house_report("子", 2026, "坎", "巽", "震", birth_year=1976, gender="male")
    assert dong["unified_quality"] == "吉"
    assert xi["unified_quality"] == "凶"


def test_double_xiong_detected():
    """乾命：灶(东)在玄空衰方又命卦五鬼 → 理气形法皆凶。"""
    xi = build_unified_house_report("子", 2026, "坎", "巽", "震", birth_year=1976, gender="male")
    zao = next(it for it in xi["cross_items"] if it["role"] == "灶")
    assert zao["combine_q"] == "凶"


def test_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r = c.post("/api/v1/fengshui/house_report",
               json={"sitting_mountain": "子", "year": 2026, "men": "坎", "zhu": "巽", "zao": "震"})
    assert r.json()["success"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
