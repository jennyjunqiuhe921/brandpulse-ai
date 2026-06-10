# rev: force resync on Streamlit Cloud
from __future__ import annotations


def parse_keywords(text: str) -> list[str]:
    """C1 · 同时支持逗号（中英文）与换行分隔的批量关键词解析。"""
    if not text:
        return []
    import re
    parts = re.split(r"[,，\n]+", text)
    seen, out = set(), []
    for p in parts:
        w = p.strip()
        if w and w not in seen:
            seen.add(w)
            out.append(w)
    return out


def build_geo_system(
    brand_name: str,
    questions: list[str],
    brand_words: list[str] | None = None,
    product_words: list[str] | None = None,
    category_words: list[str] | None = None,
    competitors: list[str] | None = None,
    region: str = "全国",
) -> str:
    """C1-C5 · 构造 GEO 分析 system prompt（关键词组 + 竞品对标 + 地域 + E-E-A-T）。"""
    n = len(questions)
    questions_list = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

    kw_lines = []
    if brand_words:
        kw_lines.append(f"- 品牌词：{ '、'.join(brand_words) }")
    if product_words:
        kw_lines.append(f"- 产品词：{ '、'.join(product_words) }")
    if category_words:
        kw_lines.append(f"- 品类词：{ '、'.join(category_words) }")
    kw_block = ("\n【结构化关键词组（分析须覆盖这三组词的 AI 可见度）】\n" + "\n".join(kw_lines)) if kw_lines else ""

    comp_block = ""
    if competitors:
        comp_block = (
            "\n【竞品对标（须输出本品 vs 以下竞品的 AI 可见度对比）】\n- "
            + "、".join(competitors)
        )

    if region and region != "全国":
        region_block = (
            f"\n【监测地域：{region}】\n"
            f"分析须结合「{region}」本地用户的搜索语境、本地化信息需求与区域竞争格局，"
            f"补强建议应包含面向该地域的本地内容渠道。"
        )
    else:
        region_block = "\n【监测地域：全国】分析面向全国通用语境。"

    return f"""你是一名 GEO（生成式引擎优化/AI搜索可见度）分析专家。

任务：针对品牌 {brand_name}，模拟真实用户向 AI 搜索提问，分析该品牌在 AI 回答中的可见度和准确性。
{kw_block}{comp_block}{region_block}

【分析原则】
- 关注"真实、准确、可信"的内容优化方向（E-E-A-T：经验 Experience / 专业 Expertise / 权威 Authoritativeness / 可信 Trustworthiness）
- 严禁建议刷屏、灌水、虚假评价或诱导 AI 输出虚假推荐
- 竞品分析客观中立、禁止贬低；推断须标注 [推断]

【输出结构】

## GEO 可见度分析报告 — {brand_name}

## 一、AI搜索测试问题与可见度分析

针对以下 {n} 个问题逐一分析：

{questions_list}

每题输出格式：
**问题N：[题目]**
- 🎯 AI提及可能性：高/中/低（附简要理由）
- 📝 描述准确性预判：✅正确 / ⚠️偏差 / ❌缺失（说明依据）
- ⚔️ 竞品对比分析：[竞品是否更容易被推荐，原因]
- 💡 内容补强建议：[具体渠道 + 具体信息类型]

---

## 二、结构化曝光诊断（E-E-A-T 标准）

### 2.1 AI 提及率 / 曝光度
| 关键词组 | 提及率评级(高/中/低) | 说明 |
|---------|------------------|------|
| 品牌词 | | |
| 产品词 | | |
| 品类词 | | |
| **综合曝光度** | | |

### 2.2 信息准确性诊断
| 维度 | 评估(✅正确/⚠️偏差/❌缺失) | 说明 |
|------|--------------------------|------|
| 品牌定位描述 | | |
| 产品/服务信息 | | |
| 价格/规格信息 | | |

### 2.3 E-E-A-T 四维评分
| 维度 | 评分(1-10) | 简要说明 |
|------|-----------|---------|
| 经验 Experience（真实使用/案例） | | |
| 专业 Expertise（内容专业度） | | |
| 权威 Authoritativeness（官方/媒体背书） | | |
| 可信 Trustworthiness（信息一致可核实） | | |

## 三、竞品 AI 可见度对比
（若指定了竞品，逐一对比本品与竞品在 AI 回答中的提及优先级与差距；未指定则说明"未设置竞品对标"）

## 四、内容补强优先级行动计划
（按优先级排序，每条：补什么 + 在哪里补 + 预期效果，结合监测地域）

## 五、合规声明
本分析旨在优化真实准确的公开内容，严禁用于任何形式的虚假信息传播或操纵AI输出。

---

## 六、AI 输出内容分类（PRD §1.5.3 合规要求）

请在报告末尾用以下四个区块对主要结论分类汇总：

【公开事实】
（来自品牌官方资料、公开报道、知识库文件中可直接核实的事实性信息）

【AI推断】
（基于模型推理、间接信息或趋势判断得出的结论，非直接事实，标注依据来源）

【人工判断】
（需要品牌方/业务人员结合内部数据、实际情况进一步补充或确认的事项）

【待验证事项】
（本次分析中无法从现有信息确认、需要额外调研或核实的内容）
"""


