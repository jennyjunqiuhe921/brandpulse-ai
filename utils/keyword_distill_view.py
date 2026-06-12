"""G1 · GEO 关键词蒸馏视图（嵌入 GEO 页「关键词蒸馏」tab）。"""
import streamlit as st
import pandas as pd
from modules import keyword_distill as KD
import config.geo_keywords as GK

_SCORE_COLOR = {"高": "#C62828", "中": "#F9A825", "低": "#9C8E82"}
_INTENT_ICON = {"价格敏感型": "💰", "B2B选品型": "🏭", "决策参考型": "🧭", "通用型": "🔹"}


def render(brand: str) -> None:
    st.caption("输入产品/服务+地域+卖点，蒸馏长尾词，自动标注「通用词/成交词」、成交意图分、"
               "意图类型与推荐平台。优先做高意图成交词。")

    # ── 蒸馏输入 ─────────────────────────────────────────────────────────────
    with st.expander("▶️ 蒸馏关键词", expanded=not GK.list_batches(brand)):
        c1, c2 = st.columns(2)
        product = c1.text_input("产品 / 服务（必填）", key="kd_product",
                                placeholder="如：空调维修 / 多肉葡萄")
        region = c2.text_input("目标地域（选填）", key="kd_region", placeholder="如：南京江宁")
        service = st.text_input("服务属性 / 卖点（逗号分隔，选填）", key="kd_service",
                                placeholder="如：上门,厂家直销,3年质保")
        if st.button("🔍 开始蒸馏", type="primary"):
            if not product.strip():
                st.warning("请至少填写产品 / 服务")
            else:
                rows = KD.distill(product, region, service)
                if rows:
                    bid = GK.save_batch(brand, rows)
                    try:
                        from db.audit import log
                        log("GEO关键词蒸馏", f"brand={brand} 产品={product} 词数={len(rows)}")
                    except Exception:
                        pass
                    st.success(f"蒸馏出 {len(rows)} 个关键词（成交词优先排序）")
                    st.session_state["kd_last_batch"] = bid
                    st.rerun()

    batches = GK.list_batches(brand)
    if not batches:
        st.info("当前品牌暂无蒸馏记录。展开上方「蒸馏关键词」生成一批即可。")
        return

    # ── 批次选择 ─────────────────────────────────────────────────────────────
    bid = st.selectbox("蒸馏批次", [b["batch_id"] for b in batches],
                       index=0,
                       format_func=lambda i: next(
                           f"{b['created_at']} · {b['count']}词（{b['batch_id']}）"
                           for b in batches if b["batch_id"] == i))
    rows = GK.list_keywords(brand, bid)

    # 概览
    deal = [r for r in rows if r["kw_type"] == "成交词"]
    high = [r for r in rows if r["intent_score"] == "高"]
    c = st.columns(3)
    c[0].metric("关键词总数", len(rows))
    c[1].metric("成交词", len(deal))
    c[2].metric("高意图词", len(high))

    # ── 关键词表 ─────────────────────────────────────────────────────────────
    st.markdown("#### 蒸馏关键词清单")
    df = pd.DataFrame([{
        "关键词": r["keyword"],
        "类型": r["kw_type"],
        "意图": f'{_INTENT_ICON.get(r["intent_type"],"")} {r["intent_type"]}',
        "意图分": r["intent_score"],
        "推荐平台": r["platform"],
    } for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── 一键带入下游（G1-4）──────────────────────────────────────────────────
    st.markdown("#### 带入下游")
    st.caption("勾选关键词，带入「收录监测」检测其 AI 收录情况，或带去内容工坊创作。")
    default_high = KD.high_intent(rows)[:10]
    picked = st.multiselect("选择关键词", [r["keyword"] for r in rows], default=default_high)
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("📡 带入收录监测", use_container_width=True):
            if picked:
                st.session_state["gi_kw"] = "\n".join(picked)
                st.success(f"已带入 {len(picked)} 个词 → 请切到「📡 收录监测」tab 运行检测")
            else:
                st.warning("请先勾选关键词")
    with cc2:
        st.page_link("pages/4_内容工坊.py", label="✍️ 去内容工坊创作", icon="✍️")

    st.caption("提示：高意图成交词（💰价格敏感 / 🏭B2B选品）成交概率更高，建议优先做。"
               "所有内容优化须基于真实信息，严禁刷量灌水。")
