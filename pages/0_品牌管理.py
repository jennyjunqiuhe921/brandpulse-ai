"""品牌管理 — 品牌列表 / 新增品牌 / 知识库 / 品牌分析 / 产品分析。"""
from __future__ import annotations
import io
import streamlit as st
from utils.sidebar import render as render_sidebar
from utils.result_banner import maybe_show_banner
from utils.prd_components import render_four_blocks, render_source_meta, render_disclaimer
from config.settings import BRAND_DISPLAY_NAMES
from prompts.geo_analysis_prompt import parse_keywords
from utils.followup_chat import render as render_chat
from config.brand_manager import (
    INDUSTRY_OPTIONS,
    TONE_OPTIONS,
    load_all_brands,
    get_brand,
    create_brand,
    update_brand,
    delete_brand,
)
from core.rag_engine import (
    ingest_text,
    collection_count,
    get_sources,
    delete_source,
    clear_collection,
)
import modules.brand_analysis as brand_mod
import modules.product_analysis as product_mod
import modules.market_positioning as mp_mod
import modules.competitor_analysis as comp_mod

st.set_page_config(page_title="品牌管理 · PinSight AI", layout="wide", initial_sidebar_state="expanded")
selected_brand = render_sidebar()

# 品牌切换时清除所有分析结果缓存，防止串台显示
if st.session_state.get("_bm_last_brand") != selected_brand:
    for _k in ("brand_result", "product_result", "mp_result", "comp_result", "comp_pair"):
        st.session_state.pop(_k, None)
    st.session_state["_bm_last_brand"] = selected_brand

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">品牌中心</h1>
  <p class="page-desc">管理品牌信息、知识库，并在此直接运行品牌与产品深度分析。</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.brand-card {
    background:#FDFAF5; border:1px solid #DDD4C4; border-radius:10px;
    padding:18px 20px; margin-bottom:10px; display:flex; align-items:center; gap:16px;
    box-shadow:0 1px 6px rgba(60,40,20,0.06); transition:border-color 0.15s, box-shadow 0.15s;
}
.brand-card:hover { border-color:#C4522A; box-shadow:0 3px 14px rgba(60,40,20,0.10); }
.brand-dot {
    width:40px; height:40px; border-radius:10px;
    display:flex; align-items:center; justify-content:center;
    font-size:16px; font-weight:700; color:#fff; flex-shrink:0;
}
.brand-info { flex:1; }
.brand-name { font-size:15px; font-weight:700; color:#1C1510; margin:0 0 2px; font-family:'Noto Serif SC',serif; }
.brand-meta { font-size:12px; color:#9C8E82; margin:0; }
.demo-badge {
    display:inline-block; background:rgba(43,108,176,0.08); border:1px solid rgba(43,108,176,0.2);
    border-radius:20px; padding:1px 8px; font-size:10px; color:#2B6CB0;
    font-weight:600; letter-spacing:0.3px; margin-left:8px; vertical-align:middle;
}
.kb-source-row {
    display:flex; align-items:center; justify-content:space-between;
    padding:10px 16px; background:#FDFAF5; border:1px solid #DDD4C4;
    border-radius:8px; margin-bottom:6px; transition:border-color 0.15s;
}
.kb-source-row:hover { border-color:#C4522A; }
.kb-source-name { font-size:13px; font-weight:500; color:#1C1510; }
.kb-source-meta { font-size:11px; color:#9C8E82; }
.kb-stat-box {
    background:#FDFAF5; border:1px solid #DDD4C4; border-radius:10px;
    padding:16px 20px; text-align:center; box-shadow:0 1px 6px rgba(60,40,20,0.06);
}
.kb-stat-num { font-size:30px; font-weight:700; color:#1C1510; line-height:1; font-family:'Noto Serif SC',serif; }
.kb-stat-label { font-size:11px; color:#9C8E82; margin-top:4px; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("bm_edit_id", None), ("bm_confirm_del", None), ("kb_confirm_clear", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── brand_data must be set BEFORE tabs so all tab blocks can use it ───────────
brand_data  = get_brand(selected_brand)
brand_label = brand_data["name"] if brand_data else selected_brand

tab_list, tab_new, tab_kb, tab_brand_analysis, tab_product, tab_mp, tab_comp = st.tabs([
    "品牌列表", "新增品牌", "知识 库", "品牌分析", "产品分析", "市场定位", "竞品快速对比"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — brand list
# ══════════════════════════════════════════════════════════════════════════════
with tab_list:
    brands = load_all_brands()

    if not brands:
        st.info("还没有任何品牌，请在「新增品牌」标签页创建第一个品牌。")
    else:
        # Use a single stable container — prevents React removeChild errors
        # when brand list length changes after delete/add
        list_container = st.container()
        with list_container:
            for bid, b in brands.items():
                color   = b.get("color", "#1A1A1A")
                initial = b["name"][0] if b.get("name") else "?"
                kb_n    = collection_count(bid)
                badge   = '<span class="demo-badge">内置</span>' if b.get("is_demo") else ""

                col_card, col_actions = st.columns([5, 2])
                with col_card:
                    kb_hint = f"{kb_n} 个文档块" if kb_n else "知识库为空"
                    st.markdown(
                        f"""
<div class="brand-card">
  <div class="brand-dot" style="background:{color}">{initial}</div>
  <div class="brand-info">
    <p class="brand-name">{b['name']}{badge}</p>
    <p class="brand-meta">{b.get('industry','')} · {b.get('focus','')} &nbsp;·&nbsp; 🗂 {kb_hint}</p>
  </div>
</div>""",
                        unsafe_allow_html=True,
                    )

                with col_actions:
                    st.write("")
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("编辑", key=f"edit_{bid}", use_container_width=True):
                            st.session_state["bm_edit_id"] = bid
                            st.session_state["bm_confirm_del"] = None
                    with btn_col2:
                        if st.session_state.get("bm_confirm_del") == bid:
                            if st.button("确认删除", key=f"del_confirm_{bid}", use_container_width=True):
                                try:
                                    delete_brand(bid)
                                    st.session_state["bm_confirm_del"] = None
                                    st.session_state["bm_edit_id"] = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))
                        else:
                            if st.button("删除", key=f"del_{bid}", use_container_width=True):
                                st.session_state["bm_confirm_del"] = bid

        # ── Inline edit form ──────────────────────────────────────────────
        edit_id = st.session_state.get("bm_edit_id")
        if edit_id and (b := get_brand(edit_id)):
            st.markdown("---")
            st.subheader(f"编辑品牌：{b['name']}")
            with st.form("edit_form"):
                new_name = st.text_input("品牌名称 *", value=b.get("name", ""))
                new_industry = st.selectbox(
                    "行业分类 *", INDUSTRY_OPTIONS,
                    index=INDUSTRY_OPTIONS.index(b["industry"])
                    if b.get("industry") in INDUSTRY_OPTIONS else 0,
                )
                new_desc  = st.text_area("品牌描述", value=b.get("description", ""), height=80)
                new_focus = st.text_input("分析重点（逗号分隔）", value=b.get("focus", ""))
                # F2 · 品牌调性枚举
                _tone_opts = ["（未设置）"] + TONE_OPTIONS
                _cur_tone = b.get("tone", "")
                new_tone = st.selectbox(
                    "品牌调性（联动内容生成风格）", _tone_opts,
                    index=_tone_opts.index(_cur_tone) if _cur_tone in _tone_opts else 0,
                )
                # F1 · 品牌词库 / 禁用词库（逗号或换行分隔）
                fc1, fc2 = st.columns(2)
                with fc1:
                    new_brand_words = st.text_area(
                        "品牌词库（优先融入文案）",
                        value="\n".join(b.get("brand_words", [])), height=100,
                        placeholder="如：灵感之茶\n悦己时刻")
                with fc2:
                    new_forbidden = st.text_area(
                        "禁用词库（文案严禁出现）",
                        value="\n".join(b.get("forbidden_words", [])), height=100,
                        placeholder="如：最便宜\n第一")
                new_color = st.color_picker("品牌主色", value=b.get("color", "#1A1A1A"))
                c1, c2 = st.columns(2)
                save   = c1.form_submit_button("保存", use_container_width=True, type="primary")
                cancel = c2.form_submit_button("取消", use_container_width=True)

            if save:
                if not new_name.strip():
                    st.error("品牌名称不能为空")
                else:
                    update_brand(edit_id, name=new_name.strip(), industry=new_industry,
                                 description=new_desc.strip(), focus=new_focus.strip(),
                                 color=new_color,
                                 tone="" if new_tone == "（未设置）" else new_tone,
                                 brand_words=parse_keywords(new_brand_words),
                                 forbidden_words=parse_keywords(new_forbidden))
                    st.session_state["bm_edit_id"] = None
                    st.success("已保存更改！")
                    st.rerun()
            if cancel:
                st.session_state["bm_edit_id"] = None
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — create new brand
# ══════════════════════════════════════════════════════════════════════════════
with tab_new:
    st.markdown(
        """
<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-left:3px solid #C4522A;border-radius:6px;padding:12px 16px;margin-bottom:18px">
  <p style="margin:0 0 4px;font-size:13px;font-weight:600;color:#1C1510">
    填写品牌信息，点击「➕ 保存并创建」完成新增</p>
  <p style="margin:0 0 4px;font-size:12px;color:#5C4F42">
    💡 这里的「品牌」= 你要优化的<b>业务主体</b>，可以是品牌、门店或业务（如：XX空调维修、张姐家政）。</p>
  <p style="margin:0;font-size:12px;color:#9C8E82">
    创建后在侧边栏切换到该主体，再到「📚 知识库」标签上传相关文档。</p>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.form("create_form", clear_on_submit=True):
        name        = st.text_input("品牌 / 主体名称 *", placeholder="例：元气森林 / XX空调维修")
        industry    = st.selectbox("行业分类 *", INDUSTRY_OPTIONS)
        description = st.text_area("品牌简介", placeholder="品牌定位、核心产品线、目标客群……", height=100)
        focus       = st.text_input("分析重点（逗号分隔）", placeholder="例：年轻化、无糖健康、渠道扩张")
        tone        = st.selectbox("品牌调性（联动内容生成风格）", ["（未设置）"] + TONE_OPTIONS)
        nc1, nc2 = st.columns(2)
        with nc1:
            cw_brand_words = st.text_area("品牌词库（选填）", height=80, placeholder="每行一个，如：灵感之茶")
        with nc2:
            cw_forbidden = st.text_area("禁用词库（选填）", height=80, placeholder="每行一个，如：最便宜")
        color       = st.color_picker("品牌主色（侧边栏标识色）", value="#1A1A1A")
        submitted   = st.form_submit_button("➕ 保存并创建品牌", type="primary", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("请填写品牌名称")
        else:
            try:
                new_id = create_brand(name.strip(), industry, description.strip(),
                                      focus.strip(), color,
                                      tone="" if tone == "（未设置）" else tone,
                                      brand_words=parse_keywords(cw_brand_words),
                                      forbidden_words=parse_keywords(cw_forbidden))
                st.success(f"品牌「{name.strip()}」已创建！")
                st.info("💡 切换到该品牌后，点「📚 知识库」标签上传文档。")
                st.rerun()
            except Exception as e:
                st.error(f"创建失败：{e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — knowledge base
# ══════════════════════════════════════════════════════════════════════════════
with tab_kb:
    kb_count = collection_count(selected_brand)
    sources  = get_sources(selected_brand)

    # ── Header row ────────────────────────────────────────────────────────
    st.markdown(
        f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
  <div>
    <p style="margin:0;font-size:18px;font-weight:700;color:#1A1A1A">
      {brand_label} · 知识库</p>
    <p style="margin:0;font-size:12px;color:#999;margin-top:2px">
      侧边栏切换品牌可管理不同品牌的知识库</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Stats row ─────────────────────────────────────────────────────────
    s1, s2, s3 = st.columns(3)
    s1.markdown(
        f'<div class="kb-stat-box"><div class="kb-stat-num">{kb_count}</div>'
        f'<div class="kb-stat-label">文档块总数</div></div>',
        unsafe_allow_html=True,
    )
    s2.markdown(
        f'<div class="kb-stat-box"><div class="kb-stat-num">{len(sources)}</div>'
        f'<div class="kb-stat-label">文件来源数</div></div>',
        unsafe_allow_html=True,
    )
    status_icon = "✅" if kb_count > 0 else "⚠️"
    status_text = "就绪" if kb_count > 0 else "空库"
    s3.markdown(
        f'<div class="kb-stat-box"><div class="kb-stat-num">{status_icon}</div>'
        f'<div class="kb-stat-label">状态：{status_text}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Existing sources（F3 · 文件详情：文件名 / 大小 / 上传时间）──────────────
    if sources:
        st.markdown("**已有文件来源**")

        def _fmt_size(n):
            try:
                n = int(n)
            except Exception:
                return "—"
            if n <= 0:
                return "—"
            for unit in ("B", "KB", "MB"):
                if n < 1024:
                    return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                n /= 1024
            return f"{n:.1f} GB"

        for src in sources:
            col_src, col_del = st.columns([6, 1])
            with col_src:
                _size = _fmt_size(src.get("size", 0))
                _added = src.get("added_at") or "—"
                st.markdown(
                    f'<div class="kb-source-row">'
                    f'<span class="kb-source-name">📄 {src["source"]}</span>'
                    f'<span class="kb-source-meta">{src["chunks"]} 块 · {_size} · 上传于 {_added}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_del:
                safe_key = src["source"].replace(".", "_").replace("/", "_")
                if st.button("🗑", key=f"del_src_{selected_brand}_{safe_key}",
                             help=f"删除 {src['source']} 的所有块"):
                    n = delete_source(selected_brand, src["source"])
                    st.success(f"已删除「{src['source']}」({n} 块)")
                    st.rerun()
    else:
        st.info("知识库为空，请通过下方方式上传品牌文档。")

    st.markdown("---")

    # ── Upload section ────────────────────────────────────────────────────
    up_tab, text_tab, url_tab, clear_tab = st.tabs(["📁 上传文件", "📝 粘贴文本", "🌐 抓取网页", "🗑 清空知识库"])

    # ── Upload files ──────────────────────────────────────────────────────
    with up_tab:
        st.markdown(
            '<p style="font-size:13px;color:#666;margin-bottom:12px">'
            "支持 PDF、Markdown（.md）、纯文本（.txt）格式，可同时上传多个文件。</p>",
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "选择文件",
            type=["pdf", "md", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded:
            if st.button("📥 导入所选文件到知识库", type="primary"):
                total_chunks = 0
                errors = []
                prog = st.progress(0)
                for i, f in enumerate(uploaded):
                    try:
                        raw = f.read()
                        if f.name.endswith(".pdf"):
                            from pypdf import PdfReader
                            reader = PdfReader(io.BytesIO(raw))
                            text = "\n".join(p.extract_text() or "" for p in reader.pages)
                        else:
                            text = raw.decode("utf-8", errors="replace")

                        if text.strip():
                            n = ingest_text(selected_brand, text, source=f.name)
                            total_chunks += n
                        else:
                            errors.append(f"{f.name}：文件内容为空")
                    except Exception as e:
                        errors.append(f"{f.name}：{e}")
                    prog.progress((i + 1) / len(uploaded))

                prog.empty()
                if total_chunks:
                    st.success(f"✅ 成功导入 {len(uploaded) - len(errors)} 个文件，共 {total_chunks} 个文档块")
                for err in errors:
                    st.warning(err)
                st.rerun()

    # ── Paste text ────────────────────────────────────────────────────────
    with text_tab:
        st.markdown(
            '<p style="font-size:13px;color:#666;margin-bottom:12px">'
            "直接粘贴品牌文案、官网介绍、报告节选等文本内容。</p>",
            unsafe_allow_html=True,
        )
        with st.form("paste_form", clear_on_submit=True):
            paste_source = st.text_input(
                "来源名称（用于标识，可自定义）",
                placeholder="例：官网介绍、2025年报、微信公众号文章",
            )
            paste_text = st.text_area(
                "粘贴文本内容",
                placeholder="将品牌相关文本粘贴到此处……",
                height=200,
            )
            paste_submit = st.form_submit_button("📥 导入到知识库", type="primary", use_container_width=True)

        if paste_submit:
            if not paste_text.strip():
                st.error("请粘贴文本内容")
            elif not paste_source.strip():
                st.error("请填写来源名称")
            else:
                try:
                    with st.spinner("正在分块并写入知识库…"):
                        n = ingest_text(selected_brand, paste_text.strip(),
                                        source=paste_source.strip())
                    st.success(f"✅ 已导入 {n} 个文档块（来源：{paste_source.strip()}）")
                    st.rerun()
                except Exception as e:
                    # 知识库（向量库）在演示/云端环境可能未启用——优雅提示而非整页崩溃
                    st.warning("⚠️ 知识库暂不可用：当前演示环境未启用本地向量库（chromadb），"
                               "文本未写入。其余功能不受影响。")
                    st.caption(f"技术详情：{type(e).__name__}: {e}")

    # ── URL scrape ────────────────────────────────────────────────────────
    with url_tab:
        st.markdown(
            '<p style="font-size:13px;color:#666;margin-bottom:4px">'
            "输入网页地址，系统自动抓取正文内容并写入知识库。"
            "适合官网、产品页、新闻稿、公众号文章等。</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-size:12px;color:#aaa;margin-bottom:16px">'
            "⚠️ 动态渲染（React/Vue SPA）页面可能抓取失败；微信文章需在浏览器打开后复制完整链接。</p>",
            unsafe_allow_html=True,
        )

        # ── 批量 URL 输入 ────────────────────────────────────────────────
        url_input = st.text_area(
            "网页地址（每行一个，可批量）",
            placeholder="https://www.brand.com/about\nhttps://www.brand.com/product",
            height=120,
            label_visibility="collapsed",
        )

        col_btn, col_preview = st.columns([2, 3])
        with col_btn:
            do_scrape = st.button("🌐 抓取并导入知识库", type="primary", use_container_width=True)
        with col_preview:
            preview_only = st.checkbox("仅预览内容，不写入知识库", value=False)

        if do_scrape and url_input.strip():
            from core.url_scraper import scrape_url, ingest_url

            raw_urls = [u.strip() for u in url_input.strip().splitlines() if u.strip()]
            if not raw_urls:
                st.warning("请输入至少一个网址")
            else:
                progress_bar = st.progress(0, text="准备中…")
                results_log = []

                for idx, url in enumerate(raw_urls):
                    progress_bar.progress(
                        (idx + 1) / len(raw_urls),
                        text=f"正在处理：{url[:60]}{'…' if len(url) > 60 else ''}",
                    )
                    if preview_only:
                        res = scrape_url(url)
                        if res["ok"]:
                            results_log.append({
                                "url": url, "ok": True,
                                "title": res["title"],
                                "preview": res["text"][:500],
                                "msg": f"预览成功（{len(res['text'])} 字）",
                            })
                        else:
                            results_log.append({"url": url, "ok": False, "msg": res["error"]})
                    else:
                        res = ingest_url(url, selected_brand)
                        if res["ok"]:
                            results_log.append({
                                "url": url, "ok": True,
                                "title": res["title"],
                                "msg": f"✅ 导入 {res['chunks_added']} 个文档块",
                            })
                        else:
                            results_log.append({"url": url, "ok": False, "msg": f"❌ {res['error']}"})

                progress_bar.empty()

                # ── 结果汇总 ────────────────────────────────────────────
                ok_count = sum(1 for r in results_log if r["ok"])
                fail_count = len(results_log) - ok_count

                if not preview_only:
                    if ok_count:
                        st.success(f"✅ 成功导入 {ok_count} 个网页到知识库")
                    if fail_count:
                        st.warning(f"⚠️ {fail_count} 个网页抓取失败")
                else:
                    st.info(f"预览完成：{ok_count} 个成功 / {fail_count} 个失败（未写入知识库）")

                for r in results_log:
                    if r["ok"]:
                        with st.expander(
                            f"✅ {r.get('title') or r['url']}　·　{r['msg']}",
                            expanded=preview_only,
                        ):
                            st.caption(f"来源：{r['url']}")
                            if "preview" in r:
                                st.text(r["preview"] + ("\n…（截断）" if len(r.get("preview", "")) == 500 else ""))
                    else:
                        st.error(f"❌ {r['url']}\n{r['msg']}")

                if not preview_only and ok_count:
                    st.rerun()

    # ── Clear KB ──────────────────────────────────────────────────────────
    with clear_tab:
        st.warning(f"⚠️ 此操作将删除「{brand_label}」知识库中的**全部 {kb_count} 个文档块**，不可恢复。")

        if not st.session_state.get("kb_confirm_clear"):
            if st.button("🗑 清空整个知识库", type="secondary"):
                st.session_state["kb_confirm_clear"] = True
                st.rerun()
        else:
            st.error("⚠️ 确认清空？此操作不可撤销。")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 确认清空", type="primary", use_container_width=True):
                    removed = clear_collection(selected_brand)
                    st.session_state["kb_confirm_clear"] = False
                    st.success(f"已清空知识库，共删除 {removed} 个文档块。")
                    st.rerun()
            with c2:
                if st.button("取消", use_container_width=True):
                    st.session_state["kb_confirm_clear"] = False
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — brand analysis
# ══════════════════════════════════════════════════════════════════════════════
with tab_brand_analysis:
    st.markdown(
        f"**当前品牌：{brand_data['name'] if brand_data else selected_brand}**　"
        "　→　在侧边栏切换品牌",
        unsafe_allow_html=False,
    )
    st.info("输入：品牌知识库　输出：定位、关键词、调性、目标客群、优势、一致性评估、风险提示")

    col_ba1, col_ba2 = st.columns([3, 1])
    with col_ba2:
        run_refcheck = st.checkbox("开启 RefCheck（合规标注）", value=False, key="brand_rc")

    if st.button("🚀 运行品牌分析", type="primary", key="run_brand"):
        with st.spinner("正在分析品牌知识库…（约 15-30 秒）"):
            try:
                result = brand_mod.run(selected_brand, run_refcheck=run_refcheck)
                st.session_state["brand_result"] = result
            except Exception as e:
                st.error(f"分析失败：{e}")

    if "brand_result" in st.session_state:
        res = st.session_state["brand_result"]
        st.markdown("---")
        maybe_show_banner(res)
        st.markdown(res["output"])

        if res.get("chunks"):
            st.markdown("**📎 主要依据来源**（知识库）")
            for c in res["chunks"][:2]:
                st.caption(f"来源：`{c['source']}` · {c['text'][:80]}...")

        if res.get("refcheck"):
            st.markdown("---")
            st.subheader("🔎 RefCheck 合规标注")
            st.markdown(res["refcheck"])

        with st.expander("📚 完整知识库引用来源", expanded=False):
            for i, c in enumerate(res["chunks"], 1):
                st.markdown(f"**[{i}] 来源：`{c['source']}`**")
                st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

        render_chat(selected_brand, res["output"], key=f"brand_{selected_brand}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — product analysis
# ══════════════════════════════════════════════════════════════════════════════
with tab_product:
    st.markdown(
        f"**当前品牌：{brand_data['name'] if brand_data else selected_brand}**　"
        "　→　在侧边栏切换品牌",
        unsafe_allow_html=False,
    )
    st.info("输入：产品名称 + 知识库　输出：功能拆解、痛点匹配、核心卖点、使用场景、价值主张")

    col_pa, col_pb = st.columns([2, 1])
    with col_pa:
        product_name = st.text_input(
            "产品名称",
            value=st.session_state.get("selected_product", ""),
            placeholder="输入要分析的产品或服务名称",
            key="product_name_input",
        )
    with col_pb:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.caption("填写品牌旗下任意产品/服务名称")

    run_rc2 = st.checkbox("开启 RefCheck", value=False, key="prod_rc")

    if st.button("🚀 运行产品分析", type="primary", key="run_product") and product_name:
        with st.spinner(f"正在分析产品「{product_name}」…"):
            try:
                result = product_mod.run(selected_brand, product_name, run_refcheck=run_rc2)
                st.session_state["product_result"] = result
            except Exception as e:
                st.error(f"分析失败：{e}")

    if "product_result" in st.session_state:
        res = st.session_state["product_result"]
        st.markdown("---")
        maybe_show_banner(res)
        st.markdown(res["output"])

        if res.get("chunks"):
            st.markdown("**📎 主要依据来源**（知识库）")
            for c in res["chunks"][:2]:
                st.caption(f"来源：`{c['source']}` · {c['text'][:80]}...")

        if res.get("refcheck"):
            st.markdown("---")
            st.subheader("🔎 RefCheck 合规标注")
            st.markdown(res["refcheck"])

        with st.expander("📚 完整知识库引用来源", expanded=False):
            for i, c in enumerate(res["chunks"], 1):
                st.markdown(f"**[{i}] 来源：`{c['source']}`**")
                st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

        render_chat(selected_brand, res["output"], key=f"product_{selected_brand}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — market positioning
# ══════════════════════════════════════════════════════════════════════════════
with tab_mp:
    st.markdown(
        f"**当前品牌：{brand_data['name'] if brand_data else selected_brand}**　→　在侧边栏切换品牌"
    )
    st.markdown(
        '<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-left:3px solid #C4522A;border-radius:6px;'
        'padding:12px 16px;margin:0 0 18px;font-size:13px;color:#7B8299;line-height:1.65">'
        '<strong style="color:#1C1510">输入</strong>：品牌知识库&nbsp;&nbsp;'
        '<strong style="color:#1C1510">输出</strong>：STP 市场细分 / 目标市场 / 定位陈述 + SWOT 分析<br>'
        '结论标注 ✅ 官方事实 / ⚠️ AI推断 / ❓ 待复核</div>',
        unsafe_allow_html=True,
    )

    _, col_rc_mp = st.columns([3, 1])
    with col_rc_mp:
        run_refcheck_mp = st.checkbox("开启 RefCheck", value=False, key="mp_rc")

    if st.button("🚀 运行市场定位分析", type="primary", key="run_mp"):
        with st.spinner("正在生成市场定位分析…（约 20-35 秒）"):
            try:
                result = mp_mod.run(selected_brand, run_refcheck=run_refcheck_mp)
                st.session_state["mp_result"] = result
            except Exception as e:
                st.error(f"分析失败：{e}")

    if "mp_result" in st.session_state:
        res = st.session_state["mp_result"]
        st.markdown("---")
        maybe_show_banner(res)
        output = res["output"]
        if "## SWOT" in output:
            stp_part, swot_part = output.split("## SWOT", 1)
            col_stp, col_swot = st.columns(2)
            with col_stp:
                st.markdown(stp_part)
            with col_swot:
                st.markdown("## SWOT" + swot_part)
        else:
            st.markdown(output)
        if res.get("refcheck"):
            st.markdown("---")
            st.subheader("🔎 RefCheck 合规标注")
            st.markdown(res["refcheck"])
        with st.expander("📚 知识库引用来源", expanded=False):
            for i, c in enumerate(res.get("chunks", []), 1):
                st.markdown(f"**[{i}] 来源：`{c['source']}`**")
                st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — competitor analysis
# ══════════════════════════════════════════════════════════════════════════════
with tab_comp:
    # 方案A：本 tab 定位为「一次性快速对比快照」；常态化监控请用竞品情报仓库
    st.markdown(
        '<div style="background:#EEF4FB;border:1px solid #C9DDF0;border-left:3px solid #2B6CB0;'
        'border-radius:6px;padding:10px 14px;margin-bottom:10px;font-size:13px;color:#1E4E8C">'
        '🔭 <b>这里是「快速对比快照」</b>：拿主品牌与单个竞品做一次性 AI 对标解读。<br>'
        '如需 <b>7×24 常态化竞品监控</b>（六维情报 / 异动预警 / 历史归档 / 多品牌对标），'
        '请使用左侧菜单的 <b>竞品情报仓库</b>。</div>',
        unsafe_allow_html=True)
    st.page_link("pages/17_竞品情报.py", label="🔭 打开竞品情报仓库（常态化监控）", icon="🔭")

    # 原生组件替代 unsafe_allow_html，避免相邻元素 stale DOM
    st.info("分析维度：品牌定位 · 产品卖点 · 内容策略 · AI/GEO 可见度 · 策略建议　|　"
            "结论标注 ✅ 官方事实 / ⚠️ AI推断，禁止对竞品作任何负面评价。")

    competitors = {k: v for k, v in BRAND_DISPLAY_NAMES.items() if k != selected_brand}
    comp_keys = list(competitors.keys())

    if not comp_keys:
        st.info("至少需要两个品牌才能进行竞品分析，请先在「新增品牌」中添加更多品牌。")
    else:
        # 主品牌标题用原生 st.subheader（不含任何 HTML），且整块禁用 unsafe_allow_html，
        # 从根上消除 tabs+columns 下相邻 HTML 块引发的旧品牌标题残留
        with st.container():
            col_brand_c, col_vs_c, col_comp_c = st.columns([2, 0.3, 2])
            with col_brand_c:
                st.caption("主品牌")
                # 禁用 selectbox 渲染主品牌，「不设 key」——每次运行都用当前 options，
                # 始终显示当前品牌（与能正常更新的 keyword 框同机制）。
                # 切忌用品牌后缀 key：那会产生孤儿 widget 导致旧品牌标题 stale DOM 残留。
                st.selectbox(
                    "主品牌",
                    [selected_brand],
                    format_func=lambda k: BRAND_DISPLAY_NAMES.get(k, k),
                    disabled=True,
                    label_visibility="collapsed",
                )
            with col_vs_c:
                st.write("")
                st.markdown("**vs**")
            with col_comp_c:
                st.markdown("**选择竞品**")
                competitor = st.selectbox(
                    "竞品",
                    comp_keys,
                    format_func=lambda k: BRAND_DISPLAY_NAMES[k],
                    label_visibility="collapsed",
                    key="comp_select",
                )

            if st.button("🚀 运行竞品对标分析", type="primary", key="run_comp"):
                with st.spinner(f"正在对标分析 {brand_label} vs {BRAND_DISPLAY_NAMES[competitor]}…（约 20-35 秒）"):
                    try:
                        result = comp_mod.run(selected_brand, competitor)
                        result["_brand"] = selected_brand
                        st.session_state["comp_result"] = result
                        st.session_state["comp_pair"] = (selected_brand, competitor)
                    except Exception as e:
                        st.error(f"分析失败：{e}")

            # 主品牌切换时立即清除旧竞品分析（双重保险：_brand 字段 + comp_pair）
            if st.session_state.get("comp_result", {}).get("_brand") != selected_brand:
                st.session_state.pop("comp_result", None)
                st.session_state.pop("comp_pair", None)

            if "comp_result" in st.session_state:
                pair = st.session_state.get("comp_pair", (None, None))
                if pair[1] != competitor:
                    stored_comp = BRAND_DISPLAY_NAMES.get(pair[1], pair[1]) if pair[1] else "?"
                    st.info(f"当前显示的是与「{stored_comp}」的分析，如需更新请重新运行")

                res = st.session_state["comp_result"]
                maybe_show_banner(res)
                st.markdown("---")
                render_four_blocks(res["output"])
                render_source_meta(res.get("chunks", []))
                st.markdown("---")
                send_col, _ = st.columns([2, 5])
                with send_col:
                    if st.button("📤 送往合规审查", key="comp_to_compliance", use_container_width=True):
                        st.session_state["content_for_compliance"] = res["output"]
                        st.switch_page("pages/8_合规卫士.py")
                render_disclaimer()
