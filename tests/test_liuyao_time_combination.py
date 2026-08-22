"""六爻「所问 × 占卦时刻」组合分析参验
任何起卦皆受时间影响（月令定用神旺衰、应期相对占时算）且有有效时间段。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _div(vals, topic, qt):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/liuyao/divine",
        json={"question": topic, "method": "manual", "yao_values": vals,
              "topic": topic, "query_time": qt}).json()["data"]


def test_strength_by_month_order_not_day():
    """用神旺衰严格按月令（非日支）：乾为天求财·妻财寅木 春旺/夏休/秋死/冬相。"""
    exp = {"2026-02-10T10:00:00": ("寅", "旺"), "2026-06-10T10:00:00": ("午", "休"),
           "2026-09-10T10:00:00": ("酉", "死"), "2026-12-10T10:00:00": ("子", "相")}
    for qt, (mz_exp, st_exp) in exp.items():
        d = _div([7, 7, 7, 7, 7, 7], "求财", qt)
        assert d["month_zhi"] == mz_exp, qt
        cai = next(y for y in d["yaos"] if y["liu_qin"] == "妻财")
        assert cai["strength"]["label"] == st_exp, f"{qt} 妻财旺衰"


def test_yongshen_consistent_across_paths():
    """用神三处一致（顶层 / timing / full_reading），含自占类世爻。"""
    qt = "2026-09-10T10:00:00"
    for topic in ["求财", "求医疾病", "婚姻感情", "考试功名", "官司诉讼", "出行远行"]:
        d = _div([7, 8, 7, 8, 7, 8], topic, qt)
        ta = d["topic_analysis"]
        top = ta["yong_shen_name"]
        tim = ta["timing"]["yong_shen_name"]
        fr = d["full_reading"]["yong_shen_name"]
        assert top == tim == fr, f"{topic}: {top}/{tim}/{fr}"


def test_current_moment_anchored_to_cast_time():
    """当下维度锚定占卦时刻（divine_date），非服务器现在。"""
    qt = "2026-09-10T10:00:00"
    d = _div([7, 8, 7, 8, 7, 8], "求财", qt)
    assert d["divine_date"] == qt
    cm = next(dv for dv in d["master_synthesis"]["dimension_verdicts"] if dv.get("dim") == "当下")
    assert "2026-09-10" in cm["verdict"]
    assert "白露" in cm["verdict"]


def test_yingqi_shifts_with_cast_time():
    """应期相对占卦时刻推算——同卦不同占时，应期绝对日期随之平移。"""
    a = _div([9, 8, 7, 8, 7, 8], "求财", "2026-09-10T10:00:00")
    b = _div([9, 8, 7, 8, 7, 8], "求财", "2025-12-01T10:00:00")
    da = a["yingqi"]["primary"]["date"]; db = b["yingqi"]["primary"]["date"]
    assert da.startswith("2026-09") and db.startswith("2025-12"), f"{da} / {db}"


def test_valid_time_window_stated():
    """总汇明示有效时间段：起算点(占卦时刻) → 应期止。"""
    qt = "2026-09-10T10:00:00"
    d = _div([9, 8, 7, 8, 7, 8], "求财", qt)
    vt = next((p for p in d["master_synthesis"]["integrated_paragraphs"] if "有效时间段" in p), "")
    assert "2026-09-10" in vt and "应期" in vt


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
