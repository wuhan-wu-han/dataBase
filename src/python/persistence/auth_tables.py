"""统一认证与 RBAC 表模型。"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .database import Base


user_roles = Table(
    "auth_user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "auth_role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("auth_permissions.id", ondelete="CASCADE"), primary_key=True),
)


class AuthUser(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    email = Column(String(128), nullable=True, index=True)
    phone = Column(String(32), nullable=True, index=True)
    department_id = Column(String(64), nullable=True)
    password_hash = Column(String(255), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    roles = relationship("AuthRole", secondary=user_roles, back_populates="users", lazy="joined")


class AuthRole(Base):
    __tablename__ = "auth_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    users = relationship("AuthUser", secondary=user_roles, back_populates="roles")
    permissions = relationship(
        "AuthPermission", secondary=role_permissions, back_populates="roles", lazy="joined"
    )


class AuthPermission(Base):
    __tablename__ = "auth_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    roles = relationship("AuthRole", secondary=role_permissions, back_populates="permissions")

