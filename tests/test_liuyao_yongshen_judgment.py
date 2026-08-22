"""六爻用神落爻多维断参验 — 现伏×旺衰×动静化象×空破墓×元神×忌神×世应。
独立核验：元神/忌神六亲合古法生克环；判语随月令旺衰真实变化（非硬编码）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _yj(topic, qt="2026-09-10T10:00:00", yv=None):
    from fastapi.testclient import TestClient
    from main import app
    yv = yv or [7, 9, 8, 7, 8, 6]
    r = TestClient(app).post("/api/v1/liuyao/divine",
        json={"method": "manual", "yao_values": yv, "gender": "male", "topic": topic, "query_time": qt}).json()
    return r["data"].get("yongshen_judgment", {})


def test_yuanshen_jishen_liuqin_classical():
    """元神/忌神六亲合古法生克环（五种用神全核）。"""
    from core.liuyao.yongshen_judgment import expected_yuanshen, expected_jishen
    exp = {"妻财": ("子孙", "兄弟"), "官鬼": ("妻财", "子孙"), "父母": ("官鬼", "妻财"),
           "子孙": ("兄弟", "父母"), "兄弟": ("父母", "官鬼")}
    for lq, (ey, ej) in exp.items():
        assert expected_yuanshen(lq) == ey, lq
        assert expected_jishen(lq) == ej, lq


def test_judgment_present_and_hidden():
    """用神现/伏两态均出断；伏神给出出伏条件。"""
    pj = _yj("官司")           # 用神世爻兄弟，现
    assert pj["available"] and pj["present_state"] == "现"
    assert pj["role_check"]["yuanshen_ok"] and pj["role_check"]["jishen_ok"]
    hj = _yj("求财")           # 用神妻财，伏
    assert hj["available"] and hj["present_state"] == "伏"
    assert any("伏" in d["text"] for d in hj["dimensions"])


def test_hidden_yongshen_locates_yuanshen_jishen_from_yaos():
    """用神伏时（roles 空）原神/忌神仍从 yaos 正确定位——求财忌神兄弟在卦(酉/申)。"""
    hj = _yj("求财")
    ji_dim = next(d for d in hj["dimensions"] if d["dim"] == "忌神克制")
    assert "兄弟酉" in ji_dim["text"] or "兄弟申" in ji_dim["text"]    # 曾误判"不上卦"，已修
    assert "不上卦" not in ji_dim["text"]


def test_verdict_varies_with_yuelin():
    """判语随月令旺衰真实变化（非硬编码）：用神兄弟酉(金)酉月旺、午月囚。"""
    sep = _yj("官司", "2026-09-10T10:00:00")   # 酉月金旺
    jun = _yj("官司", "2026-06-10T10:00:00")   # 午月金囚
    assert sep["net_score"] > jun["net_score"], (sep["net_score"], jun["net_score"])
    assert jun["verdict_level"] == "inauspicious"


def test_dimensions_completeness():
    """现卦用神含七维（现伏/旺衰/动静/空破墓/元神/忌神/世应）。"""
    pj = _yj("官司")
    dims = {d["dim"] for d in pj["dimensions"]}
    for need in ("用神现伏", "旺衰得令", "动静化象", "空破墓绝", "元神生扶", "忌神克制", "世应关系"):
        assert need in dims, need


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
