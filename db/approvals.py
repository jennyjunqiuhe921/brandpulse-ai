"""S2-1 多级审批中心 — 数据库存储（按租户隔离）。

支持：单级/多级/多条件分支路由、驳回评论(高亮段落)、修改重提(版本留痕)、
版本 Diff、催办、在线协作评论区。审批人角色简化为企业领导(ROLE_ADMIN)，
通过 approver_label 区分"市场主管 / 品牌负责人"等多级节点。
"""
from __future__ import annotations
import uuid
import difflib
from datetime import datetime

from db.engine import get_session
from db.models import (
    ApprovalRequest, ApprovalStep, ApprovalComment,
    APR_PENDING, APR_APPROVED, APR_REJECTED, APR_WITHDRAWN,
    STEP_WAIT, STEP_PASS, STEP_REJECT, ROLE_ADMIN,
)
from db import context as ctx
from db import messages as msg_store
from db.models import MSG_APPROVAL


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── 多条件分支路由：根据风险 + 优先级决定审批链 ──────────────────────────────
def _route_steps(risk_level: str, priority: str) -> list[dict]:
    """返回步骤定义列表 [{step_no, approver_role, approver_label}]。"""
    high = risk_level == "高" or priority == "紧急"
    mid = risk_level == "中"
    chain = [{"step_no": 1, "approver_role": ROLE_ADMIN, "approver_label": "市场主管"}]
    if high:
        chain.append({"step_no": 2, "approver_role": ROLE_ADMIN, "approver_label": "品牌/法务负责人"})
    elif mid:
        chain.append({"step_no": 2, "approver_role": ROLE_ADMIN, "approver_label": "品牌负责人"})
    return chain


def route_preview(risk_level: str, priority: str) -> list[str]:
    """供 UI 预览审批链。"""
    return [s["approver_label"] for s in _route_steps(risk_level, priority)]


# ── 发起审批 ─────────────────────────────────────────────────────────────────
def submit(biz_type: str, biz_id: str, title: str, content: str, *,
           brand: str = "", risk_level: str = "低", priority: str = "普通") -> str:
    rid = "apr_" + uuid.uuid4().hex[:8]
    now = _now()
    steps = _route_steps(risk_level, priority)
    with get_session() as s:
        s.add(ApprovalRequest(
            id=rid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            owner_name=ctx.user_name(), biz_type=biz_type, biz_id=biz_id, brand=brand,
            title=title, content=content, risk_level=risk_level, priority=priority,
            status=APR_PENDING, current_step=1, version=1, history=[],
            created_at=now, updated_at=now,
        ))
        for st_def in steps:
            s.add(ApprovalStep(request_id=rid, **st_def, status=STEP_WAIT))
    # 通知审批人（全员定向到管理层，用全员消息简化）
    msg_store.push(f"新审批待处理：{title}", f"{biz_type} · 风险{risk_level} · 由 {ctx.user_name()} 发起",
                   category=MSG_APPROVAL, level="warn", link="pages/11_审批中心.py")
    return rid


def _req_dict(r: ApprovalRequest, steps: list[ApprovalStep]) -> dict:
    return {
        "id": r.id, "owner_id": r.owner_id, "owner_name": r.owner_name,
        "biz_type": r.biz_type, "biz_id": r.biz_id, "brand": r.brand,
        "title": r.title, "content": r.content, "risk_level": r.risk_level,
        "priority": r.priority, "status": r.status, "current_step": r.current_step,
        "version": r.version, "history": r.history or [], "urged": r.urged,
        "created_at": r.created_at, "updated_at": r.updated_at,
        "steps": [{
            "step_no": x.step_no, "approver_label": x.approver_label,
            "approver_role": x.approver_role, "status": x.status,
            "comment": x.comment, "quote": x.quote, "decided_at": x.decided_at,
        } for x in sorted(steps, key=lambda y: y.step_no)],
    }


def _load(rid: str):
    with get_session() as s:
        r = s.query(ApprovalRequest).filter(
            ApprovalRequest.id == rid, ApprovalRequest.tenant_id == ctx.tenant_id()).first()
        if not r:
            return None
        steps = s.query(ApprovalStep).filter(ApprovalStep.request_id == rid).all()
        return _req_dict(r, steps)


def get(rid: str) -> dict | None:
    return _load(rid)


def list_requests(scope: str = "todo") -> list:
    """scope: todo(待我审批) / done(我已审批) / mine(我发起的)。"""
    uid = ctx.user_id()
    role = ctx.user_role()
    with get_session() as s:
        rs = s.query(ApprovalRequest).filter(
            ApprovalRequest.tenant_id == ctx.tenant_id()).all()
        out = []
        for r in rs:
            steps = s.query(ApprovalStep).filter(ApprovalStep.request_id == r.id).all()
            d = _req_dict(r, steps)
            if scope == "mine":
                if r.owner_id == uid:
                    out.append(d)
            elif scope == "todo":
                # 待我审批：单据审批中 + 当前步骤指派给我的角色 + 我不是发起人
                if r.status == APR_PENDING and role == ROLE_ADMIN and r.owner_id != uid:
                    cur = next((x for x in d["steps"] if x["step_no"] == r.current_step), None)
                    if cur and cur["status"] == STEP_WAIT and cur["approver_role"] == role:
                        out.append(d)
            elif scope == "done":
                # 我已审批：存在由我决策过的步骤
                if any(x["decided_at"] and x["status"] != STEP_WAIT for x in d["steps"]) \
                        and role == ROLE_ADMIN and r.owner_id != uid:
                    out.append(d)
        return sorted(out, key=lambda x: x.get("created_at", ""), reverse=True)


