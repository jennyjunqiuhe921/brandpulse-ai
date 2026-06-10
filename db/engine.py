"""SQLAlchemy 引擎与会话工厂。

连接串解析优先级：
1. 环境变量 DATABASE_URL
2. Streamlit Secrets 的 DATABASE_URL
3. 默认本地 SQLite：sqlite:///data/app.db
"""
from __future__ import annotations
import os
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_DATA_DIR = Path(__file__).parent.parent / "data"
_DATA_DIR.mkdir(exist_ok=True)

Base = declarative_base()


def _resolve_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # 尝试 Streamlit Secrets（在 Streamlit 运行环境内）
    try:
        import streamlit as st
        u = st.secrets.get("DATABASE_URL")  # type: ignore
        if u:
            return u
    except Exception:
        pass
    # 默认本地 SQLite
    return f"sqlite:///{_DATA_DIR / 'app.db'}"


DATABASE_URL = _resolve_url()

# SQLite 需要 check_same_thread=False 以配合 Streamlit 多线程
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def get_session():
    """事务上下文：自动提交/回滚/关闭。"""
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite")
