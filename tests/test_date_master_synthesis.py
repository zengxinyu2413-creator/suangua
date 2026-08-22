"""择日 — 综合总论（总汇）+ 月支/节气名 严谨性回归"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _sel(**kw):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"purpose": "结婚", "year": 2026, "month": 7}
    body.update(kw)
    return c.post("/api/v1/date-selection/select", json=body).json()["data"]


def test_master_present():
    d = _sel(birth_year=1990, birth_month=5, birth_day=22)
    ms = d.get("master_synthesis", {})
    assert ms.get("available")
    dims = {dv["dim"] for dv in ms["dimension_verdicts"]}
    assert "月令丰歉" in dims and "通用首选" in dims
    assert "个人首选" in dims  # 带生辰应有个性化
    assert ms["integrated_paragraphs"] and ms["master_advice"]


def test_month_zhi_by_solar_term():
    """7月中应未月（非申）；月支按节气而非日历月号。"""
    d = _sel()
    assert d["month_zhi"] == "未"


def test_month_jieqi_names_correct():
    """7月节气应为小暑/大暑（非立秋/处暑）。"""
    d = _sel()
    names = " ".join(d.get("month_jieqi", []))
    assert "小暑" in names and "大暑" in names
    assert "立秋" not in names


def test_dec_jieqi():
    d = _sel(month=12)
    names = " ".join(d.get("month_jieqi", []))
    assert "大雪" in names and "冬至" in names


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
