"""护栏量化回归（pytest marker: regression）。

复用 scripts/narration_metrics.py 的语料构建器，断言护栏未退化：
  · 忠实通过率 == 1.0（零误报）
  · 拦截率 >= 0.98（4 类对抗：判断实体 / 吉凶翻转 / 干支 / 年份）

CI 通过 `pytest -m regression` 或 `make regression` 触发；
本地快速迭代可 `pytest -m "not regression"` 跳过。
"""
import os
import sys

import pytest

# 让 scripts/ 可导入
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

MIN_INTERCEPTION = 0.98


@pytest.mark.regression
def test_guard_not_degraded():
    from narration_metrics import build_corpus
    from core.narration import guard_metrics

    corpus = build_corpus()
    m = guard_metrics(corpus)

    assert m["samples"] >= 30, f"语料过小：{m['samples']}"
    assert m["faithful_pass_rate"] == 1.0, \
        f"出现误报，忠实通过率 {m['faithful_pass_rate']}（护栏冤枉了忠实转写）"
    assert m["interception_rate"] >= MIN_INTERCEPTION, \
        f"拦截率 {m['interception_rate']} < {MIN_INTERCEPTION}（护栏漏判增多）"
    # 四类对抗逐一达标
    for kind, v in m["by_kind"].items():
        if v["rate"] is not None:
            assert v["rate"] >= MIN_INTERCEPTION, \
                f"[{kind}] 拦截率 {v['rate']} < {MIN_INTERCEPTION}"
