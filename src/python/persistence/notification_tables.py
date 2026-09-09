"""告警通知偏好与发送任务持久化模型。"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from .database import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=False)
    min_alert_level = Column(String(16), nullable=False, default="ORANGE")
    area_only = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class NotificationTask(Base):
    __tablename__ = "notification_tasks"
    __table_args__ = (
        UniqueConstraint("alert_id", "user_id", "channel", name="uq_notification_alert_user_channel"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(String(16), nullable=False, index=True)
    recipient = Column(String(128), nullable=False)
    recipient_name = Column(String(100), nullable=True)
    subject = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    alert_level = Column(String(16), nullable=True)
    business_type = Column(String(64), nullable=True)
    area_id = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retry_count = Column(Integer, nullable=False, default=3)
    error_message = Column(String(500), nullable=True)
    provider_message = Column(String(200), nullable=True)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    sent_at = Column(DateTime, nullable=True)
