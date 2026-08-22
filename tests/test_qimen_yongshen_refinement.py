"""奇门用神取法精化参验 — 类神分门/星/神，逆向用神(病符/盗神)五行受制反判。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_POS_WX = {"坎宫": "水", "坤宫": "土", "震宫": "木", "巽宫": "木", "中宫": "土",
           "乾宫": "金", "兑宫": "金", "艮宫": "土", "离宫": "火"}


def _layout(purpose, y=2026, m=1, d=15, h=14):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/qimen/layout",
        json={"year": y, "month": m, "day": d, "hour": h, "minute": 0, "purpose": purpose}).json()["data"]


def test_star_deity_yongshen_located_correctly():
    """学业=天辅(星)、疾病=天芮(星)、失物=玄武(神)，用神宫该字段确含此 marker。"""
    for purpose, marker, field in [("学业", "天辅", "star"), ("疾病", "天芮", "star"), ("失物", "玄武", "deity")]:
        r = _layout(purpose)
        ys = r["yong_shen"]
        assert marker in ys["name"], f"{purpose} name"
        pal = next(p for p in r["palaces"] if p["palace_name"] == ys["palace"])
        assert marker in str(pal.get(field, "")), f"{purpose} 落宫{field}"


def test_door_yongshen_unaffected():
    """门类用神不受精化影响：求财生门、事业开门、出行生门。"""
    assert "生门" in _layout("求财")["yong_shen"]["name"]
    assert "开门" in _layout("事业")["yong_shen"]["name"]
    assert "生门" in _layout("出行")["yong_shen"]["name"]


def test_adverse_yongshen_wuxing_control():
    """逆向用神(病符天芮·土)五行受制反判：木宫克/金宫泄→吉，火宫生/土宫比和→凶。"""
    KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    seen = set()
    for m, d in [(1, 15), (3, 20), (5, 10), (7, 7), (9, 12), (11, 3), (2, 8), (6, 18)]:
        r = _layout("疾病", m=m, d=d)
        ys = r["yong_shen"]
        gw = _POS_WX.get(ys["palace"])
        q = ys["quality"]
        seen.add(q)
        # 校验五行关系与品质一致（土=天芮）
        if gw == "木" or SHENG.get("土") == gw:          # 木克土 / 土生金(泄)
            assert q == "吉", f"{m}-{d} {gw}→{q}"
        elif SHENG.get(gw) == "土" or gw == "土":         # 火生土 / 土比和
            assert q == "凶", f"{m}-{d} {gw}→{q}"
    # 跨日期应有吉有凶（非恒定，证明真正区分病符受制）
    assert "吉" in seen and "凶" in seen, seen


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))


def test_deity_star_yongshen_refined():
    """感情/婚姻=六合(神)、健康=天心(星)，按类神定位非门。"""
    for purpose, marker, field in [("感情", "六合", "deity"), ("婚姻", "六合", "deity"), ("健康", "天心", "star")]:
        r = _layout(purpose)
        ys = r["yong_shen"]
        assert marker in ys["name"], f"{purpose} name={ys['name']}"
        pal = next(p for p in r["palaces"] if p["palace_name"] == ys["palace"])
        assert marker in str(pal.get(field, "")), f"{purpose} 落宫{field}"


def test_xunren_uses_hour_stem():
    """寻人=时干(所寻之人)，观落宫门星断远近归否；临生门吉、死门凶。"""
    seen = set()
    for m, d in [(1, 15), (3, 20), (5, 10), (7, 7), (9, 12), (11, 3)]:
        r = _layout("寻人", m=m, d=d)
        ys = r["yong_shen"]
        assert ys["topic"] == "寻人"
        assert "时干" in ys["name"] and "门" not in ys["name"].split("临")[0]
        seen.add(ys["quality"])
    assert len(seen) >= 2, seen      # 随落宫门星有别
