"""择日 purpose 别名归一回归守护 —— 防同义词落通用默认、拿不到神煞择事专属断。
此前 bug：'下葬'(安葬同义)未在 PURPOSE_KEYWORDS → get(purpose,[purpose]) → 匹配不到 → 通用默认。"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _support(purpose):
    from fastapi.testclient import TestClient
    from main import app
    r = TestClient(app).post("/api/v1/date-selection/select",
        json={"purpose": purpose, "year": 2026, "month": 3}).json()["data"]
    ss = next((d for d in r["master_synthesis"]["dimension_verdicts"] if d["dim"] == "神煞总论"), {})
    m = re.search(r"常助此事之吉神为([^；。]+)", ss.get("verdict", ""))
    return m.group(1) if m else ""


def test_aliases_match_canonical():
    """常用同义词与规范 purpose 得相同的常助吉神。"""
    pairs = [("结婚", "婚礼"), ("开业", "开张"), ("安葬", "下葬"),
             ("搬家", "乔迁"), ("出行", "远行"), ("求医", "看病")]
    for canon, alias in pairs:
        sc, sa = _support(canon), _support(alias)
        assert sc and sc == sa, f"{canon}({sc}) != {alias}({sa})"


def test_funeral_alias_gets_specific_shensha():
    """下葬须拿到安葬专属（鸣吠），而非通用默认。"""
    assert "鸣吠" in _support("下葬")


def test_unit_alias_normalization():
    from core.date_selection.shensha_meanings import synthesize_shensha_for_purpose, PURPOSE_KEYWORDS
    # 别名归一后应命中规范键的关键词集
    r = synthesize_shensha_for_purpose(["鸣吠", "天德"], ["土符"], "下葬")
    assert isinstance(r, dict) and "support" in r


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
