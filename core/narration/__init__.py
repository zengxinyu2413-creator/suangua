"""行文层（AI 叙事层）—— 下游转写引擎产出的确定性事实为流畅古文，绝不新增判断。"""
from core.narration.narrator import (
    build_lexicon, extract_fact_blob, build_narration_prompt,
    verify_fidelity, narrate, llm_anthropic, STYLES, DEFAULT_STYLE, collect_facts, collect_facts_multi, guard_metrics, build_export_document,
)
__all__ = ["build_lexicon", "extract_fact_blob", "build_narration_prompt",
           "verify_fidelity", "narrate", "llm_anthropic", "STYLES", "DEFAULT_STYLE", "collect_facts", "collect_facts_multi", "guard_metrics", "build_export_document"]
