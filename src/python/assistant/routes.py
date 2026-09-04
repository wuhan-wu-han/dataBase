"""智能助手路由 —— POST /assistant/chat"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from . import config
from .service import run_chat

router = APIRouter(prefix="/assistant", tags=["平台智能助手"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    message: str = Field(..., min_length=1, description="用户本轮自然语言提问")
    history: Optional[List[ChatMessage]] = Field(default=None, description="最近若干轮对话，用于上下文")


@router.post("/chat", summary="智能助手对话（自然语言→数据查询/模块跳转）")
def chat(body: ChatBody):
    history = [{"role": h.role, "content": h.content} for h in body.history] if body.history else None
    return run_chat(body.message, history)


@router.get("/tools", summary="列出助手可用工具（调试/前端展示能力清单）")
def list_tools():
    from . import tools
    return {"count": len(tools.TOOL_SCHEMAS),
            "tools": [{"name": t["function"]["name"],
                       "description": t["function"]["description"]}
                      for t in tools.TOOL_SCHEMAS],
            "modules": tools.MODULE_ROUTES}


@router.get("/status", summary="助手配置状态（是否已配置密钥）")
def status():
    return {"configured": config.has_key(),
            "model": config.DEEPSEEK_MODEL,
            "base_url": config.DEEPSEEK_BASE_URL}
