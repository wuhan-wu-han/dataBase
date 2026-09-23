"""统一验证码服务：Redis 存储、频率限制、SMTP 邮件和可替换短信通道。"""

import hashlib
import json
import logging
import os
import secrets
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _load_env() -> None:
    """加载同目录 .env；已存在的系统环境变量优先。"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()

try:
    import redis
except ImportError:  # 启动时给出明确错误，不让验证码静默退化为不安全的前端校验
    redis = None

# 验证码至少保留 5 分钟；即使演示电脑残留了更短的环境变量也不会提前过期。
CODE_TTL = max(300, int(os.environ.get("VERIFICATION_CODE_TTL", "300")))
TOKEN_TTL = int(os.environ.get("VERIFICATION_TOKEN_TTL", "600"))
SEND_COOLDOWN = int(os.environ.get("VERIFICATION_SEND_COOLDOWN", "60"))
HOURLY_LIMIT = int(os.environ.get("VERIFICATION_HOURLY_LIMIT", "5"))
MAX_ATTEMPTS = int(os.environ.get("VERIFICATION_MAX_ATTEMPTS", "5"))
CODE_SECRET = os.environ.get("VERIFICATION_SECRET", os.environ.get("RBAC_JWT_SECRET", "verification-secret"))


def _client():
    if redis is None:
        raise HTTPException(status_code=503, detail="验证码服务依赖未安装，请安装 redis")
    try:
        client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            password=os.environ.get("REDIS_PASSWORD") or None,
            db=int(os.environ.get("REDIS_VERIFICATION_DB", "1")),
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return client
    except Exception as exc:
        logger.error("Redis verification service unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="验证码服务暂时不可用，请稍后重试") from exc


def _digest(code: str, scene: str, channel: str, target: str) -> str:
    raw = f"{CODE_SECRET}:{scene}:{channel}:{target}:{code}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _prefix(scene: str, channel: str, target: str) -> str:
    identity = hashlib.sha256(target.encode("utf-8")).hexdigest()[:24]
    return f"verify:{scene}:{channel}:{identity}"


class VerificationSender:
    def send(self, target: str, code: str, scene: str) -> None:
        raise NotImplementedError


class EmailVerificationSender(VerificationSender):
    def send(self, target: str, code: str, scene: str) -> None:
        host = os.environ.get("SMTP_HOST", "").strip()
        username = os.environ.get("SMTP_USER", os.environ.get("SMTP_USERNAME", "")).strip()
        password = os.environ.get("SMTP_PASSWORD", "")
        if not host or not username or not password:
            raise HTTPException(status_code=503, detail="邮件服务配置不完整")
        labels = {"register": "注册账号", "forgot_password": "重置密码", "change_contact": "修改联系方式"}
        message = EmailMessage()
        message["Subject"] = f"【安塞智慧平台】{labels.get(scene, '身份验证')}验证码"
        message["From"] = os.environ.get("SMTP_FROM", username)
        message["To"] = target
        message.set_content(
            f"您正在进行{labels.get(scene, '身份验证')}。\n\n验证码：{code}\n有效期：{CODE_TTL // 60} 分钟。\n\n如非本人操作，请忽略本邮件。"
        )
        port = int(os.environ.get("SMTP_PORT", "465"))
        if os.environ.get("SMTP_SSL", "true").lower() == "true":
            with smtplib.SMTP_SSL(host, port, timeout=10, context=ssl.create_default_context()) as client:
                client.login(username, password)
                client.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=10) as client:
                client.starttls(context=ssl.create_default_context())
                client.login(username, password)
                client.send_message(message)


class SmsVerificationSender(VerificationSender):
    """短信通道抽象。console 用于开发；aliyun/tencent 可后续实现同一接口。"""
    def send(self, target: str, code: str, scene: str) -> None:
        provider = os.environ.get("SMS_PROVIDER", "console").lower()
        if provider == "console":
            logger.warning("[SMS-DEV] target=%s scene=%s code=%s", target[-4:].rjust(len(target), "*"), scene, code)
            return
        raise HTTPException(status_code=503, detail=f"短信服务商 {provider} 尚未配置")


SENDERS = {"email": EmailVerificationSender(), "sms": SmsVerificationSender()}


def send_code(scene: str, channel: str, target: str) -> int:
    client = _client()
    base = _prefix(scene, channel, target)
    if client.exists(f"{base}:cooldown"):
        raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")
    hour_key = f"{base}:hour"
    if int(client.get(hour_key) or 0) >= HOURLY_LIMIT:
        raise HTTPException(status_code=429, detail="本小时发送次数已达上限")
    code = f"{secrets.randbelow(1_000_000):06d}"
    SENDERS[channel].send(target, code, scene)
    pipe = client.pipeline()
    pipe.setex(f"{base}:code", CODE_TTL, json.dumps({"hash": _digest(code, scene, channel, target), "attempts": 0}))
    pipe.setex(f"{base}:cooldown", SEND_COOLDOWN, "1")
    pipe.incr(hour_key)
    pipe.expire(hour_key, 3600)
    pipe.execute()
    return CODE_TTL


def verify_code(scene: str, channel: str, target: str, code: str) -> str:
    client = _client()
    base = _prefix(scene, channel, target)
    code_key = f"{base}:code"
    raw = client.get(code_key)
    if not raw:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    record = json.loads(raw)
    if int(record.get("attempts", 0)) >= MAX_ATTEMPTS:
        client.delete(code_key)
        raise HTTPException(status_code=400, detail="验证码错误次数过多，请重新获取")
    if not secrets.compare_digest(record.get("hash", ""), _digest(code, scene, channel, target)):
        record["attempts"] = int(record.get("attempts", 0)) + 1
        client.setex(code_key, max(1, client.ttl(code_key)), json.dumps(record))
        raise HTTPException(status_code=400, detail="验证码错误")
    token = secrets.token_urlsafe(32)
    client.delete(code_key)
    client.setex(f"verify:token:{token}", TOKEN_TTL, json.dumps({
        "scene": scene, "channel": channel, "target": target
    }))
    return token


def consume_token(token: str, scene: str, target: Optional[str] = None) -> dict:
    client = _client()
    key = f"verify:token:{token}"
    raw = client.get(key)
    if not raw:
        raise HTTPException(status_code=400, detail="验证凭证无效或已过期")
    payload = json.loads(raw)
    if payload.get("scene") != scene or (target and payload.get("target") != target):
        raise HTTPException(status_code=400, detail="验证凭证与当前操作不匹配")
    client.delete(key)
    return payload