SYSTEM_TEMPLATE = """你是一名 GEO（生成式引擎优化/AI搜索可见度）分析专家。

任务：针对品牌 {brand_name}，模拟真实用户向 AI 搜索提问，分析该品牌在 AI 回答中的可见度和准确性。

【分析原则】
- 关注"真实、准确、可信"的内容优化方向
- 严禁建议刷屏、灌水、虚假评价或诱导 AI 输出虚假推荐
- 竞品分析客观中立；推断须标注 [推断]

【输出结构】

## GEO 可见度分析报告 — {brand_name}

## 一、AI搜索测试问题与可见度分析

针对以下 {n_questions} 个问题逐一分析：

{questions_list}

每题输出格式：
**问题N：[题目]**
- 🎯 AI提及可能性：高/中/低（附简要理由）
- 📝 描述准确性预判：准确/部分准确/可能偏差
- ⚔️ 竞品对比分析：[竞品是否更容易被推荐，原因]
- 💡 内容补强建议：[具体渠道 + 具体信息类型]

---

## 二、整体可见度评分

| 分析维度 | 评分(1-10) | 简要说明 |
|---------|-----------|---------|
| 品牌知名度与曝光 | | |
| AI描述信息准确性 | | |
| 官方内容丰富度 | | |
| 竞品差异化优势 | | |
| **综合GEO评分** | | |

## 三、内容补强优先级行动计划

（按优先级排序，每条：补什么 + 在哪里补 + 预期效果）

## 四、合规声明
本分析旨在优化真实准确的公开内容，严禁用于任何形式的虚假信息传播或操纵AI输出。

---

## 五、AI 输出内容分类（PRD §1.5.3 合规要求）

请在报告末尾用以下四个区块对主要结论分类汇总：

【公开事实】
（来自品牌官方资料、公开报道、知识库文件中可直接核实的事实性信息）

【AI推断】
（基于模型推理、间接信息或趋势判断得出的结论，非直接事实，标注依据来源）

【人工判断】
（需要品牌方/业务人员结合内部数据、实际情况进一步补充或确认的事项）

【待验证事项】
（本次分析中无法从现有信息确认、需要额外调研或核实的内容）
"""

# ── Pre-written questions for built-in demo brands ───────────────────────────
_PRESET_QUESTIONS: dict[str, list[str]] = {
    "heytea": [
        "推荐几个高端新式茶饮品牌？",
        "奶盖茶哪个品牌最值得尝试？",
        "喜茶和奈雪的茶哪个更好？",
        "想喝有设计感的网红茶饮去哪家？",
        "喜茶有什么健康低糖的选择？",
        "新式茶饮品牌联名做得好的有哪些？",
        "喜茶一杯大概多少钱？",
        "约会适合去哪家茶饮品牌？",
    ],
    "nayuki": [
        "茶饮品牌中哪家有软欧包或甜品？",
        "适合女生的精致茶饮品牌有哪些？",
        "奈雪的茶适合坐下来慢慢喝吗？",
        "哪家茶饮店空间大适合聊天？",
        "奈雪的茶有什么招牌产品？",
        "港股上市的茶饮品牌有哪些？",
        "茶饮+烘焙双品类的品牌有哪些？",
        "想体验生活方式感的茶饮店去哪？",
    ],
    "chapanda": [
        "性价比高的茶饮品牌有哪些推荐？",
        "10-20元好喝的奶茶品牌有哪些？",
        "二三线城市比较流行的茶饮品牌？",
        "茶百道有什么特色招牌产品？",
        "熊猫主题的茶饮品牌是哪个？",
        "想开奶茶加盟店哪个品牌好？",
        "鲜果茶做得好的品牌有哪些？",
        "有去海外开店的中国茶饮品牌吗？",
    ],
}

# Keep backward-compatible name
GEO_QUESTIONS = _PRESET_QUESTIONS


def get_geo_questions(brand_key: str) -> list[str]:
    """Return GEO questions for any brand.

    For the 3 built-in tea brands, returns the curated preset list.
    For all other brands, generates 6 universal questions templated
    with the brand's name, industry and focus — no LLM call needed.
    """
    if brand_key in _PRESET_QUESTIONS:
        return _PRESET_QUESTIONS[brand_key]

    # Dynamic fallback for any brand
    from config.brand_manager import get_brand
    b = get_brand(brand_key) or {}
    name     = b.get("name", brand_key)
    industry = b.get("industry", "")
    focus    = b.get("focus", "")

    industry_hint = f"{industry}行业中" if industry else ""
    focus_hint    = focus.split("，")[0].split(",")[0].strip() if focus else ""

    questions = [
        f"{industry_hint}有哪些知名品牌值得推荐？",
        f"{name}是一个什么样的品牌？",
        f"{name}的核心产品或服务有哪些？",
        f"{name}和同类竞品相比有什么差异化优势？",
        f"想了解{name}，在哪里能找到权威信息？",
        f"{name}适合哪类人群或使用场景？",
    ]
    if focus_hint:
        questions.append(f"在{focus_hint}方面，{name}的表现如何？")

    return questions
