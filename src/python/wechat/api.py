"""微信公众号 API —— access_token 管理 + 客服消息发送

用于异步推送：收到用户消息后先回 success，后台调大模型生成答案后通过客服消息接口推送。
"""
import time

import httpx

from assistant.config import WECHAT_APPID, WECHAT_APPSECRET

_access_token: str = ""
_token_expires_at: float = 0.0


def _get_access_token() -> str:
    global _access_token, _token_expires_at
    if _access_token and time.time() < _token_expires_at:
        return _access_token
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": WECHAT_APPID,
        "secret": WECHAT_APPSECRET,
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url, params=params).json()
    if "access_token" not in resp:
        raise RuntimeError(f"获取 access_token 失败: {resp}")
    _access_token = resp["access_token"]
    _token_expires_at = time.time() + resp.get("expires_in", 7200) - 300
    return _access_token


def send_customer_service_text(openid: str, text: str) -> dict:
    """通过客服消息接口给用户发文本消息"""
    token = _get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={token}"
    body = {
        "touser": openid,
        "msgtype": "text",
        "text": {"content": text},
    }
    with httpx.Client(timeout=10.0) as client:
        return client.post(url, json=body).json()


def is_configured() -> bool:
    return bool(WECHAT_APPID and WECHAT_APPSECRET)
