"""助手核心对话逻辑 —— 供 routes.py 和 wechat 模块共同调用"""
import json
from typing import Any, Dict, List, Optional

from . import config, llm, tools

SYSTEM_PROMPT = """你是"安塞区城市安全生命线管网AI智慧平台"的官方智能助手。
平台覆盖城市生命线全链条业务，包括：工单管理、应急预案、资产成本、综合管廊、危化品监管、数据治理（以上为本平台直管），
以及燃气资产管理、道路塌陷监测、燃气风控、供水管网监测、井盖管控（以上为协同子模块）。

工作准则：
1. 凡涉及数量、状态、统计、明细、KPI 的问题，必须调用相应工具获取真实数据后再回答，严禁凭空编造任何数字或记录。
2. 用户想查看/进入某个功能页面时，调用 navigate_to_module 工具（模块名见工具枚举）。
3. 一次回答可调用多个工具；拿到工具结果后用简洁中文总结，关键数据用要点列出，不要照搬原始 JSON。
4. 工具返回中包含 _error 字段时，如实说明失败原因并给出下一步建议，不要假装成功。
5. 回答面向城市安全运维管理者，专业、准确、精炼。"""


def run_chat(message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for h in history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    tool_results: List[Dict[str, Any]] = []
    action: Optional[Dict[str, Any]] = None
    answer = ""

    try:
        for _ in range(4):
            msg = llm.chat(messages, tools=tools.TOOL_SCHEMAS, tool_choice="auto")
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                answer = msg.get("content") or ""
                break

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
