"""登录态持久化：把签名 token 写进浏览器 cookie，刷新 / websocket 重连后恢复会话。

设计要点
- **读** 用原生 `st.context.cookies`（随 HTTP 请求即时可用，无需挂组件，每页可靠）。
- **写 / 删** 用 `streamlit-cookies-controller`（仅登录后补写、登出清除时才实例化组件）。
- 品牌端 / 运营端 cookie 名分离（`pin_auth` / `pin_platform_auth`），互不复用，保持物理隔离。
- token 用 stdlib hmac-sha256 签名 + 过期时间，防伪造；只放 uid + scope + exp，恢复时再回库取最新用户。
- 全程 try/except 降级：组件缺失 / 异常时退回"无持久化"旧行为，绝不影响主流程。
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import time

import streamlit as st

from config.settings import _get_env

_SECRET = (_get_env("AUTH_TOKEN_SECRET", "") or "pinsight-dev-secret-change-me").encode()
_TTL = 7 * 24 * 3600  # 7 天

# scope → cookie 名（品牌端 / 运营端隔离）
_COOKIE = {"brand": "pin_auth", "platform": "pin_platform_auth"}


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(scope: str, uid: int) -> str:
    payload = {"uid": int(uid), "scope": scope, "exp": int(time.time()) + _TTL}
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(_SECRET, body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def _verify(token: str, scope: str) -> int | None:
    try:
        body, sig = token.split(".", 1)
        expected = _b64e(hmac.new(_SECRET, body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64d(body))
        if payload.get("scope") != scope:
            return None
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return int(payload["uid"])
    except Exception:
        return None


def _controller():
    try:
        from streamlit_cookies_controller import CookieController
        return CookieController(key="pin_cookie_ctrl")
    except Exception:
        return None


def read_uid(scope: str) -> int | None:
    """从请求 cookie 原生读取 token 并验签，返回 uid 或 None（不挂组件）。"""
    name = _COOKIE.get(scope)
    if not name:
        return None
    try:
        token = st.context.cookies.get(name)
    except Exception:
        token = None
    return _verify(token, scope) if token else None


def write(scope: str, uid: int) -> None:
    """登录后补写签名 cookie（实例化组件）。失败静默降级。"""
    name = _COOKIE.get(scope)
    c = _controller()
    if not name or not c:
        return
    try:
        c.set(name, _sign(scope, uid), max_age=_TTL, same_site="lax")
    except Exception:
        try:
            c.set(name, _sign(scope, uid))
        except Exception:
            pass


def ensure(scope: str, uid: int) -> None:
    """登录态在但 cookie 缺失/不匹配 → 补写。务必在 set_page_config 之后调用（侧边栏内）。"""
    try:
        if read_uid(scope) != int(uid):
            write(scope, int(uid))
    except Exception:
        pass


def clear(scope: str) -> None:
    """登出清除 cookie（实例化组件）。失败静默降级。"""
    name = _COOKIE.get(scope)
    c = _controller()
    if not name or not c:
        return
    try:
        c.remove(name)
    except Exception:
        pass
