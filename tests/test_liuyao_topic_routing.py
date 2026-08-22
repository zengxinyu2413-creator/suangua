"""六爻 topic 简写/别名路由回归守护 —— 防非规范 topic 落默认世爻、绕过性别专用神。
此前 bug：topic='婚姻'(非规范键'婚姻感情')→ explicit 不匹配 → 退回空 question → 默认世爻，
        男占婚不取妻财、女占婚不取官鬼。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _yong(topic, gender):
    from fastapi.testclient import TestClient
    from main import app
    r = TestClient(app).post("/api/v1/liuyao/divine",
        json={"method": "manual", "yao_values": [7, 9, 8, 7, 8, 6], "gender": gender,
              "topic": topic, "query_time": "2026-05-10T10:00:00"}).json()["data"]
    return (r.get("full_reading", {}).get("yong_shen_name")
            or r.get("yongshen_judgment", {}).get("yong_shen_name"))


def test_marriage_alias_gender_specific():
    """婚姻简写各式 → 男妻财/女官鬼（性别专用神不被绕过）。"""
    for topic in ("婚姻", "婚姻感情", "感情", "结婚"):
        assert _yong(topic, "male") == "妻财", topic
        assert _yong(topic, "female") == "官鬼", topic


def test_topic_aliases_route_correctly():
    """常见简写 topic 路由到正确用神。"""
    assert _yong("财运", "male") == "妻财"
    assert _yong("升职", "male") == "官鬼"
    assert _yong("找工作", "male") == "官鬼"


def test_canonical_key_still_works():
    """规范键不受影响。"""
    assert _yong("求财", "male") == "妻财"


def test_get_yong_shen_unit():
    """单元层：规范键性别分流仍正确（回归锚点）。"""
    from core.liuyao.interpreter import get_yong_shen
    assert get_yong_shen("婚姻感情", "male") == ["妻财"]
    assert get_yong_shen("婚姻感情", "female") == ["官鬼"]
    assert get_yong_shen("婚姻感情", "女") == ["官鬼"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
