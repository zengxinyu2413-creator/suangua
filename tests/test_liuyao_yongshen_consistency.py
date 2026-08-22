"""六爻 — 用神判定三路一致（full_reading / topic_analysis / yingqi 同源）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TOPICS = ["求财能成否", "婚姻", "功名考试", "疾病", "求子", "失物", "官司", "出行"]


def test_yongshen_consistent_across_paths():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    bad = []
    for q in TOPICS:
        d = c.post("/api/v1/liuyao/divine",
                   json={"question": q, "method": "time",
                         "query_time": "2026-06-24T14:00:00"}).json()["data"]
        ta = d.get("topic_analysis", {})
        t = (ta.get("timing", {}) or {}).get("yong_shen_name") or ta.get("yong_shen_name")
        y = d.get("yingqi", {}).get("yong_shen_name")
        f = d.get("full_reading", {}).get("yong_shen_name")
        if not (t == y == f):
            bad.append((q, t, y, f))
    assert not bad, f"用神不一致：{bad}"


def test_self_divined_topics_use_world():
    """自占类（疾病/官司/出行）用神应为世爻。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    for q in ["疾病", "官司", "出行"]:
        d = c.post("/api/v1/liuyao/divine",
                   json={"question": q, "method": "time",
                         "query_time": "2026-06-24T14:00:00"}).json()["data"]
        assert d["full_reading"]["yong_shen_name"] == "世爻", f"{q} 应以世爻为用"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
