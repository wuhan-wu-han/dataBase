"""助手核心对话逻辑 —— 供 routes.py 和 wechat 模块共同调用"""
import json
from typing import Any, Dict, List, Optional

from . import config, llm, rag, tools

SYSTEM_PROMPT = """你是"安塞区城市安全生命线管网AI智慧平台"的官方智能助手。
平台覆盖城市生命线全链条业务，包括：工单管理、应急预案、资产成本、综合管廊、危化品监管、数据治理（以上为本平台直管），
以及燃气资产管理、道路塌陷监测、燃气风控、供水管网监测、井盖管控（以上为协同子模块）。

工作准则：
1. 凡涉及数量、状态、统计、明细、KPI 的问题，必须调用相应工具获取真实数据后再回答，严禁凭空编造任何数字或记录。
2. 用户想查看/进入某个功能页面时，调用 navigate_to_module 工具（模块名见工具枚举）。
3. 一次回答可调用多个工具；拿到工具结果后用简洁中文总结，关键数据用要点列出，不要照搬原始 JSON。
4. 工具返回中包含 _error 字段时，如实说明失败原因并给出下一步建议，不要假装成功。
5. 回答面向城市安全运维管理者，专业、准确、精炼。"""


def _select_tool_schemas(message: str) -> List[Dict[str, Any]]:
    """按问题领域缩小工具集，避免把四十多个工具全部塞给本地小模型。"""
    text = message.lower()
    groups = [
        (("预警", "告警"), ("query_alert_",)),
        (("工单", "派单"), ("query_workorder_",)),
        (("预案", "应急"), ("query_plan_",)),
        (("资产", "成本", "运维"), ("query_asset_",)),
        (("管廊", "隧道"), ("query_tunnel_",)),
        (("危化", "危险品", "危化品"), ("query_hazmat_",)),
        (("治理", "主数据"), ("query_governance_",)),
        (("道路", "塌陷", "空洞", "施工"), ("query_road_",)),
        (("燃气", "泄漏", "占压"), ("query_gas_",)),
        (("供水", "水压", "水质", "爆管", "dma"), ("query_water_",)),
        (("井盖",), ("query_manhole_",)),
    ]
    prefixes = set()
    for keywords, names in groups:
        if any(keyword in text for keyword in keywords):
            prefixes.update(names)

    selected = []
    for schema in tools.TOOL_SCHEMAS:
        name = schema["function"]["name"]
        if name == "navigate_to_module" or any(name.startswith(prefix) for prefix in prefixes):
            selected.append(schema)

    if prefixes:
        return selected

    # 无明确领域时只提供各模块概览和页面导航，控制本地推理上下文大小。
    overview_names = {
        "query_alert_overview",
        "query_workorder_overview", "query_plan_overview", "query_asset_overview",
        "query_tunnel_overview", "query_hazmat_overview", "query_governance_overview",
        "query_gas_asset_summary", "query_road_subsidence_stats",
        "query_water_monitor_latest", "query_manhole_monitor_stats", "navigate_to_module",
    }
    return [s for s in tools.TOOL_SCHEMAS if s["function"]["name"] in overview_names]


def _fast_path(message: str) -> Optional[Dict[str, Any]]:
    """高频精确查询直接访问真实接口，不让用户等待两轮模型推理。"""
    text = message.strip().lower()
    count_words = ("多少", "数量", "总数", "几条", "几个")
    if ("预警" in text or "告警" in text) and any(word in text for word in count_words):
        data = tools.execute("query_alert_overview", {})
        if not data.get("_error"):
            count = int(data.get("total", 0))
            return {
                "success": True,
                "answer": f"当前共有 **{count} 条预警**。",
                "action": None,
                "tool_results": [{"tool": "query_alert_overview", "args": {}, "data": data}],
                "model": "local-data-router",
            }
    if "工单" in text and ("待派单" in text or "未派单" in text):
        data = tools.execute("query_workorder_overview", {})
        if not data.get("_error"):
            count = int(data.get("pending_dispatch", 0))
            return {
                "success": True,
                "answer": f"当前有 **{count} 个待派单工单**。",
                "action": None,
                "tool_results": [{"tool": "query_workorder_overview", "args": {}, "data": data}],
                "model": "local-data-router",
            }
    return None


