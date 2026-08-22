"""
core/log.py
===========
项目级日志设施 + 装配安全包装。

历史教训：六件套/总汇装配处遍布 `except Exception: pass`，引擎一旦报错，该件
便无声消失——前端看不到、测试测不出（六爻 query_time bug 即如此潜伏）。今立此
工具：装配失败一律记日志（开发/测试期可见），不再静默。

用法：
    from core.log import attach_safe
    attach_safe(result, "master_synthesis", build_master_synthesis, chart,
                component="bazi")
等价于 try/build/若 available 则挂载/except 记日志，但失败可见。
"""
from __future__ import annotations
import logging
import os
import sys
from typing import Any, Callable, Dict, Optional

_LEVEL = os.environ.get("BAGUA_LOG_LEVEL", "WARNING").upper()

logger = logging.getLogger("bagua")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(getattr(logging, _LEVEL, logging.WARNING))
    logger.propagate = False


def get_logger(component: str = "") -> logging.Logger:
    return logger.getChild(component) if component else logger


def attach_safe(result: Dict[str, Any],
                key: str,
                builder: Callable[..., Dict[str, Any]],
                *args,
                component: str = "",
                require_available: bool = True,
                **kwargs) -> bool:
    """
    安全装配一个「件」到 result[key]。
    - 调 builder(*args, **kwargs)；若返回 dict 且（require_available 时）available 为真，挂载。
    - 失败不再静默：记 WARNING 日志，返回 False。
    返回是否成功挂载。
    """
    log = get_logger(component)
    try:
        piece = builder(*args, **kwargs)
    except Exception as e:  # noqa: BLE001
        log.warning("装配 '%s' 失败：%s: %s", key, type(e).__name__, e)
        return False
    if not isinstance(piece, dict):
        log.warning("装配 '%s' 返回非 dict（%s），跳过", key, type(piece).__name__)
        return False
    if require_available and not piece.get("available"):
        # available=False 是正常情形（数据不足），记 DEBUG 而非 WARNING
        log.debug("装配 '%s' available=False，跳过", key)
        return False
    result[key] = piece
    return True


def log_failure(component: str, what: str, exc: Exception) -> None:
    """记录一处被吞的异常（替代裸 except: pass）。"""
    get_logger(component).warning("%s 失败：%s: %s", what, type(exc).__name__, exc)
