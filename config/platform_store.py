"""S5 运营侧存储 — 租户/大模型/Prompt 全局管理（不按租户隔离，平台级）。"""
from __future__ import annotations
import difflib
from datetime import datetime

from db.engine import get_session
from db.models import (
    Tenant, User, Brand, ModelConfig, PromptTemplate,
    AiCallLog, ContentTask, SentimentTask,
)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ══ 租户管理（S5 2.2）═════════════════════════════════════════════════════════
def list_tenants() -> list:
    with get_session() as s:
        out = []
        for t in s.query(Tenant).all():
            users = s.query(User).filter(User.tenant_id == t.id).count()
            ai = s.query(AiCallLog).filter(AiCallLog.tenant_id == t.id).count()
            out.append({
                "id": t.id, "name": t.name, "industry": t.industry, "plan": t.plan,
                "ai_daily_quota": t.ai_daily_quota, "max_users": getattr(t, "max_users", 10),
                "contact": getattr(t, "contact", ""), "expire_at": getattr(t, "expire_at", ""),
                "status": getattr(t, "status", "正常"),
                "user_count": users, "ai_calls": ai,
            })
        return out


def create_tenant(name: str, industry: str, plan: str, *, max_users: int = 10,
                  ai_quota: int = 1000, contact: str = "", expire_at: str = "") -> int:
    with get_session() as s:
        t = Tenant(name=name, industry=industry, plan=plan, ai_daily_quota=ai_quota,
                   max_users=max_users, contact=contact, expire_at=expire_at, status="正常")
        s.add(t)
        s.flush()
        return t.id


def update_tenant(tid: int, **kv) -> bool:
    with get_session() as s:
        t = s.query(Tenant).filter(Tenant.id == tid).first()
        if not t:
            return False
        for k, v in kv.items():
            if hasattr(t, k):
                setattr(t, k, v)
        return True


def set_tenant_status(tid: int, status: str) -> bool:
    return update_tenant(tid, status=status)


# ══ 大模型配置中心（S5 2.5）═══════════════════════════════════════════════════
def list_models() -> list:
    with get_session() as s:
        return [{"id": m.id, "name": m.name, "model_type": m.model_type,
                 "api_base": m.api_base, "status": m.status, "note": m.note}
                for m in s.query(ModelConfig).all()]


def add_model(name: str, model_type: str, api_base: str, api_key: str, note: str = "") -> int:
    masked = (api_key[:3] + "****" + api_key[-2:]) if len(api_key) > 5 else "****"
    with get_session() as s:
        m = ModelConfig(name=name, model_type=model_type, api_base=api_base,
                        api_key_masked=masked, status="未启用", note=note, created_at=_now())
        s.add(m)
        s.flush()
        return m.id


def set_model_status(mid: int, status: str) -> bool:
    with get_session() as s:
        m = s.query(ModelConfig).filter(ModelConfig.id == mid).first()
        if not m:
            return False
        m.status = status
        return True


def delete_model(mid: int) -> bool:
    with get_session() as s:
        m = s.query(ModelConfig).filter(ModelConfig.id == mid).first()
        if not m:
            return False
        s.delete(m)
        return True


# ══ Prompt 统一管理中心（S5 2.6）══════════════════════════════════════════════
def list_prompts(category: str | None = None) -> list:
    with get_session() as s:
        q = s.query(PromptTemplate)
        if category and category != "全部":
            q = q.filter(PromptTemplate.category == category)
        return [{"id": p.id, "name": p.name, "category": p.category,
                 "model_name": p.model_name, "content": p.content, "version": p.version,
                 "status": p.status, "history": p.history or [], "updated_at": p.updated_at}
                for p in q.order_by(PromptTemplate.category, PromptTemplate.id).all()]


def add_prompt(name: str, category: str, model_name: str, content: str, created_by: str = "") -> int:
    with get_session() as s:
        p = PromptTemplate(name=name, category=category, model_name=model_name,
                           content=content, version=1, status="草稿", history=[],
                           created_by=created_by, updated_at=_now())
        s.add(p)
        s.flush()
        return p.id


def new_version(pid: int, new_content: str) -> bool:
    """已启用模板必须新建版本：存历史，版本+1，回到草稿。"""
    with get_session() as s:
        p = s.query(PromptTemplate).filter(PromptTemplate.id == pid).first()
        if not p:
            return False
        hist = list(p.history or [])
        hist.append({"version": p.version, "content": p.content})
        p.history = hist
        p.content = new_content
        p.version += 1
        p.status = "草稿"
        p.updated_at = _now()
        return True


def enable_prompt(pid: int) -> bool:
    """启用：同分类其余置草稿，本条启用。"""
    with get_session() as s:
        p = s.query(PromptTemplate).filter(PromptTemplate.id == pid).first()
        if not p:
            return False
        for other in s.query(PromptTemplate).filter(
                PromptTemplate.category == p.category).all():
            other.status = "草稿"
        p.status = "已启用"
        p.updated_at = _now()
        return True


def disable_prompt(pid: int) -> bool:
    with get_session() as s:
        p = s.query(PromptTemplate).filter(PromptTemplate.id == pid).first()
        if not p:
            return False
        p.status = "草稿"
        return True


def rollback_prompt(pid: int, to_version: int) -> bool:
    with get_session() as s:
        p = s.query(PromptTemplate).filter(PromptTemplate.id == pid).first()
        if not p:
            return False
        snap = next((h for h in (p.history or []) if h["version"] == to_version), None)
        if not snap:
            return False
        hist = list(p.history or [])
        hist.append({"version": p.version, "content": p.content})
        p.history = hist
        p.content = snap["content"]
        p.version += 1
        p.status = "草稿"
        p.updated_at = _now()
        return True


def diff_text(old: str, new: str) -> str:
    sm = difflib.SequenceMatcher(None, old, new)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        seg_old = old[i1:i2].replace("<", "&lt;")
        seg_new = new[j1:j2].replace("<", "&lt;")
        if tag == "equal":
            out.append(seg_old)
        elif tag == "delete":
            out.append(f'<span style="background:#FBE3E0;text-decoration:line-through">{seg_old}</span>')
        elif tag == "insert":
            out.append(f'<span style="background:#DDF3E4">{seg_new}</span>')
        elif tag == "replace":
            out.append(f'<span style="background:#FBE3E0;text-decoration:line-through">{seg_old}</span>')
            out.append(f'<span style="background:#DDF3E4">{seg_new}</span>')
    return "".join(out)
