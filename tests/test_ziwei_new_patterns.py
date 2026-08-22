"""紫微补遗格局参验 — 10 新经典吉格（位置格证据独立核验、化曜格实有四化）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NEW = {"三奇加会格", "双禄朝垣格", "禄马交驰格", "财荫夹印格", "日月夹命格",
       "文桂文华格", "坐贵向贵格", "极向离明格", "金灿光辉格", "月生沧海格"}


def _scan():
    from core.ziwei.chart import build_ziwei_chart
    from core.ziwei.pattern_detector import detect_all_patterns
    rows = []
    for y in range(1958, 2006):
        for mo in (2, 5, 8, 11):
            for d in (3, 12, 21):
                for hi in range(0, 12, 2):
                    ch = build_ziwei_chart(f"{y}-{mo:02d}-{d:02d}", hi, "男")
                    pals = ch["palaces"]
                    res = detect_all_patterns(pals)
                    rows.append((pals, res))
    return rows


_ROWS = None
def _rows():
    global _ROWS
    if _ROWS is None:
        _ROWS = _scan()
    return _ROWS


def _soul_info(pals):
    soul = next((p for p in pals if p.get("is_soul")), None)
    sb = soul.get("earthly_branch") if soul else "?"
    ss = set()
    if soul:
        for k in ("major_stars", "minor_stars", "adj_stars"):
            for s in (soul.get(k) or []):
                if isinstance(s, dict):
                    ss.add(s.get("name"))
    return sb, ss


def test_no_crash_all_patterns():
    rows = _rows()
    assert len(rows) > 3000      # 扫描成功、无异常中断


def test_new_patterns_all_fire():
    """10 新格在大样本中均有触发。"""
    fired = set()
    for pals, res in _rows():
        for g in res["good_patterns"]:
            if g["name"] in NEW:
                fired.add(g["name"])
    assert NEW.issubset(fired), NEW - fired


def test_position_patterns_evidence_correct():
    """位置格证据与命宫实配一致（极向离明=紫微午/金灿光辉=太阳午/月生沧海=太阴子/财荫夹印=命坐天相）。"""
    bad = 0
    for pals, res in _rows():
        sb, ss = _soul_info(pals)
        for g in res["good_patterns"]:
            nm = g["name"]
            if nm == "极向离明格" and not (sb == "午" and "紫微" in ss):
                bad += 1
            elif nm == "金灿光辉格" and not (sb == "午" and "太阳" in ss):
                bad += 1
            elif nm == "月生沧海格" and not (sb == "子" and "太阴" in ss):
                bad += 1
            elif nm == "财荫夹印格" and "天相" not in ss:
                bad += 1
    assert bad == 0, f"{bad} 个位置格证据不符"


def test_sanqi_has_actual_sihua():
    """三奇加会格命盘三方四正确含禄权科三化。"""
    from core.ziwei.pattern_detector import (_san_fang_si_zheng_indices, _find_soul_palace,
                                             _by_index, _all_stars_in_palace, _star_mutagen)
    checked = 0
    for pals, res in _rows():
        if any(g["name"] == "三奇加会格" for g in res["good_patterns"]):
            soul = _find_soul_palace(pals)
            inds = _san_fang_si_zheng_indices(soul["index"])
            by = _by_index(pals)
            muts = set()
            for i in inds:
                for s in _all_stars_in_palace(by.get(i) or {}):
                    m = _star_mutagen(s)
                    if m in ("禄", "权", "科"):
                        muts.add(m)
            assert {"禄", "权", "科"}.issubset(muts)
            checked += 1
            if checked >= 5:
                break
    assert checked >= 1


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
