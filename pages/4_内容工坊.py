import streamlit as st
import sys
import re as _re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.content_generator as content_mod
import modules.product_link_extractor as link_mod
from modules.compliance_precheck import precheck
import config.content_tasks as ct
from utils.result_banner import maybe_show_banner
from utils.prd_components import render_four_blocks, render_disclaimer, review_gate
from prompts.content_generation_prompt import PLATFORM_GUIDES, DEFAULT_PLATFORMS
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="内容生成工厂 — PinSight AI", page_icon="✍️", layout="wide")
brand = render_sidebar()

# ── 表单字段默认值（widget key 统一管理，避免 value/session_state 双绑冲突）──────
_DEFAULTS = {
    "cw_mode": "快速模式",
    "cw_link": "",
    "cw_product_name": "",
    "cw_selling_points": "",
    "cw_goal": "",
    "cw_tone": "酷/有态度",
    "cw_word_limit": "不限",
    "cw_region": "",
    "cw_platforms": list(DEFAULT_PLATFORMS),
    "cw_versions": 3,
}
for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

# 「复制配置」预填：在所有 widget 实例化之前应用，规避修改已实例化 widget 报错
if "cw_prefill" in st.session_state:
    _pf = st.session_state.pop("cw_prefill")
    for _k in _DEFAULTS:
        short = _k[3:]  # 去掉 cw_ 前缀
        if short in _pf:
            st.session_state[_k] = _pf[short]

# 品牌切换时清掉旧生成结果
if st.session_state.get("_cw_last_brand") != brand:
    st.session_state.pop("content_result", None)
    st.session_state.pop("cw_selected_versions", None)
    st.session_state["_cw_last_brand"] = brand

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">内容工坊</h1>
  <p class="page-desc">品牌锚定 · 场景分层 · 合规预检 三层创作法，多平台内容矩阵一键生成，人工复核后可用</p>
