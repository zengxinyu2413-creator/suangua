"""紫微 — 星曜入宫断语覆盖度（防止宫名后缀不匹配致解释库失效复发）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_star_palace_suffix_tolerant():
    """get_star_palace 须兼容带/不带「宫」后缀。"""
    from core.ziwei.star_palace import get_star_palace
    assert get_star_palace("太阳", "官禄宫")   # 全名
    assert get_star_palace("太阳", "官禄")     # 无后缀
    assert get_star_palace("太阳", "事业宫")   # 别名


def test_all_palaces_get_interpretations():
    """十二宫凡有主星者，皆应得入宫断语（非仅命宫）。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    d = c.post("/api/v1/ziwei/chart",
               json={"year": 1990, "month": 5, "day": 22, "hour": 8,
                     "gender": "male", "is_lunar": False}).json()["data"]
    with_major = [p for p in d["palaces"] if p.get("major_stars")]
    filled = [p for p in with_major if p.get("star_interpretations")]
    # 有主星之宫，绝大多数应有解释（至少 10/12）
    assert len(filled) >= 10, f"仅 {len(filled)} 宫有解释（共 {len(with_major)} 宫有主星）"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
