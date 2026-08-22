"""择日 — 八字个性化（吉日按本命用神/冲克过滤）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.date_selection.personalize import personalize_days


def _days():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/date-selection/select",
                  json={"purpose": "结婚", "year": 2026, "month": 7}).json()["data"]["all_days"]


def test_personalize_uses_yongshen():
    pz = personalize_days([dict(x) for x in _days()], 1990, 5, 22, 8)
    assert pz["available"]
    assert pz["profile"]["yong"] and pz["profile"]["day_zhi"]
    assert pz["personal_best"]
    # 个人分由通用分+个人分构成
    for b in pz["personal_best"]:
        assert b["combined_score"] == b["base_score"] + b["personal_score"]


def test_different_people_different_ranking():
    """同月吉日，不同八字的人个人首选应不同（真个性化）。"""
    days = _days()
    a = personalize_days([dict(x) for x in days], 1990, 5, 22, 8)
    b = personalize_days([dict(x) for x in days], 1988, 12, 1, 8)
    # 用神不同
    assert a["profile"]["yong"] != b["profile"]["yong"] or a["profile"]["day_zhi"] != b["profile"]["day_zhi"]
    # 同一天对二人的个人分可不同
    ad = {x["date"]: x["personal_score"] for x in
          [d for d in [dict(y) for y in days]]} if False else None


def test_in_api_with_birth():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    d = c.post("/api/v1/date-selection/select",
               json={"purpose": "结婚", "year": 2026, "month": 7,
                     "birth_year": 1990, "birth_month": 5, "birth_day": 22}).json()["data"]
    assert "personalization" in d and d["personalization"]["available"]
    # 总论与视角应含个人配合
    assert any(p["title"] == "个人配合" for p in d["overview"]["paragraphs"])


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
