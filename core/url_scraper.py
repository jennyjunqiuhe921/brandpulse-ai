"""URL 网页内容抓取 → 知识库入库工具"""
from __future__ import annotations

import re
from typing import Optional


def scrape_url(url: str) -> dict:
    """
    抓取网页正文内容，返回 {"ok": bool, "text": str, "title": str, "error": str}
    优先用 trafilatura（效果最好），回退到 BeautifulSoup。
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # ── 方案1：trafilatura（主力，去噪能力强）──────────────────────────────
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )
            if text and len(text.strip()) > 100:
                title = _extract_title(downloaded)
                return {"ok": True, "text": text.strip(), "title": title, "error": ""}
    except Exception as e:
        pass  # 继续尝试备用方案

    # ── 方案2：requests + BeautifulSoup 备用 ─────────────────────────────
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"

        soup = BeautifulSoup(resp.text, "html.parser")

        # 去除无用标签
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "form", "noscript", "iframe"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else url

        # 优先取 article/main，其次 body
        body = soup.find("article") or soup.find("main") or soup.body
        if body is None:
            return {"ok": False, "text": "", "title": "", "error": "页面无可读内容"}

        text = body.get_text(separator="\n", strip=True)
        # 压缩连续空行
        text = re.sub(r"\n{3,}", "\n\n", text)

        if len(text.strip()) < 50:
            return {"ok": False, "text": "", "title": "", "error": "提取内容过短，可能是动态渲染页面"}

        return {"ok": True, "text": text.strip(), "title": title, "error": ""}

    except Exception as e:
        return {"ok": False, "text": "", "title": "", "error": str(e)}


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


def ingest_url(url: str, brand_key: str) -> dict:
    """
    抓取 URL 并写入该品牌的 RAG 知识库。
    返回 {"ok": bool, "chunks_added": int, "title": str, "error": str}
    """
    result = scrape_url(url)
    if not result["ok"]:
        return {"ok": False, "chunks_added": 0, "title": "", "error": result["error"]}

    text = result["text"]
    title = result["title"] or url

    try:
        from core.rag_engine import ingest_text
        chunks_added = ingest_text(brand_key, text, source=url)
        return {"ok": True, "chunks_added": chunks_added, "title": title, "error": ""}
    except Exception as e:
        return {"ok": False, "chunks_added": 0, "title": title, "error": str(e)}
