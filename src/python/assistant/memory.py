"""SQLite 会话记忆：保留最近20轮，较早消息压缩成短摘要。"""

import json
import re
import uuid
from datetime import datetime

try:
    from persistence import SessionLocal, init_db
    from persistence.assistant_tables import AssistantConversation, AssistantMessage
except ImportError:
    from src.python.persistence import SessionLocal, init_db
    from src.python.persistence.assistant_tables import AssistantConversation, AssistantMessage

MAX_RECENT_MESSAGES = 40
SUMMARY_LIMIT = 5000


def normalize_id(value=None):
    text = str(value or "").strip()
    return text if re.fullmatch(r"[A-Za-z0-9_-]{8,64}", text) else str(uuid.uuid4())


def ensure_conversation(conversation_id=None):
    init_db()
    cid = normalize_id(conversation_id)
    with SessionLocal() as db:
        row = db.get(AssistantConversation, cid)
        if not row:
            row = AssistantConversation(id=cid)
            db.add(row)
            db.commit()
    return cid


def append_message(conversation_id, role, content, metadata=None):
    cid = ensure_conversation(conversation_id)
    clean = str(content or "").strip()
    with SessionLocal() as db:
        conversation = db.get(AssistantConversation, cid)
        if conversation.title == "新对话" and role == "user" and clean:
            conversation.title = clean[:60]
        conversation.updated_at = datetime.utcnow()
        db.add(AssistantMessage(
            conversation_id=cid, role=role, content=clean,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        ))
        db.commit()
    compact(cid)
    return cid


def _summary_lines(messages):
    lines = []
    for item in messages:
        label = "用户" if item.role == "user" else "助手"
        text = re.sub(r"\s+", " ", item.content or "").strip()
        if text:
            lines.append(f"{label}: {text[:240]}")
    return lines


def compact(conversation_id):
    with SessionLocal() as db:
        rows = db.query(AssistantMessage).filter_by(conversation_id=conversation_id).order_by(AssistantMessage.id).all()
        if len(rows) <= MAX_RECENT_MESSAGES:
            return
        old = rows[:-MAX_RECENT_MESSAGES]
        conversation = db.get(AssistantConversation, conversation_id)
        combined = ([conversation.summary] if conversation.summary else []) + _summary_lines(old)
        conversation.summary = "\n".join(combined)[-SUMMARY_LIMIT:]
        conversation.summarized_count += len(old)
        for row in old:
            db.delete(row)
        db.commit()


def context(conversation_id):
    cid = ensure_conversation(conversation_id)
    with SessionLocal() as db:
        conversation = db.get(AssistantConversation, cid)
        rows = db.query(AssistantMessage).filter_by(conversation_id=cid).order_by(AssistantMessage.id).all()
        return conversation.summary or "", [
            {"role": row.role, "content": row.content} for row in rows[-MAX_RECENT_MESSAGES:]
        ]


def detail(conversation_id):
    summary, messages = context(conversation_id)
    return {"conversation_id": conversation_id, "summary": summary, "messages": messages}


def clear(conversation_id):
    cid = ensure_conversation(conversation_id)
    with SessionLocal() as db:
        db.query(AssistantMessage).filter_by(conversation_id=cid).delete()
        conversation = db.get(AssistantConversation, cid)
        conversation.summary = ""
        conversation.summarized_count = 0
        conversation.title = "新对话"
        conversation.updated_at = datetime.utcnow()
        db.commit()
    return cid
