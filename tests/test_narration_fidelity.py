"""行文层·忠实度护栏测试 —— firm boundary：AI 只转写、不新增判断。
护栏不依赖 LLM，可独立测试，是该边界的强制执行点（fail-closed）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.narration import (build_lexicon, extract_fact_blob, verify_fidelity,
                            narrate, build_narration_prompt)


def _ms(module="bazi"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    if module == "bazi":
        r = c.post("/api/v1/bazi/chart", json={"year": 1990, "month": 6, "day": 15,
                   "hour": 10, "gender": "male", "is_lunar": False})
    elif module == "liuyao":
        r = c.post("/api/v1/liuyao/divine", json={"method": "manual",
                   "yao_values": [7, 9, 8, 7, 8, 6], "gender": "male",
                   "topic": "求财", "query_time": "2026-05-10T10:00:00"})
    elif module == "xuankong":
        r = c.post("/api/v1/fengshui/xuankong", json={"sitting_mountain": "子", "year": 2010})
    return r.json()["data"]["master_synthesis"]


_LEX = build_lexicon()


def test_lexicon_covers_categories():
    """术语表含星曜/神煞/十神/六亲/奇门等判断性实体。"""
    for t in ("紫微", "白虎", "正官", "用神", "天蓬", "七杀"):
        assert t in _LEX, t
    assert len(_LEX) >= 100


def test_facts_are_faithful_to_themselves():
    """自洽铁律：引擎事实对自身必 clean（否则护栏会冤枉忠实转写）。"""
    for mod in ("bazi", "liuyao", "xuankong"):
        ms = _ms(mod)
        fid = verify_fidelity(ms, extract_fact_blob(ms), lexicon=_LEX)
        assert fid["clean"], (mod, fid["violations"][:3])


def test_hallucinated_entity_caught():
    """AI 引入事实中没有的星曜 → 判违规。"""
    ms = _ms("bazi")
    prose = extract_fact_blob(ms)[:120] + "又见紫微化禄、天魁天钺夹命、廉贞七杀会照。"
    fid = verify_fidelity(ms, prose, lexicon=_LEX)
    assert not fid["clean"]
    terms = {v["term"] for v in fid["violations"] if v["type"] == "hallucinated_entity"}
    # 这些星曜确不在八字事实中
    assert terms & {"紫微", "廉贞", "七杀", "天魁", "天钺"}


def test_quality_flip_caught():
    """AI 把引擎判凶之域写成大吉 → 判违规。"""
    ms = _ms("bazi")
    dom = next((dv["domain"] for dv in ms["dimension_verdicts"]
                if dv.get("quality") == "凶"), None)
    if not dom:
        return  # 该盘无凶域则跳过
    fid = verify_fidelity(ms, f"{dom}大吉昌隆，万事亨通。", lexicon=_LEX)
    assert not fid["clean"]
    assert any(v["type"] == "quality_flip" for v in fid["violations"])


def test_narrate_fail_closed_on_bad_llm():
    """越界 LLM → fail-closed：丢弃 AI 文本，退回确定性拼接。"""
    ms = _ms("bazi")
    bad = lambda p: "紫微天府坐命，化权化禄，贵不可言，富甲一方。"
    res = narrate(ms, llm_call=bad, lexicon=_LEX)
    assert res["source"] == "fallback_fidelity"
    assert not res["fidelity"]["clean"]
    assert "贵不可言" not in res["prose"]          # 被拒文本未泄入正式输出
    assert res.get("rejected_prose")               # 但留档以供审计


def test_narrate_passes_faithful_llm():
    """忠实 LLM（仅用事实词）→ source=ai。"""
    ms = _ms("bazi")
    good = lambda p: extract_fact_blob(ms)
    res = narrate(ms, llm_call=good, lexicon=_LEX)
    assert res["source"] == "ai" and res["fidelity"]["clean"]


def test_narrate_no_llm_deterministic():
    """无 LLM → 确定性拼接（纯引擎事实，无 AI 生成）。"""
    ms = _ms("bazi")
    res = narrate(ms, llm_call=None, lexicon=_LEX)
    assert res["source"] == "fallback_no_llm"
    assert res["prose"]
    # 退路文本中不得含事实外的判断性实体
    fid = verify_fidelity(ms, res["prose"], lexicon=_LEX)
    assert fid["clean"]


def test_prompt_states_boundary():
    """提示须明示下游边界（不新增判断）。"""
    ms = _ms("bazi")
    p = build_narration_prompt(ms)
    assert "不可新增任何判断" in p and "不是「判断」的作者" in p


def test_api_endpoints():
    """synthesize / verify 端点连通。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    ms = _ms("bazi")
    r = c.post("/api/v1/narration/synthesize", json={"master_synthesis": ms}).json()
    assert r["success"] and r["data"]["prose"]
    v = c.post("/api/v1/narration/verify",
               json={"master_synthesis": ms, "prose": "廉贞七杀坐命。"}).json()
    assert not v["data"]["clean"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))


