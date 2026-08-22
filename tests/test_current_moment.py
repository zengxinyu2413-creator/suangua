"""当下时辰 — 任何解读皆纳入此刻时空合参"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calendar.current_moment import current_sizhu, moment_vs_yongshen


def test_sizhu_complete():
    m = current_sizhu(datetime(2026, 6, 24, 14, 30))
    assert m["year_gz"] == "丙午" and m["month_gz"] == "甲午"
    assert m["day_gz"] == "己巳" and m["hour_gz"] == "辛未"
    assert m["hour_wuxing"] == "土" and m["solar_term"] == "夏至"


def test_moment_vs_yongshen():
    m = current_sizhu(datetime(2026, 6, 24, 14, 30))  # 未时土 月令火
    assert moment_vs_yongshen(m, ["木", "火"])["tone"] == "扶用"
    assert moment_vs_yongshen(m, ["金", "水"])["tone"] == "助忌"


def _ms(path, body):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post(path, json=body).json()["data"].get("master_synthesis", {})


def test_all_modules_have_current_moment():
    cases = [
        ("/api/v1/bazi/chart", {"year": 1990, "month": 5, "day": 22, "hour": 8, "gender": "male", "is_lunar": False}),
        ("/api/v1/ziwei/chart", {"year": 1990, "month": 5, "day": 22, "hour": 8, "gender": "male", "is_lunar": False}),
        ("/api/v1/liuyao/divine", {"question": "测", "method": "time"}),
        ("/api/v1/qimen/layout", {"year": 2026, "month": 6, "day": 24, "hour": 14, "minute": 0, "purpose": "求财"}),
        ("/api/v1/fengshui/xuankong", {"sitting_mountain": "子", "year": 2026}),
        ("/api/v1/fengshui/yangzhai_sanyao", {"men": "坎", "zhu": "巽", "zao": "震"}),
        ("/api/v1/date-selection/select", {"purpose": "结婚", "year": 2026, "month": 7}),
    ]
    for path, body in cases:
        ms = _ms(path, body)
        dv = ms.get("dimension_verdicts", [])
        has = any((x.get("dim") == "当下" or x.get("domain") == "当下") for x in dv)
        assert has, f"{path} 缺当下维度"
        # 汇总段落应织入当下
        assert any("当下" in p for p in ms.get("integrated_paragraphs", [])), f"{path} 段落未织当下"


def test_qimen_uses_layout_time():
    """奇门当下应取局时（非 now）。"""
    ms = _ms("/api/v1/qimen/layout",
             {"year": 2026, "month": 6, "day": 24, "hour": 14, "minute": 0, "purpose": "求财"})
    mo = next(x for x in ms["dimension_verdicts"] if x.get("dim") == "当下")
    assert "2026-06-24" in mo["verdict"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
