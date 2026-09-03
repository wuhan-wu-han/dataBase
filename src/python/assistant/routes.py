"""智能助手路由 —— POST /assistant/chat

流程（ReAct 式工具调用循环）：
  用户自然语言 → DeepSeek 决定是否调用工具 → 后端执行工具(回调只读接口) →
  把结果回喂模型 → 模型产出中文自然语言回答。
返回给前端：answer(文字) + action(跳转意图) + tool_results(结构化数据,供渲染表格/卡片)。
"""
import json

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from . import config, llm, tools

router = APIRouter(prefix="/assistant", tags=["平台智能助手"])

SYSTEM_PROMPT = """你是"安塞区城市安全生命线管网AI智慧平台"的官方智能助手。
平台覆盖城市生命线的工单管理、应急预案、资产成本、综合管廊、危化品监管、数据治理等业务。

工作准则：
1. 凡涉及数量、状态、统计、明细、KPI 的问题，必须调用相应工具获取真实数据后再回答，严禁凭空编造任何数字或记录。
2. 用户想查看/进入某个功能页面时，调用 navigate_to_module 工具（模块名见工具枚举）。
3. 一次回答可调用多个工具；拿到工具结果后用简洁中文总结，关键数据用要点列出，不要照搬原始 JSON。
4. 工具返回中包含 _error 字段时，如实说明失败原因并给出下一步建议，不要假装成功。
5. 回答面向城市安全运维管理者，专业、准确、精炼。"""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    message: str = Field(..., min_length=1, description="用户本轮自然语言提问")
    history: Optional[List[ChatMessage]] = Field(default=None, description="最近若干轮对话，用于上下文")


@router.post("/chat", summary="智能助手对话（自然语言→数据查询/模块跳转）")
def chat(body: ChatBody):
    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # 携带最近上下文（裁剪到最近 8 条，控制 token）
    if body.history:
        for h in body.history[-8:]:
            messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": body.message})

    tool_results: List[Dict[str, Any]] = []
    action: Optional[Dict[str, Any]] = None
    answer = ""

    try:
        # 最多 4 轮工具调用，防止死循环
        for _ in range(4):
            msg = llm.chat(messages, tools=tools.TOOL_SCHEMAS, tool_choice="auto")
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                answer = msg.get("content") or ""
                break

            # 把含 tool_calls 的 assistant 消息原样加入上下文
            messages.append({
                "role": "assistant",
                "content": msg.get("content"),
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except (ValueError, TypeError):
                    args = {}

                result = tools.execute(name, args)
                tool_results.append({"tool": name, "args": args, "data": result})

                # 跳转工具：提取导航意图给前端
                if name == "navigate_to_module" and isinstance(result, dict) and result.get("path"):
                    action = {"type": "navigate", "path": result["path"],
                              "label": result.get("label", "")}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": json.dumps(result, ensure_ascii=False)[:4000],
                })
        else:
            answer = answer or "已为你查询到相关数据，请查看下方结果。"
    except llm.LLMError as exc:
        return {"success": False, "error": str(exc), "answer": "",
                "action": None, "tool_results": tool_results,
                "model": config.DEEPSEEK_MODEL}

    return {"success": True, "answer": answer, "action": action,
            "tool_results": tool_results, "model": config.DEEPSEEK_MODEL}


@router.get("/tools", summary="列出助手可用工具（调试/前端展示能力清单）")
def list_tools():
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
