"""S1-5 统一 AI 网关 — 调用计量、限流、调用日志。

所有 LLM 调用经 llm_client.chat() 自动记录到 ai_call_logs；
业务侧也可显式调用 gateway_chat() 携带模块/Prompt分类标签。

设计为"尽力而为"：日志/限流失败绝不阻断主流程（除非显式额度拦截）。
"""
from __future__ import annotations
from datetime import datetime

QuotaError = type("QuotaError", (RuntimeError,), {})


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def usage_today(tenant_id: int | None = None) -> int:
    """当前租户今日 AI 调用次数。"""
    try:
        from sqlalchemy import func
        from db.engine import get_session
        from db.models import AiCallLog
        from db import context as ctx
        tid = tenant_id if tenant_id is not None else ctx.tenant_id()
        with get_session() as s:
            return (s.query(func.count(AiCallLog.id))
                    .filter(AiCallLog.tenant_id == tid)
                    .filter(func.date(AiCallLog.ts) == _today_str())
                    .scalar() or 0)
    except Exception:
        return 0


def quota_limit(tenant_id: int | None = None) -> int:
    try:
        from db.engine import get_session
        from db.models import Tenant
        from db import context as ctx
        tid = tenant_id if tenant_id is not None else ctx.tenant_id()
        with get_session() as s:
            t = s.query(Tenant).filter(Tenant.id == tid).first()
            return int(t.ai_daily_quota) if t and t.ai_daily_quota else 1000
    except Exception:
        return 1000


def check_quota(tenant_id: int | None = None) -> tuple[bool, int, int]:
    """返回 (是否可调用, 已用, 上限)。"""
    used = usage_today(tenant_id)
    limit = quota_limit(tenant_id)
    return used < limit, used, limit


def record_call(module: str = "", prompt_category: str = "", model: str = "",
                tokens: int = 0, latency_ms: int = 0, success: bool = True) -> None:
    """写入一条 AI 调用日志（尽力而为）。"""
    try:
        from db.engine import get_session
        from db.models import AiCallLog
        from db import context as ctx
        with get_session() as s:
            s.add(AiCallLog(
                tenant_id=ctx.tenant_id(), user_id=ctx.user_id(),
                module=module, prompt_category=prompt_category, model=model,
                tokens=tokens, latency_ms=latency_ms, success=success,
                ts=datetime.now(),  # 本地时间，保证按本地自然日计量
            ))
    except Exception:
        pass


def gateway_chat(system: str, user: str, *, module: str = "", prompt_category: str = "",
                 max_tokens: int = 2048, enforce_quota: bool = False) -> str:
    """带计量/限流的 AI 调用入口。

    enforce_quota=True 时超额抛 QuotaError（业务侧捕获后提示用户）。
    """
    from core import llm_client
    if enforce_quota:
        ok, used, limit = check_quota()
        if not ok:
            raise QuotaError(f"AI 调用额度不足：今日已用 {used}/{limit} 次，请联系管理员扩容。")
    # 设置调用标签，llm_client.chat 内部会写日志（避免重复计量）
    llm_client.set_call_tag(module=module, prompt_category=prompt_category)
    return llm_client.chat(system, user, max_tokens=max_tokens)
