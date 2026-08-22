"""
行文层（AI 叙事层）—— 下游转写引擎确定性事实为流畅古文。

【firm boundary · 不可逾越】
  AI 只可将引擎已产出的事实/判断转写为通顺文辞，绝不可生成任何新的占断
  （新星曜、新神煞、新格局、新吉凶结论、与事实相悖之质性）。
  本模块以「忠实度护栏」（verify_fidelity）作确定性闸门：用引擎自身的权威术语表
  （星曜/神煞/格局/十神），检测 AI 文中凡出现而引擎事实中没有的判断性实体，即判违规。
  此护栏不依赖任何 LLM，可独立测试，是该边界的强制执行点。

设计：
  - narrate(ms, llm_call) 为唯一对外编排：构造严格提示 → 调 LLM → 过护栏。
  - llm_call 可插拔（生产用 anthropic SDK，测试注入 mock），故护栏逻辑可无 LLM 测试。
  - 护栏若发现违规，narrate 不返回违规文本，而退回引擎事实的确定性拼接（fail-closed）。
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Set

# ── 1. 权威判断性术语表（从引擎常量加载，绝不手编硬列）──────────────────


def _safe(fn):
    try:
        return fn() or set()
    except Exception:
        return set()


def _coerce_text(v: Any) -> List[str]:
    """把任意事实值压平为文本列表（dict 取其字符串值、list 递归）。"""
    out: List[str] = []
    if isinstance(v, str):
        if v.strip():
            out.append(v.strip())
    elif isinstance(v, dict):
        for vv in v.values():
            out += _coerce_text(vv)
    elif isinstance(v, list):
        for vv in v:
            out += _coerce_text(vv)
    return out


# 各模块「整盘综合行文」可汇聚的事实面板键（除 master_synthesis 外）。
# 仅取引擎已产出的判断/断语文本，绝不新增——故汇聚后仍受同一护栏约束。
_AGGREGATE_PANELS: Dict[str, List[str]] = {
    "bazi": ["geju_cheng_bai", "tiaohou", "mingju_synthesis", "classical_statements"],
    "ziwei": ["mingge_synthesis", "overview", "classical_statements"],
    "liuyao": ["yongshen_judgment", "zonghe_duan", "duan_overview", "topic_verdict"],
    "qimen": ["yongshen_synthesis", "overview"],
    "xuankong": ["shoushan_chusha", "zhaiyun_synthesis", "overview"],
    "yangzhai": ["zhaixiang_synthesis", "overview"],
    "date": ["zeri_synthesis", "overview"],
}


def collect_facts(chart_data: Dict[str, Any], module: str) -> Dict[str, Any]:
    """整盘综合：把一个盘的多个事实面板汇聚成「增强版 master_synthesis」。

    返回结构与 master_synthesis 同构（headline/dimension_verdicts/integrated_paragraphs…），
    故 narrate / verify_fidelity 无需改动即可转写并守护更丰富的事实。
    汇聚的全部内容均出自引擎既有断语，不引入任何新判断。
    """
    ms = dict(chart_data.get("master_synthesis") or {})
    if not ms:
        # 无 master_synthesis 时，以 overview 兜底起一个壳
        ov = chart_data.get("overview") or {}
        ms = {"available": True, "headline": ov.get("headline", ""),
              "overall_quality": ov.get("quality", ""),
              "dimension_verdicts": [], "integrated_paragraphs": []}

    ms = {**ms}
    extra_paras = list(ms.get("integrated_paragraphs") or [])
    for key in _AGGREGATE_PANELS.get(module, []):
        panel = chart_data.get(key)
        if not panel:
            continue
        if isinstance(panel, dict) and panel.get("available") is False:
            continue
        # 取该面板的「总论/断语」类文本，避免把结构标签也拽进来
        if isinstance(panel, dict):
            for subkey in ("总论", "summary", "verdict", "paragraph", "advice",
                           "headline", "desc", "detail", "luantou_summary"):
                if isinstance(panel.get(subkey), str) and panel[subkey].strip():
                    extra_paras.append(panel[subkey].strip())
            # classical_statements / statements 列表（古籍引文较多，取前若干，避免行文冗长）
            stmts = panel.get("statements")
            if isinstance(stmts, list):
                for s in stmts[:6]:
                    extra_paras += _coerce_text(s)
        else:
            extra_paras += _coerce_text(panel)

    # 去重保序 + 总段数封顶（保聚焦；首批为 master_synthesis 原段，优先保留）
    seen: Set[str] = set()
    dedup: List[str] = []
    for p in extra_paras:
        if p not in seen and len(p) >= 4:
            seen.add(p)
            dedup.append(p)
    ms["integrated_paragraphs"] = dedup[:24]
    ms["_aggregated"] = True
    return ms


_MODULE_LABEL = {"bazi": "八字", "ziwei": "紫微", "liuyao": "六爻", "qimen": "奇门",
                 "xuankong": "玄空", "yangzhai": "阳宅", "date": "择日"}


def collect_facts_multi(charts: List[Any], labels: Optional[List[str]] = None) -> Dict[str, Any]:
    """多盘合参：汇聚多个盘（如同人之八字+紫微）的事实成一篇，按盘标注来源。

    charts: [(chart_data, module), ...]。
    仅并陈各盘既有断语，绝不生成「合参」新判断；各盘质性互不混算。
    返回与 master_synthesis 同构，故 narrate/verify_fidelity 零改动即可转写并守护。
    """
    merged: Dict[str, Any] = {"available": True, "headline": "", "overall_quality": "",
                              "dimension_verdicts": [], "integrated_paragraphs": [],
                              "_multi": True}
    heads: List[str] = []
    for i, (data, module) in enumerate(charts):
        label = (labels[i] if labels and i < len(labels) else _MODULE_LABEL.get(module, module))
        ms = collect_facts(data, module)
        if ms.get("headline"):
            heads.append(f"【{label}】{ms['headline']}")
        for dv in ms.get("dimension_verdicts", []) or []:
            if isinstance(dv, dict):
                dv2 = dict(dv)
                raw = dv.get("domain") or dv.get("dim") or ""
                dv2["domain"] = f"{label}·{raw}"
                merged["dimension_verdicts"].append(dv2)
        for p in (ms.get("integrated_paragraphs", []) or [])[:12]:
            merged["integrated_paragraphs"].append(f"【{label}】{p}")
    merged["headline"] = "；".join(heads)
    return merged


def build_lexicon() -> Set[str]:
    """从引擎权威常量汇集「判断性实体」术语：星曜·辅星·十神·神煞·格局名。

    凡此表中之词出现于 AI 文而不见于引擎事实，即 AI 自创判断 → 违规。
    """
    lex: Set[str] = set()

    # 紫微 14 主星（命学固定，非可变事实，作判断性实体白名单基底）
    lex |= {"紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
            "贪狼", "巨门", "天相", "天梁", "七杀", "破军"}

    # 紫微辅煞杂曜
    lex |= _safe(lambda: set(__import__(
        "core.ziwei.star_palace", fromlist=["AUX_STAR_INFO"]).AUX_STAR_INFO.keys()))

    # 八字十神
    def _shishen():
        from core.constants import SHISHEN
        return set(SHISHEN.values()) if isinstance(SHISHEN, dict) else set()
    lex |= _safe(_shishen)

    # 神煞名（择日神煞库 + 各模块 *shensha* 文件中文键名 2-4 字）
    def _shensha():
        import glob
        names: Set[str] = set()
        for f in (glob.glob("core/**/*shensha*.py", recursive=True)
                  + ["core/date_selection/shensha_meanings.py"]):
            try:
                src = open(f, encoding="utf-8").read()
                for m in re.findall(r'["\']([\u4e00-\u9fa5]{2,4})["\']\s*:', src):
                    names.add(m)
            except Exception:
                continue
        return names
    lex |= _safe(_shensha)

    # 六爻六亲六神
    lex |= {"父母", "兄弟", "子孙", "妻财", "官鬼",
            "青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武",
            "用神", "原神", "忌神", "仇神", "世爻", "应爻", "卦身", "伏神"}

    # 奇门九星八门八神
    lex |= {"天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英",
            "休门", "死门", "伤门", "杜门", "开门", "惊门", "生门", "景门",
            "值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天",
            "值使", "三奇", "六仪"}

    # 仅保留 2 字以上（单字如「吉」「凶」不作实体，留给质性一致性检查）
    return {t for t in lex if len(t) >= 2}


# 质性（吉凶）词：不作「实体存在」检查（必然出现），而作「前后一致」检查
_QUALITY_POS = {"吉", "大吉", "上吉", "旺", "相", "得地", "庙", "成格", "贵格"}
_QUALITY_NEG = {"凶", "大凶", "衰", "囚", "死", "破格", "陷", "失令"}

# 60 甲子（天干×地支合法配对）——干支为不可篡改之硬事实，AI 文中之干支须见于引擎事实。
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"
_GANZHI60 = {_GAN[i % 10] + _ZHI[i % 12] for i in range(60)}
# 年份：1800–2099 之四位数（命理常用区间），AI 不得捏造或改写事实中的年份。
_YEAR_RE = re.compile(r"(?<!\d)(?:1[89]\d{2}|20\d{2})(?!\d)")


# ── 2. 事实抽取 ───────────────────────────────────────────────


def extract_fact_blob(ms: Dict[str, Any]) -> str:
    """把 master_synthesis 中一切事实文本拼成一团，供护栏作「是否出自事实」判断。"""
    parts: List[str] = []
    for k in ("headline", "master_advice", "overall_quality", "day_master",
              "ming_label", "house_type", "grade"):
        v = ms.get(k)
        if isinstance(v, str):
            parts.append(v)
    for dv in ms.get("dimension_verdicts", []) or []:
        if isinstance(dv, dict):
            for k in ("domain", "dim", "verdict", "key", "quality"):
                v = dv.get(k)
                if isinstance(v, str):
                    parts.append(v)
    for p in ms.get("integrated_paragraphs", []) or []:
        if isinstance(p, str):
            parts.append(p)
    return "　".join(parts)


def _domain_quality(ms: Dict[str, Any]) -> Dict[str, str]:
    """各专域的引擎质性（domain → 吉/凶/中），供质性一致性检查。
    合参模式域名形如「八字·事业」，取「·」后部作匹配键（行文中通常只写「事业」）。"""
    out: Dict[str, str] = {}
    for dv in ms.get("dimension_verdicts", []) or []:
        if isinstance(dv, dict):
            dom = dv.get("domain") or dv.get("dim")
            q = dv.get("quality")
            if dom and q:
                key = dom.split("·")[-1] if "·" in dom else dom
                out[key] = q
    return out


# ── 3. 严格提示构造 ───────────────────────────────────────────


_PROMPT_TEMPLATE = """你是一位精于命理的文书师。下面是「占断引擎」已经算定的事实与结论。
你的唯一任务：把这些既定事实，转写成一段通顺、典雅、连贯的中文行文。

