"""择日参验 — 建除十二神（含节气重复）对古法独立校验"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _select(purpose, year, month):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/date-selection/select",
        json={"purpose": purpose, "year": year, "month": month}).json()["data"]


def test_jian_day_matches_month_branch():
    """建日：日支 == 当日节气月建。"""
    from core.calendar.solar_terms import month_dizhi_at
    z = _select("结婚", 2026, 7)
    jian_days = [d for d in z.get("all_days", []) if d.get("officer") == "建"]
    assert jian_days, "无建日"
    for d in jian_days:
        dt = datetime.fromisoformat(d["date"])
        assert d["ganzhi"][-1] == month_dizhi_at(dt), f"{d['date']} 建日"


def test_jianchu_repeats_at_jie():
    """建除遇节重复：节气交节日建除值与前日相同（致序列出现连重）。"""
    from core.calendar.solar_terms import solar_term_on
    z = _select("结婚", 2026, 7)
    days = z.get("all_days", [])
    # 小暑(07-07)处应有建除重复
    found_repeat = False
    for i in range(1, len(days)):
        if days[i].get("officer") == days[i - 1].get("officer"):
            dt = datetime.fromisoformat(days[i]["date"])
            if solar_term_on(dt) or solar_term_on(datetime.fromisoformat(days[i - 1]["date"])):
                found_repeat = True
    assert found_repeat, "节气处应有建除重复"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
