"""S3-1 选品任务 — 数据库存储（按租户隔离）。"""
from __future__ import annotations
import uuid
from datetime import datetime

from db.engine import get_session
from db.models import SelectionTask
from db import context as ctx

GOALS = ["新品", "迭代", "区域款", "竞品对标"]
DIMENSIONS = ["人群-年轻女性", "人群-学生", "价格-高端", "价格-平价",
              "场景-到店", "场景-外卖", "口味-果茶", "口味-奶茶", "功能-低糖"]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _to_dict(t: SelectionTask) -> dict:
    return {
        "id": t.id, "brand": t.brand, "name": t.name, "industry": t.industry,
        "categories": t.categories or [], "dimensions": t.dimensions or [],
        "regions": t.regions or [], "goal": t.goal, "competitors": t.competitors or [],
        "priority": t.priority, "task_tags": t.task_tags or [], "due_date": t.due_date,
        "status": t.status, "score": t.score, "result": t.result or {},
        "created_at": t.created_at,
    }


def add_task(brand: str, name: str, industry: str, categories: list, dimensions: list,
             regions: list, goal: str, competitors: list, result: dict,
             priority: str = "普通", task_tags: list | None = None, due_date: str = "") -> str:
    tid = "sel_" + uuid.uuid4().hex[:8]
    with get_session() as s:
        s.add(SelectionTask(
            id=tid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            brand=brand, name=name, industry=industry, categories=categories or [],
            dimensions=dimensions or [], regions=regions or [], goal=goal,
            competitors=competitors or [], priority=priority, task_tags=task_tags or [],
            due_date=due_date, status="已完成", score=int(result.get("top_score", 0)),
            result=result or {}, created_at=_now()))
    return tid


def list_tasks(brand: str | None = None, status: str | None = None) -> list:
    with get_session() as s:
        q = s.query(SelectionTask).filter(SelectionTask.tenant_id == ctx.tenant_id())
        if brand:
            q = q.filter(SelectionTask.brand == brand)
        if status and status != "全部":
            q = q.filter(SelectionTask.status == status)
        rows = [_to_dict(t) for t in q.all()]
    return sorted(rows, key=lambda x: x["created_at"], reverse=True)


def get_task(tid: str) -> dict | None:
    with get_session() as s:
        t = s.query(SelectionTask).filter(
            SelectionTask.id == tid, SelectionTask.tenant_id == ctx.tenant_id()).first()
        return _to_dict(t) if t else None


def set_status(tid: str, status: str) -> bool:
    with get_session() as s:
        t = s.query(SelectionTask).filter(
            SelectionTask.id == tid, SelectionTask.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        t.status = status
        return True


def delete_task(tid: str) -> bool:
    with get_session() as s:
        t = s.query(SelectionTask).filter(
            SelectionTask.id == tid, SelectionTask.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        s.delete(t)
        return True
