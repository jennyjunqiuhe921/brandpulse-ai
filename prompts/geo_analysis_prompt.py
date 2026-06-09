from __future__ import annotations

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
