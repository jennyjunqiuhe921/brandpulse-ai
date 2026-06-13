"""G3 · GEO 发布计划 — 合规版分发（人工发布，系统绝不自动发布）。

仅做：发布清单管理 + 导出发布包（含水印）+ 发布状态回填。
不含：账号授权、自动投喂、批量发布、防封控等任何自动分发能力（合规红线）。
"""
from __future__ import annotations
from datetime import datetime

from db.engine import get_session
from db.models import GeoPublishItem
from db import context as ctx


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def add_items(brand: str, tasks: list[dict], plan_time: str = "") -> int:
    """从内容任务加入发布清单。tasks: [{id,title,platforms,output,meta}]。"""
    n = 0
    with get_session() as s:
        for t in tasks:
            platform = (t.get("platforms") or ["综合"])[0]
            keyword = (t.get("meta") or {}).get("keyword", "")
            s.add(GeoPublishItem(
                tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(), brand=brand,
                task_id=t.get("id", ""), keyword=keyword, platform=platform,
                title=t.get("title", ""), content=t.get("output", ""),
                plan_time=plan_time, status="待发布", created_at=_now()))
            n += 1
    return n


def _to_dict(i: GeoPublishItem) -> dict:
    return {"id": i.id, "task_id": i.task_id, "keyword": i.keyword, "platform": i.platform,
            "title": i.title, "content": i.content, "plan_time": i.plan_time,
            "status": i.status, "created_at": i.created_at, "published_at": i.published_at}


def list_items(brand: str, status: str | None = None) -> list[dict]:
    with get_session() as s:
        q = s.query(GeoPublishItem).filter(
            GeoPublishItem.tenant_id == ctx.tenant_id(), GeoPublishItem.brand == brand)
        if status:
            q = q.filter(GeoPublishItem.status == status)
        rows = [_to_dict(i) for i in q.all()]
    return sorted(rows, key=lambda x: (x["status"] != "待发布", x["created_at"]), reverse=False)


def set_published(item_id: int) -> bool:
    with get_session() as s:
        i = s.query(GeoPublishItem).filter(
            GeoPublishItem.id == item_id, GeoPublishItem.tenant_id == ctx.tenant_id()).first()
        if not i:
            return False
        i.status = "已发布"
        i.published_at = _now()
        return True


def delete_item(item_id: int) -> bool:
    with get_session() as s:
        i = s.query(GeoPublishItem).filter(
            GeoPublishItem.id == item_id, GeoPublishItem.tenant_id == ctx.tenant_id()).first()
        if not i:
            return False
        s.delete(i)
        return True


def export_package(brand: str, items: list[dict]) -> str:
    """生成可下载的发布包文本（含水印 + 人工发布说明）。"""
    from utils.watermark import stamp_text_export
    lines = [
        "# GEO 内容发布包",
        "",
        "> ⚠️ **人工发布说明**：本发布包由你**自行登录各平台手动发布**，"
        "系统不提供任何自动发布功能。发布内容须真实合规，严禁夸大宣传、刷量灌水。",
        "",
        f"品牌/主体：{brand}　条目数：{len(items)}",
        "",
    ]
    for n, it in enumerate(items, 1):
        lines += [
            f"## {n}. [{it['platform']}] {it['title']}",
            f"- 关键词：{it['keyword'] or '—'}　计划发布：{it['plan_time'] or '—'}",
            "",
            it["content"],
            "",
            "---",
            "",
        ]
    return stamp_text_export("\n".join(lines), title="GEO发布包")
