from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite数据库路径：锚定到本文件所在目录，避免因启动工作目录不同而把 data.db 生成到别处
# Windows 反斜杠转正斜杠，兼容 SQLAlchemy 的 sqlite:/// URL 格式
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")
DATABASE_URL = "sqlite:///" + _DB_PATH.replace("\\", "/")

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite多线程支持
    pool_pre_ping=True
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
