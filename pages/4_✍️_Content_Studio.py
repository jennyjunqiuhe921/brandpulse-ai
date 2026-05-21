import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.content_generator as content_mod
from prompts.content_generation_prompt import PLATFORM_GUIDES

st.set_page_config(page_title="内容生成工厂 — BrandPulse AI", page_icon="✍️", layout="wide")
brand = render_sidebar()

st.title("✍️ 内容生成工厂")
st.caption("任务卡4：多平台内容矩阵生成")

PRODUCT_DEFAULTS = {
    "heytea": "多肉葡萄",
    "nayuki": "霸气玉油柑",
    "chapanda": "杨枝甘露",
}

col1, col2 = st.columns(2)
with col1:
    product_name = st.text_input(
        "产品名称 *",
        value=PRODUCT_DEFAULTS.get(brand, ""),
        placeholder="输入要推广的产品",
    )
    goal = st.text_input(
        "推广目标",
        value="夏日新品上线，提升年轻消费者种草转化",
        placeholder="例如：新品上市、节日限定、品牌活动",
    )

with col2:
    tone_key = st.selectbox(
        "品牌语气",
        options=["酷/有态度", "温柔/精致", "亲民/接地气"],
        index={"heytea": 0, "nayuki": 1, "chapanda": 2}.get(brand, 0),
    )
    platforms = st.multiselect(
        "目标平台（可多选）",
        options=list(PLATFORM_GUIDES.keys()),
        default=["小红书种草文案", "抖音/短视频脚本", "海报标题组合"],
    )

if not platforms:
    st.warning("请至少选择一个目标平台")

if st.button("🚀 生成内容矩阵", type="primary", disabled=not platforms or not product_name):
    with st.spinner(f"正在为「{product_name}」生成 {len(platforms)} 个平台的内容...（约 20-40 秒）"):
        try:
            result = content_mod.run(brand, product_name, platforms, tone_key, goal)
            st.session_state["content_result"] = result
            st.session_state["content_for_compliance"] = result["output"]
        except Exception as e:
            st.error(f"生成失败：{e}")

if "content_result" in st.session_state:
    res = st.session_state["content_result"]
    st.markdown("---")

    generated_platforms = res.get("platforms", platforms)
    sections = res["output"].split("---")

    if len(sections) > 1 and len(generated_platforms) > 0:
        tabs = st.tabs([f"📄 {p}" for p in generated_platforms])
        for i, (tab, section) in enumerate(zip(tabs, sections)):
            with tab:
                st.markdown(section.strip())
    else:
        st.markdown(res["output"])

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.success("✅ 内容生成完成，请人工复核后使用")
    with col_b:
        if st.button("🛡️ 发送至合规审查", type="secondary"):
            st.session_state["content_for_compliance"] = res["output"]
            st.info("已保存到会话，请前往 **7_合规审查** 页面进行审查")

    with st.expander("📋 查看完整输出", expanded=False):
        st.text_area("完整文本（可复制）", value=res["output"], height=300)

    with st.expander("⚠️ 使用说明", expanded=False):
        st.markdown("""
- 所有生成内容须经品牌授权人员**人工复核**后方可发布
- 标注 `[创意内容]` 的部分为 AI 创意发挥，需核实是否符合品牌调性
- 标注 `[品牌信息]` 的部分来自知识库，需核实信息是否仍然准确
- 建议在「合规审查」模块对生成内容进行进一步合规扫描
""")
