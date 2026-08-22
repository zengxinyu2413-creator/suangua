"""六爻 — 多视角整合解读（子模块尽其用·无孤儿）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.liuyao.perspectives import build_perspectives


def _divine(vals, q="求测"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/liuyao/divine", json={
        "method": "manual", "query_time": "2026-01-02T10:00:00", "yao_values": vals, "question": q, "gender": "male"}).json()["data"]


def test_six_lenses_present():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    p = build_perspectives(d)
    assert p["available"]
    ids = {l["id"] for l in p["lenses"]}
    assert ids == {"yongshen", "renwo", "dongbian", "geju", "qingtai", "shiji"}


def test_each_lens_weaves_modules():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    p = build_perspectives(d)
    for l in p["lenses"]:
        assert l["modules"]            # 言明所汇子模块
        assert len(l["text"]) > 30     # 成篇
        assert l["title"] in l["text"][:14] or "从" in l["text"][:3]


def test_no_orphans_previously_isolated_modules_covered():
    """此前孤立的子模块，现都须被某视角消费。"""
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    p = build_perspectives(d)
    covered = set(p["coverage"].keys())
    # 之前查出的孤儿，其代表概念现都应在 coverage 中
    for needed in ["持世断", "世身", "卦身", "三合三会", "六神", "应期推算", "用神力量推理链"]:
        assert needed in covered, f"孤儿未纳入视角: {needed}"


def test_dynamics_lens_uses_real_moving_count():
    """动变视角以 yaos 实算动爻，不受 dong_jing 失准 count 影响。"""
    d = _divine([9, 8, 7, 8, 9, 6], "升职")   # 实际 3 动
    p = build_perspectives(d)
    dyn = next(l for l in p["lenses"] if l["id"] == "dongbian")
    assert "3爻发动" in dyn["text"]


def test_in_api():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    assert "perspectives" in d and d["perspectives"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