def test_styles_distinct_prompts():
    """三档文风产出不同的提示指令，但事实部分一致。"""
    ms = _ms("bazi")
    ps = {s: build_narration_prompt(ms, style=s) for s in ("白话", "半文", "文言")}
    # 文风指令各异
    assert ps["白话"] != ps["半文"] != ps["文言"]
    assert "白话" in ps["白话"] and "文言" in ps["文言"]
    # 事实（总评）三档一致
    for s in ("白话", "半文", "文言"):
        assert ms["headline"] in ps[s]


def test_guard_applies_to_all_styles():
    """护栏对三档一视同仁：幻觉文在任一文风下都被 fail-closed。"""
    ms = _ms("bazi")
    bad = lambda p: "紫微化禄坐命，廉贞七杀，富贵不可言。"
    for s in ("白话", "半文", "文言"):
        res = narrate(ms, llm_call=bad, lexicon=_LEX, style=s)
        assert res["source"] == "fallback_fidelity" and res["style"] == s


def test_invalid_style_falls_to_default():
    """非法文风回落默认。"""
    ms = _ms("bazi")
    res = narrate(ms, llm_call=None, lexicon=_LEX, style="火星文")
    assert res["style"] == "半文"


def test_collect_facts_aggregates():
    """整盘综合：collect_facts 汇聚多面板事实（段落数增多），仍对自身忠实。"""
    from fastapi.testclient import TestClient
    from main import app
    from core.narration import collect_facts
    c = TestClient(app)
    data = c.post("/api/v1/bazi/chart", json={"year": 1990, "month": 6, "day": 15,
                  "hour": 10, "gender": "male", "is_lunar": False}).json()["data"]
    single = data["master_synthesis"]
    full = collect_facts(data, "bazi")
    assert full.get("_aggregated")
    assert len(full["integrated_paragraphs"]) >= len(single.get("integrated_paragraphs", []))
    # 汇聚后对自身忠实（护栏不冤枉引擎事实）
    assert verify_fidelity(full, extract_fact_blob(full), lexicon=_LEX)["clean"]


def test_collect_facts_guard_still_catches():
    """整盘汇聚后，护栏仍拦截幻觉。"""
    from fastapi.testclient import TestClient
    from main import app
    from core.narration import collect_facts
    c = TestClient(app)
    data = c.post("/api/v1/bazi/chart", json={"year": 1990, "month": 6, "day": 15,
                  "hour": 10, "gender": "male", "is_lunar": False}).json()["data"]
    full = collect_facts(data, "bazi")
    res = narrate(full, llm_call=lambda p: "紫微化禄、太岁冲命、廉贞化忌。", lexicon=_LEX)
    assert res["source"] == "fallback_fidelity"


