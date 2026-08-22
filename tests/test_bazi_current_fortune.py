"""八字 — 大运流年并入主读盘（时间维度）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.bazi.current_fortune import build_current_fortune
from core.bazi.consistency_audit import audit_consistency


def _chart(year=1990):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/bazi/chart",
                  json={"year": year, "month": 5, "day": 22, "hour": 8,
                        "gender": "male", "is_lunar": False}).json()["data"]


def test_current_fortune_in_chart():
    d = _chart()
    cf = d.get("current_fortune")
    assert cf and cf["available"]
    assert cf["current_dayun"]["ganzhi"]
    assert cf["current_liunian"]["year"] == 2026


def test_dayun_matches_age():
    """1990年生，2026年36岁，当前大运须覆盖该年龄段。"""
    cf = _chart(1990)["current_fortune"]
    dy = cf["current_dayun"]
    assert dy["start_year"] <= 2026 < dy["end_year"]


def test_overview_has_fortune_para():
    d = _chart()
    titles = [p["title"] for p in d["overview"]["paragraphs"]]
    assert "当前运程" in titles


def test_synthesis_separates_innate_and_temporal():
    """先天命局评定不被后天运改变，但推理链含后天段。"""
    d = _chart()
    s = d["mingju_synthesis"]
    assert "后天" in s["chain_text"]
    assert s["composite_label"].startswith("命局")  # 标签仍是先天命局


def test_perspectives_has_temporal_lens():
    d = _chart()
    ids = {l["id"] for l in d["perspectives"]["lenses"]}
    assert "yuncheng" in ids
    for needed in ["大运", "流年", "岁运组合"]:
        assert needed in d["perspectives"]["coverage"]


def test_audit_detects_ming_yun_divergence():
    fake_good = {"day_master": "甲", "day_master_wx": "木",
                 "mingju_synthesis": {"composite_label": "命局上佳"},
                 "current_fortune": {"available": True,
                                     "current_dayun": {"ganzhi": "庚申", "help": "助忌"}}}
    assert "good_ming_bad_yun" in {f["id"] for f in audit_consistency(fake_good)["findings"]}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
