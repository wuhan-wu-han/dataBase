"""统一告警通知服务：任务持久化、SMTP 邮件、演示短信和失败重试。"""

import os
import smtplib
import ssl
import threading
import time
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session


def _load_notification_env() -> None:
    """加载本模块旁的 .env；系统环境变量优先，不覆盖部署配置。"""
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


_load_notification_env()

try:
    from auth import current_user, has_permission, mask_email, mask_phone
    from persistence import SessionLocal, get_db
    from persistence.auth_tables import AuthUser
    from persistence.notification_tables import NotificationPreference, NotificationTask
except ImportError:
    from src.python.auth import current_user, has_permission, mask_email, mask_phone
    from src.python.persistence import SessionLocal, get_db
    from src.python.persistence.auth_tables import AuthUser
    from src.python.persistence.notification_tables import NotificationPreference, NotificationTask


# 外部统一地址为 /api/platform/notifications/**；Vite 与 Java 网关会剥离
# /api/platform 前缀，因此平台服务内部注册为 /notifications/**。
router = APIRouter(prefix="/notifications", tags=["告警通知"])

LEVEL_RANK = {"BLUE": 1, "YELLOW": 2, "ORANGE": 3, "RED": 4}
VALID_CHANNELS = {"EMAIL", "SMS"}
AUTO_ENABLED = os.environ.get("NOTIFICATION_AUTO_ENABLED", "false").lower() == "true"
INTERNAL_TOKEN = os.environ.get("NOTIFICATION_INTERNAL_TOKEN", "change-notification-internal-token")


class NotificationSendRequest(BaseModel):
    alertId: str
    userIds: list[int]
    channels: list[str]
    subject: str
    content: str
    alertLevel: Optional[str] = None
    businessType: Optional[str] = None
    areaId: Optional[str] = None


class NotificationAlertRequest(BaseModel):
    alertId: str
    alertLevel: str
    title: str
    deviceId: Optional[str] = None
    deviceType: Optional[str] = None
    areaId: Optional[str] = None
    metricKey: Optional[str] = None
    metricValue: Optional[str] = None
    thresholdValue: Optional[str] = None
    eventTimestamp: Optional[int] = None


class ConfiguredEmailRequest(BaseModel):
    alertId: str
    subject: str
    content: str
    alertLevel: Optional[str] = None
    businessType: Optional[str] = None
    areaId: Optional[str] = None


def require_permission(permission: str):
    def dependency(claims: dict = Depends(current_user)) -> dict:
        if not has_permission(claims, permission):
            raise HTTPException(status_code=403, detail="当前角色无权执行此操作")
        return claims
    return dependency


def _preference(db: Session, user_id: int) -> NotificationPreference:
    row = db.query(NotificationPreference).filter_by(user_id=user_id).first()
    if not row:
        row = NotificationPreference(user_id=user_id)
        db.add(row)
        db.flush()
    return row


def _mask_recipient(task: NotificationTask) -> str:
    return mask_email(task.recipient) if task.channel == "EMAIL" else mask_phone(task.recipient)


def _task_dict(task: NotificationTask) -> dict:
    return {
        "id": task.id,
        "alertId": task.alert_id,
        "userId": task.user_id,
        "recipientName": task.recipient_name or "",
        "channel": task.channel,
        "recipient": _mask_recipient(task),
        "subject": task.subject,
        "alertLevel": task.alert_level or "",
        "businessType": task.business_type or "",
        "areaId": task.area_id or "",
        "status": task.status,
        "retryCount": task.retry_count,
        "maxRetryCount": task.max_retry_count,
        "errorMessage": task.error_message or "",
        "providerMessage": task.provider_message or "",
        "createdAt": task.created_at.isoformat(sep=" ", timespec="seconds") if task.created_at else None,
        "sentAt": task.sent_at.isoformat(sep=" ", timespec="seconds") if task.sent_at else None,
    }


