"""紫微性别归一化回归守护 —— 防 'female' 被静默 fallback 成男。
此前 bug：api/ziwei.py `gender if gender in ('男','女') else '男'` 把合法 'female' 误判为男，
        女命大限顺逆算反、命主身主可能错。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _chart(g):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/ziwei/chart",
        json={"year": 1990, "month": 6, "day": 15, "hour": 10,
              "gender": g, "calendar": "solar"}).json()["data"]


def test_female_not_coerced_to_male():
    """英文 'female' 须得女命，不可 fallback 成男。"""
    assert _chart("female")["metadata"]["gender"] == "女"
    assert _chart("male")["metadata"]["gender"] == "男"


def test_english_equals_chinese():
    """male≡男、female≡女（英文与中文产生同一盘）。"""
    en_m = _chart("male")
    zh_m = _chart("男")
    en_f = _chart("female")
    zh_f = _chart("女")
    assert en_m["metadata"]["gender"] == zh_m["metadata"]["gender"] == "男"
    assert en_f["metadata"]["gender"] == zh_f["metadata"]["gender"] == "女"
    # 大限范围一致
    assert [p.get("decadal_range") for p in en_m["palaces"]] == \
           [p.get("decadal_range") for p in zh_m["palaces"]]


def test_male_female_differ():
    """男女大限顺逆不同（性别真正参与排盘，非被吞）。"""
    m = [p.get("decadal_range") for p in _chart("男")["palaces"]]
    f = [p.get("decadal_range") for p in _chart("女")["palaces"]]
    assert m != f


def test_norm_gender_helper():
    """归一化 helper 覆盖常见写法。"""
    from api.ziwei import _norm_gender
    for x in ("女", "female", "Female", "FEMALE", "woman", "f"):
        assert _norm_gender(x) == "女", x
    for x in ("男", "male", "Male", "man", "m"):
        assert _norm_gender(x) == "男", x


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
