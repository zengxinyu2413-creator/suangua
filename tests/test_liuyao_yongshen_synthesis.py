"""六爻 — 用神力量综合评估（子模块互助集成层）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.liuyao.yongshen_synthesis import synthesize_yongshen_strength


def _divine(vals, q="求测"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/liuyao/divine", json={
        "method": "manual", "query_time": "2026-01-02T10:00:00", "yao_values": vals, "question": q, "gender": "male"}).json()["data"]


def test_integrates_multiple_modules():
    """综合力须纳入月日之外的修正（动变/合局/四位动）。"""
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    s = synthesize_yongshen_strength(d)
    assert s["available"]
    sources = {f["source"] for f in s["factors"]}
    # 至少含旺衰 + 一个跨模块修正
    assert any(x.startswith("旺衰") for x in sources)
    assert any(x.startswith(("三合", "动变", "四位")) for x in sources)
    # 综合力 ≠ 基力（说明确实叠加了修正）
    assert s["composite_force"] != s["base_force"] or len(s["factors"]) <= 1


def test_chain_text_shows_attribution():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    s = synthesize_yongshen_strength(d)
    assert "〔" in s["chain_text"]      # 标注模块出处
    assert "⟹" in s["chain_text"]       # 收束到综合


def test_in_api():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    assert "yongshen_strength" in d


def test_xie_qi_case():
    """用神生局 = 泄气减力。"""
    d = _divine([7, 7, 7, 7, 7, 7], "财运")   # 妻财寅木 入 寅午戌火局 = 木生火泄
    s = synthesize_yongshen_strength(d)
    labels = " ".join(f["label"] for f in s["factors"])
    # 火局对木用神应判为泄或中性，不应误判为合起增力
    assert "聚力大增" not in labels


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
