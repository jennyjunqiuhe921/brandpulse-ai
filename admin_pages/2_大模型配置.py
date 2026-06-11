"""S5 2.5 大模型统一配置中心（运营侧）。"""
import streamlit as st
from utils.admin_sidebar import render
from config import platform_store as PS
from db.models import MODEL_TYPES

render()

st.markdown('<div class="page-header"><h1>大模型统一配置中心</h1>'
            '<p class="page-desc">统一接入文本/生图/生视频大模型，连通性测试与状态管理。'
            'API 密钥仅存掩码，不落明文。</p></div>', unsafe_allow_html=True)

with st.expander("➕ 接入新模型"):
    with st.form("new_model"):
        c1, c2 = st.columns(2)
        name = c1.text_input("模型名称")
        mtype = c2.selectbox("模型类型", MODEL_TYPES)
        api_base = st.text_input("API 地址", placeholder="https://api.example.com/v1")
        api_key = st.text_input("API 密钥", type="password")
        note = st.text_input("备注", placeholder="如：主力文本模型")
        if st.form_submit_button("接入", type="primary"):
            if name.strip() and api_base.strip():
                PS.add_model(name, mtype, api_base, api_key, note)
                st.success("已接入，请做连通性测试后启用")
                st.rerun()
            else:
                st.warning("请填写模型名称与 API 地址")

models = PS.list_models()
st.markdown(f"#### 已接入模型（{len(models)}）")
if not models:
    st.info("暂无模型。演示运行时系统使用内置 Demo 模型，无需配置即可体验。")

_sc = {"未启用": "#9C8E82", "测试中": "#F9A825", "正常": "#2E7D32", "已停用": "#C62828"}
for m in models:
    with st.container(border=True):
        c1, c2 = st.columns([4, 2])
        with c1:
            st.markdown(
                f'**{m["name"]}** · {m["model_type"]}　'
                f'<span style="background:{_sc.get(m["status"],"#999")};color:#fff;'
                f'padding:1px 8px;border-radius:8px;font-size:11px">{m["status"]}</span>',
                unsafe_allow_html=True)
            st.caption(f"{m['api_base']} · {m['note'] or ''}")
        with c2:
            bc = st.columns(3)
            with bc[0]:
                if st.button("测试", key=f"ts_{m['id']}", use_container_width=True):
                    PS.set_model_status(m["id"], "测试中")
                    st.toast("连通性测试中…（演示）")
                    PS.set_model_status(m["id"], "正常")
                    st.rerun()
            with bc[1]:
                if m["status"] == "正常":
                    if st.button("停用", key=f"sp_{m['id']}", use_container_width=True):
                        PS.set_model_status(m["id"], "已停用"); st.rerun()
                else:
                    if st.button("启用", key=f"en_{m['id']}", use_container_width=True):
                        PS.set_model_status(m["id"], "正常"); st.rerun()
            with bc[2]:
                if st.button("删除", key=f"dl_{m['id']}", use_container_width=True):
                    PS.delete_model(m["id"]); st.rerun()
