"""微信公众号 / 测试号对接 —— 消息回调 + 自动回复

流程：
  微信用户发消息 → 微信服务器 POST XML → 本接口解析 → 调用助手 → XML 回复

配置：
  在 .env 中设置 WECHAT_TOKEN（与微信公众平台/测试号后台填的 Token 一致）
"""
import hashlib
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict
from typing import Dict, List

from fastapi import Request
from fastapi.responses import PlainTextResponse

from assistant.service import run_chat

# 每个用户保留最近对话（内存，重启清空，够用）
_sessions: Dict[str, List[Dict[str, str]]] = OrderedDict()
_MAX_SESSIONS = 200

# 已处理消息 ID（防微信重试重复调用）
_seen_msg_ids: OrderedDict = OrderedDict()
_MAX_SEEN = 500


def _token() -> str:
    from assistant.config import os
    return os.environ.get("WECHAT_TOKEN", "ai_platform_2026")


def _check_sig(signature: str, timestamp: str, nonce: str) -> bool:
    tmp = sorted([_token(), timestamp, nonce])
    return hashlib.sha1("".join(tmp).encode()).hexdigest() == signature


def _parse_xml(body: bytes) -> dict:
    root = ET.fromstring(body)
    return {child.tag: (child.text or "") for child in root}


def _text_reply(to_user: str, from_user: str, content: str) -> str:
    return (
        "<xml>"
        "<ToUserName><![CDATA[%s]]></ToUserName>"
        "<FromUserName><![CDATA[%s]]></FromUserName>"
        "<CreateTime>%d</CreateTime>"
        "<MsgType><![CDATA[text]]></MsgType>"
        "<Content><![CDATA[%s]]></Content>"
        "</xml>"
    ) % (to_user, from_user, int(time.time()), content)


def _evict(d: OrderedDict, max_size: int):
    while len(d) > max_size:
        d.popitem(last=False)


async def wechat_verify(request: Request) -> PlainTextResponse:
    """GET /wechat — 微信服务器 URL 验证"""
    p = request.query_params
    if _check_sig(p.get("signature", ""), p.get("timestamp", ""), p.get("nonce", "")):
        return PlainTextResponse(p.get("echostr", ""))
    return PlainTextResponse("forbidden", status_code=403)


async def wechat_message(request: Request) -> PlainTextResponse:
    """POST /wechat — 接收用户消息，调用助手，回复结果"""
    body = await request.body()
    try:
        msg = _parse_xml(body)
    except ET.ParseError:
        return PlainTextResponse("success")

    msg_type = msg.get("MsgType", "")
    content = msg.get("Content", "").strip()
    from_user = msg.get("FromUserName", "")
    to_user = msg.get("ToUserName", "")
    msg_id = msg.get("MsgId", "")

    # 非文本消息
    if msg_type != "text" or not content:
        reply = "你好！我是安塞区城市安全生命线管网AI智慧平台助手，请直接输入问题，例如：\n- 当前有多少工单？\n- 管廊告警情况\n- 打开应急预案"
        return PlainTextResponse(_text_reply(to_user, from_user, reply), media_type="application/xml")

    # 去重：微信 5 秒超时重试
    if msg_id and msg_id in _seen_msg_ids:
        return PlainTextResponse("success")
    if msg_id:
        _seen_msg_ids[msg_id] = True
        _evict(_seen_msg_ids, _MAX_SEEN)

    # 获取/创建用户对话历史
    history = _sessions.setdefault(from_user, [])

    # 调用助手
    result = run_chat(content, history)
    answer = result.get("answer", "")

    if not result.get("success"):
        answer = "抱歉，助手暂时出现问题，请稍后重试。"

    # 追加到历史
    history.append({"role": "user", "content": content})
    history.append({"role": "assistant", "content": answer})
    if len(history) > 20:
        _sessions[from_user] = history[-20:]
    _evict(_sessions, _MAX_SESSIONS)

    return PlainTextResponse(_text_reply(to_user, from_user, answer), media_type="application/xml")
