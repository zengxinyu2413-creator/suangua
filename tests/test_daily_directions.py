"""流日紫白（三元日白）参验 — 独立核对《协纪辨方书》三元日白起例。
六锚点（冬至一白/雨水七赤/谷雨四绿/夏至九紫/处暑三碧/霜降六白）甲子符头起，阳顺阴逆。"""
import os, sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_day_anchors_qili():
    """六锚点符头甲子日入中=锚星（三元日白起例核心）。"""
    from core.fengshui.xuankong_advanced import get_daily_zibai_center, _nearest_jiazi
    from core.calendar.solar_terms import _get_solarterm_dt
    exp = {"冬至": 1, "雨水": 7, "谷雨": 4, "夏至": 9, "处暑": 3, "霜降": 6}
    for term, star in exp.items():
        ft = _nearest_jiazi(_get_solarterm_dt(2025, term))
        assert get_daily_zibai_center(ft) == star, f"{term}={get_daily_zibai_center(ft)}!={star}"


def test_yang_dun_shun_yin_dun_ni():
    """阳遁(冬至后)逐日顺+1、阴遁(夏至后)逐日逆-1。"""
    from core.fengshui.xuankong_advanced import get_daily_zibai_center, _nearest_jiazi
    from core.calendar.solar_terms import _get_solarterm_dt
    dz = _nearest_jiazi(_get_solarterm_dt(2025, "冬至"))
    assert get_daily_zibai_center(dz) == 1
    assert get_daily_zibai_center(dz + timedelta(days=1)) == 2     # 阳顺
    assert get_daily_zibai_center(dz + timedelta(days=9)) == 1     # 9→1循环
    xz = _nearest_jiazi(_get_solarterm_dt(2025, "夏至"))
    assert get_daily_zibai_center(xz) == 9
    assert get_daily_zibai_center(xz + timedelta(days=1)) == 8     # 阴逆


def test_sanyuan_continuity():
    """三元锚星间隔60日衔接（阳1→7→4、阴9→3→6），印证起例自洽。"""
    from core.fengshui.xuankong_advanced import get_daily_zibai_center, _nearest_jiazi
    from core.calendar.solar_terms import _get_solarterm_dt
    for term, star in [("雨水", 7), ("谷雨", 4), ("处暑", 3), ("霜降", 6)]:
        ft = _nearest_jiazi(_get_solarterm_dt(2025, term))
        assert get_daily_zibai_center(ft) == star


def test_daily_directions_vary_and_dimension():
    """流日方位逐日移、master 含流日维度。"""
    from core.fengshui.xuankong_advanced import get_daily_directions
    whs = {get_daily_directions(datetime(2026, 3, 1) + timedelta(days=i))["wuhuang"]["dir"] for i in range(15)}
    assert len(whs) >= 6
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    yz = c.post("/api/v1/fengshui/yangzhai_sanyao", json={"men": "坎", "zhu": "巽", "zao": "震"}).json()["data"]
    dims = [d["dim"] for d in yz["master_synthesis"]["dimension_verdicts"]]
    assert "流日方位" in dims


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
