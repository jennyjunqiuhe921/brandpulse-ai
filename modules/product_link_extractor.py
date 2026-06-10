"""B2 · 商品链接自动提取。

输入电商商品页 URL，尽力提取产品名称与卖点，填入内容工坊表单。
- 对淘宝/京东/拼多多等反爬严格的站点，抓取失败时优雅降级（从 URL/标题猜测），
  绝不抛未捕获异常导致页面崩溃。
- 非法输入（非 URL）返回明确错误。
"""
from __future__ import annotations
import re
from urllib.parse import urlparse, unquote

import requests

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

_KNOWN_SITES = {
    "taobao.com": "淘宝", "tmall.com": "天猫", "jd.com": "京东",
    "pinduoduo.com": "拼多多", "yangkeduo.com": "拼多多",
    "xiaohongshu.com": "小红书", "douyin.com": "抖音",
    "meituan.com": "美团", "ele.me": "饿了么", "1688.com": "1688",
}


class ExtractError(Exception):
    """提取失败（含输入非法）。"""


def _is_valid_url(text: str) -> bool:
    try:
        p = urlparse(text.strip())
        return p.scheme in ("http", "https") and bool(p.netloc) and "." in p.netloc
    except Exception:
        return False


def _site_name(netloc: str) -> str:
    host = netloc.lower().lstrip("www.")
    for domain, name in _KNOWN_SITES.items():
        if host.endswith(domain) or domain in host:
            return name
    return host


def _fetch_title(url: str, timeout: int = 8) -> str:
    """抓取页面 <title>。失败返回空串（不抛异常）。"""
    try:
        resp = requests.get(
            url, headers={"User-Agent": _UA, "Accept-Language": "zh-CN,zh;q=0.9"},
            timeout=timeout, allow_redirects=True,
        )
        resp.encoding = resp.apparent_encoding or "utf-8"
        m = re.search(r"<title[^>]*>(.*?)</title>", resp.text, re.S | re.I)
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).strip()
            # 去除常见站点后缀
            title = re.split(r"[-_|—]\s*(淘宝|天猫|京东|拼多多|Tmall|JD|首页)", title)[0].strip()
            return title[:80]
    except Exception:
        pass
    return ""


def extract(url: str) -> dict:
    """提取商品信息。

    返回 {product_name, source, raw_title, confidence}
    失败抛 ExtractError，调用方需捕获并提示用户。
    """
    if not url or not url.strip():
        raise ExtractError("请输入商品链接")

    url = url.strip()
    if not _is_valid_url(url):
        raise ExtractError("链接格式无效，请输入完整的商品页 URL（以 http:// 或 https:// 开头）")

    netloc = urlparse(url).netloc
    site = _site_name(netloc)

    title = _fetch_title(url)

    if title:
        return {
            "product_name": title,
            "source": site,
            "raw_title": title,
            "confidence": "high",
        }

    # 降级：从 URL path 中尝试还原可读片段
    path_guess = unquote(urlparse(url).path).strip("/").replace("-", " ").replace("_", " ")
    guess = path_guess.split("/")[-1][:40] if path_guess else ""
    return {
        "product_name": guess,
        "source": site,
        "raw_title": "",
        "confidence": "low",
        "note": (
            f"未能直接读取「{site}」商品页（电商平台通常有反爬限制），"
            "已根据链接做基础推断，请手动补全产品名称与卖点。"
        ),
    }
