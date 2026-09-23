"""智能助手路由 —— POST /assistant/chat"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from . import config
from . import llm
from .service import run_chat
from . import memory

router = APIRouter(prefix="/assistant", tags=["平台智能助手"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    message: str = Field(..., min_length=1, description="用户本轮自然语言提问")
    conversation_id: Optional[str] = Field(default=None, description="持久化会话 ID")
    history: Optional[List[ChatMessage]] = Field(default=None, description="最近若干轮对话，用于上下文")


@router.post("/chat", summary="智能助手对话（自然语言→数据查询/模块跳转）")
def chat(body: ChatBody):
    conversation_id = memory.ensure_conversation(body.conversation_id)
    summary, stored_history = memory.context(conversation_id)
    # 兼容旧前端传入 history；有数据库会话时以服务端记录为准，避免本轮问题被重复注入。
    history = stored_history or ([{"role": h.role, "content": h.content} for h in body.history] if body.history else [])
    memory.append_message(conversation_id, "user", body.message)
    result = run_chat(body.message, history, summary)
    assistant_text = result.get("answer") or result.get("error") or ""
    memory.append_message(conversation_id, "assistant", assistant_text, {
        "action": result.get("action"), "rag_sources": result.get("rag_sources", [])
    })
    result["conversation_id"] = conversation_id
    return result


@router.post("/conversations", summary="新建助手对话")
def create_conversation():
    conversation_id = memory.ensure_conversation()
    return {"conversation_id": conversation_id, "messages": [], "summary": ""}


@router.get("/conversations/{conversation_id}", summary="读取助手对话")
def get_conversation(conversation_id: str):
    return memory.detail(memory.ensure_conversation(conversation_id))


@router.delete("/conversations/{conversation_id}/memory", summary="清空当前对话记忆")
def clear_conversation(conversation_id: str):
    conversation_id = memory.clear(conversation_id)
    return {"conversation_id": conversation_id, "message": "当前对话记忆已清空"}


@router.get("/tools", summary="列出助手可用工具（调试/前端展示能力清单）")
def list_tools():
    from . import tools
    return {"count": len(tools.TOOL_SCHEMAS),
            "tools": [{"name": t["function"]["name"],
                       "description": t["function"]["description"]}
                      for t in tools.TOOL_SCHEMAS],
            "modules": tools.MODULE_ROUTES}


@router.get("/status", summary="助手及本地模型状态")
def status():
    return {
        "configured": config.configured(),
        "provider": config.ASSISTANT_PROVIDER,
        "model": config.LOCAL_LLM_MODEL if config.ASSISTANT_PROVIDER != "deepseek" else config.DEEPSEEK_MODEL,
        "base_url": config.LOCAL_LLM_BASE_URL if config.ASSISTANT_PROVIDER != "deepseek" else config.DEEPSEEK_BASE_URL,
        "local": llm.local_status(),
        "deepseek_fallback_configured": config.has_key(),
    }
