"""择日 — 总论 + 推理链 + 多视角 + 一致性审核"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.date_selection.overview import synthesize_overview
from core.date_selection.synthesis import synthesize_zeri
from core.date_selection.perspectives import build_perspectives
from core.date_selection.consistency_audit import audit_consistency


def _sel(purpose="结婚"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/date-selection/select",
                  json={"purpose": purpose, "year": 2026, "month": 7}).json()["data"]


def test_overview_varies_by_purpose():
    hun = synthesize_overview(_sel("结婚"))
    ban = synthesize_overview(_sel("搬家"))
    assert hun["available"] and ban["available"]
    # 不同用途首选日或吉日数应不同
    assert (hun["top_date"], hun["good_count"]) != (ban["top_date"], ban["good_count"]) or hun["top_score"] != ban["top_score"]


def test_synthesis_integrates():
    s = synthesize_zeri(_sel("动土"))
    mods = {f["module"] for f in s["factors"]}
    assert "建除十二神" in mods
    assert s["composite_label"] in ("上吉之日", "吉日可用", "平和之日", "次日宜慎", "凶日勿用")


def test_synonym_matching_huangli():
    """结婚 应能匹配老黄历『嫁娶』（同义词修复）。"""
    s = synthesize_zeri(_sel("结婚"))
    a = audit_consistency(_sel("结婚"))
    # 力量因子或审核应认出宜/忌「结婚」
    has = any("老黄历" in f["module"] for f in s["factors"]) or \
          any("老黄历" in "".join(f["modules"]) or "建除忌" in f["title"] for f in a["findings"])
    assert has


def test_perspectives_no_orphans():
    p = build_perspectives(_sel())
    ids = {l["id"] for l in p["lenses"]}
    assert ids == {"topday", "shensha", "fangwei", "chong", "month", "personal"}
    for needed in ["彭祖百忌", "胎神", "旬空", "忌避之日"]:
        assert needed in p["coverage"]


def test_audit_breaker_synthetic():
    """构造首选日犯岁破 → 矛盾。"""
    fake = {"purpose": "结婚",
            "best_days": [{"date": "2026-07-01", "ganzhi": "甲子", "score": 7,
                           "is_year_breaker": True, "yi": [], "ji": []}]}
    a = audit_consistency(fake)
    assert "top_is_breaker" in {f["id"] for f in a["findings"]}


def test_in_api():
    d = _sel()
    assert all(k in d for k in ("overview", "zeri_synthesis", "perspectives", "consistency_audit"))


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