def decide(rid: str, approve: bool, comment: str = "", quote: str = "") -> bool:
    """对当前步骤做出审批决策。通过则推进/终审，驳回则整单驳回。"""
    now = _now()
    with get_session() as s:
        r = s.query(ApprovalRequest).filter(
            ApprovalRequest.id == rid, ApprovalRequest.tenant_id == ctx.tenant_id()).first()
        if not r or r.status != APR_PENDING:
            return False
        step = s.query(ApprovalStep).filter(
            ApprovalStep.request_id == rid, ApprovalStep.step_no == r.current_step).first()
        if not step or step.status != STEP_WAIT:
            return False
        step.comment = comment
        step.quote = quote
        step.decided_by = ctx.user_id()
        step.decided_at = now
        r.updated_at = now
        if not approve:
            step.status = STEP_REJECT
            r.status = APR_REJECTED
            msg_store.push(f"审批被驳回：{r.title}", comment or "请修改后重新提交",
                           category=MSG_APPROVAL, level="danger",
                           user_id=r.owner_id, link="pages/12_我的审批.py")
        else:
            step.status = STEP_PASS
            total = s.query(ApprovalStep).filter(ApprovalStep.request_id == rid).count()
            if r.current_step >= total:
                r.status = APR_APPROVED
                msg_store.push(f"审批已通过：{r.title}", "全部节点已通过，可正式使用",
                               category=MSG_APPROVAL, level="info",
                               user_id=r.owner_id, link="pages/12_我的审批.py")
            else:
                r.current_step += 1
        return True


def resubmit(rid: str, new_content: str) -> bool:
    """修改重提：内容存入历史，版本+1，重置步骤，回到审批中。"""
    now = _now()
    with get_session() as s:
        r = s.query(ApprovalRequest).filter(
            ApprovalRequest.id == rid, ApprovalRequest.tenant_id == ctx.tenant_id()).first()
        if not r or r.owner_id != ctx.user_id():
            return False
        hist = list(r.history or [])
        hist.append({"version": r.version, "content": r.content, "at": r.updated_at})
        r.history = hist
        r.content = new_content
        r.version += 1
        r.status = APR_PENDING
        r.current_step = 1
        r.urged = False
        r.updated_at = now
        for x in s.query(ApprovalStep).filter(ApprovalStep.request_id == rid).all():
            x.status = STEP_WAIT
            x.comment = ""
            x.quote = ""
            x.decided_at = ""
            x.decided_by = None
    msg_store.push(f"审批已重新提交：（v{_get_version(rid)}）", "发起人修改后重提，请重新审批",
                   category=MSG_APPROVAL, level="warn", link="pages/11_审批中心.py")
    return True


def _get_version(rid: str) -> int:
    with get_session() as s:
        r = s.query(ApprovalRequest).filter(ApprovalRequest.id == rid).first()
        return r.version if r else 1


def withdraw(rid: str) -> bool:
    with get_session() as s:
        r = s.query(ApprovalRequest).filter(
            ApprovalRequest.id == rid, ApprovalRequest.tenant_id == ctx.tenant_id()).first()
        if not r or r.owner_id != ctx.user_id() or r.status != APR_PENDING:
            return False
        r.status = APR_WITHDRAWN
        r.updated_at = _now()
        return True


def urge(rid: str) -> bool:
    """催办：标记并推送给审批人。"""
    with get_session() as s:
        r = s.query(ApprovalRequest).filter(
            ApprovalRequest.id == rid, ApprovalRequest.tenant_id == ctx.tenant_id()).first()
        if not r or r.status != APR_PENDING:
            return False
        r.urged = True
        title = r.title
    msg_store.push(f"⏰ 催办：{title}", "发起人催办，请尽快处理该审批",
                   category=MSG_APPROVAL, level="warn", link="pages/11_审批中心.py")
    return True


# ── 协作评论区 ───────────────────────────────────────────────────────────────
def add_comment(rid: str, body: str) -> bool:
    if not body.strip():
        return False
    with get_session() as s:
        s.add(ApprovalComment(request_id=rid, user_id=ctx.user_id(),
                              username=ctx.user_name(), body=body, created_at=_now()))
    return True


def list_comments(rid: str) -> list:
    with get_session() as s:
        rows = s.query(ApprovalComment).filter(
            ApprovalComment.request_id == rid).order_by(ApprovalComment.id).all()
        return [{"username": c.username, "body": c.body, "created_at": c.created_at}
                for c in rows]


# ── 版本 Diff ────────────────────────────────────────────────────────────────
def diff_versions(old: str, new: str) -> str:
    """返回 HTML 高亮的差异（绿增/红删）。"""
    sm = difflib.SequenceMatcher(None, old, new)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(_esc(old[i1:i2]))
        elif tag == "delete":
            out.append(f'<span style="background:#FBE3E0;color:#8C2010;text-decoration:line-through">{_esc(old[i1:i2])}</span>')
        elif tag == "insert":
            out.append(f'<span style="background:#DDF3E4;color:#1E5C3A">{_esc(new[j1:j2])}</span>')
        elif tag == "replace":
            out.append(f'<span style="background:#FBE3E0;color:#8C2010;text-decoration:line-through">{_esc(old[i1:i2])}</span>')
            out.append(f'<span style="background:#DDF3E4;color:#1E5C3A">{_esc(new[j1:j2])}</span>')
    return "".join(out)


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