def test_synthesize_full_endpoint():
    """整盘行文端点连通（多模块）。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    data = c.post("/api/v1/fengshui/xuankong",
                  json={"sitting_mountain": "子", "year": 2010}).json()["data"]
    r = c.post("/api/v1/narration/synthesize_full",
               json={"chart_data": data, "module": "xuankong"}).json()
    assert r["success"] and r["data"]["prose"]
    assert r["data"]["aggregated_paragraphs"] >= 1


def test_guard_metrics_quality():
    """护栏量化：忠实零误报、对抗高拦截（回归监控阈值）。"""
    from fastapi.testclient import TestClient
    from main import app
    from core.narration import guard_metrics
    c = TestClient(app)
    ms_list = []
    for y in (1985, 1990, 1995, 2000):
        ms_list.append(c.post("/api/v1/bazi/chart", json={"year": y, "month": 6,
                       "day": 15, "hour": 10, "gender": "male",
                       "is_lunar": False}).json()["data"]["master_synthesis"])
    for s in ("子", "午", "卯"):
        ms_list.append(c.post("/api/v1/fengshui/xuankong",
                       json={"sitting_mountain": s, "year": 2010}).json()["data"]["master_synthesis"])
    m = guard_metrics(ms_list, lexicon=_LEX)
    assert m["faithful_pass_rate"] == 1.0, m            # 零误报
    assert m["interception_rate"] >= 0.95, m            # 高拦截
    assert m["adversarial_total"] >= 7


def test_ganzhi_fidelity():
    """干支保真：捏造事实外的干支 → 拦截；事实中的干支不冤枉。"""
    from core.narration.narrator import _GANZHI60
    ms = _ms("bazi")
    blob = extract_fact_blob(ms)
    fake = next(g for g in _GANZHI60 if g not in blob)
    fid = verify_fidelity(ms, f"此命{fake}年生。", lexicon=_LEX)
    assert not fid["clean"]
    assert any(v["type"] == "hallucinated_ganzhi" and v["term"] == fake for v in fid["violations"])
    # 事实自身的干支不被冤枉
    assert verify_fidelity(ms, blob, lexicon=_LEX)["clean"]


def test_year_fidelity():
    """年份保真：捏造事实外的四位年份 → 拦截。"""
    ms = _ms("bazi")
    fid = verify_fidelity(ms, "至2071年大运转吉。", lexicon=_LEX)
    assert not fid["clean"]
    assert any(v["type"] == "hallucinated_number" and v["term"] == "2071" for v in fid["violations"])


def test_metrics_cover_four_kinds():
    """量化指标覆盖 4 类对抗，全高拦截。"""
    from core.narration import guard_metrics
    ms_list = [_ms("bazi"), _ms("xuankong"), _ms("liuyao")]
    m = guard_metrics(ms_list, lexicon=_LEX)
    for k in ("hallucinated_entity", "quality_flip", "hallucinated_ganzhi", "hallucinated_number"):
        assert k in m["by_kind"] and m["by_kind"][k]["rate"] == 1.0, (k, m["by_kind"])
    assert m["faithful_pass_rate"] == 1.0


def test_collect_facts_multi():
    """多盘合参：汇聚八字+紫微，按盘标注，自洽 clean，仍拦幻觉。"""
    from fastapi.testclient import TestClient
    from main import app
    from core.narration import collect_facts_multi
    c = TestClient(app)
    bazi = c.post("/api/v1/bazi/chart", json={"year": 1990, "month": 6, "day": 15,
                  "hour": 10, "gender": "male", "is_lunar": False}).json()["data"]
    ziwei = c.post("/api/v1/ziwei/chart", json={"year": 1990, "month": 6, "day": 15,
                   "hour": 10, "gender": "男", "is_lunar": False}).json()["data"]
    merged = collect_facts_multi([(bazi, "bazi"), (ziwei, "ziwei")])
    assert merged.get("_multi")
    doms = [dv["domain"] for dv in merged["dimension_verdicts"]]
    assert any(d.startswith("八字·") for d in doms) and any(d.startswith("紫微·") for d in doms)
    assert verify_fidelity(merged, extract_fact_blob(merged), lexicon=_LEX)["clean"]
    res = narrate(merged, llm_call=lambda p: "又见甲子年生、化忌冲命、天罡会照。", lexicon=_LEX)
    assert res["source"] == "fallback_fidelity"


def test_synthesize_multi_endpoint():
    """多盘合参端点连通。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    bazi = c.post("/api/v1/bazi/chart", json={"year": 1990, "month": 6, "day": 15,
                  "hour": 10, "gender": "male", "is_lunar": False}).json()["data"]
    ziwei = c.post("/api/v1/ziwei/chart", json={"year": 1990, "month": 6, "day": 15,
                   "hour": 10, "gender": "男", "is_lunar": False}).json()["data"]
    r = c.post("/api/v1/narration/synthesize_multi", json={"charts": [
        {"chart_data": bazi, "module": "bazi"},
        {"chart_data": ziwei, "module": "ziwei"}]}).json()
    assert r["success"] and r["data"]["prose"]
    assert r["data"]["charts"] == ["bazi", "ziwei"]


