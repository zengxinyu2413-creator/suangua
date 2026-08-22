"""
总汇契约一致性 — 七模块 master_synthesis 须符合统一契约（构造级保证）。

以测试代替基类：任何模块的总汇若字段形状漂移（缺字段/质量值非法/维度无标签/
段落空），此测试即失败。同时校验「当下」维度必在（任何解读纳入当下时辰）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.contracts import validate_master_synthesis, must_have_current_moment

CASES = [
    ("八字", "/api/v1/bazi/chart",
     {"year": 1990, "month": 5, "day": 22, "hour": 8, "gender": "male", "is_lunar": False}),
    ("紫微", "/api/v1/ziwei/chart",
     {"year": 1990, "month": 5, "day": 22, "hour": 8, "gender": "male", "is_lunar": False}),
    ("六爻", "/api/v1/liuyao/divine", {"question": "测", "method": "time", "query_time": "2026-01-02T10:00:00"}),
    ("奇门", "/api/v1/qimen/layout",
     {"year": 2026, "month": 6, "day": 24, "hour": 14, "minute": 0, "purpose": "求财"}),
    ("玄空", "/api/v1/fengshui/xuankong", {"sitting_mountain": "子", "year": 2026}),
    ("阳宅", "/api/v1/fengshui/yangzhai_sanyao", {"men": "坎", "zhu": "巽", "zao": "震"}),
    ("择日", "/api/v1/date-selection/select", {"purpose": "结婚", "year": 2026, "month": 7}),
]


def _client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


def test_all_master_synthesis_conform():
    c = _client()
    failures = {}
    for name, path, body in CASES:
        ms = c.post(path, json=body).json()["data"].get("master_synthesis", {})
        errs = validate_master_synthesis(ms)
        if errs:
            failures[name] = errs
    assert not failures, f"总汇契约违规：{failures}"


def test_all_have_current_moment_dimension():
    c = _client()
    missing = []
    for name, path, body in CASES:
        ms = c.post(path, json=body).json()["data"].get("master_synthesis", {})
        if not must_have_current_moment(ms):
            missing.append(name)
    assert not missing, f"缺「当下」维度：{missing}"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
