"""
tests/test_qimen_yingqi_zeji.py
奇门遁甲 — 应期推算 / 奇门择吉（与择日打通）
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qimen.algorithm import calculate_qimen
from core.qimen.analyzer import analyze_qimen
from core.qimen.purpose_analysis import enrich_qimen_analysis
from core.qimen.yingqi import (
    analyze_yingqi, _palace_yingqi, _CHONG, ZHI_MONTH, ZHI_HOUR,
)
from core.qimen.zeji import select_qimen_times, _SHICHEN_HOUR, _PALACE_DIR, _score_hour_chart


def _enriched(y=2024, m=6, d=15, h=14, birth=1988):
    lay = calculate_qimen(y, m, d, h)
    if birth:
        lay["_birth_year"] = birth
    res = analyze_qimen(lay)
    return enrich_qimen_analysis(res)


# ── 应期 ──
def test_yingqi_in_enrich():
    """enrich 后含 yingqi，含 rows + summary。"""
    res = _enriched()
    yq = res["yingqi"]
    assert yq["success"] and yq["rows"] and yq["summary"]


def test_yingqi_rows_cover_roles():
    """应期逐用神宫推算（值符/值使/日干/时干/年命）。"""
    res = _enriched()
    roles = {r["role"] for r in res["yingqi"]["rows"]}
    assert "值符宫" in roles and "日干宫" in roles
    for r in res["yingqi"]["rows"]:
        assert r["yingqi"]


def test_yingqi_far_near():
    """旺衰定远近：吉宫近应、凶宫远应。"""
    res = _enriched()
    for r in res["yingqi"]["rows"]:
        if r.get("quality") in ("大吉", "吉", "小吉"):
            assert "近应" in r["far_near"]
        elif r.get("quality") in ("凶", "大凶"):
            assert "远应" in r["far_near"]


def test_yingqi_kong_fill():
    """逢空之宫应期含'填实/冲空'。"""
    res = _enriched()
    kong_rows = [r for r in res["yingqi"]["rows"] if "空亡" in r.get("flags", [])]
    for r in kong_rows:
        assert "填实" in r["yingqi"] or "冲空" in r["yingqi"]


def test_yingqi_mu_chong():
    """入墓之宫应期含'冲墓开库'。"""
    res = _enriched()
    mu_rows = [r for r in res["yingqi"]["rows"] if "入墓" in r.get("flags", [])]
    for r in mu_rows:
        assert "冲墓开库" in r["yingqi"]


def test_chong_table():
    """六冲表完整且对称。"""
    for a, b in _CHONG.items():
        assert _CHONG[b] == a
    assert len(_CHONG) == 12


def test_zhi_month_hour_tables():
    """地支→月/时辰表齐全。"""
    assert len(ZHI_MONTH) == 12 and len(ZHI_HOUR) == 12


# ── 择吉 ──
def test_zeji_returns_ranked():
    """择吉返回排序后的最佳时空。"""
    r = select_qimen_times("求财", 2024, 6, birth_year=1988, top_n=5, day_limit=6)
    assert r["success"] and r["best_times"]
    scores = [c["total_score"] for c in r["best_times"]]
    assert scores == sorted(scores, reverse=True)   # 降序


def test_zeji_time_structure():
    """每个时空含日期/时辰/吉方/分数。"""
    r = select_qimen_times("出行", 2024, 6, top_n=4, day_limit=5)
    for c in r["best_times"]:
        for k in ("date", "shichen", "best_dir", "total_score", "day_score", "qimen_score"):
            assert k in c
        assert c["total_score"] == c["day_score"] + c["qimen_score"]


def test_zeji_performance():
    """择吉扫描性能可接受（< 3s）。"""
    t = time.time()
    select_qimen_times("求财", 2024, 6, day_limit=8)
    assert time.time() - t < 3.0


def test_zeji_purpose_mapping():
    """择日近义用事映射到奇门用事。"""
    r = select_qimen_times("搬家", 2024, 6, top_n=2, day_limit=3)
    assert r["purpose"] in ("出行", "谋事")   # 搬家→出行


def test_shichen_hour_map():
    """十二时辰→代表时齐全。"""
    assert len(_SHICHEN_HOUR) == 12
    assert set(_PALACE_DIR.values()) >= {"北", "南", "东", "西"}


def test_score_hour_chart():
    """单时盘评分含 base + 格局奖罚。"""
    lay = calculate_qimen(2024, 6, 26, 22)
    sc = _score_hour_chart(lay, "求财")
    assert "score" in sc and "best_dir" in sc
    assert sc["score"] == sc["base"] + sc["pattern_bonus"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
