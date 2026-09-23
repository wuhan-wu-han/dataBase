"""OpenAI 兼容大模型客户端：本地 Ollama 优先，可回退到 DeepSeek。

用 httpx（项目已装，requests 未装）。所有异常统一抛 LLMError，由路由层转成友好提示。
"""
import time
import httpx

from . import config

_LOCAL_TIMEOUT = 60.0
_CLOUD_TIMEOUT = 30.0


class LLMError(Exception):
    """大模型调用失败（缺 key / 网络 / 非 200 / 响应结构异常）"""


def _providers():
    local = {
        "provider": "local",
        "model": config.LOCAL_LLM_MODEL,
        "base_url": config.LOCAL_LLM_BASE_URL,
        "api_key": config.LOCAL_LLM_API_KEY,
        "timeout": _LOCAL_TIMEOUT,
    }
    cloud = {
        "provider": "deepseek",
        "model": config.DEEPSEEK_MODEL,
        "base_url": config.DEEPSEEK_BASE_URL,
        "api_key": config.DEEPSEEK_API_KEY,
        "timeout": _CLOUD_TIMEOUT,
    }
    if config.ASSISTANT_PROVIDER == "local":
        return [local]
    if config.ASSISTANT_PROVIDER == "deepseek":
        return [cloud]
    return [local, cloud]


def _request(provider, messages, tools, tool_choice, temperature):
    if provider["provider"] == "deepseek" and not provider["api_key"]:
        raise LLMError("未配置 DEEPSEEK_API_KEY，无法使用云端备用模型")

    payload = {
        "model": provider["model"],
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if provider["provider"] == "local":
        # 业务查询更看重响应速度；关闭长推理，避免纯 CPU 首轮等待数分钟。
        payload["reasoning_effort"] = "none"
        payload["max_tokens"] = 384
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    headers = {
        "Authorization": "Bearer " + provider["api_key"],
        "Content-Type": "application/json",
    }
    url = provider["base_url"] + "/chat/completions"
    last_error = None
    attempts = 1
    for attempt in range(attempts):
        try:
            # 当前机器的系统代理会拦截 localhost，且会导致 DeepSeek TLS/连接异常。
            with httpx.Client(
                timeout=provider["timeout"],
                trust_env=False,
            ) as client:
                resp = client.post(url, json=payload, headers=headers)
            break
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.4)
    else:
        raise LLMError("%s 模型连接失败：%s" % (provider["provider"], last_error))

    if resp.status_code != 200:
        raise LLMError("%s 模型返回 HTTP %d：%s" % (
            provider["provider"], resp.status_code, resp.text[:300]))

    try:
        message = resp.json()["choices"][0]["message"]
        message["_assistant_provider"] = provider["provider"]
        message["_assistant_model"] = provider["model"]
        return message
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError("%s 模型响应结构异常：%s" % (provider["provider"], exc))


def chat(messages, tools=None, tool_choice="auto", temperature=0.3):
    """单轮对话补全。返回 message dict（可能含 tool_calls）。

    :param messages: OpenAI 格式消息列表
    :param tools: OpenAI 格式工具定义列表；为空则普通对话
    """
    errors = []
    for provider in _providers():
        try:
            message = _request(provider, messages, tools, tool_choice, temperature)
            if errors:
                message["_assistant_warning"] = "本地模型不可用，已自动切换 DeepSeek。"
            return message
        except LLMError as exc:
            errors.append(str(exc))
    raise LLMError("；".join(errors))


def local_status():
    """返回 Ollama 服务及目标模型状态，供健康检查接口使用。"""
    api_root = config.LOCAL_LLM_BASE_URL
    if api_root.endswith("/v1"):
        api_root = api_root[:-3]
    try:
        with httpx.Client(timeout=2.5, trust_env=False) as client:
            resp = client.get(api_root + "/api/tags")
        resp.raise_for_status()
        names = [m.get("name", "") for m in resp.json().get("models", [])]
        wanted = config.LOCAL_LLM_MODEL
        installed = wanted in names or (":" not in wanted and wanted + ":latest" in names)
        return {"reachable": True, "model_installed": installed, "models": names}
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        return {"reachable": False, "model_installed": False, "error": str(exc)}
