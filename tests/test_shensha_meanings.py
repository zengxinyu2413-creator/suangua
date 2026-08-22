"""择日神煞释义 + 择事专属断 参验。
独立核验：① 释义库覆盖实占神煞；② 同日异事神煞相关性不同（非硬编码）；
③ 关键神煞宜忌方向合古法（天德诸事宜/往亡忌嫁娶出行/月破大凶）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _days(purpose, m=3):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/date-selection/select",
        json={"purpose": purpose, "year": 2026, "month": m}).json()["data"]["all_days"]


def test_shensha_meanings_directions():
    """关键神煞释义方向合古法。"""
    from core.date_selection.shensha_meanings import explain
    assert explain("天德")["type"] == "吉" and explain("天德")["level"] == "上吉"
    assert explain("月破")["type"] == "凶" and explain("月破")["level"] == "大凶"
    assert "嫁娶" in explain("往亡")["ji"] and "出行" in explain("往亡")["ji"]
    assert "求医" in explain("天医")["yi"]
    assert "嫁娶" in explain("天喜")["yi"]
    assert "针灸" in explain("血忌")["ji"]


def test_coverage_of_real_shensha():
    """释义库覆盖全年实占神煞（监控收录率）。"""
    from core.date_selection.shensha_meanings import SHENSHA
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    allss = set()
    for m in range(1, 13):
        for day in c.post("/api/v1/date-selection/select",
                          json={"purpose": "结婚", "year": 2026, "month": m}).json()["data"]["all_days"]:
            allss.update(x for x in (day.get("ji_shen") or []) + (day.get("xiong_sha") or []) if x and x != "无")
    cov = sum(1 for s in allss if s in SHENSHA)
    assert cov / len(allss) >= 0.95, f"{cov}/{len(allss)}"


def test_purpose_synthesis_discriminates():
    """择事专属断真实区分：结婚逢往亡/月破判忌、得三合/天喜判宜。"""
    from core.date_selection.shensha_meanings import synthesize_shensha_for_purpose
    days = _days("结婚")
    levels = set()
    for day in days:
        syn = synthesize_shensha_for_purpose(day.get("ji_shen", []), day.get("xiong_sha", []), "结婚")
        levels.add(syn["level"])
        # 逢往亡必判忌嫁娶
        if "往亡" in (day.get("xiong_sha") or []):
            assert any(a["name"] == "往亡" for a in syn["against"]), day["date"]
        # 逢月破必判忌
        if "月破" in (day.get("xiong_sha") or []):
            assert syn["level"] == "忌", day["date"]
    assert {"宜", "忌"}.issubset(levels)     # 既有宜也有忌（非全同）


def test_same_day_differs_by_purpose():
    """同一日，不同择事，神煞相关性不同（非硬编码）。"""
    from core.date_selection.shensha_meanings import synthesize_shensha_for_purpose
    day = _days("结婚")[7]   # 含往亡之日(忌嫁娶/出行，但于纳财未必忌)
    s_wed = synthesize_shensha_for_purpose(day.get("ji_shen", []), day.get("xiong_sha", []), "结婚")
    s_cai = synthesize_shensha_for_purpose(day.get("ji_shen", []), day.get("xiong_sha", []), "纳财")
    # 针对不同事，命中的 support/against 集应不同
    assert (set(a["name"] for a in s_wed["against"]) != set(a["name"] for a in s_cai["against"])) \
        or (set(s["name"] for s in s_wed["support"]) != set(s["name"] for s in s_cai["support"]))


def test_api_attaches_annotation():
    """API 每日附 shensha_purpose + 释义。"""
    days = _days("结婚")
    assert all("shensha_purpose" in d for d in days)
    assert any(d["shensha_annotated"]["ji_shen_explained"] for d in days)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