class EmailSender:
    def send(self, task: NotificationTask) -> str:
        enabled = os.environ.get("ALERT_MAIL_ENABLED", os.environ.get("NOTIFICATION_EMAIL_ENABLED", "true"))
        if enabled.lower() != "true":
            raise RuntimeError("邮件通知通道未启用")
        host = os.environ.get("SMTP_HOST", "").strip()
        username = os.environ.get("SMTP_USER", os.environ.get("SMTP_USERNAME", "")).strip()
        password = os.environ.get("SMTP_PASSWORD", "")
        if not host or not username or not password:
            raise RuntimeError("SMTP 配置不完整")
        port = int(os.environ.get("SMTP_PORT", "465"))
        use_ssl = os.environ.get("SMTP_SSL", "true").lower() == "true"
        message = EmailMessage()
        message["Subject"] = task.subject
        message["From"] = os.environ.get("SMTP_FROM", username)
        message["To"] = task.recipient
        message.set_content(task.content)
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10, context=ssl.create_default_context()) as client:
                client.login(username, password)
                client.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=10) as client:
                client.starttls(context=ssl.create_default_context())
                client.login(username, password)
                client.send_message(message)
        return "SMTP_ACCEPTED"


class SmsSender:
    def send(self, task: NotificationTask) -> str:
        if os.environ.get("NOTIFICATION_SMS_ENABLED", "true").lower() != "true":
            raise RuntimeError("短信通知通道未启用")
        if os.environ.get("NOTIFICATION_SMS_DEMO_MODE", "true").lower() == "true":
            return "DEMO_SMS_ACCEPTED"
        raise RuntimeError("尚未配置真实短信服务商")


SENDERS = {"EMAIL": EmailSender(), "SMS": SmsSender()}


def _send_task(db: Session, task: NotificationTask) -> None:
    task.status = "SENDING"
    task.retry_count = (task.retry_count or 0) + 1
    task.updated_at = datetime.now()
    db.commit()
    try:
        task.provider_message = SENDERS[task.channel].send(task)
        task.status = "SUCCESS"
        task.error_message = None
        task.next_retry_at = None
        task.sent_at = datetime.now()
    except Exception as exc:
        task.status = "FAILED"
        task.error_message = str(exc)[:500]
        delays = (1, 5, 15)
        if task.retry_count < task.max_retry_count:
            delay = delays[min(task.retry_count - 1, len(delays) - 1)]
            task.next_retry_at = datetime.now() + timedelta(minutes=delay)
        else:
            task.next_retry_at = None
    task.updated_at = datetime.now()
    db.commit()


def _create_tasks(db: Session, request: NotificationSendRequest, honor_preference: bool = True) -> tuple[list[NotificationTask], list[str]]:
    channels = {channel.upper() for channel in request.channels}
    if not channels or not channels.issubset(VALID_CHANNELS):
        raise HTTPException(status_code=400, detail="通知通道仅支持 EMAIL 或 SMS")
    users = db.query(AuthUser).filter(AuthUser.id.in_(set(request.userIds)), AuthUser.enabled.is_(True)).all()
    user_map = {user.id: user for user in users}
    tasks = []
    skipped = []
    for user_id in request.userIds:
        user = user_map.get(user_id)
        if not user:
            skipped.append(f"用户 {user_id} 不存在或已停用")
            continue
        preference = _preference(db, user.id)
        for channel in sorted(channels):
            if honor_preference and channel == "EMAIL" and not preference.email_enabled:
                skipped.append(f"{user.display_name}未开启邮件通知")
                continue
            if honor_preference and channel == "SMS" and not preference.sms_enabled:
                skipped.append(f"{user.display_name}未开启短信通知")
                continue
            recipient = user.email if channel == "EMAIL" else user.phone
            if not recipient:
                skipped.append(f"{user.display_name}未绑定{'邮箱' if channel == 'EMAIL' else '手机号'}")
                continue
            existing = db.query(NotificationTask).filter_by(
                alert_id=request.alertId, user_id=user.id, channel=channel
            ).first()
            if existing:
                skipped.append(f"{user.display_name}的{channel}通知已创建")
                continue
            task = NotificationTask(
                alert_id=request.alertId,
                user_id=user.id,
                channel=channel,
                recipient=recipient,
                recipient_name=user.display_name,
                subject=request.subject.strip()[:200],
                content=request.content.strip(),
                alert_level=(request.alertLevel or "").upper() or None,
                business_type=request.businessType,
                area_id=request.areaId,
                status="PENDING",
            )
            db.add(task)
            db.flush()
            tasks.append(task)
    db.commit()
    return tasks, skipped


