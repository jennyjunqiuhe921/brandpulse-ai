"""G4 · GEO 多平台收录监测 — 数据库存储（按租户隔离）。

监测品牌在各大国产 AI 平台（DeepSeek/豆包/元宝/通义/文心/纳米/KIMI/智谱）回答中的
「收录情况」：是否被提及/收录、命中名次。Demo 模式下确定性合成数据；后续轮次收录率
随"持续优化"递增，便于演示趋势。接真实 API 后替换 _simulate 即可。
"""
from __future__ import annotations
import uuid
import hashlib
from datetime import datetime

from db.engine import get_session
from db.models import GeoInclusion, GEO_AI_PLATFORMS
from db import context as ctx

PLATFORMS = GEO_AI_PLATFORMS


def _seed(s: str) -> float:
    return (int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % 1000) / 1000.0


def _round_index(brand: str) -> int:
    """该品牌已有多少轮检测（用于演示收录率随轮次提升）。"""
    with get_session() as s:
        rounds = (s.query(GeoInclusion.round_id)
                  .filter(GeoInclusion.tenant_id == ctx.tenant_id(),
                          GeoInclusion.brand == brand)
                  .distinct().count())
    return rounds


def _simulate(brand: str, keyword: str, platform: str, round_idx: int) -> tuple[bool, int]:
    """确定性合成：是否收录 + 命中名次。已知演示品牌基础收录更高，轮次越多收录率越高。"""
    from core.llm_client import DEMO_MODE  # noqa
    base = 0.45 if brand in {"heytea", "nayuki", "chapanda"} else 0.28
    prob = min(0.92, base + round_idx * 0.09)
    r = _seed(f"{brand}|{keyword}|{platform}|{round_idx}")
    included = r < prob
    position = (1 + int(_seed(f"{brand}|{keyword}|{platform}|pos") * 9)) if included else 0
    return included, position


def run_check(brand: str, keywords: list[str]) -> str:
    """对一组关键词 × 全平台跑一轮收录检测，返回 round_id。"""
    keywords = [k.strip() for k in keywords if k.strip()][:20]
    if not keywords:
        return ""
    rid = "inc_" + uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ridx = _round_index(brand)
    with get_session() as s:
        for kw in keywords:
            for pf in PLATFORMS:
                inc, pos = _simulate(brand, kw, pf, ridx)
                s.add(GeoInclusion(
                    tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
                    brand=brand, round_id=rid, keyword=kw, platform=pf,
                    included=inc, position=pos, checked_at=now))
    return rid


def list_rounds(brand: str) -> list[dict]:
    """该品牌全部检测轮次（按时间倒序）。"""
    with get_session() as s:
        rows = (s.query(GeoInclusion)
                .filter(GeoInclusion.tenant_id == ctx.tenant_id(),
                        GeoInclusion.brand == brand).all())
    rounds: dict[str, dict] = {}  # max_id 兜底排序，分钟级时间戳相同也能定先后
    for r in rows:
        cur = rounds.get(r.round_id)
        if cur is None or r.id > cur["max_id"]:
            rounds[r.round_id] = {"checked_at": r.checked_at, "max_id": r.id}
    out = [{"round_id": k, "checked_at": v["checked_at"], "_o": v["max_id"]} for k, v in rounds.items()]
    return sorted(out, key=lambda x: x["_o"], reverse=True)


def _round_rows(brand: str, round_id: str | None):
    with get_session() as s:
        q = s.query(GeoInclusion).filter(
            GeoInclusion.tenant_id == ctx.tenant_id(), GeoInclusion.brand == brand)
        if round_id:
            q = q.filter(GeoInclusion.round_id == round_id)
        return [(r.keyword, r.platform, r.included, r.position) for r in q.all()]


def round_stats(brand: str, round_id: str | None = None) -> dict:
    """某轮（默认最新）收录统计：按平台、整体、按关键词、平均名次。"""
    rounds = list_rounds(brand)
    if not rounds:
        return {}
    rid = round_id or rounds[0]["round_id"]
    rows = _round_rows(brand, rid)
    keywords = sorted({k for k, *_ in rows})
    n_kw = len(keywords)

    per_platform = {}
    for pf in PLATFORMS:
        inc = sum(1 for k, p, i, pos in rows if p == pf and i)
        per_platform[pf] = {"included": inc, "total": n_kw,
                            "rate": round(inc / n_kw * 100, 1) if n_kw else 0}

    total_cells = len(rows)
    total_inc = sum(1 for *_, i, pos in [(k, p, i, pos) for k, p, i, pos in rows] if i)
    overall = round(total_inc / total_cells * 100, 1) if total_cells else 0

    by_keyword = []
    for kw in keywords:
        hit = sum(1 for k, p, i, pos in rows if k == kw and i)
        by_keyword.append({"keyword": kw, "platforms_hit": hit, "total_platforms": len(PLATFORMS)})

    positions = [pos for *_, i, pos in [(k, p, i, pos) for k, p, i, pos in rows] if i and pos]
    avg_pos = round(sum(positions) / len(positions), 1) if positions else 0
    top10 = round(len(positions) / total_cells * 100, 1) if total_cells else 0  # 占位率
    # 前3名占比：被收录且排进前3名的格子占全部检测格子的比例（衡量"排名靠前"，与收录率区分开）
    top3_rate = round(sum(1 for p in positions if p <= 3) / total_cells * 100, 1) if total_cells else 0

    return {
        "round_id": rid, "checked_at": rounds[0]["checked_at"] if not round_id else None,
        "keywords": keywords, "per_platform": per_platform, "overall_rate": overall,
        "by_keyword": by_keyword, "avg_position": avg_pos, "occupancy_rate": top10,
        "top3_rate": top3_rate,
        "total_included": total_inc, "total_cells": total_cells,
    }


def round_matrix(brand: str, round_id: str | None = None) -> dict:
    """问题 × 平台 收录矩阵：{keywords, platforms, cells[kw][pf]=(included, position)}。

    供前端展示"哪个问题、在哪个平台、是否收录、排第几"——直接回答用户"这是哪个问题
    在各平台的收录情况、排名在前吗"的疑问。数据源为逐条 (问题,平台,收录,名次)。
    """
    rounds = list_rounds(brand)
    if not rounds:
        return {}
    rid = round_id or rounds[0]["round_id"]
    rows = _round_rows(brand, rid)
    keywords = sorted({k for k, *_ in rows})
    cells = {k: {pf: (False, 0) for pf in PLATFORMS} for k in keywords}
    for k, pf, inc, pos in rows:
        cells[k][pf] = (bool(inc), int(pos or 0))
    return {"keywords": keywords, "platforms": list(PLATFORMS), "cells": cells}


def trend(brand: str) -> list[dict]:
    """各轮整体收录率趋势（时间正序）。"""
    out = []
    for r in sorted(list_rounds(brand), key=lambda x: x["checked_at"]):
        st = round_stats(brand, r["round_id"])
        out.append({"time": r["checked_at"][:16], "收录率": st.get("overall_rate", 0)})
    return out
