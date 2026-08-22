"""
core/contracts.py
=================
「件」契约 —— 把六件套/总汇的字段形状由「约定一致」升级为「构造一致」。

架构审查曾指出：七模块的 overview/master_synthesis 字段形状靠复制粘贴保持一致，
无基类或 Protocol 强制，随时可能漂移。今立此契约 + 校验器；conformance 测试
逐模块校验真实输出，任何漂移即失败——以测试代替基类，零重构而得构造级保证。
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple

_QUALITY = {"吉", "中", "凶", "平"}


def validate_master_synthesis(ms: Dict[str, Any]) -> List[str]:
    """校验一个 master_synthesis（总汇合参）。返回违规清单（空=合规）。"""
    errs: List[str] = []
    if not isinstance(ms, dict):
        return ["master_synthesis 非 dict"]
    if not ms.get("available"):
        return errs  # available=False 是合法的「数据不足」态，不校验其余

    # 必备顶层字段
    for k in ("headline", "overall_quality", "dimension_verdicts",
              "integrated_paragraphs", "master_advice"):
        if k not in ms:
            errs.append(f"缺字段 {k}")

    if ms.get("overall_quality") not in _QUALITY:
        errs.append(f"overall_quality 非法值：{ms.get('overall_quality')!r}")

    if not isinstance(ms.get("headline", ""), str) or not ms.get("headline", "").strip():
        errs.append("headline 须为非空字符串")

    # 单点：dimension_verdicts
    dvs = ms.get("dimension_verdicts")
    if not isinstance(dvs, list) or not dvs:
        errs.append("dimension_verdicts 须为非空 list")
    else:
        for i, dv in enumerate(dvs):
            if not isinstance(dv, dict):
                errs.append(f"dimension_verdicts[{i}] 非 dict"); continue
            label = dv.get("dim") or dv.get("domain")
            if not label:
                errs.append(f"dimension_verdicts[{i}] 缺标签（dim/domain）")
            if dv.get("quality") not in _QUALITY:
                errs.append(f"dimension_verdicts[{i}] quality 非法：{dv.get('quality')!r}")
            if not str(dv.get("verdict", "")).strip():
                errs.append(f"dimension_verdicts[{i}] verdict 空")

    # 组合：integrated_paragraphs
    ip = ms.get("integrated_paragraphs")
    if not isinstance(ip, list) or not ip or not all(isinstance(p, str) and p.strip() for p in ip):
        errs.append("integrated_paragraphs 须为非空字符串 list")

    # 汇总：master_advice
    if not str(ms.get("master_advice", "")).strip():
        errs.append("master_advice 空")

    return errs


def must_have_current_moment(ms: Dict[str, Any]) -> bool:
    """校验：总汇须含「当下」维度（任何解读纳入当下时辰）。"""
    if not ms.get("available"):
        return True
    dvs = ms.get("dimension_verdicts", []) or []
    return any((dv.get("dim") == "当下" or dv.get("domain") == "当下") for dv in dvs)


def normalize_dimension_label(dv: Dict[str, Any]) -> Dict[str, Any]:
    """补齐维度标签：确保 dim 与 domain 二键并存（前端任取其一皆可渲染）。"""
    label = dv.get("dim") or dv.get("domain")
    if label:
        dv.setdefault("dim", label)
        dv.setdefault("domain", label)
    return dv


def normalize_master_synthesis(ms: Dict[str, Any]) -> Dict[str, Any]:
    """对总汇做无损规整：统一维度标签双键。"""
    if isinstance(ms, dict) and ms.get("dimension_verdicts"):
        for dv in ms["dimension_verdicts"]:
            if isinstance(dv, dict):
                normalize_dimension_label(dv)
    return ms
