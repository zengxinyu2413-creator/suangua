"""数据丰富度 — 富数据须接到输出（防止键不匹配致解释库失效）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _c():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


def test_bazi_pattern_desc_classical():
    """八字格局描述须有《子平真诠》级内容（非空）。"""
    c = _c()
    for y, m, d_, h in [(1990, 5, 22, 8), (1985, 3, 15, 14), (1978, 11, 8, 6)]:
        data = c.post("/api/v1/bazi/chart",
                      json={"year": y, "month": m, "day": d_, "hour": h,
                            "gender": "male", "is_lunar": False}).json()["data"]
        if data.get("pattern"):
            assert len(data.get("pattern_desc", "")) >= 30, \
                f"{y} 格局 {data['pattern']} 描述过浅"


def test_ziwei_palace_interpretations_surfaced():
    """紫微有主星之宫须得入宫断语（非仅命宫）。"""
    c = _c()
    d = c.post("/api/v1/ziwei/chart",
               json={"year": 1990, "month": 5, "day": 22, "hour": 8,
                     "gender": "male", "is_lunar": False}).json()["data"]
    with_major = [p for p in d["palaces"] if p.get("major_stars")]
    filled = [p for p in with_major if p.get("star_interpretations")]
    assert len(filled) >= len(with_major) - 1


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
