"""六爻 动爻/化合冲 接入回归守护 —— 防 is_changing↔is_moving 键错配复发。
此前 bug：化合冲恒空、独发独静恒判全静（dong 读 is_moving/type 而爻用 is_changing）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _div(yv):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/liuyao/divine",
        json={"method": "manual", "yao_values": yv, "gender": "male",
              "topic": "求财", "query_time": "2026-05-10T10:00:00"}).json()["data"]


def test_hua_he_chong_fires():
    """化合/化冲能触发（独立核对：子丑六合化合、巳亥六冲化冲）。"""
    import itertools
    seen = set()
    for yv in itertools.product([6, 7, 8, 9], repeat=2):
        d = _div(list(yv) + [7, 8, 7, 8])
        for h in d.get("hua_he_chong", []):
            seen.add(h["type"])
            if h["type"] == "化合":
                # 化合爻：原支与化支六合
                LIU_HE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
                          "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
                assert LIU_HE.get(h["orig_zhi"]) == h["changed_zhi"]
            if h["type"] == "化冲":
                LIU_CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
                             "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
                assert LIU_CHONG.get(h["orig_zhi"]) == h["changed_zhi"]
    assert "化合" in seen and "化冲" in seen, seen     # 修复前恒空


def test_dong_jing_distinguishes():
    """独发/全静/多发三态正确区分（修复前恒判全静）。"""
    du = _div([9, 7, 8, 7, 8, 7])      # 仅初爻动
    jing = _div([7, 8, 7, 8, 7, 8])    # 全静
    duo = _div([9, 7, 9, 7, 9, 7])     # 三爻动
    du_t = du["dong_jing_analysis"].get("type", "")
    jing_t = jing["dong_jing_analysis"].get("type", "")
    duo_t = duo["dong_jing_analysis"].get("type", "")
    assert "独发" in du_t, du_t
    assert "全静" in jing_t or "静" in jing_t, jing_t
    assert "多" in duo_t, duo_t
    assert du_t != jing_t != duo_t


def test_dong_jing_not_always_static():
    """有动爻之卦绝不可恒判全静（核心回归点）。"""
    d = _div([9, 7, 8, 7, 8, 7])
    assert "全静" not in d["dong_jing_analysis"].get("type", "")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
