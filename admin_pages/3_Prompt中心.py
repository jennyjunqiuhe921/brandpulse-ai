"""S5 2.6 Prompt 统一管理中心（运营侧）— 6 分类 / 版本 / Diff / 回滚 / 启停。"""
import streamlit as st
from utils.admin_sidebar import render
from config import platform_store as PS
from db.models import PROMPT_CATEGORIES

render()

st.markdown('<div class="page-header"><h1>Prompt 统一管理中心</h1>'
            '<p class="page-desc">六大业务分类的提示词管理：新建/编辑/版本管理(Diff/回滚)/启用停用。'
            '同一分类仅一条可启用，AI 网关自动加载已启用版本。</p></div>', unsafe_allow_html=True)

with st.expander("➕ 新建 Prompt"):
    with st.form("new_prompt"):
        c1, c2 = st.columns(2)
        name = c1.text_input("名称")
        cat = c2.selectbox("所属分类", PROMPT_CATEGORIES)
        model_name = st.text_input("关联模型", value="默认文本模型")
        content = st.text_area("Prompt 正文", height=140)
        if st.form_submit_button("保存为草稿", type="primary"):
            if name.strip() and content.strip():
                PS.add_prompt(name, cat, model_name, content, created_by="platform")
                st.success("已保存为草稿")
                st.rerun()
            else:
                st.warning("请填写名称与正文")

fcat = st.selectbox("分类筛选", ["全部"] + PROMPT_CATEGORIES)
prompts = PS.list_prompts(category=fcat)

for p in prompts:
    sc = "#2E7D32" if p["status"] == "已启用" else "#9C8E82"
    with st.container(border=True):
        st.markdown(
            f'**{p["name"]}** · {p["category"]} · v{p["version"]}　'
            f'<span style="background:{sc};color:#fff;padding:1px 8px;border-radius:8px;'
            f'font-size:11px">{p["status"]}</span>', unsafe_allow_html=True)
        st.caption(f"关联模型：{p['model_name']} · 更新 {p['updated_at']}")
        with st.expander("查看 / 编辑 / 版本"):
            st.text_area("当前正文", value=p["content"], height=120,
                         key=f"view_{p['id']}", disabled=True)
            new_content = st.text_area("编辑（保存将新建版本）", value=p["content"],
                                       height=120, key=f"edit_{p['id']}")
            bc = st.columns(4)
            with bc[0]:
                if st.button("新建版本", key=f"nv_{p['id']}"):
                    if new_content != p["content"]:
                        PS.new_version(p["id"], new_content); st.rerun()
                    else:
                        st.toast("内容未变更")
            with bc[1]:
                if p["status"] != "已启用":
                    if st.button("启用", key=f"en_{p['id']}"):
                        PS.enable_prompt(p["id"]); st.rerun()
                else:
                    if st.button("停用", key=f"di_{p['id']}"):
                        PS.disable_prompt(p["id"]); st.rerun()
            # 版本历史 + Diff + 回滚
            if p["history"]:
                with bc[2]:
                    vers = [h["version"] for h in p["history"]]
                    tov = st.selectbox("回滚到", vers, key=f"rb_{p['id']}")
                with bc[3]:
                    if st.button("回滚", key=f"rbb_{p['id']}"):
                        PS.rollback_prompt(p["id"], tov); st.rerun()
                last = p["history"][-1]
                st.markdown(f"**版本 Diff**（v{last['version']} → v{p['version']}）：", unsafe_allow_html=True)
                st.markdown(
                    f'<div style="background:#fff;border:1px solid #DDD4C4;border-radius:6px;'
                    f'padding:8px;font-size:13px">{PS.diff_text(last["content"], p["content"])}</div>',
                    unsafe_allow_html=True)