def _local_fallback(message: str, error: Exception) -> Optional[Dict[str, Any]]:
    """模型异常时，仍尝试用平台真实接口回答高频数据问题。"""
    result = _fast_path(message)
    if result:
        result["model"] = "local-data-fallback"
        result["warning"] = "大模型暂时不可用，已使用平台实时数据回答。"
    return result


def run_chat(message: str, history: Optional[List[Dict[str, str]]] = None,
             memory_summary: str = "") -> Dict[str, Any]:
    fast_result = _fast_path(message)
    if fast_result:
        return fast_result

    rag_chunks = rag.retrieve(message)
    context_parts = []
    if memory_summary:
        context_parts.append("较早对话摘要：\n" + memory_summary)
    if rag_chunks:
        docs = "\n\n".join("[%s] %s" % (item["source"], item["content"]) for item in rag_chunks)
        context_parts.append("项目资料检索结果（仅在与问题相关时引用）：\n" + docs)
    system_content = SYSTEM_PROMPT
    if context_parts:
        system_content += "\n\n" + "\n\n".join(context_parts)
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_content}]
    if history:
        for h in history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})
    selection_context = " ".join(h.get("content", "") for h in (history or [])[-4:]) + " " + message
    selected_tools = _select_tool_schemas(selection_context)

    tool_results: List[Dict[str, Any]] = []
    action: Optional[Dict[str, Any]] = None
    answer = ""
    active_model = config.LOCAL_LLM_MODEL if config.ASSISTANT_PROVIDER != "deepseek" else config.DEEPSEEK_MODEL
    active_provider = config.ASSISTANT_PROVIDER
    warning = None

    try:
        for _ in range(4):
            # 小型本地模型拿到工具结果后直接总结，避免重复选工具造成长时间空转。
            if tool_results and active_provider == "local":
                available_tools = None
                compact_results = json.dumps(tool_results, ensure_ascii=False)[:6000]
                request_messages = [
                    {"role": "system", "content": "根据给定的真实查询结果，用简洁中文回答用户问题。不得编造数据，不要描述工具调用过程。"},
                    {"role": "user", "content": "用户问题：%s\n真实查询结果：%s" % (message, compact_results)},
                ]
            else:
                available_tools = selected_tools
                request_messages = messages
            msg = llm.chat(request_messages, tools=available_tools, tool_choice="auto")
            active_model = msg.pop("_assistant_model", active_model)
            active_provider = msg.pop("_assistant_provider", active_provider)
            warning = msg.pop("_assistant_warning", warning)
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
        fallback = _local_fallback(message, exc)
        if fallback:
            return fallback
        return {"success": False, "error": str(exc), "answer": "",
                "action": None, "tool_results": tool_results,
                "model": active_model}

    result = {"success": True, "answer": answer, "action": action,
              "tool_results": tool_results, "model": active_model,
              "rag_sources": sorted({item["source"] for item in rag_chunks})}
    if warning:
        result["warning"] = warning
    return result


WECHAT_PROMPT = (
    '你是安塞区城市安全生命线管网AI智慧平台的智能助手。'
    '简洁回答，控制在100字以内。涉及实时数据时提示用户到平台Web端查询。'
)


def run_simple_chat(message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """快速对话（不走工具调用），用于微信等 5 秒内必须响应的场景。"""
    messages: List[Dict[str, str]] = [{"role": "system", "content": WECHAT_PROMPT}]
    if history:
        for h in history[-4:]:
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        msg = llm.chat(messages, max_tokens=120)
        answer = msg.get("content") or ""
        return {"success": True, "answer": answer}
    except llm.LLMError as exc:
        return {"success": False, "error": str(exc), "answer": ""}
    except Exception as exc:
        return {"success": False, "error": str(exc), "answer": ""}
