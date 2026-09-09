"""登录、JWT 与数据库 RBAC。

仅使用 Python 标准库完成 PBKDF2 密码哈希与 HS256 JWT，避免给现有部署增加依赖。
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from persistence import SessionLocal, get_db, init_db
    from persistence.auth_tables import AuthPermission, AuthRole, AuthUser
    from persistence.notification_tables import NotificationPreference
except ImportError:
    from src.python.persistence import SessionLocal, get_db, init_db
    from src.python.persistence.auth_tables import AuthPermission, AuthRole, AuthUser
    from src.python.persistence.notification_tables import NotificationPreference


JWT_SECRET = os.environ.get("RBAC_JWT_SECRET", "change-this-rbac-secret-in-production")
JWT_TTL_SECONDS = int(os.environ.get("RBAC_JWT_TTL_SECONDS", "28800"))
PBKDF2_ITERATIONS = 210_000
bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/auth", tags=["认证与权限"])

PERMISSIONS = {
    "dashboard:view": "查看监控大屏",
    "gis:view": "查看 GIS 综合态势",
    "alert:view": "查看预警",
    "alert:manage": "管理预警和规则",
    "failure:view": "查看故障预测",
    "risk:view": "查看风险研判",
    "gas-risk:view": "查看燃气风控",
    "hazmat:view": "查看危化品监管",
    "tunnel:view": "查看综合管廊",
    "road-hazard:view": "查看道路塌陷",
    "plan:view": "查看应急预案",
    "asset:view": "查看资产",
    "asset-cost:view": "查看资产成本",
    "work-order:view": "查看工单",
    "work-order:manage": "处理工单",
    "user:manage": "管理平台用户",
    "user:contact:manage": "管理用户联系方式",
    "notification:view": "查看通知记录",
    "notification:send": "发送告警通知",
    "notification:retry": "重试失败通知",
    "notification:config": "管理通知配置",
}

VIEW_PERMISSIONS = [code for code in PERMISSIONS if code.endswith(":view")]
ROLE_DEFINITIONS = {
    "admin": ("系统管理员", ["*"]),
    "operator": ("值班人员", VIEW_PERMISSIONS + [
        "alert:manage", "work-order:manage",
        "notification:view", "notification:send", "notification:retry",
    ]),
    "viewer": ("只读用户", VIEW_PERMISSIONS),
}


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    displayName: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    departmentId: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str

class ForgotPasswordRequest(BaseModel):
    username: str
    contact: str
    newPassword: str

class CreateUserRequest(BaseModel):
    username: str
    displayName: str
    password: str
    roles: list[str]
    email: Optional[str] = None
    phone: Optional[str] = None
    departmentId: Optional[str] = None

class UpdateUserRequest(BaseModel):
    displayName: str
    roles: list[str]
    enabled: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    departmentId: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    newPassword: str

class UpdateContactRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    departmentId: Optional[str] = None

class NotificationPreferenceRequest(BaseModel):
    emailEnabled: bool = True
    smsEnabled: bool = False
    minAlertLevel: str = "ORANGE"
    areaOnly: bool = False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64url(salt)}${_b64url(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _b64decode(salt), int(iterations)
        )
        return hmac.compare_digest(_b64url(digest), expected)
    except (TypeError, ValueError):
        return False


def issue_token(user: AuthUser) -> str:
    now = int(time.time())
    roles = sorted({role.code for role in user.roles})
    permissions = sorted({p.code for role in user.roles for p in role.permissions})
    payload = {
        "sub": str(user.id), "username": user.username, "name": user.display_name,
        "roles": roles, "permissions": permissions, "iat": now, "exp": now + JWT_TTL_SECONDS,
    }
    header_part = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload_part = _b64url(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
    signature = hmac.new(JWT_SECRET.encode(), f"{header_part}.{payload_part}".encode(), hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64url(signature)}"


def decode_token(token: str) -> dict:
    try:
        header_part, payload_part, signature_part = token.split(".")
        expected = hmac.new(
            JWT_SECRET.encode(), f"{header_part}.{payload_part}".encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _b64decode(signature_part)):
            raise ValueError("bad signature")
        payload = json.loads(_b64decode(payload_part))
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录") from exc


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="请先登录")
    return decode_token(credentials.credentials)


def has_permission(user: dict, permission: str) -> bool:
    granted = set(user.get("permissions") or [])
    return "*" in granted or permission in granted

def require_admin(claims: dict = Depends(current_user)) -> dict:
    if not has_permission(claims, "user:manage"):
        raise HTTPException(status_code=403, detail="仅系统管理员可以管理用户")
    return claims

def validate_password(password: str) -> None:
    if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise HTTPException(status_code=400, detail="密码至少 8 位，且必须同时包含字母和数字")

def normalize_email(value: Optional[str]) -> Optional[str]:
    email = (value or "").strip().lower()
    if not email:
        return None
    if len(email) > 128 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    return email

def normalize_phone(value: Optional[str]) -> Optional[str]:
    phone = re.sub(r"[\s-]", "", value or "")
    if not phone:
        return None
    if not re.fullmatch(r"(?:\+?86)?1\d{10}", phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    return phone[-11:]

def ensure_unique_contact(db: Session, email: Optional[str], phone: Optional[str], exclude_user_id: Optional[int] = None) -> None:
    if email:
        query = db.query(AuthUser).filter(AuthUser.email == email)
        if exclude_user_id is not None:
            query = query.filter(AuthUser.id != exclude_user_id)
        if query.first():
            raise HTTPException(status_code=409, detail="该邮箱已绑定其他账号")
    if phone:
        query = db.query(AuthUser).filter(AuthUser.phone == phone)
        if exclude_user_id is not None:
            query = query.filter(AuthUser.id != exclude_user_id)
        if query.first():
            raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")

def mask_phone(phone: Optional[str]) -> str:
    return f"{phone[:3]}****{phone[-4:]}" if phone and len(phone) >= 7 else ""

def mask_email(email: Optional[str]) -> str:
    if not email or "@" not in email:
        return ""
    name, domain = email.split("@", 1)
    visible = name[:2] if len(name) > 2 else name[:1]
    return f"{visible}***@{domain}"

def resolve_roles(db: Session, codes: list[str]) -> list[AuthRole]:
    normalized = sorted(set(codes))
    roles = db.query(AuthRole).filter(AuthRole.code.in_(normalized)).all() if normalized else []
    if len(roles) != len(normalized):
        raise HTTPException(status_code=400, detail="包含无效角色")
    return roles


def seed_rbac() -> None:
    """幂等初始化角色、权限与三个演示账号。密码可通过环境变量覆盖。"""
    init_db()
    db = SessionLocal()
    try:
        permission_rows = {}
        for code, name in {**PERMISSIONS, "*": "全部权限"}.items():
            row = db.query(AuthPermission).filter_by(code=code).first()
            if not row:
                row = AuthPermission(code=code, name=name)
                db.add(row)
                db.flush()
            permission_rows[code] = row

        roles = {}
        for code, (name, permission_codes) in ROLE_DEFINITIONS.items():
            role = db.query(AuthRole).filter_by(code=code).first()
            if not role:
                role = AuthRole(code=code, name=name)
                db.add(role)
            role.permissions = [permission_rows[p] for p in permission_codes]
            roles[code] = role
        db.flush()

        users = [
            ("admin", "系统管理员", "admin", os.environ.get("RBAC_ADMIN_PASSWORD", "Admin@123")),
            ("operator", "值班人员", "operator", os.environ.get("RBAC_OPERATOR_PASSWORD", "Operator@123")),
            ("viewer", "只读用户", "viewer", os.environ.get("RBAC_VIEWER_PASSWORD", "Viewer@123")),
        ]
        for username, display_name, role_code, password in users:
            user = db.query(AuthUser).filter_by(username=username).first()
            if not user:
                user = AuthUser(
                    username=username, display_name=display_name,
                    password_hash=hash_password(password), enabled=True,
                )
                db.add(user)
            user.roles = [roles[role_code]]
        db.commit()
    finally:
        db.close()


def _public_user(user: AuthUser) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "email": user.email or "",
        "phone": user.phone or "",
        "emailMasked": mask_email(user.email),
        "phoneMasked": mask_phone(user.phone),
        "departmentId": user.department_id or "",
        "roles": sorted({role.code for role in user.roles}),
        "permissions": sorted({p.code for role in user.roles for p in role.permissions}),
    }


@router.post("/login", summary="用户名密码登录")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AuthUser).filter_by(username=request.username.strip()).first()
    if not user or not user.enabled or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"accessToken": issue_token(user), "tokenType": "Bearer", "expiresIn": JWT_TTL_SECONDS,
            "user": _public_user(user)}

@router.post("/register", summary="注册平台账号")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    username = request.username.strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{3,31}", username):
        raise HTTPException(status_code=400, detail="用户名须为 4-32 位，并以字母开头")
    if db.query(AuthUser).filter_by(username=username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")

    display_name = request.displayName.strip()
    if not display_name or len(display_name) > 64:
        raise HTTPException(status_code=400, detail="姓名不能为空且不能超过 64 个字符")
    validate_password(request.password)
    email = normalize_email(request.email)
    phone = normalize_phone(request.phone)
    if not email and not phone:
        raise HTTPException(status_code=400, detail="请至少绑定一个邮箱或手机号")
    ensure_unique_contact(db, email, phone)

    viewer_role = db.query(AuthRole).filter_by(code="viewer").first()
    if not viewer_role:
        raise HTTPException(status_code=503, detail="系统角色尚未初始化，请稍后重试")
    user = AuthUser(
        username=username,
        display_name=display_name,
        password_hash=hash_password(request.password),
        email=email,
        phone=phone,
        department_id=(request.departmentId or "").strip() or None,
        enabled=True,
        roles=[viewer_role],
    )
    db.add(user)
    db.commit()
    return {"message": "注册成功，请登录", "username": user.username}


@router.get("/me", summary="获取当前用户")
def me(claims: dict = Depends(current_user), db: Session = Depends(get_db)):
    user = db.get(AuthUser, int(claims["sub"]))
    if not user or not user.enabled:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    return _public_user(user)

@router.put("/me/contact", summary="修改自己的联系方式")
def update_my_contact(request: UpdateContactRequest, claims: dict = Depends(current_user), db: Session = Depends(get_db)):
    user = db.get(AuthUser, int(claims["sub"]))
    if not user or not user.enabled:
        raise HTTPException(status_code=404, detail="用户不存在或已停用")
    email = normalize_email(request.email)
    phone = normalize_phone(request.phone)
    ensure_unique_contact(db, email, phone, user.id)
    user.email = email
    user.phone = phone
    user.department_id = (request.departmentId or "").strip() or None
    db.commit()
    db.refresh(user)
    return _public_user(user)

def _preference_for(db: Session, user_id: int) -> NotificationPreference:
    preference = db.query(NotificationPreference).filter_by(user_id=user_id).first()
    if not preference:
        preference = NotificationPreference(user_id=user_id)
        db.add(preference)
        db.commit()
        db.refresh(preference)
    return preference

def _public_preference(preference: NotificationPreference) -> dict:
    return {
        "emailEnabled": preference.email_enabled,
        "smsEnabled": preference.sms_enabled,
        "minAlertLevel": preference.min_alert_level,
        "areaOnly": preference.area_only,
    }

@router.get("/me/notification-preference", summary="获取自己的通知偏好")
def get_my_notification_preference(claims: dict = Depends(current_user), db: Session = Depends(get_db)):
    return _public_preference(_preference_for(db, int(claims["sub"])))

@router.put("/me/notification-preference", summary="修改自己的通知偏好")
def update_my_notification_preference(request: NotificationPreferenceRequest, claims: dict = Depends(current_user), db: Session = Depends(get_db)):
    level = request.minAlertLevel.upper()
    if level not in {"BLUE", "YELLOW", "ORANGE", "RED"}:
        raise HTTPException(status_code=400, detail="最低告警等级无效")
    preference = _preference_for(db, int(claims["sub"]))
    preference.email_enabled = request.emailEnabled
    preference.sms_enabled = request.smsEnabled
    preference.min_alert_level = level
    preference.area_only = request.areaOnly
    db.commit()
    db.refresh(preference)
    return _public_preference(preference)

@router.post("/change-password", summary="修改自己的密码")
def change_password(request: ChangePasswordRequest, claims: dict = Depends(current_user), db: Session = Depends(get_db)):
    user = db.get(AuthUser, int(claims["sub"]))
    if not user or not verify_password(request.currentPassword, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    validate_password(request.newPassword)
    user.password_hash = hash_password(request.newPassword)
    db.commit()
    return {"message": "密码修改成功，请重新登录"}

@router.post("/forgot-password", summary="通过已绑定联系方式重置密码")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """适用于校内实训环境的账号找回流程。

    用户名与已绑定邮箱或手机号必须同时匹配。生产环境应替换为短信/邮件验证码或一次性链接。
    """
    username = request.username.strip()
    raw_contact = request.contact.strip()
    user = db.query(AuthUser).filter_by(username=username).first()
    if not user or not user.enabled:
        raise HTTPException(status_code=400, detail="账号或绑定联系方式不正确")

    matched = False
    if "@" in raw_contact:
        matched = bool(user.email and hmac.compare_digest(user.email, normalize_email(raw_contact) or ""))
    else:
        matched = bool(user.phone and hmac.compare_digest(user.phone, normalize_phone(raw_contact) or ""))
    if not matched:
        raise HTTPException(status_code=400, detail="账号或绑定联系方式不正确")

    validate_password(request.newPassword)
    user.password_hash = hash_password(request.newPassword)
    db.commit()
    return {"message": "密码重置成功，请使用新密码登录"}

@router.get("/roles", summary="角色清单")
def list_roles(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    return [{"code": role.code, "name": role.name} for role in db.query(AuthRole).order_by(AuthRole.id).all()]

@router.get("/users", summary="用户清单")
def list_users(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    return [_public_user(user) | {"enabled": user.enabled} for user in db.query(AuthUser).order_by(AuthUser.id).all()]

@router.post("/users", summary="新增用户")
def create_user(request: CreateUserRequest, _: dict = Depends(require_admin), db: Session = Depends(get_db)):
    username = request.username.strip()
    if not username or db.query(AuthUser).filter_by(username=username).first():
        raise HTTPException(status_code=409, detail="用户名为空或已存在")
    validate_password(request.password)
    email = normalize_email(request.email)
    phone = normalize_phone(request.phone)
    ensure_unique_contact(db, email, phone)
    user = AuthUser(username=username, display_name=request.displayName.strip() or username,
                    email=email, phone=phone, department_id=(request.departmentId or "").strip() or None,
                    password_hash=hash_password(request.password), enabled=True, roles=resolve_roles(db, request.roles))
    db.add(user); db.commit(); db.refresh(user)
    return _public_user(user) | {"enabled": user.enabled}

@router.put("/users/{user_id}", summary="更新用户")
def update_user(user_id: int, request: UpdateUserRequest, claims: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(AuthUser, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == int(claims["sub"]) and not request.enabled: raise HTTPException(status_code=400, detail="不能停用当前登录账号")
    user.display_name = request.displayName.strip() or user.username
    email = normalize_email(request.email)
    phone = normalize_phone(request.phone)
    ensure_unique_contact(db, email, phone, user.id)
    user.email = email
    user.phone = phone
    user.department_id = (request.departmentId or "").strip() or None
    user.enabled = request.enabled
    user.roles = resolve_roles(db, request.roles)
    db.commit()
    return _public_user(user) | {"enabled": user.enabled}

@router.put("/users/{user_id}/contact", summary="管理员维护用户联系方式")
def update_user_contact(user_id: int, request: UpdateContactRequest, _: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(AuthUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    email = normalize_email(request.email)
    phone = normalize_phone(request.phone)
    ensure_unique_contact(db, email, phone, user.id)
    user.email = email
    user.phone = phone
    user.department_id = (request.departmentId or "").strip() or None
    db.commit()
    db.refresh(user)
    return _public_user(user) | {"enabled": user.enabled}

@router.put("/users/{user_id}/password", summary="管理员重置密码")
def reset_password(user_id: int, request: ResetPasswordRequest, _: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(AuthUser, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")
    validate_password(request.newPassword)
    user.password_hash = hash_password(request.newPassword)
    db.commit()
    return {"message": "密码重置成功"}
