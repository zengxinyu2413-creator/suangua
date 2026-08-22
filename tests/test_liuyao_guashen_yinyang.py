"""六爻卦身·世爻阴阳回归守护 —— 防 world_yin_yang 键错配恒「阴」致阳世卦卦身全错。
此前 bug：interpreter 读 world_y.get('type')/('yin_yang')（爻无此键）→ world_yy 恒「阴」→
        所有阳世卦（世爻为阳爻）误用「阴世从午起」，卦身算错（应「阳世从子起」）。"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _div(yv):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/liuyao/divine",
        json={"method": "manual", "yao_values": yv, "gender": "male",
              "topic": "求财", "query_time": "2026-05-10T10:00:00"}).json()["data"]


def test_world_yinyang_not_constant():
    """world_yin_yang 不可恒为「阴」（修复前 80/80 恒阴）。"""
    seen = set()
    random.seed(11)
    for _ in range(60):
        yv = [random.choice([7, 8]) for _ in range(6)]
        seen.add(_div(yv).get("gua_shen", {}).get("world_yin_yang"))
    assert "阳" in seen and "阴" in seen, seen


def test_world_yinyang_tracks_line_nature():
    """world_yin_yang 须等于世爻爻性（阳爻→阳世，阴爻→阴世）。"""
    random.seed(7)
    for _ in range(40):
        yv = [random.choice([7, 8]) for _ in range(6)]
        d = _div(yv)
        wline = next((y.get("line") for y in d["yaos"] if y.get("is_world")), None)
        assert d["gua_shen"]["world_yin_yang"] == wline


def test_guashen_classical_anchors():
    """古法锚点：乾(世阳,从子)卦身巳；坤(世阴,从午)卦身亥。"""
    qian = _div([9, 9, 9, 9, 9, 9])["gua_shen"]
    kun = _div([6, 6, 6, 6, 6, 6])["gua_shen"]
    assert qian["world_yin_yang"] == "阳" and qian["zhi"] == "巳", qian
    assert kun["world_yin_yang"] == "阴" and kun["zhi"] == "亥", kun
    assert "从子" in qian["rule"] and "从午" in kun["rule"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
