"""六爻 — 完整断卦合成（所问 × 全卦信号 → 一篇扣题断语）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.liuyao.full_reading import build_full_reading, _gua_he_chong


def _divine(vals, q="求测", gender="male"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/liuyao/divine", json={
        "method": "manual", "query_time": "2026-01-02T10:00:00", "yao_values": vals, "question": q, "gender": gender}).json()["data"]


def test_full_reading_structured_and_on_topic():
    d = _divine([9, 8, 7, 8, 9, 6], "今年能否升职")
    fr = build_full_reading(d)
    assert fr["available"]
    titles = [p["title"] for p in fr["paragraphs"]]
    assert "所问与用神" in titles
    assert "用神态势" in titles
    assert "结论" in titles
    blob = " ".join(p["text"] for p in fr["paragraphs"])
    assert "升职" in blob          # 扣住所问
    assert len(blob) > 200          # 成篇


def test_weaves_dynamic_signals():
    """持世 / 动象 / 应期等必须并入。"""
    d = _divine([9, 8, 7, 8, 9, 6], "今年能否升职")
    fr = build_full_reading(d)
    blob = " ".join(p["text"] for p in fr["paragraphs"])
    assert "持世" in blob            # 用神持世并入
    assert "发动" in blob or "动象" in blob  # 动爻并入
    assert "应" in blob              # 应期并入


def test_gua_he_chong_helper():
    assert _gua_he_chong(["子", "寅", "辰", "午", "申", "戌"]) == "六冲"   # 乾
    assert _gua_he_chong(["未", "巳", "卯", "午", "申", "戌"]) == "六合"   # 否
    assert _gua_he_chong(["卯", "巳", "未", "申", "午", "辰"]) == ""        # 既济


def test_liuchong_gua_integrated():
    d = _divine([7, 7, 7, 7, 7, 7], "今年财运")   # 乾为天 六冲
    fr = build_full_reading(d)
    titles = [p["title"] for p in fr["paragraphs"]]
    assert "卦体合冲" in titles
    blob = " ".join(p["text"] for p in fr["paragraphs"])
    assert "六冲" in blob


def test_in_divine_api():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    assert "full_reading" in d and d["full_reading"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
