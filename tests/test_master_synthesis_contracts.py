"""master_synthesis 契约一致性 conformance —— 复活 core/contracts.py 之孤儿校验器。
contracts.py 原意：「逐模块校验真实输出，任何漂移即失败」，但校验器从未被调用。
此测试将其接入，逐模块校验 + 自检校验器本身确能抓违规（验证验证器）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.contracts import (validate_master_synthesis, must_have_current_moment,
                            normalize_master_synthesis)

_CASES = [
    ("六爻", "/api/v1/liuyao/divine",
     {"method": "manual", "yao_values": [7, 9, 8, 7, 8, 6], "gender": "male",
      "topic": "求财", "query_time": "2026-05-10T10:00:00"}),
    ("八字", "/api/v1/bazi/chart",
     {"year": 1988, "month": 4, "day": 10, "hour": 14, "gender": "male", "is_lunar": False}),
    ("紫微", "/api/v1/ziwei/chart",
     {"year": 1988, "month": 4, "day": 10, "hour": 14, "gender": "男", "is_lunar": False}),
    ("奇门", "/api/v1/qimen/layout",
     {"year": 2026, "month": 3, "day": 10, "hour": 14, "purpose": "求财"}),
    ("玄空", "/api/v1/fengshui/xuankong",
     {"sitting_mountain": "子", "year": 2010}),
    ("择日", "/api/v1/date-selection/select",
     {"purpose": "结婚", "year": 2026, "month": 3}),
    ("阳宅", "/api/v1/fengshui/yangzhai_sanyao",
     {"men": "坎", "zhu": "巽", "zao": "震"}),
]


def _ms(ep, body):
    from fastapi.testclient import TestClient
    from main import app
    d = TestClient(app).post(ep, json=body).json().get("data", {})
    return d.get("master_synthesis", {})


def test_all_modules_master_synthesis_conform():
    """七模块 master_synthesis 均合契约（字段形状/quality合法值/非空维度）。"""
    failures = {}
    for name, ep, body in _CASES:
        errs = validate_master_synthesis(_ms(ep, body))
        if errs:
            failures[name] = errs
    assert not failures, failures


def test_all_modules_have_current_moment():
    """七模块总汇均纳入「当下」维度。"""
    missing = [name for name, ep, body in _CASES
               if not must_have_current_moment(_ms(ep, body))]
    assert not missing, missing


def test_validator_actually_catches_violations():
    """验证验证器：故意注入违规 ms，校验器必须报出（防验证器本身失效）。"""
    bad = {"available": True}      # 缺全部必备字段
    assert validate_master_synthesis(bad)            # 须非空（报违规）

    bad2 = {"available": True, "headline": "x", "overall_quality": "超吉",  # 非法 quality
            "dimension_verdicts": [{"dim": "a", "quality": "吉", "verdict": "v"}],
            "integrated_paragraphs": ["p"], "master_advice": "adv"}
    assert any("overall_quality" in e for e in validate_master_synthesis(bad2))

    bad3 = {"available": True, "headline": "x", "overall_quality": "吉",
            "dimension_verdicts": [{"dim": "a", "quality": "吉", "verdict": ""}],  # 空 verdict
            "integrated_paragraphs": ["p"], "master_advice": "adv"}
    assert any("verdict" in e for e in validate_master_synthesis(bad3))


def test_normalize_dual_label():
    """normalize 补齐 dim/domain 双键（前端任取其一可渲染）。"""
    ms = {"available": True, "dimension_verdicts": [{"dim": "用神", "quality": "吉", "verdict": "v"}]}
    normalize_master_synthesis(ms)
    dv = ms["dimension_verdicts"][0]
    assert dv["dim"] == dv["domain"] == "用神"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
