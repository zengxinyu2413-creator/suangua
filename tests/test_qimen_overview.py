"""奇门 — 局势总论合成 + 用神 purpose 修复回归"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.qimen.overview import synthesize_overview


def _layout(purpose=None, question=""):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"year": 2026, "month": 6, "day": 24, "hour": 14, "minute": 0, "question": question}
    if purpose:
        body["purpose"] = purpose
    return c.post("/api/v1/qimen/layout", json=body).json()["data"]


def test_purpose_drives_yongshen():
    """不同 purpose 须取不同用神门（修复前永远生门求财）。"""
    cai = _layout("求财")
    shi = _layout("事业")
    hun = _layout("婚姻")
    assert cai["yong_shen"]["topic"] == "求财" and "生门" in cai["yong_shen"]["name"]
    assert shi["yong_shen"]["topic"] == "事业" and "开门" in shi["yong_shen"]["name"]
    assert hun["yong_shen"]["topic"] == "婚姻" and "六合" in hun["yong_shen"]["name"]


def test_question_keyword_fallback():
    d = _layout(question="求官能否升迁")
    assert d["yong_shen"]["topic"] == "事业"


def test_overview_weaves_and_hero():
    d = _layout("事业")
    ov = synthesize_overview(d)
    assert ov["available"]
    titles = [p["title"] for p in ov["paragraphs"]]
    assert "用神落宫" in titles and "综断总评" in titles
    assert ov["quality"] in ("吉", "中", "凶")
    assert ov["yongshen_palace"] and ov["topic"] == "事业"


def test_in_api():
    d = _layout("求财")
    assert "overview" in d and d["overview"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
