"""
基础常量一致性守护 — 防止各模块本地重定义与 core.constants 分叉。

历史教训：干支五行/地支冲合/地支五行 散在 9~15 文件各自重定义，是潜在分叉炸弹。
此测试扫描各模块内 12 地支/10 天干的本地 dict，逐一比对 core.constants 权威表；
任何一处分叉（写错一个字）即测试失败，从而锁定一致性。
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from core.constants import TIANGAN_WUXING, DIZHI_WUXING, LIUCHONG, LIUHE

ZHI = set("子丑寅卯辰巳午未申酉戌亥")
GAN = set("甲乙丙丁戊己庚辛壬癸")


def _iter_dict_literals(path):
    """产出文件中所有 {str:str} 字面量 dict。"""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except Exception:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            pairs = {}
            ok = True
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant) \
                        and isinstance(k.value, str) and isinstance(v.value, str):
                    pairs[k.value] = v.value
                else:
                    ok = False
                    break
            if ok and pairs:
                yield pairs


def _all_py():
    for dp, _, fs in os.walk(os.path.join(ROOT, "core")):
        for fn in fs:
            if fn.endswith(".py"):
                yield os.path.join(dp, fn)


def test_no_divergent_dizhi_wuxing():
    """任何完整的「12地支→五行」本地 dict 必须等于 DIZHI_WUXING。"""
    bad = []
    for path in _all_py():
        for d in _iter_dict_literals(path):
            keys = set(d.keys())
            # 完整 12 地支映射到五行字
            if keys == ZHI and set(d.values()) <= set("木火土金水"):
                if d != DIZHI_WUXING:
                    bad.append((path, d))
    assert not bad, f"地支五行分叉：{bad}"


def test_no_divergent_tiangan_wuxing():
    bad = []
    for path in _all_py():
        for d in _iter_dict_literals(path):
            keys = set(d.keys())
            if keys == GAN and set(d.values()) <= set("木火土金水"):
                if d != TIANGAN_WUXING:
                    bad.append((path, d))
    assert not bad, f"天干五行分叉：{bad}"


def test_no_divergent_liuchong():
    """完整的「12地支六冲」本地 dict 必须等于 LIUCHONG。"""
    bad = []
    for path in _all_py():
        for d in _iter_dict_literals(path):
            keys = set(d.keys())
            if keys == ZHI and set(d.values()) == ZHI:
                # 是冲（子↔午）还是合（子↔丑）？冲：子→午
                if d.get("子") == "午" and d != LIUCHONG:
                    bad.append((path, "冲", d))
                elif d.get("子") == "丑" and d != LIUHE:
                    bad.append((path, "合", d))
    assert not bad, f"地支冲/合分叉：{bad}"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q", "-v"]))
