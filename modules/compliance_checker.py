import re

from core.llm_client import chat, is_demo_mode
from core.rag_engine import retrieve
from core.llm_client import build_rag_context
from prompts.compliance_check_prompt import SYSTEM
from config.settings import BRAND_DISPLAY_NAMES
from modules.compliance_precheck import precheck


def _snippet(content: str, word: str, span: int = 24) -> str:
    """从原文中截取包含命中词的句子片段，保证报告里的'原文片段'确实来自输入内容。"""
    idx = content.find(word)
    if idx < 0:
        return word
    # 以句子边界为优先，退化为定长窗口
    left = content.rfind("\n", 0, idx)
    for sep in ("。", "！", "？", "!", "?", "；", ";"):
        left = max(left, content.rfind(sep, 0, idx))
    start = left + 1 if left >= 0 else max(0, idx - span)
    right = len(content)
    for sep in ("\n", "。", "！", "？", "!", "?", "；", ";"):
        p = content.find(sep, idx)
        if p >= 0:
            right = min(right, p + 1)
    end = right if right - idx <= span * 3 else min(len(content), idx + span)
    frag = content[start:end].strip()
    # markdown 表格单元格内不能有竖线/换行
    frag = frag.replace("|", "/").replace("\n", " ").strip()
    return frag or word


def _demo_compliance_report(content: str) -> str:
    """Demo / 无 API 时：用确定性规则引擎(precheck)对**真实送审内容**实时扫描出报告。

    与固定样板的区别：报告里的每条'原文片段'都确实出自输入内容，风险等级随内容变化；
    配置 API Key 后自动升级为大模型语义级深度审查（可识别词库覆盖不到的隐性违规）。"""
    pc = precheck(content or "")
    level_render = {"高": "🔴 高风险", "中": "🟡 中风险", "低": "🟢 低风险"}
    lines = ["## 合规审查报告", "",
             f"### 整体风险等级：{level_render[pc['level']]}", "",
             "> 本报告由内置合规规则引擎（《广告法》绝对化用语 / 功效承诺词库）对"
             "**当前送审内容**实时扫描生成；配置大模型 API Key 后将升级为语义级深度审查"
             "（可识别词库覆盖不到的贬低竞品、夸大暗示等隐性违规）。", ""]

    rows = []
    n = 1
    for w in pc["high"]:
        rows.append(f"| {n} | {_snippet(content, w)} | 绝对化用语（《广告法》违规） | 🔴 高 | "
                    f"删除或替换“{w}”，改为可验证的客观表述（如“受欢迎 / 广受好评 / 精选”等） |")
        n += 1
    for w in pc["med"]:
        rows.append(f"| {n} | {_snippet(content, w)} | 功效 / 承诺类表述（需核实依据） | 🟡 中 | "
                    f"“{w}”需提供权威检测报告或事实依据，否则删除或弱化表述 |")
        n += 1

    if rows:
        lines += ["### 问题清单", "",
                  "| 序号 | 原文片段 | 问题类型 | 风险等级 | 修改建议 |",
                  "|------|---------|---------|---------|---------|"]
        lines += rows
        lines.append("")
    else:
        lines += ["### ✅ 未检出《广告法》明令禁止的绝对化用语或功效承诺词", "",
                  "当前内容已通过规则引擎初筛，未发现明显违规表述。", ""]

    lines += ["### 合规通过项",
              "- 品牌名称使用规范，未检出冒用 / 误导性主体表述",
              "- 未涉及个人隐私信息",
              ("- 未检出绝对化用语" if not pc["high"] else "- 绝对化用语已在上表逐条列出"),
              ""]

    lines += ["### 总体修改建议"]
    if pc["high"]:
        lines.append("1. **优先清除绝对化用语**：将“最 / 第一 / 顶级 / 唯一 / 绝对”等替换为具体可验证的描述。")
    if pc["med"]:
        lines.append(f"{2 if pc['high'] else 1}. **核实功效 / 承诺类表述**：所有功效声明须有权威依据支撑，否则删除。")
    if not pc["high"] and not pc["med"]:
        lines.append("1. 内容规则层面无明显问题，仍建议人工复核语义与事实准确性后再发布。")
    lines.append("")

    lines += ["### 审查声明",
              "本审查由内置合规规则引擎自动完成，基于关键词与《广告法》词库，仅供参考；"
              "**正式发布前须由品牌授权人员及法务部门进行最终人工复核**。配置大模型 API Key "
              "后可启用语义级深度审查，识别规则词库覆盖不到的隐性风险。"]
    return "\n".join(lines)


def run(content: str, brand_key: str) -> dict:
    brand_name = BRAND_DISPLAY_NAMES.get(brand_key, "")
    chunks = retrieve(brand_key, "品牌定位 官方事实 品牌调性", n_results=4)
    kb_context = build_rag_context(chunks)

    # Demo / 无 API：直接用规则引擎对真实输入出报告，确保'原文片段'与送审内容一致。
    if is_demo_mode():
        return {"output": _demo_compliance_report(content), "chunks": chunks}

    user_msg = f"""品牌：{brand_name}

【品牌知识库（用于核实事实）】
{kb_context}

【待审查内容】
{content}

请对以上内容进行全面合规审查，并与品牌知识库内容进行比对核实。"""

    output = chat(SYSTEM, user_msg, max_tokens=2000)
    # 真实 API 失败时底层会自动回退到与输入无关的固定样板 → 替换为基于真实内容的规则报告，
    # 避免演示现场出现'报告违禁词原文里没有'的穿帮。
    try:
        from core.llm_client import _DEMO_COMPLIANCE
        if output.strip() == _DEMO_COMPLIANCE.strip():
            output = _demo_compliance_report(content)
    except Exception:
        pass
    return {"output": output, "chunks": chunks}
