"""SQLite 轻量幂等迁移；用于兼容已有 platform.db。"""

from sqlalchemy import text

from .database import engine


AUTH_USER_COLUMNS = {
    "email": "VARCHAR(128)",
    "phone": "VARCHAR(32)",
    "department_id": "VARCHAR(64)",
}


def run_migrations() -> None:
    with engine.begin() as connection:
        existing = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(auth_users)")).fetchall()
        }
        for name, sql_type in AUTH_USER_COLUMNS.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE auth_users ADD COLUMN {name} {sql_type}"))
