"""奇门官司用神参验 — 日干为我、时干为彼，比二宫强弱 + 干五行生克定胜负。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _gs(y=2026, m=3, d=20, h=14, purpose="官司"):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/qimen/layout",
        json={"year": y, "month": m, "day": d, "hour": h, "minute": 0, "purpose": purpose}).json()["data"]["yong_shen"]


def test_guansi_uses_day_vs_hour_stem():
    """官司用神=日干(我)vs时干(彼)，非简化为门；含双方落宫。"""
    ys = _gs()
    assert ys["topic"] == "官司"
    assert "日干" in ys["name"] and "时干" in ys["name"]
    assert "palace" in ys and "other_palace" in ys
    assert "门" not in ys["name"]                       # 不再是门用神


def test_guansi_verdict_consistent_with_scores():
    """胜负与（宫强弱差 + 生克）一致：我优→吉、彼优→凶。"""
    for m, d in [(1, 15), (3, 20), (5, 10), (7, 7), (9, 12), (11, 3), (2, 8), (6, 18)]:
        ys = _gs(m=m, d=d)
        sm, so = ys["me_score"], ys["other_score"]
        edge = (sm - so) + {"我克彼": 1.5, "彼克我": -1.5, "我生彼": -0.5, "彼生我": 0.5}.get(ys["ke_relation"], 0)
        if edge >= 1.5:
            assert ys["quality"] == "吉", f"{m}-{d}"
        elif edge <= -1.5:
            assert ys["quality"] == "凶", f"{m}-{d}"
        else:
            assert ys["quality"] == "平", f"{m}-{d}"


def test_guansi_varies():
    """跨日期胜负有别（非恒定）。"""
    seen = {_gs(m=m, d=d)["quality"] for m, d in [(1, 15), (9, 12), (6, 18), (3, 20)]}
    assert len(seen) >= 2, seen


def test_shengfu_uses_day_vs_hour_stem():
    """胜负/比赛同官司法：日干(我)vs时干(彼)，措辞为竞斗（避其锋/主动进取/抢占吉时）。"""
    for purpose in ["胜负", "比赛", "竞争"]:
        ys = _gs(purpose=purpose)
        assert ys["topic"] == "胜负"
        assert "日干" in ys["name"] and "时干" in ys["name"]
        assert "门" not in ys["name"]
    # 胜负措辞与官司不同
    sf = _gs(m=9, d=12, purpose="胜负")
    assert "进取" in sf["verdict"] or "锋" in sf["verdict"] or "旗鼓" in sf["verdict"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
