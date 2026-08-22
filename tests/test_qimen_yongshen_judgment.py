"""奇门用神落宫多维断语参验 — 门×星×神×旺衰×神煞合成。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _ys(purpose, m=3, d=20):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/qimen/layout",
        json={"year": 2026, "month": m, "day": d, "hour": 14, "purpose": purpose}).json()["data"]["yong_shen"]


def test_judgment_multidimensional():
    """门星神类用神含多维断语（得地/门户/星/神至少3维）+ 综合段。"""
    ys = _ys("求财")
    dims = [d["dim"] for d in ys.get("judgment_dimensions", [])]
    assert "得地旺衰" in dims          # 曾因 gong_wx 键不匹配(艮宫vs艮八宫)缺失，已修
    assert "门户对口" in dims
    assert len(dims) >= 3
    assert ys.get("judgment", "").startswith("综断")


def test_judgment_door_fitness():
    """门户对口随用事变：求财临生门为正应（得宜）。"""
    ys = _ys("求财")
    fit = next(d for d in ys["judgment_dimensions"] if d["dim"] == "门户对口")
    assert "生门" in fit["text"]


def test_judgment_dedi_wuxing_correct():
    """得地旺衰按五行生克：比和/生为得力得生、克为受制。"""
    for purpose in ["求财", "事业", "婚姻", "学业", "健康"]:
        ys = _ys(purpose)
        dd = next((d for d in ys.get("judgment_dimensions", []) if d["dim"] == "得地旺衰"), None)
        if dd:
            assert any(k in dd["text"] for k in ["比和", "得生", "受制", "泄气", "克"])


def test_guansi_no_palace_judgment():
    """官司/胜负/寻人自有专断，不挂落宫多维断语。"""
    for purpose in ["官司", "胜负", "寻人"]:
        ys = _ys(purpose)
        assert "judgment_dimensions" not in ys or not ys.get("judgment_dimensions")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
