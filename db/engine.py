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

from sqlalchemy import create_engine, event
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


def _sanitize_pg(url: str) -> str:
    """清洗 Postgres 连接串：剥离 psycopg2 不识别的 Prisma 参数(pgbouncer)，
    确保 sslmode=require（Supabase 需要）。"""
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query))
    q.pop("pgbouncer", None)          # Prisma 专用，psycopg2 会报错
    q.setdefault("sslmode", "require")  # Supabase 强制 SSL
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


DATABASE_URL = _resolve_url()
_IS_SQLITE = DATABASE_URL.startswith("sqlite")
if not _IS_SQLITE and DATABASE_URL.startswith("postgres"):
    DATABASE_URL = _sanitize_pg(DATABASE_URL)

# SQLite：check_same_thread=False 配合 Streamlit 多线程；timeout 等待锁释放
_connect_args = {"check_same_thread": False, "timeout": 30} if _IS_SQLITE else {}

_engine_kwargs = dict(echo=False, future=True, connect_args=_connect_args, pool_pre_ping=True)
if not _IS_SQLITE:
    # 连接池友好设置（Supabase Session pooler）：回收空闲连接，避免被池化层断开
    _engine_kwargs.update(pool_size=5, max_overflow=5, pool_recycle=1800)

engine = create_engine(DATABASE_URL, **_engine_kwargs)


# SQLite 并发健壮性：WAL 模式(读写不互斥) + busy_timeout(等待锁) + 外键
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _rec):  # noqa: ANN001
        cur = dbapi_conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass
        finally:
            cur.close()

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
