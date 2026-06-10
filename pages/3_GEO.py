import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from utils.sidebar import render as render_sidebar
import modules.geo_analysis as geo_mod
import config.geo_tasks as geo_tasks
from utils.result_banner import maybe_show_banner
from utils.prd_components import render_four_blocks, render_source_meta, render_disclaimer, review_gate
from prompts.geo_analysis_prompt import get_geo_questions, parse_keywords
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="GEO分析 — PinSight AI", page_icon="🌐", layout="wide", initial_sidebar_state="expanded")
brand = render_sidebar()

# 监测地域选项（全国 + 主要省市，C3）
REGION_OPTIONS = [
    "全国", "北京", "上海", "广州", "深圳", "杭州", "成都", "重庆",
    "武汉", "西安", "南京", "苏州", "长沙", "广东省", "江浙沪", "华北", "华南", "华东", "西南",
]

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">GEO 分析</h1>
  <p class="page-desc">模拟真实用户向 AI 搜索提问，评估品牌在 AI 回答中的可见度与内容补强方向（E-E-A-T 标准）</p>
</div>
""",
    unsafe_allow_html=True,
)

# 品牌切换时刷新品牌相关默认值（静态 key + 预写 session_state，规避 stale DOM）
if st.session_state.get("_geo_last_brand") != brand:
    st.session_state["geo_brand_words"] = "\n".join(BRAND_DISPLAY_NAMES[brand].split())
    st.session_state["geo_questions_text"] = "\n".join(get_geo_questions(brand))
    st.session_state["_geo_last_brand"] = brand
    # 品牌切换清除上一品牌的结果
    if st.session_state.get("geo_result", {}).get("_brand") != brand:
        st.session_state.pop("geo_result", None)
        st.session_state.pop("reviewed_geo", None)

tab_geo, tab_compare, tab_history = st.tabs(["🌐 GEO 分析", "📈 复测评估", "📜 监测历史"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — GEO 分析
# ══════════════════════════════════════════════════════════════════════════════
with tab_geo:
    st.info("什么是 GEO？模拟真实用户向 ChatGPT、Perplexity 等 AI 引擎提问，分析品牌是否被准确"
            "提及、与竞品的差距，并给出合规的内容补强建议。⚠️ 严禁用于刷屏、灌水或虚假评价。")

    # ── C1 · 结构化关键词组 ────────────────────────────────────────────────────
    st.subheader("① 结构化关键词组")
    st.caption("支持逗号（，/,）或换行分隔批量输入")
    kc1, kc2, kc3 = st.columns(3)
    with kc1:
        st.text_area("品牌词", key="geo_brand_words", height=110,
                     placeholder="如：喜茶, HEYTEA")
    with kc2:
        st.text_area("产品词", key="geo_product_words", height=110,
                     placeholder="如：多肉葡萄\n芝士奶盖\n轻乳茶")
    with kc3:
        st.text_area("品类词", key="geo_category_words", height=110,
                     placeholder="如：新式茶饮, 奶盖茶, 高端茶饮")

    brand_words = parse_keywords(st.session_state.get("geo_brand_words", ""))
    product_words = parse_keywords(st.session_state.get("geo_product_words", ""))
    category_words = parse_keywords(st.session_state.get("geo_category_words", ""))

    # ── C2/C3/C4 · 竞品 / 地域 / 周期 ──────────────────────────────────────────
    st.subheader("② 监测设置")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        competitors_text = st.text_input("竞品名称（选填，1-2 个）", key="geo_competitors",
                                         placeholder="如：奈雪的茶, 茶百道")
    with sc2:
        region = st.selectbox("监测地域", REGION_OPTIONS, key="geo_region")
    with sc3:
        period = st.selectbox("监测周期", geo_tasks.PERIODS, key="geo_period",
                              help="单次：立即分析一次；每日/每周：记录为周期性监测任务")
    competitors = parse_keywords(competitors_text)[:2]

    # ── S2-3 · 复测对比配置（关联历史任务 / 对比基准周期）──────────────────────────
    _prior = geo_tasks.list_records(brand_key=brand)
    link_base = False
    base_id = None
    if _prior:
        link_base = st.checkbox("📈 本轮作为复测，关联历史任务作对比基准", key="geo_link_base")
        if link_base:
            base_id = st.selectbox(
                "对比基准周期", [r["id"] for r in _prior],
                format_func=lambda i: next(
                    f"{r.get('created_at','')} · {r['period']} · {r['region']}"
                    for r in _prior if r["id"] == i),
                key="geo_base_id")

    # ── 测试问题 ────────────────────────────────────────────────────────────────
    with st.expander("③ 查看/编辑 AI 测试问题（可修改）", expanded=False):
        questions_text = st.text_area("每行一个问题（建议至少 4 个）", key="geo_questions_text", height=180)
    questions = [q.strip() for q in st.session_state.get("geo_questions_text", "").strip().split("\n") if q.strip()]
    st.caption(f"当前共 {len(questions)} 个测试问题"
               + (f"　|　关键词组：品牌词 {len(brand_words)} · 产品词 {len(product_words)} · 品类词 {len(category_words)}"))
    if len(questions) < 4:
        st.warning("建议至少设置 4 个测试问题以获得更全面的分析")

    if st.button("🚀 运行 GEO 分析", type="primary"):
        with st.spinner("正在进行 GEO 可见度分析…（约 30-60 秒）"):
            try:
                result = geo_mod.run(
                    brand, custom_questions=questions,
                    brand_words=brand_words, product_words=product_words,
                    category_words=category_words, competitors=competitors,
                    region=region, period=period,
                )
                result["_query_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                result["_brand"] = brand
                st.session_state["geo_result"] = result
                st.session_state.pop("reviewed_geo", None)
                # C4 · 记录监测历史（S2-3：附结构化指标 + 对比基准）
                from modules import geo_compare as _GC
                _meta = dict(result.get("_meta", {}))
                _meta["metrics"] = _GC.synth_metrics(
                    brand + region, result["_query_time"])
                if link_base and base_id:
                    _meta["base_id"] = base_id
                new_gid = geo_tasks.add_record(
                    brand, period, region, _meta,
                    summary=f"{len(questions)}题 · 竞品 {len(competitors)} · {region}",
                )
                if link_base and base_id:
                    st.session_state["_geo_new_compare"] = (new_gid, base_id)
            except Exception as e:
                st.error(f"分析失败：{e}")

    # S2-3 · 复测完成后给出快捷入口
    if st.session_state.get("_geo_new_compare"):
        st.success("✅ 本轮已关联基准，请切到上方「📈 复测评估」标签查看前后对比与效果评级。")

    # 品牌切换后旧结果保护
    if st.session_state.get("geo_result", {}).get("_brand") != brand:
        st.session_state.pop("geo_result", None)

    if "geo_result" in st.session_state:
        res = st.session_state["geo_result"]
        st.markdown("---")
        maybe_show_banner(res)

        m = res.get("_meta", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("测试问题数", len(res.get("questions") or questions))
        with col2:
            st.metric("知识库引用块", len(res["chunks"]))
        with col3:
            st.metric("监测地域", m.get("region", "全国"))
        with col4:
            st.metric("竞品对标", f"{len(m.get('competitors', []))} 个")

        st.markdown("---")
        # A1 · 四大区块渲染（含 E-E-A-T 结构化诊断）
        render_four_blocks(res["output"])
        # A2 · 信息溯源
        render_source_meta(res["chunks"], query_time=res.get("_query_time"))
        # A4 · 人工复核门控
        review_gate("geo")
        st.info("💡 **下一步**：将内容补强建议中的具体措施交由品牌方核实后，"
                "在官网/FAQ/媒体稿中补充对应内容，不得用于虚假宣传。")
        # A3 · 免责声明
        render_disclaimer()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — 复测评估（S2-3，并入 GEO 页）
# ══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    from utils.geo_compare_view import render as render_geo_compare
    render_geo_compare(brand)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — 监测历史（C4）
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.caption("GEO 监测任务历史记录（含时间戳、周期、地域与状态）。仅显示当前品牌。")
    f_period = st.selectbox("按周期筛选", ["全部"] + geo_tasks.PERIODS, key="geo_hist_period")
    records = geo_tasks.list_records(brand_key=brand, period=None if f_period == "全部" else f_period)

    if not records:
        st.info("暂无监测记录。在「GEO 分析」标签页运行一次分析后即会生成历史记录。")
    else:
        _pb = {"单次": "▶️", "每日": "🔁", "每周": "📅"}
        for r in records:
            with st.container(border=True):
                hc1, hc2 = st.columns([5, 1])
                with hc1:
                    st.markdown(f"**{_pb.get(r['period'],'•')} {r['period']}监测** · 地域：{r['region']} · `{r['status']}`")
                    st.caption(f"⏱ {r.get('created_at','')}　|　{r.get('summary','')}")
                with hc2:
                    if st.button("删除", key=f"geo_del_{r['id']}", use_container_width=True):
                        geo_tasks.delete_record(r["id"])
                        st.rerun()
