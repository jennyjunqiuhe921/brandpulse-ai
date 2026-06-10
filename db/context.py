"""当前请求的租户/用户上下文（从登录会话解析，带降级兜底）。

存储层用它来做数据隔离：所有读写都限定在当前租户内。
若在 Streamlit 之外（脚本/测试）调用，降级为默认租户 1。
"""
from __future__ import annotations


def tenant_id() -> int:
    try:
        from auth.login import current_tenant_id
        t = current_tenant_id()
        if t:
            return int(t)
    except Exception:
        pass
    return 1  # 兜底：默认演示租户（脚本/测试用）


def user_id():
    try:
        from auth.login import current_user_id
        return current_user_id()
    except Exception:
        return None