</div>
""",
    unsafe_allow_html=True,
)

tab_gen, tab_tasks = st.tabs(["✍️ 内容生成", "📋 文案任务列表"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — 内容生成
# ══════════════════════════════════════════════════════════════════════════════
with tab_gen:
    # ── B1 · 快速 / 高级 双模式 ────────────────────────────────────────────────
    mode = st.radio(
        "创作模式",
        ["快速模式", "高级模式"],
        key="cw_mode",
        horizontal=True,
        help="快速模式仅需 3 个核心字段；高级模式开放全部参数（语气/字数/地域/平台/版本数）",
    )
    advanced = mode == "高级模式"

    # ── B2 · 商品链接自动提取（放在产品名 widget 之前，便于回填）──────────────
    with st.expander("🔗 输入商品链接（选填）· 自动提取产品信息", expanded=False):
        lc1, lc2 = st.columns([4, 1])
        with lc1:
            st.text_input(
                "商品链接",
                key="cw_link",
                placeholder="粘贴淘宝 / 京东 / 拼多多等商品页 URL",
                label_visibility="collapsed",
            )
        with lc2:
            do_extract = st.button("📥 提取", use_container_width=True)
        if do_extract:
            try:
                info = link_mod.extract(st.session_state["cw_link"])
                if info.get("product_name"):
                    st.session_state["cw_product_name"] = info["product_name"]
                if info.get("confidence") == "low":
                    st.warning(info.get("note", "提取置信度较低，请手动补全。"))
                else:
                    st.success(f"已从「{info['source']}」提取：{info['product_name']}")
            except link_mod.ExtractError as e:
                st.error(f"提取失败：{e}")
            except Exception as e:
                st.error(f"提取出错：{e}")

    # ── 核心字段（快速模式 3 个）──────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        product_name = st.text_input("产品名称 *", key="cw_product_name",
                                     placeholder="输入要推广的产品或服务名称")
        selling_points = st.text_area("核心卖点（1-3 条，每行一条）", key="cw_selling_points",
                                      placeholder="例如：\n0 添加蔗糖\n冷萃工艺\n限定联名款", height=90)
    with c2:
        goal = st.text_input("推广目标", key="cw_goal",
                             placeholder="例如：新品上市、节日限定、品牌活动")
        if advanced:
            tone_key = st.selectbox("品牌语气", ["酷/有态度", "温柔/精致", "亲民/接地气"], key="cw_tone")
        else:
            tone_key = st.session_state["cw_tone"]

    # ── B1 · 高级模式额外字段 ──────────────────────────────────────────────────
    if advanced:
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            st.selectbox("字数限制", ["不限", "50字以内", "100字以内", "200字以内", "300字以内"],
                         key="cw_word_limit")
        with ac2:
            st.text_input("地域限定（选填）", key="cw_region", placeholder="例如：华东 / 成都")
        with ac3:
            st.slider("每平台版本数", 2, 5, key="cw_versions",
                      help="PRD 要求每平台输出 3-5 个差异化版本")
        platforms = st.multiselect("目标平台（可多选）", options=list(PLATFORM_GUIDES.keys()),
                                    key="cw_platforms")
    else:
        # 快速模式：平台用默认，版本数固定 3
        platforms = st.session_state["cw_platforms"]
        st.caption(f"📌 快速模式默认平台：{' · '.join(platforms)}（切换高级模式可自定义）")

    word_limit = "" if st.session_state["cw_word_limit"] == "不限" else st.session_state["cw_word_limit"]
    region = st.session_state["cw_region"] if advanced else ""
    versions = st.session_state["cw_versions"] if advanced else 3

    if not platforms:
        st.warning("请至少选择一个目标平台")

    # ── 生成按钮 ────────────────────────────────────────────────────────────────
    if st.button("🚀 生成内容矩阵", type="primary",
                 disabled=not platforms or not product_name):
        with st.spinner(f"正在为「{product_name}」生成 {len(platforms)} 个平台 × {versions} 版本的内容…（约 25-50 秒）"):
            try:
                result = content_mod.run(
                    brand, product_name, platforms, tone_key, goal,
                    selling_points=selling_points,
                    versions_per_platform=versions,
                    word_limit=word_limit,
                    region=region,
                )
                st.session_state["content_result"] = result
                st.session_state["content_for_compliance"] = result["output"]
                st.session_state.pop("reviewed_content", None)
                st.session_state.pop("cw_selected_versions", None)
            except Exception as e:
                st.error(f"生成失败：{e}")

    # ── 结果展示 ────────────────────────────────────────────────────────────────
    if "content_result" in st.session_state:
        res = st.session_state["content_result"]
        st.markdown("---")
        maybe_show_banner(res)

        raw_output = res["output"]

        # 拆出末尾的「AI 输出内容分类」章节
        split_marker = "---\n\n### AI 输出内容分类"
        classification_part = ""
        body = raw_output
        if split_marker in raw_output:
            body, tail = raw_output.split(split_marker, 1)
            classification_part = split_marker + tail

        # ── B5 · 合规预检（即时关键词扫描）────────────────────────────────────
        pc = precheck(body)
        level_render = {"高": st.error, "中": st.warning, "低": st.success}
        level_render[pc["level"]](f"🛡️ 合规预检风险等级：**{pc['level']}** — {pc['summary']}")
        if pc["high"]:
            st.caption("⚠️ 高风险词：" + "、".join(pc["high"]))
        if pc["med"]:
            st.caption("⚠️ 需核实表述：" + "、".join(pc["med"]))

        st.markdown("---")

        # ── 解析平台 → 版本 ───────────────────────────────────────────────────
        generated_platforms = res.get("platforms", platforms)
        plat_sections = [s.strip() for s in _re.split(r"(?=^###\s)", body, flags=_re.M) if s.strip()]

        selected = st.session_state.setdefault("cw_selected_versions", {})

        if plat_sections:
            tab_labels = [f"📄 {p}" for p in generated_platforms]
            ptabs = st.tabs(tab_labels) if len(tab_labels) > 1 else [st.container()]
            for i, ptab in enumerate(ptabs):
                with ptab:
                    section = plat_sections[i] if i < len(plat_sections) else ""
                    plat_name = generated_platforms[i] if i < len(generated_platforms) else f"平台{i+1}"
                    # 按 #### 版本 拆分
                    versions_raw = [v.strip() for v in _re.split(r"(?=^####\s)", section, flags=_re.M) if v.strip()]
                    # 第一段可能是平台标题，过滤掉不含 #### 的
                    ver_blocks = [v for v in versions_raw if v.startswith("####")]
                    if not ver_blocks:
                        st.markdown(section)
                    else:
                        for vi, vb in enumerate(ver_blocks):
                            is_sel = selected.get(plat_name) == vi
                            with st.container(border=True):
                                st.markdown(vb)
                                bc1, bc2 = st.columns([1, 4])
                                with bc1:
                                    if is_sel:
                                        st.success("✅ 已选用")
                                    else:
                                        if st.button("选用此版本", key=f"sel_{i}_{vi}"):
                                            selected[plat_name] = vi
                                            st.rerun()
        else:
            st.markdown(body)

        st.markdown("---")

        # ── B4 · 保存为文案任务 ────────────────────────────────────────────────
        sc1, sc2 = st.columns([2, 3])
        with sc1:
            if st.button("💾 保存为文案任务", use_container_width=True):
                meta = res.get("_meta", {})
                ct.add_task(
                    brand,
                    title=meta.get("product_name") or "未命名文案",
                    platforms=generated_platforms,
                    meta=meta,
                    output=raw_output,
                )
                st.success("已保存到「文案任务列表」（状态：草稿）")
        with sc2:
            st.caption("保存后可在「文案任务列表」标签页跟踪 草稿→待审批→已通过→已归档 流程")

        # A1 · 分类区块
        if classification_part:
            render_four_blocks(classification_part)

        # A4 · 人工复核门控
        reviewed = review_gate("content")

        # ── B5 · 导出门控（高风险 + 未复核 双重拦截）────────────────────────────
        st.markdown("---")
        can_export = reviewed and pc["can_export"]
        col_a, col_b = st.columns([2, 2])
        with col_a:
            if not pc["can_export"]:
                st.error("🚫 存在高风险词，请修改后重新生成方可导出/送审")
            elif not reviewed:
                st.info("🔒 完成人工复核后可送往合规审查")
            else:
                st.success("✅ 已复核且无高风险，可送审/导出")
        with col_b:
            if st.button("🛡️ 一键送往合规审查", type="primary",
                         use_container_width=True, disabled=not can_export):
                st.session_state["content_for_compliance"] = res["output"]
                st.session_state["auto_run_compliance"] = False
                st.switch_page("pages/8_合规卫士.py")

        with st.expander("📋 查看完整输出", expanded=False):
            st.text_area("完整文本（可复制）", value=res["output"], height=300)

        # A3 · 免责声明
        render_disclaimer()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — 文案任务列表（B4）
# ══════════════════════════════════════════════════════════════════════════════
with tab_tasks:
    st.caption("文案完整生命周期：草稿 → 待审批 → 已通过 → 已归档。仅显示当前品牌的任务。")

    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        f_status = st.selectbox("按状态筛选", ["全部"] + ct.STATUS_FLOW, key="cw_f_status")
    with fc2:
        all_plats = ["全部"] + list(PLATFORM_GUIDES.keys())
        f_plat = st.selectbox("按平台筛选", all_plats, key="cw_f_plat")
    with fc3:
        show_arch = st.checkbox("含已归档", value=True, key="cw_f_arch")

    tasks = ct.list_tasks(
        brand_key=brand,
        status=None if f_status == "全部" else f_status,
        platform=None if f_plat == "全部" else f_plat,
        include_archived=show_arch,
    )

    if not tasks:
        st.info("暂无文案任务。在「内容生成」标签页生成内容后点击「保存为文案任务」即可加入列表。")
    else:
        _status_badge = {"草稿": "📝", "待审批": "⏳", "已通过": "✅", "已归档": "📦"}
        for t in tasks:
            badge = _status_badge.get(t["status"], "•")
            with st.container(border=True):
                hc1, hc2 = st.columns([4, 2])
                with hc1:
                    st.markdown(f"**{badge} {t['title']}** · `{t['status']}`")
                    st.caption(f"平台：{' / '.join(t.get('platforms', [])) or '—'} ｜ 创建：{t.get('created_at','')}")
                with hc2:
                    nxt = ct.STATUS_NEXT.get(t["status"])
                    bcols = st.columns(3)
                    with bcols[0]:
                        if nxt and st.button(f"→{nxt}", key=f"adv_{t['id']}", use_container_width=True):
                            ct.advance(t["id"])
                            st.rerun()
                    with bcols[1]:
                        if st.button("复制配置", key=f"copy_{t['id']}", use_container_width=True):
                            st.session_state["cw_prefill"] = t.get("meta", {})
                            st.success("已载入到「内容生成」表单，请切到该标签查看")
                            st.rerun()
                    with bcols[2]:
                        if st.button("删除", key=f"del_{t['id']}", use_container_width=True):
                            ct.delete_task(t["id"])
                            st.rerun()
                with st.expander("查看内容", expanded=False):
                    st.text_area("文案内容", value=t.get("output", ""), height=200,
                                 key=f"ta_{t['id']}", disabled=True)
