"""数据库包：SQLAlchemy 引擎、模型、会话。

DATABASE_URL 环境变量/Secrets 决定连哪个库：
- 本地默认：sqlite:///data/app.db（开发用，持久在本机）
- 线上生产：postgresql+psycopg2://...（Supabase/Neon 等托管 Postgres）
"""
