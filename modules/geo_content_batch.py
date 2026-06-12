"""G2 · GEO 批量内容创作 + SEO 埋词引擎。

针对一批关键词 × 平台，按平台专属模板批量生成内容草稿，并做 SEO 埋词：
- 标题前缀加「地域+产品」
- 结尾插入 CTA / 联系方式

纯模板实现（确定性、零 token、合规——规避绝对化用语）。生成的草稿落 ContentTask，
复用既有「合规预检 + 人工复核 + 审批」流程，不自动对外发布（守合规底线）。
"""
from __future__ import annotations

PLATFORMS = ["抖音", "小红书", "知乎", "微博"]


def _seo_title(region: str, product: str, keyword: str, tail: str = "") -> str:
    prefix = f"{region}{product}" if region else product
    base = f"{prefix}｜{keyword}" if keyword not in prefix else f"{prefix}"
    return (base + tail).strip()


def _hl_list(highlights: str) -> list[str]:
    return [h.strip() for h in (highlights or "").replace("，", ",").split(",") if h.strip()] or ["专业服务", "用心做好每一单"]


def _cta(contact: str) -> str:
    return f"📞 联系方式：{contact}" if contact else "📞 详情可在主页留言咨询"


def _douyin(subject, product, region, keyword, hls, contact) -> str:
    return (
        "【抖音口播脚本 · 约15秒】\n"
        f"🎬 0-3秒（痛点开头）：还在为「{keyword}」发愁？看完这条少走弯路。\n"
        f"🛠 3-10秒（解决方案）：{subject}，{ '、'.join(hls[:2]) }，{keyword}也能放心交给我们。\n"
        f"📣 10-15秒（行动指令）：想了解{product}，私信或" + _cta(contact).replace('📞 ', '') + "，马上为你安排。\n"
        "（口语化、语速快，结尾出示联系方式；内容须真实，不夸大。）")


def _xhs(subject, product, region, keyword, hls, contact) -> str:
    tags = " ".join(f"#{t}" for t in [product, f"{region}{product}".strip(), keyword, "本地推荐", "干货整理"] if t)
    body = "\n".join(f"{i+1}️⃣ {h}" for i, h in enumerate(hls[:4]))
    return (
        f"✨{(region+ '·') if region else ''}{keyword}，亲测整理✨\n"
        f"关于「{keyword}」，整理了几点干货 👇\n{body}\n"
        f"💡 {subject} 在做{product}，有需要可以问～\n{_cta(contact)}\n{tags}")


def _zhihu(subject, product, region, keyword, hls, contact) -> str:
    return (
        f"在{region or '本地'}，如何挑选靠谱的{product}？（围绕「{keyword}」）\n\n"
        "作为从业者，分享几条实用判断标准：\n"
        f"1. 避坑指南：留意资质与口碑，{ hls[0] if hls else '正规服务' }。\n"
        "2. 成本核算：明确报价构成，避免后续加价。\n"
        "3. 技术标准：关注服务流程是否规范、是否有质保。\n"
        f"\n{subject} 在 {product} 上的做法：{ '、'.join(hls[:3]) }。以上仅供参考，"
        f"具体以实际沟通为准。\n{_cta(contact)}")


def _weibo(subject, product, region, keyword, hls, contact) -> str:
    return (
        f"#{region}{product}# {subject}：针对「{keyword}」，{ hls[0] if hls else '提供专业服务' }，"
        f"支持快速响应。有需求欢迎咨询。{_cta(contact)}（内容基于真实服务，不夸大宣传。）")


_BUILDERS = {"抖音": _douyin, "小红书": _xhs, "知乎": _zhihu, "微博": _weibo}


def generate_batch(subject: str, keywords: list[str], platforms: list[str],
                   product: str = "", region: str = "", contact: str = "",
                   highlights: str = "") -> list[dict]:
    """对 关键词 × 平台 批量生成草稿。返回 [{keyword, platform, title, output}]。"""
    product = (product or subject or "").strip()
    keywords = [k.strip() for k in keywords if k.strip()][:30]
    platforms = [p for p in platforms if p in PLATFORMS] or PLATFORMS
    hls = _hl_list(highlights)
    out = []
    for kw in keywords:
        for pf in platforms:
            builder = _BUILDERS[pf]
            content = builder(subject, product, region, kw, hls, contact)
            title = _seo_title(region, product, kw, tail=f"（{pf}）")
            out.append({"keyword": kw, "platform": pf, "title": title, "output": content})
    return out


def save_drafts(brand: str, drafts: list[dict]) -> int:
    """落 ContentTask（草稿），复用内容工坊的合规/审批流程。返回保存条数。"""
    import config.content_tasks as ct
    n = 0
    for d in drafts:
        ct.add_task(brand, d["title"], [d["platform"]],
                    meta={"source": "GEO批量创作", "keyword": d["keyword"]},
                    output=d["output"], task_tags=["GEO获客"])
        n += 1
    return n
