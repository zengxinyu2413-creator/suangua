"""择日 master 神煞总论参验 — 逐日择事专属断聚合为本月神煞合参。
独立核验：总论最宜/正忌日与每日层级一致；异事聚合不同（非硬编码）。"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _data(purpose, m=3):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/date-selection/select",
        json={"purpose": purpose, "year": 2026, "month": m}).json()["data"]


def _ss_dim(d):
    return next((x for x in d["master_synthesis"]["dimension_verdicts"] if x["dim"] == "神煞总论"), None)


def test_shensha_summary_present():
    d = _data("结婚")
    ss = _ss_dim(d)
    assert ss and "结婚" in ss["verdict"]
    assert "正利者" in ss["verdict"] and "正忌者" in ss["verdict"]


def test_summary_best_days_match_per_day():
    """总论所列神煞最宜之日，必在每日 shensha_purpose 宜集内（一致）。"""
    d = _data("结婚")
    ss = _ss_dim(d)
    yi = {x["date"][5:] for x in d["all_days"] if (x.get("shensha_purpose") or {}).get("level") == "宜"}
    m = re.search(r"最宜之日：([^。]+)", ss["verdict"])
    listed = re.findall(r"\d\d-\d\d", m.group(1)) if m else []
    assert listed and all(x in yi for x in listed)


def test_summary_worst_days_match_per_day():
    d = _data("结婚")
    ss = _ss_dim(d)
    ji = {x["date"][5:] for x in d["all_days"] if (x.get("shensha_purpose") or {}).get("level") == "忌"}
    m = re.search(r"正忌当避：([^。]+)", ss["verdict"])
    listed = re.findall(r"\d\d-\d\d", m.group(1)) if m else []
    assert listed and all(x in ji for x in listed)


def test_summary_varies_by_purpose():
    """异事聚合之常助吉神不同：结婚见不将、安葬见鸣吠、开业见五富。"""
    v_wed = _ss_dim(_data("结婚"))["verdict"]
    v_fun = _ss_dim(_data("安葬"))["verdict"]
    v_biz = _ss_dim(_data("开业"))["verdict"]
    assert "不将" in v_wed
    assert "鸣吠" in v_fun
    assert ("五富" in v_biz or "五合" in v_biz)
    assert v_wed != v_fun != v_biz


def test_summary_in_integrated_paragraphs():
    d = _data("结婚")
    paras = " ".join(d["master_synthesis"]["integrated_paragraphs"])
    assert "神煞" in paras or "正利" in paras or "正忌" in paras


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
