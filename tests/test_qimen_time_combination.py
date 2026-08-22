"""奇门「起局时刻 × 求测目的」组合分析参验
时家奇门：局依起局之刻而起、一局只管一时辰（有效时间段）；用神随目的变。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _layout(purpose="求财", question="", y=2025, m=12, d=22, h=12):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/qimen/layout",
        json={"year": y, "month": m, "day": d, "hour": h, "minute": 0,
              "purpose": purpose, "question": question}).json()["data"]


def test_current_moment_anchored_to_layout_time():
    """当下维度锚定起局时刻（datetime），非服务器现在。"""
    r = _layout(h=12)
    cm = next(dv for dv in r["master_synthesis"]["dimension_verdicts"] if dv.get("dim") == "当下")
    assert "2025-12-22" in cm["verdict"]
    assert "冬至" in cm["verdict"]


def test_purpose_routing_no_caishen_fallback():
    """非规范目的键归并到正确用事，不再静默回退求财。"""
    # 求职求官→事业(开门)、诉讼→官司(日干vs时干)、考试→学业(天辅)、求医→疾病(天芮)
    assert "事业" in _layout("求职求官")["yong_shen"]["name"]
    assert _layout("诉讼")["yong_shen"]["topic"] == "官司"      # 官司另法：日干我vs时干彼
    assert "天辅" in _layout("考试")["yong_shen"]["name"]
    assert "天芮" in _layout("求医")["yong_shen"]["name"]
    # 旧 bug：求职求官曾→"生门（求财谋利用神）"
    assert "求财谋利" not in _layout("求职求官")["yong_shen"]["name"]


def test_question_keyword_routing():
    """空 purpose 时由 question 关键词归并。"""
    assert _layout("", "这次诉讼能赢吗")["yong_shen"]["topic"] == "官司"


def test_yongshen_varies_by_purpose():
    """同局不同目的 → 用神宫不同。"""
    palaces = {p: _layout(p)["yong_shen"].get("palace") for p in ["求财", "婚姻", "疾病"]}
    assert len(set(palaces.values())) >= 2, palaces


def test_valid_time_window_shichen():
    """有效时间段：一局只管一时辰，窗口随起局时刻变（含子时跨日）。"""
    def _vt(h):
        r = _layout(h=h)
        return next((p for p in r["master_synthesis"]["integrated_paragraphs"] if "有效时间段" in p), "")
    assert "午时" in _vt(12) and "11:00" in _vt(12)
    assert "辰时" in _vt(8)
    assert "子时" in _vt(23) and "次日" in _vt(23)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