def test_export_document_structure():
    """导出存档：三段结构 + 区分引擎判断/AI行文 + 凭据边界声明。"""
    from core.narration import build_export_document
    ms = _ms("bazi")
    doc = build_export_document(ms, {"文言": "命主辛金，格局上佳。", "白话": "你是辛金日主。"},
                                scope_label="整盘综合", fidelity_note="全部风格均通过忠实度护栏。")
    assert "一、引擎判断" in doc and "二、行文" in doc and "三、凭据" in doc
    assert "不新增、不篡改任何判断" in doc
    assert "文言" in doc and "白话" in doc
    assert ms["headline"] in doc


def test_export_endpoint():
    """导出端点：整盘 + 全部三档，返回 markdown + 各风格凭据。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    data = c.post("/api/v1/bazi/chart", json={"year": 1990, "month": 6, "day": 15,
                  "hour": 10, "gender": "male", "is_lunar": False}).json()["data"]
    r = c.post("/api/v1/narration/export", json={"chart_data": data, "module": "bazi"}).json()
    assert r["success"]
    assert set(r["data"]["parts"].keys()) == {"白话", "半文", "文言"}
    assert r["data"]["filename"].endswith(".md")
    assert "## 三、凭据" in r["data"]["document"]


def test_metrics_catch_degraded_guard():
    """自检的自检：CI 阈值须能拦住退化的护栏（伪护栏漏判 → 拦截率掉 → CI 失败）。

    证明 guard_metrics + CI 阈值不是「静默通过」——确实能识别护栏退化。
    """
    from core.narration import guard_metrics
    ms_list = [_ms("bazi"), _ms("xuankong"), _ms("liuyao")]

    def ci_pass(m):
        return m["faithful_pass_rate"] == 1.0 and m["interception_rate"] >= 0.98

    # ① 真护栏 → CI 通过
    real = guard_metrics(ms_list, _LEX)
    assert ci_pass(real), real

    # ② 伪护栏「永远放行」→ 拦截率 0 → CI 拦下
    fake_pass = lambda ms, prose, lexicon=None: {"clean": True, "violations": []}
    m1 = guard_metrics(ms_list, _LEX, verify_fn=fake_pass)
    assert m1["interception_rate"] == 0.0
    assert not ci_pass(m1)

    # ③ 退化护栏「只抓判断实体、丢干支/年份/质性」→ 部分类型漏判 → CI 拦下
    def entity_only(ms, prose, lexicon=None):
        blob = extract_fact_blob(ms)
        viols = [t for t in (lexicon or set()) if t in prose and t not in blob]
        return {"clean": not viols, "violations": [{"type": "e", "term": t} for t in viols]}
    m2 = guard_metrics(ms_list, _LEX, verify_fn=entity_only)
    assert m2["by_kind"]["hallucinated_ganzhi"]["rate"] == 0.0
    assert m2["by_kind"]["hallucinated_number"]["rate"] == 0.0
    assert not ci_pass(m2)
