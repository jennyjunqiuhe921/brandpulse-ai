"""G5 · GEO 区域竞争指数 — 数据库存储（按租户隔离）。

省份 × 5平台 提及率 → 可调权重加权 → 省份综合「区域竞争指数」；含竞品分省对比、
同比/环比趋势。Demo 确定性合成（己方随轮次走高、竞品较稳），接真实平台 API 后替换 _sim。
合规：纯监测分析，无刷量/自动发布。
"""
from __future__ import annotations
import uuid
import hashlib
from datetime import datetime

from db.engine import get_session
from db.models import GeoRegionRecord, GEO_REGION_PLATFORMS, GEO_PROVINCES
from db import context as ctx

PLATFORMS = GEO_REGION_PLATFORMS
PROVINCES = GEO_PROVINCES
DEFAULT_WEIGHTS = {p: round(1 / len(PLATFORMS), 3) for p in PLATFORMS}


def _seed(s: str) -> float:
    return (int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % 1000) / 1000.0


def _round_index(brand: str) -> int:
    with get_session() as s:
        return (s.query(GeoRegionRecord.round_id)
                .filter(GeoRegionRecord.tenant_id == ctx.tenant_id(),
                        GeoRegionRecord.brand == brand).distinct().count())


def _sim(subject: str, province: str, platform: str, ridx: int, is_comp: bool) -> float:
    base = 30 if is_comp else 22  # 己方初始略低，靠优化追赶
    growth = 0 if is_comp else ridx * 7   # 己方随轮次走高
    r = _seed(f"{subject}|{province}|{platform}|{ridx}")
    return round(min(95, base + growth + r * 35), 1)


def run_check(brand: str, provinces: list[str], competitors: list[str]) -> str:
    provinces = [p for p in provinces if p in PROVINCES] or PROVINCES
    competitors = [c.strip() for c in competitors if c.strip()][:2]
    rid = "rg_" + uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ridx = _round_index(brand)
    subjects = [(brand, False)] + [(c, True) for c in competitors]
    with get_session() as s:
        for prov in provinces:
            for pf in PLATFORMS:
                for subj, is_comp in subjects:
                    s.add(GeoRegionRecord(
                        tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(), brand=brand,
                        round_id=rid, province=prov, platform=pf, subject=subj,
                        is_competitor=is_comp, mention_rate=_sim(subj, prov, pf, ridx, is_comp),
                        checked_at=now))
    return rid


def list_rounds(brand: str) -> list[dict]:
    with get_session() as s:
        rows = s.query(GeoRegionRecord).filter(
            GeoRegionRecord.tenant_id == ctx.tenant_id(), GeoRegionRecord.brand == brand).all()
    rounds = {}  # round_id -> {checked_at, max_id}（max_id 作为插入顺序，分钟级时间戳相同也能确定先后）
    for r in rows:
        cur = rounds.get(r.round_id)
        if cur is None or r.id > cur["max_id"]:
            rounds[r.round_id] = {"checked_at": r.checked_at, "max_id": r.id}
    out = [{"round_id": k, "checked_at": v["checked_at"], "_o": v["max_id"]} for k, v in rounds.items()]
    return sorted(out, key=lambda x: x["_o"], reverse=True)


def _rows(brand: str, round_id: str):
    with get_session() as s:
        return [(r.province, r.platform, r.subject, r.is_competitor, r.mention_rate)
                for r in s.query(GeoRegionRecord).filter(
                    GeoRegionRecord.tenant_id == ctx.tenant_id(),
                    GeoRegionRecord.brand == brand,
                    GeoRegionRecord.round_id == round_id).all()]


def _composite_by_province(rows, subject_filter, weights):
    """按省聚合某主体的加权综合指数。返回 {province: index}。"""
    acc = {}
    for prov, pf, subj, is_comp, rate in rows:
        if subject_filter(subj, is_comp):
            acc.setdefault(prov, {})[pf] = rate
    out = {}
    wsum = sum(weights.values()) or 1
    for prov, pfmap in acc.items():
        out[prov] = round(sum(pfmap.get(pf, 0) * w for pf, w in weights.items()) / wsum, 1)
    return out


def stats(brand: str, round_id: str | None = None, weights: dict | None = None) -> dict:
    rounds = list_rounds(brand)
    if not rounds:
        return {}
    rid = round_id or rounds[0]["round_id"]
    weights = weights or DEFAULT_WEIGHTS
    rows = _rows(brand, rid)
    own = _composite_by_province(rows, lambda s, c: not c, weights)
    comps = sorted({s for _, _, s, c, _ in rows if c})
    comp_idx = {c: _composite_by_province(rows, lambda s, ic, cc=c: s == cc, weights) for c in comps}

    ranking = sorted(own.items(), key=lambda x: x[1], reverse=True)
    # 竞品差距（取第一个竞品）
    gap = {}
    if comps:
        c0 = comps[0]
        for prov, idx in own.items():
            gap[prov] = round(idx - comp_idx[c0].get(prov, 0), 1)
    return {"round_id": rid, "own": own, "competitors": comps, "comp_idx": comp_idx,
            "ranking": ranking, "gap": gap, "weights": weights,
            "national_avg": round(sum(own.values()) / len(own), 1) if own else 0}


def trend(brand: str, weights: dict | None = None) -> list[dict]:
    weights = weights or DEFAULT_WEIGHTS
    out = []
    for r in sorted(list_rounds(brand), key=lambda x: x.get("_o", 0)):
        st = stats(brand, r["round_id"], weights)
        out.append({"时间": r["checked_at"][:16], "全国均值": st.get("national_avg", 0)})
    return out
