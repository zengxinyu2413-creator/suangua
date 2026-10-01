"""
test_hermes_contract_liuyao_l1.py
==================================
Consumer-driven contract test for the Hermes (crypto trading system,
github: hermes_ai / hermes_ai_2dc1c864) integration with this project's
LiuYao (六爻) divination output.

Purpose — NOT correctness, SHAPE STABILITY:
  Hermes's planned integration reads specific field paths out of the API
  response produced by POST /liuyao/divine (core.liuyao.interpreter.interpret,
  wired in api/liuyao.py). This file does not re-verify divination logic
  (see test_liuyao_relations.py for that) — it locks down that those field
  paths keep existing with the expected types, so a future refactor here
  fails LOUDLY in this suite instead of silently breaking Hermes's parser.

  Field paths under contract (from the Hermes-side task spec):
    result["deep_relations"]["line_details"][i]:
        is_yuepo (bool), is_ripo (bool), month_chs (dict), day_chs (dict),
        combined_force (number), overall (str)
    result["yaos"][i]:
        liu_shen (str, one of the Six Spirits)  —— "六神" assignment
    result["hua_bian"]["moving_lines"][i]:
        orig_branch/changed_branch/facets/tendency/score/full_text/...

  Run standalone, separate from the daily divination workflow:
    cd suangua && source venv/bin/activate && pytest tests/test_hermes_contract_liuyao_l1.py -v

KNOWN RISK — reported, not fixed (out of scope for this test file):
  core/liuyao/interpreter.py wraps the calls that produce deep_relations,
  hua_bian, and chi_shi each in a bare `try/except Exception:
  log_failure(...)` with NO re-raise. If any of those three enrichment
  steps throws (e.g. because a future change to this repo breaks the
  contract asserted here), interpret() does NOT fail the request — it
  silently omits that key from the response and only writes to
  core/log.py's failure log. A consumer that does not defensively check
  for the key's presence (e.g. `result.get("deep_relations")`) will not
  get a clear upstream error; it will either KeyError deep in its own
  parser or, if it also uses `.get()` chains, silently proceed with
  incomplete data. This test file cannot make that failure mode "loud"
  from the outside — it only proves the contract holds *today*, given
  the current code. Whether to remove that swallow-and-continue pattern
  is a separate decision for this repo's maintainer, not something this
  contract test changes.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.divination import manual_divination
from core.liuyao.najia import annotate_with_najia
from core.liuyao.interpreter import interpret
from core.liuyao.relations import analyze_liuyao_deep_relations
from core.liuyao.hua_bian import analyze_hua_bian

# Six Spirits — 六神, the closed set liu_shen must be drawn from
# (core/liuyao/najia.py::assign_liu_shen).
SIX_SPIRITS = {"青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"}

# overall's closed set (core/liuyao/relations.py::analyze_line_strength_detail)
OVERALL_LABELS = {"极旺", "旺相", "中和", "休囚", "无气"}


def _run_full_pipeline(yao_values, month_zhi="子", day_zhi="子", day_gan="甲"):
    """Reproduces exactly what api/liuyao.py's /divine endpoint does,
    minus the FastAPI/pydantic request-parsing layer, so this test does
    not depend on constructing a DivinationRequest.
    """
    result = manual_divination(yao_values)
    hex_num = result["original"]["number"]
    lower_name = result["original"]["lower"]["name"]
    upper_name = result["original"]["upper"]["name"]
    annotate_with_najia(result, hex_num, lower_name, upper_name, day_gan, 10, month_zhi)
    result["month_zhi"] = month_zhi
    result["day_zhi"] = day_zhi
    result["day_gan"] = day_gan
    result["divine_date"] = "2026-09-22T10:00:00"
    return interpret(result, "事业顺利吗", gender="male", is_proxy=False, explicit_topic=None)


# ---------------------------------------------------------------------------
# End-to-end: the real interpret() pipeline, as Hermes will actually receive it
# ---------------------------------------------------------------------------


def test_end_to_end_response_has_deep_relations_and_hua_bian_keys():
    """A yao_values combo with at least one changing line (老阳=9/老阴=6) so
    both deep_relations.line_details and hua_bian.moving_lines are non-empty
    — an all-static hexagram would trivially pass a "key exists" check
    without ever exercising the per-line contract.
    """
    out = _run_full_pipeline([9, 8, 7, 6, 9, 8])
    assert "deep_relations" in out, (
        "result['deep_relations'] missing — either interpret() no longer "
        "attaches it, or the enrichment step raised and was swallowed by "
        "the bare try/except in interpreter.py (see module docstring)"
    )
    assert "hua_bian" in out
    assert "yaos" in out


def test_deep_relations_line_details_contract():
    out = _run_full_pipeline([9, 8, 7, 6, 9, 8])
    dr = out["deep_relations"]
    assert isinstance(dr, dict)
    for key in ("yong_yuan_ji_chou", "key_lines", "changing_relations", "line_details", "summary"):
        assert key in dr, f"deep_relations missing top-level key {key!r}"

    line_details = dr["line_details"]
    assert isinstance(line_details, list)
    assert len(line_details) == 6, (
        "expected one line_details entry per yao (month_zhi/day_zhi were "
        "supplied to interpret(), which is what populates this list)"
    )

    for i, detail in enumerate(line_details):
        for key in (
            "branch", "wuxing", "month_chs", "day_chs",
            "is_yuepo", "is_ripo", "combined_force", "overall", "liu_qin",
        ):
            assert key in detail, f"line_details[{i}] missing {key!r}: {detail!r}"

        assert isinstance(detail["is_yuepo"], bool), f"line_details[{i}]['is_yuepo'] not bool"
        assert isinstance(detail["is_ripo"], bool), f"line_details[{i}]['is_ripo'] not bool"
        assert isinstance(detail["month_chs"], dict), f"line_details[{i}]['month_chs'] not dict"
        assert isinstance(detail["day_chs"], dict), f"line_details[{i}]['day_chs'] not dict"
        assert "status" in detail["month_chs"] and "force" in detail["month_chs"]
        assert "status" in detail["day_chs"] and "force" in detail["day_chs"]
        assert isinstance(detail["combined_force"], (int, float)), (
            f"line_details[{i}]['combined_force'] not numeric: {detail['combined_force']!r}"
        )
        assert detail["overall"] in OVERALL_LABELS, (
            f"line_details[{i}]['overall']={detail['overall']!r} not in known set {OVERALL_LABELS}"
        )


def test_yaos_liu_shen_six_spirits_contract():
    out = _run_full_pipeline([9, 8, 7, 6, 9, 8])
    yaos = out["yaos"]
    assert isinstance(yaos, list) and len(yaos) == 6
    seen = set()
    for i, yao in enumerate(yaos):
        assert "liu_shen" in yao, f"yaos[{i}] missing 'liu_shen' (六神)"
        assert yao["liu_shen"] in SIX_SPIRITS, (
            f"yaos[{i}]['liu_shen']={yao['liu_shen']!r} not one of {SIX_SPIRITS}"
        )
        assert "liu_shen_meaning" in yao and isinstance(yao["liu_shen_meaning"], dict)
        seen.add(yao["liu_shen"])
    # Six Spirits are assigned as a fixed rotation starting from day_stem —
    # all 6 lines together must show all 6 distinct spirits, never fewer.
    assert seen == SIX_SPIRITS, f"expected all six spirits assigned across 6 lines, got {seen}"


def test_hua_bian_moving_lines_contract():
    # yao_values chosen so positions 1/4/5 are changing (老阳=9 or 老阴=6)
    out = _run_full_pipeline([9, 8, 7, 6, 9, 8])
    hb = out["hua_bian"]
    assert isinstance(hb, dict)
    for key in ("success", "count", "moving_lines", "summary"):
        assert key in hb, f"hua_bian missing top-level key {key!r}"

    assert hb["count"] == 3, "yao_values [9,8,7,6,9,8] should produce 3 changing lines"
    assert len(hb["moving_lines"]) == 3

    for i, line in enumerate(hb["moving_lines"]):
        for key in (
            "orig_branch", "orig_wuxing", "orig_liu_qin",
            "changed_branch", "changed_wuxing", "changed_liu_qin",
            "facets", "tendency", "score", "full_text", "position", "name",
        ):
            assert key in line, f"hua_bian.moving_lines[{i}] missing {key!r}: {line!r}"
        assert isinstance(line["score"], (int, float))


def test_all_static_hexagram_hua_bian_is_empty_not_missing():
    """No changing lines (all 少阳/少阴) -- hua_bian must still be present
    with count=0 and an empty moving_lines list, not absent from the result.
    A consumer checking `"hua_bian" in result` should always find it.
    """
    out = _run_full_pipeline([7, 8, 7, 8, 7, 8])
    assert "hua_bian" in out
    hb = out["hua_bian"]
    assert hb["count"] == 0
    assert hb["moving_lines"] == []


# ---------------------------------------------------------------------------
# Narrower, function-level checks -- faster to run in isolation when the
# end-to-end tests above fail, to localize which layer broke the contract.
# ---------------------------------------------------------------------------


def test_analyze_liuyao_deep_relations_direct_contract():
    yaos = [
        {"branch": "卯", "liu_qin": "父母", "is_changing": False},
        {"branch": "巳", "liu_qin": "兄弟", "is_changing": False},
        {"branch": "未", "liu_qin": "子孙", "is_changing": True},
        {"branch": "酉", "liu_qin": "妻财", "is_changing": False},
        {"branch": "亥", "liu_qin": "官鬼", "is_changing": False},
        {"branch": "丑", "liu_qin": "子孙", "is_changing": False},
    ]
    result = analyze_liuyao_deep_relations(
        yaos, yong_shen_info={"liuqin": "妻财"}, month_zhi="巳", day_zhi="申",
    )
    assert isinstance(result["line_details"], list) and len(result["line_details"]) == 6
    for detail in result["line_details"]:
        assert {"is_yuepo", "is_ripo", "month_chs", "day_chs", "combined_force", "overall"} <= detail.keys()


def test_analyze_hua_bian_direct_contract():
    yaos = [
        {"branch": "寅", "liu_qin": "妻财", "is_changing": True,
         "changed_branch": "酉", "changed_liu_qin": "官鬼", "position": 1},
    ]
    result = analyze_hua_bian(yaos, kong_wang=[], topic="", gender="male")
    assert result["count"] == 1
    line = result["moving_lines"][0]
    assert {"orig_branch", "changed_branch", "facets", "tendency", "score", "full_text"} <= line.keys()