@router.get("/recipients", summary="可选通知接收人")
def list_recipients(_: dict = Depends(require_permission("notification:send")), db: Session = Depends(get_db)):
    users = db.query(AuthUser).filter(AuthUser.enabled.is_(True)).order_by(AuthUser.display_name).all()
    return [{
        "id": user.id,
        "displayName": user.display_name,
        "username": user.username,
        "email": mask_email(user.email),
        "phone": mask_phone(user.phone),
        "hasEmail": bool(user.email),
        "hasPhone": bool(user.phone),
    } for user in users]


@router.post("/send", summary="手动发送告警通知")
def send_notification(request: NotificationSendRequest, _: dict = Depends(require_permission("notification:send")), db: Session = Depends(get_db)):
    if not request.alertId.strip() or not request.subject.strip() or not request.content.strip():
        raise HTTPException(status_code=400, detail="告警编号、标题和内容不能为空")
    tasks, skipped = _create_tasks(db, request)
    for task in tasks:
        _send_task(db, task)
    return {"created": len(tasks), "skipped": skipped, "items": [_task_dict(task) for task in tasks]}


@router.post("/send-configured-email", summary="发送告警到系统配置邮箱")
def send_configured_email(
    request: ConfiguredEmailRequest,
    claims: dict = Depends(require_permission("notification:send")),
    db: Session = Depends(get_db),
):
    recipient = os.environ.get("ALERT_MAIL_TO", "").strip()
    if not recipient:
        raise HTTPException(status_code=503, detail="系统未配置告警收件邮箱")
    if not request.alertId.strip() or not request.subject.strip() or not request.content.strip():
        raise HTTPException(status_code=400, detail="告警编号、标题和内容不能为空")
    user = db.get(AuthUser, int(claims["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="当前用户不存在")
    existing = db.query(NotificationTask).filter_by(
        alert_id=request.alertId.strip(), user_id=user.id, channel="EMAIL"
    ).first()
    if existing:
        if existing.status != "SUCCESS":
            _send_task(db, existing)
        return {"created": 0, "items": [_task_dict(existing)]}
    task = NotificationTask(
        alert_id=request.alertId.strip(),
        user_id=user.id,
        channel="EMAIL",
        recipient=recipient,
        recipient_name="系统告警邮箱",
        subject=request.subject.strip()[:200],
        content=request.content.strip(),
        alert_level=(request.alertLevel or "").upper() or None,
        business_type=request.businessType,
        area_id=request.areaId,
        status="PENDING",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    _send_task(db, task)
    return {"created": 1, "items": [_task_dict(task)]}


@router.get("", summary="查询通知记录")
def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    channel: Optional[str] = None,
    alertId: Optional[str] = None,
    claims: dict = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = db.query(NotificationTask)
    if not has_permission(claims, "notification:view"):
        query = query.filter(NotificationTask.user_id == int(claims["sub"]))
    if status:
        query = query.filter(NotificationTask.status == status.upper())
    if channel:
        query = query.filter(NotificationTask.channel == channel.upper())
    if alertId:
        query = query.filter(NotificationTask.alert_id.contains(alertId.strip()))
    total = query.count()
    items = query.order_by(NotificationTask.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {"items": [_task_dict(item) for item in items], "total": total, "page": page, "size": size}


@router.post("/{task_id}/retry", summary="重试失败通知")
def retry_notification(task_id: int, _: dict = Depends(require_permission("notification:retry")), db: Session = Depends(get_db)):
    task = db.get(NotificationTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="通知任务不存在")
    if task.status == "SUCCESS":
        raise HTTPException(status_code=400, detail="发送成功的通知无需重试")
    if task.retry_count >= task.max_retry_count:
        task.retry_count = 0
    task.status = "PENDING"
    task.next_retry_at = datetime.now()
    db.commit()
    _send_task(db, task)
    return _task_dict(task)


def _auto_content(alert: NotificationAlertRequest) -> str:
    event_time = datetime.fromtimestamp(alert.eventTimestamp / 1000).strftime("%Y-%m-%d %H:%M:%S") if alert.eventTimestamp else "-"
    return "\n".join([
        f"告警编号：{alert.alertId}",
        f"风险等级：{alert.alertLevel}",
        f"设备编号：{alert.deviceId or '-'}",
        f"设备类型：{alert.deviceType or '-'}",
        f"所属区域：{alert.areaId or '-'}",
        f"监测指标：{alert.metricKey or '-'}",
        f"当前值：{alert.metricValue or '-'}",
        f"阈值：{alert.thresholdValue or '-'}",
        f"发生时间：{event_time}",
        "当前状态：待处理",
    ])


@router.post("/dispatch-alert", summary="高等级告警自动创建通知任务")
def dispatch_alert(
    alert: NotificationAlertRequest,
    x_notification_internal_token: str = Header(""),
    db: Session = Depends(get_db),
):
    if x_notification_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="内部通知凭证无效")
    level = alert.alertLevel.upper()
    if not AUTO_ENABLED or level not in {"ORANGE", "RED"}:
        return {"created": 0, "skipped": ["当前告警等级无需自动通知"]}
    recipients = []
    channels_by_user = {}
    for user in db.query(AuthUser).filter(AuthUser.enabled.is_(True)).all():
        permission_codes = {permission.code for role in user.roles for permission in role.permissions}
        if "*" not in permission_codes and "notification:send" not in permission_codes:
            continue
        preference = _preference(db, user.id)
        if LEVEL_RANK[level] < LEVEL_RANK.get(preference.min_alert_level, 3):
            continue
        if preference.area_only and user.department_id and alert.areaId and user.department_id != alert.areaId:
            continue
        channels = []
        if preference.email_enabled and user.email:
            channels.append("EMAIL")
        if preference.sms_enabled and user.phone:
            channels.append("SMS")
        if channels:
            recipients.append(user.id)
            channels_by_user[user.id] = channels
    created = []
    skipped = []
    for user_id in recipients:
        request = NotificationSendRequest(
            alertId=alert.alertId,
            userIds=[user_id],
            channels=channels_by_user[user_id],
            subject=f"【城市生命线平台】【{level}】{alert.title}",
            content=_auto_content(alert),
            alertLevel=level,
            businessType=alert.deviceType,
            areaId=alert.areaId,
        )
        tasks, task_skipped = _create_tasks(db, request)
        created.extend(tasks)
        skipped.extend(task_skipped)
    return {"created": len(created), "skipped": skipped}


_worker_started = False


def start_notification_worker() -> None:
    global _worker_started
    if _worker_started:
        return
    _worker_started = True

    def work() -> None:
        while True:
            time.sleep(30)
            db = SessionLocal()
            try:
                now = datetime.now()
                tasks = db.query(NotificationTask).filter(
                    NotificationTask.retry_count < NotificationTask.max_retry_count,
                    or_(
                        NotificationTask.status == "PENDING",
                        NotificationTask.status == "FAILED",
                    ),
                    or_(NotificationTask.next_retry_at.is_(None), NotificationTask.next_retry_at <= now),
                ).order_by(NotificationTask.created_at).limit(20).all()
                for task in tasks:
                    _send_task(db, task)
            except Exception:
                db.rollback()
            finally:
                db.close()

    threading.Thread(target=work, name="notification-worker", daemon=True).start()