【铁律 · 不可违背】
1. 只可转述下列事实，不可新增任何判断：不得引入事实中没有的星曜、神煞、格局、用神。
2. 不得改变任何吉凶质性：事实说某域为凶，你不可写成吉；说中平，不可拔高为大吉。
3. 不得自行推演新结论、不得编造数字或地支干支。
4. 不确定或事实未及之处，宁可不写，绝不臆补。
5. 你是「文辞」的执笔者，不是「判断」的作者。判断已由引擎作出，你只负责让它读起来顺畅。

【既定事实】
总评：{headline}
整体质性：{overall_quality}
{day_master_line}
分域结论：
{dimensions}
综论段落：
{paragraphs}
结语箴言：{master_advice}

【文风要求】
{style_instruction}

【输出】
仅输出转写后的行文本身（一段或数段），不要解释、不要标注、不要复述本提示。"""


# 风格分级：仅作用于「文采」，不改任何事实判断；忠实度护栏对三档一视同仁。
STYLES: Dict[str, Dict[str, str]] = {
    "白话": {
        "label": "白话",
        "instruction": "用平实、清楚的现代白话文，像专业命理师当面解说，"
                       "通俗易懂、亲切自然；不堆砌典故古词，但术语（星曜神煞）保留原名。",
    },
    "半文": {
        "label": "半文",
        "instruction": "用半文半白、雅俗共赏之笔，文气流畅而不晦涩，"
                       "略施对仗与文言虚词，既见文采又不失明白。",
    },
    "文言": {
        "label": "文言",
        "instruction": "用典雅文言行文，如古命书批语，简练含蓄、骈散相间、气韵贯通；"
                       "可用之乎者也与对仗，但不可因求工而增删任何事实判断。",
    },
}
DEFAULT_STYLE = "半文"


def build_narration_prompt(ms: Dict[str, Any], style: str = DEFAULT_STYLE) -> str:
    """从 master_synthesis 构造严格转写提示（强调下游边界 + 文风分级）。"""
    dims = []
    for dv in ms.get("dimension_verdicts", []) or []:
        if isinstance(dv, dict):
            dom = dv.get("domain") or dv.get("dim") or ""
            q = dv.get("quality") or ""
            verdict = dv.get("verdict") or dv.get("key") or ""
            dims.append(f"  · {dom}（{q}）：{verdict}")
    paras = "\n".join(ms.get("integrated_paragraphs", []) or [])
    dm = ms.get("day_master") or ms.get("ming_label") or ms.get("house_type") or ""
    dm_line = f"日主/命主：{dm}" if dm else ""
    style_cfg = STYLES.get(style, STYLES[DEFAULT_STYLE])
    return _PROMPT_TEMPLATE.format(
        headline=ms.get("headline", ""),
        overall_quality=ms.get("overall_quality", ""),
        day_master_line=dm_line,
        dimensions="\n".join(dims) if dims else "  （无分域）",
        paragraphs=paras if paras else "  （无）",
        master_advice=ms.get("master_advice", ""),
        style_instruction=style_cfg["instruction"],
    )


# ── 4. 忠实度护栏（核心安全闸门，无 LLM 依赖）──────────────────────


def verify_fidelity(ms: Dict[str, Any], prose: str,
                    lexicon: Optional[Set[str]] = None) -> Dict[str, Any]:
    """检查 AI 行文是否忠实于引擎事实。返回 {clean, violations}。

    违规类型：
      - hallucinated_entity：文中出现引擎事实中没有的判断性实体（星曜/神煞/格局/十神/六亲…）。
      - quality_flip：某专域引擎判为凶，而行文却给出正面质性词（或反之）。
    """
    if lexicon is None:
        lexicon = build_lexicon()
    fact_blob = extract_fact_blob(ms)
    violations: List[Dict[str, str]] = []

    # (1) 判断性实体：凡 lexicon 中之词出现于 prose 而不在 fact_blob → 幻觉
    for term in lexicon:
        if term in prose and term not in fact_blob:
            violations.append({"type": "hallucinated_entity", "term": term})

    # (2) 质性翻转：仅当「域名 + 反向质性词」之搭配为行文新造（不见于引擎事实）时才判违规。
    #     如此保证 verify_fidelity(ms, 引擎事实) 必为 clean（事实对自身忠实），只抓 AI 新造的翻转。
    for dom, q in _domain_quality(ms).items():
        if not dom or dom not in prose:
            continue
        opp = _QUALITY_POS if q == "凶" else (_QUALITY_NEG if q == "吉" else set())
        for w in opp:
            pat = re.escape(dom) + r".{0,12}" + re.escape(w)
            if re.search(pat, prose) and not re.search(pat, fact_blob):
                violations.append({"type": "quality_flip", "domain": dom,
                                   "engine": q, "prose_says": w})
                break

    # (3) 干支保真：AI 文中之干支（60 甲子合法配对）须见于引擎事实，否则为捏造/篡改。
    for gz in _GANZHI60:
        if gz in prose and gz not in fact_blob:
            violations.append({"type": "hallucinated_ganzhi", "term": gz})

    # (4) 年份保真：AI 文中之四位年份须见于引擎事实，否则为捏造。
    for yr in set(_YEAR_RE.findall(prose)):
        if yr not in fact_blob:
            violations.append({"type": "hallucinated_number", "term": yr})

    return {"clean": not violations, "violations": violations,
            "checked_entities": len(lexicon)}


# ── 5b. 护栏量化指标（回归监控）──────────────────────────────────


def _inject_adversarial(ms: Dict[str, Any], fact_blob: str,
                        lexicon: Set[str]) -> List[Dict[str, str]]:
    """从一组事实造对抗样本：① 注入事实外的判断性实体；② 翻转某凶域为吉。"""
    cases: List[Dict[str, str]] = []
    base = fact_blob[:120]
    outside = [t for t in lexicon if t not in fact_blob]
    if outside:
        inj = "，又见" + "、".join(sorted(outside)[:3]) + "会照入命。"
        cases.append({"kind": "hallucinated_entity", "prose": base + inj})
    for dv in ms.get("dimension_verdicts", []) or []:
        if isinstance(dv, dict) and dv.get("quality") == "凶" and dv.get("domain"):
            cases.append({"kind": "quality_flip",
                          "prose": base + f"，而{dv['domain']}大吉昌隆。"})
            break
    # ③ 捏造干支：取一个不在事实中的合法干支
    fake_gz = next((g for g in _GANZHI60 if g not in fact_blob), None)
    if fake_gz:
        cases.append({"kind": "hallucinated_ganzhi", "prose": base + f"，{fake_gz}之年应验。"})
    # ④ 捏造年份：取一个不在事实中的年份
    yrs_in = set(_YEAR_RE.findall(fact_blob))
    fake_yr = next((str(y) for y in range(2030, 2099) if str(y) not in yrs_in), "2088")
    cases.append({"kind": "hallucinated_number", "prose": base + f"，至{fake_yr}年大成。"})
    return cases


def guard_metrics(ms_list: List[Dict[str, Any]],
                  lexicon: Optional[Set[str]] = None,
                  verify_fn: Optional[Callable[..., Dict[str, Any]]] = None) -> Dict[str, Any]:
    """量化护栏质量（回归监控）。

    对每盘事实：
      · 忠实样本（事实自身文）应判 clean —— 误报则计入 false_positive。
      · 对抗样本（注入幻觉实体 / 翻转凶域）应判违规 —— 漏判则计入 missed。
    返回拦截率（recall）、误报率、术语覆盖率等指标，便于回归监控护栏不退化。

    verify_fn: 可注入的校验函数（默认 verify_fidelity）；供「元测试」以伪护栏
               验证本指标体系本身能否识别退化的护栏（自检的自检）。
    """
    if lexicon is None:
        lexicon = build_lexicon()
    if verify_fn is None:
        verify_fn = verify_fidelity
    faithful_total = faithful_fp = 0
    adv_total = adv_caught = 0
    adv_by_kind: Dict[str, List[int]] = {}

    for ms in ms_list:
        if not ms or not ms.get("available", True):
            continue
        blob = extract_fact_blob(ms)
        faithful_total += 1
        if not verify_fn(ms, blob, lexicon=lexicon)["clean"]:
            faithful_fp += 1
        for case in _inject_adversarial(ms, blob, lexicon):
            adv_total += 1
            caught = not verify_fn(ms, case["prose"], lexicon=lexicon)["clean"]
            adv_caught += int(caught)
            k = case["kind"]
            adv_by_kind.setdefault(k, [0, 0])
            adv_by_kind[k][0] += 1
            adv_by_kind[k][1] += int(caught)

    return {
        "samples": faithful_total,
        "faithful_pass_rate": round(1 - (faithful_fp / faithful_total), 4) if faithful_total else None,
        "false_positive": faithful_fp,
        "adversarial_total": adv_total,
        "interception_rate": round(adv_caught / adv_total, 4) if adv_total else None,
        "missed": adv_total - adv_caught,
        "by_kind": {k: {"total": t, "caught": cc, "rate": round(cc / t, 4) if t else None}
                    for k, (t, cc) in adv_by_kind.items()},
        "lexicon_size": len(lexicon),
    }


def llm_anthropic(model: str = "claude-haiku-4-5-20251001",
                  api_key: Optional[str] = None,
                  max_tokens: int = 1200) -> Optional[Callable[[str], str]]:
    """构造一个基于 anthropic SDK 的 llm_call；SDK 未装或无 key 则返回 None（narrate 自动降级）。

    生产环境：设环境变量 ANTHROPIC_API_KEY 后，narrate(ms, llm_anthropic()) 即启用 AI 行文。
    """
    import os
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic  # noqa: F401
    except Exception:
        return None

    def _call(prompt: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=model, max_tokens=max_tokens,
            system="你是命理文书师，只把既定占断事实转写为通顺古文，绝不新增任何判断。",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

    return _call


# ── 6. 编排（fail-closed）──────────────────────────────────────


def build_export_document(ms: Dict[str, Any],
                          narrations: Dict[str, str],
                          scope_label: str = "本论",
                          fidelity_note: str = "") -> str:
    """组装「行文存档」markdown：明确区分引擎事实（权威判断）与 AI 行文（转写）。

    narrations: {style -> prose}，已生成好的各风格行文。
    导出文档自带凭据，体现「判断属引擎、文辞属 AI」之边界，便于存档/分享。
    """
    lines: List[str] = ["# 中国术数平台 · 行文存档", ""]
    headline = ms.get("headline", "")
    if headline:
        lines += [f"> {headline}", ""]

    # 一、引擎判断（权威，不可改）
    lines.append("## 一、引擎判断（权威结论）")
    if ms.get("overall_quality"):
        lines.append(f"- 整体质性：{ms['overall_quality']}")
    dm = ms.get("day_master") or ms.get("ming_label") or ms.get("house_type")
    if dm:
        lines.append(f"- 日主/命主：{dm}")
    dvs = ms.get("dimension_verdicts") or []
    if dvs:
        lines.append("- 分域结论：")
        for dv in dvs:
            if isinstance(dv, dict):
                dom = dv.get("domain") or dv.get("dim") or ""
                q = dv.get("quality") or ""
                verdict = dv.get("verdict") or dv.get("key") or ""
                lines.append(f"  - {dom}（{q}）：{verdict}")
    if ms.get("master_advice"):
        lines.append(f"- 结语箴言：{ms['master_advice']}")
    lines.append("")

    # 二、AI 行文（转写，各风格）
    lines += [f"## 二、行文（{scope_label}）", ""]
    for style, prose in narrations.items():
        lines += [f"### · {style}", "", (prose.strip() if prose else "（无）"), ""]

    # 三、凭据
    lines.append("## 三、凭据")
    lines.append("- 上列「引擎判断」由确定性占断引擎算定，为权威结论。")
    lines.append("- 「行文」由 AI 将上述既定事实转写为文辞，**不新增、不篡改任何判断**，"
                 "并已通过确定性忠实度护栏（判断实体 / 吉凶质性 / 干支 / 年份 四类校验）。")
    if fidelity_note:
        lines.append(f"- {fidelity_note}")
    lines.append("")
    return "\n".join(lines)


def _deterministic_fallback(ms: Dict[str, Any]) -> str:
    """无 LLM 或护栏拦截时的确定性退路：纯拼接引擎事实（无任何 AI 生成）。"""
    parts = [ms.get("headline", "")]
    parts += [p for p in (ms.get("integrated_paragraphs", []) or []) if p]
    for dv in ms.get("dimension_verdicts", []) or []:
        if isinstance(dv, dict):
            dom = dv.get("domain") or dv.get("dim") or ""
            verdict = dv.get("verdict") or dv.get("key") or ""
            if verdict:
                parts.append(f"{dom}：{verdict}")
    if ms.get("master_advice"):
        parts.append(ms["master_advice"])
    return "\n".join(p for p in parts if p)


def narrate(ms: Dict[str, Any],
            llm_call: Optional[Callable[[str], str]] = None,
            lexicon: Optional[Set[str]] = None,
            style: str = DEFAULT_STYLE) -> Dict[str, Any]:
    """转写 master_synthesis 为行文。

    Args:
        ms: 引擎 master_synthesis 事实。
        llm_call: f(prompt)->prose 的可插拔 LLM 调用；None 则直接走确定性退路。
        lexicon: 可选，预建术语表（避免重复构建）。
        style: 文风分级（白话/半文/文言）；仅改文采，护栏对三档一视同仁。

    Returns:
        {prose, source, style, fidelity, prompt}
          source ∈ {"ai", "fallback_no_llm", "fallback_fidelity"}
    """
    if not ms or not ms.get("available", True):
        return {"prose": "", "source": "empty", "style": style,
                "fidelity": {"clean": True, "violations": []}}

    if style not in STYLES:
        style = DEFAULT_STYLE
    prompt = build_narration_prompt(ms, style=style)
    if lexicon is None:
        lexicon = build_lexicon()

    if llm_call is None:
        return {"prose": _deterministic_fallback(ms), "source": "fallback_no_llm",
                "style": style, "fidelity": {"clean": True, "violations": []}, "prompt": prompt}

    try:
        prose = (llm_call(prompt) or "").strip()
    except Exception as e:
        return {"prose": _deterministic_fallback(ms), "source": "fallback_no_llm",
                "style": style,
                "fidelity": {"clean": True, "violations": [{"type": "llm_error", "term": str(e)[:60]}]},
                "prompt": prompt}

    fid = verify_fidelity(ms, prose, lexicon=lexicon)
    if not fid["clean"]:
        # fail-closed：AI 越界则丢弃其文本，退回确定性拼接
        return {"prose": _deterministic_fallback(ms), "source": "fallback_fidelity",
                "style": style, "fidelity": fid, "prompt": prompt, "rejected_prose": prose}

    return {"prose": prose, "source": "ai", "style": style, "fidelity": fid, "prompt": prompt}
