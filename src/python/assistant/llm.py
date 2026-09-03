"""DeepSeek 大模型客户端 —— OpenAI 兼容的 /chat/completions，支持 tools(function-calling)

用 httpx（项目已装，requests 未装）。所有异常统一抛 LLMError，由路由层转成友好提示。
"""
import httpx

from . import config

_TIMEOUT = 60.0


class LLMError(Exception):
    """大模型调用失败（缺 key / 网络 / 非 200 / 响应结构异常）"""


def chat(messages, tools=None, tool_choice="auto", temperature=0.3):
    """单轮对话补全。返回 message dict（可能含 tool_calls）。

    :param messages: OpenAI 格式消息列表
    :param tools: OpenAI 格式工具定义列表；为空则普通对话
    """
    if not config.has_key():
        raise LLMError("未配置 DEEPSEEK_API_KEY：请在 src/python/.env 填入密钥后重启服务")

    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    headers = {
        "Authorization": "Bearer " + config.DEEPSEEK_API_KEY,
        "Content-Type": "application/json",
    }
    url = config.DEEPSEEK_BASE_URL + "/chat/completions"

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise LLMError("调用大模型网络异常：%s" % exc)

    if resp.status_code != 200:
        raise LLMError("大模型返回 HTTP %d：%s" % (resp.status_code, resp.text[:300]))

    try:
        data = resp.json()
        return data["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError("大模型响应结构异常：%s" % exc)
