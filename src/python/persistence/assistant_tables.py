"""智能助手会话、消息与压缩摘要。"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class AssistantConversation(Base):
    __tablename__ = "assistant_conversations"

    id = Column(String(64), primary_key=True)
    title = Column(String(160), nullable=False, default="新对话")
    summary = Column(Text, nullable=False, default="")
    summarized_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = relationship(
        "AssistantMessage", cascade="all, delete-orphan", passive_deletes=True,
        order_by="AssistantMessage.id",
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String(64), ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False, default="")
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
