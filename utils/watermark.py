"""S1-7 统一文件水印 — 导出文件附企业名/操作人/时间。

文本导出：附水印文本块。
图片导出：在右下角叠加半透明水印（需 Pillow，缺失则跳过）。
"""
from __future__ import annotations
from datetime import datetime


def watermark_text(extra: str = "") -> str:
    """生成标准水印文本行（用于文档/CSV/报表页脚）。"""
    try:
        from db import context as ctx
        from db.engine import get_session
        from db.models import Tenant, User
        with get_session() as s:
            t = s.query(Tenant).filter(Tenant.id == ctx.tenant_id()).first()
            company = t.name if t else "智营AI"
            uid = ctx.user_id()
            u = s.query(User).filter(User.id == uid).first() if uid else None
            operator = (u.name or u.username) if u else "—"
    except Exception:
        company, operator = "智营AI", "—"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"水印 · {company} · 操作人：{operator} · {ts}"
    return f"{line} · {extra}" if extra else line


def stamp_text_export(content: str, title: str = "") -> str:
    """给文本/Markdown 导出内容加页眉水印 + 页脚免责。"""
    head = f"<!-- {watermark_text(title)} -->\n"
    foot = ("\n\n---\n"
            f"_{watermark_text()}_\n"
            "_所有分析、选品、竞品情报、AI搜索分析内容均基于公开信息和AI工具辅助生成。_\n")
    return head + content + foot


def stamp_image(image_bytes: bytes) -> bytes:
    """在图片右下角叠加水印文字；无 Pillow 时原样返回。"""
    try:
        import io
        from PIL import Image, ImageDraw
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        text = watermark_text()
        x = max(8, img.width - 8 - len(text) * 6)
        y = max(8, img.height - 24)
        draw.text((x, y), text, fill=(255, 255, 255, 160))
        out = Image.alpha_composite(img, overlay).convert("RGB")
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return image_bytes
