"""工单管理路由 —— 前缀 /workorder（网关 StripPrefix=2 后对应 /api/platform/workorder）"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models_workorder as W
import schemas_workorder as S
from common import (CLOCK_BASE, ok, paginate, parse_iso, split_skills,
                    to_iso, to_space)
from database import get_db

router = APIRouter(prefix="/workorder", tags=["工单管理"])

# 与 mock.channels 完全一致
CHANNELS = [
    {"key": "hotline", "name": "热线报修"},
    {"key": "app", "name": "APP上报"},
    {"key": "patrol", "name": "巡检发现"},
    {"key": "iot", "name": "IoT自动"},
]
CATEGORIES = [
    {"key": "repair", "name": "故障维修"},
    {"key": "inspect", "name": "巡检养护"},
    {"key": "install", "name": "安装工程"},
    {"key": "complaint", "name": "投诉处理"},
]
# 与 mock.process.steps 完全一致
PROCESS_STEPS = [
    {"code": "created", "name": "工单创建"},
    {"code": "dispatched", "name": "派单"},
    {"code": "processing", "name": "处理中"},
    {"code": "completed", "name": "完工确认"},
    {"code": "closed", "name": "关闭"},
]
STATUS_NAME = {
    "pending": "待派单", "assigned": "已派单", "onsite": "处理中",
    "resolved": "已完工", "closed": "已关闭",
}
PRIORITY_NAME = {"urgent": "紧急", "high": "高", "medium": "中", "low": "低"}
STAFF_STATUS_NAME = {"idle": "空闲", "busy": "忙碌", "off": "离线"}
SLA_STATUS_NAME = {"normal": "正常", "warning": "预警", "overdue": "逾期", "escalated": "已升级"}
# step code → 推进后的工单状态
STEP_TO_STATUS = {
    "created": "pending", "dispatched": "assigned", "processing": "onsite",
    "completed": "resolved", "closed": "closed",
}
DEFAULT_SLA = {"urgent": 8, "high": 12, "medium": 24, "low": 48}


# ------------------------------------------------------------------ 内部工具
def _sla_hours_of(priority, explicit):
    if explicit:
        return int(explicit)
    return DEFAULT_SLA.get(priority, 24)


def _deadline(created_at_str, sla_hours):
    base = parse_iso(created_at_str) or CLOCK_BASE
    return to_iso(base + timedelta(hours=sla_hours))


def _order_dict(o: W.WorkOrder) -> dict:
    return {
        "order_id": o.order_id, "title": o.title, "channel": o.channel,
        "category": o.category, "priority": o.priority, "status": o.status,
        "location": o.location or "", "assignee": o.assignee,
        "reporter": o.reporter or "", "created_at": o.created_at,
        "sla_hours": o.sla_hours, "sla_deadline": o.sla_deadline,
        "resolved_at": o.resolved_at, "rating": o.rating,
        "escalated": bool(o.escalated), "description": o.description or "",
        "required_skill": o.required_skill or "",
    }


def _get_order(db: Session, order_id: str) -> W.WorkOrder:
    order = db.query(W.WorkOrder).filter(W.WorkOrder.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"工单不存在：{order_id}")
    return order


def _next_order_id(db: Session) -> str:
    prefix = "WO-2026-"
    seq = db.query(W.WorkOrder).filter(W.WorkOrder.order_id.like(prefix + "%")).count() + 1
    while db.query(W.WorkOrder).filter(
            W.WorkOrder.order_id == f"{prefix}{seq:04d}").first():
        seq += 1
    return f"{prefix}{seq:04d}"


def _skill_for_category(category: str, fallback_skill: Optional[str]) -> str:
    if fallback_skill:
        return fallback_skill
    rule = {"repair": "管道维修", "inspect": "巡检",
            "install": "安装工程", "complaint": "客户服务"}.get(category)
    return rule or "综合运维"


# ------------------------------------------------------------------ 总览
@router.get("/overview", response_model=S.OverviewOut, summary="工单总览统计")
def overview(db: Session = Depends(get_db)):
    q = db.query(W.WorkOrder)
    total = q.count()
    pending = q.filter(W.WorkOrder.status == "pending").count()

    overdue = 0
    for o in q.filter(W.WorkOrder.status.notin_(["resolved", "closed"])).all():
        created = parse_iso(o.created_at) or CLOCK_BASE
        if (CLOCK_BASE - created).total_seconds() / 3600 > (o.sla_hours or 24):
            overdue += 1

    rated = db.query(W.WorkOrder).filter(W.WorkOrder.rating.isnot(None)).all()
    avg = round(sum(r.rating for r in rated) / len(rated), 1) if rated else 0.0
    idle = db.query(W.Staff).filter(W.Staff.status == "idle").count()

    return {"total_orders": total, "pending_dispatch": pending,
            "overdue_orders": overdue, "avg_rating": avg, "staff_idle": idle}


# ------------------------------------------------------------------ 字典
@router.get("/orders/channels", response_model=S.ChannelsOut, summary="渠道与类别字典")
def channels():
    return {"channels": CHANNELS, "categories": CATEGORIES}


@router.get("/orders/stats", summary="工单状态分布统计")
def order_stats(db: Session = Depends(get_db)):
    out = {}
    for st in STATUS_NAME:
        out[st] = db.query(W.WorkOrder).filter(W.WorkOrder.status == st).count()
    return out


# ------------------------------------------------------------------ 列表 / 详情
@router.get("/orders", summary="工单列表（分页 + 条件查询）")
def list_orders(
    page: int = Query(1, ge=0),
    page_size: int = Query(20, ge=1, le=100000),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    channel: Optional[str] = None,
    category: Optional[str] = None,
    assignee: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(W.WorkOrder)
    for field, value in (("status", status), ("priority", priority),
                         ("channel", channel), ("category", category),
                         ("assignee", assignee)):
        if value:
            q = q.filter(getattr(W.WorkOrder, field) == value)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(W.WorkOrder.title.like(like),
                         W.WorkOrder.order_id.like(like),
                         W.WorkOrder.location.like(like),
                         W.WorkOrder.description.like(like)))
    items, total = paginate(q.order_by(W.WorkOrder.created_at.desc(),
                                       W.WorkOrder.order_id.desc()),
                            page, page_size)
    return {"orders": [_order_dict(o) for o in items],
            "total": total, "page": page, "page_size": page_size}


@router.get("/orders/{order_id}", response_model=S.OrderOut, summary="工单详情")
def order_detail(order_id: str, db: Session = Depends(get_db)):
    return _order_dict(_get_order(db, order_id))


# ------------------------------------------------------------------ 新增 / 编辑 / 删除
@router.post("/orders", summary="新增工单（带 order_id 时为编辑）")
def upsert_order(body: S.OrderBody, db: Session = Depends(get_db)):
    payload = body.model_dump()
    title = (body.title or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail="工单标题不能为空")

    order = None
    if body.order_id:
        order = db.query(W.WorkOrder).filter(
            W.WorkOrder.order_id == body.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"工单不存在：{body.order_id}")

    if order is None:
        priority = body.priority or "medium"
        sla = _sla_hours_of(priority, body.sla_hours)
        created = to_iso(CLOCK_BASE)
        order = W.WorkOrder(
            order_id=body.order_id or _next_order_id(db),
            title=title, channel=body.channel or "hotline",
            category=body.category or "repair", priority=priority,
            status=body.status or "pending", location=body.location or "",
            assignee=body.assignee, reporter=body.reporter or "",
            created_at=created, sla_hours=sla, sla_deadline=_deadline(created, sla),
            description=body.description or "",
            required_skill=_skill_for_category(body.category, body.required_skill),
            distance_base=1500,
        )
        db.add(order)
        db.flush()
        db.add(W.OrderTimeline(order_id=order.order_id, step="created",
                               step_name="工单创建", at=to_space(CLOCK_BASE),
                               operator=body.reporter or "系统", note="手动创建"))
        message = "创建成功"
    else:
        for f in ("title", "channel", "category", "priority", "status",
                  "location", "assignee", "reporter", "description", "required_skill"):
            if payload.get(f) is not None and payload.get(f) != "":
                setattr(order, f, payload[f])
        if body.sla_hours:
            order.sla_hours = int(body.sla_hours)
            order.sla_deadline = _deadline(order.created_at, order.sla_hours)
        if order.status in ("resolved", "closed") and not order.resolved_at:
            order.resolved_at = to_iso(CLOCK_BASE)
        message = "保存成功"

    db.commit()
    return ok(message, order_id=order.order_id)


@router.delete("/orders/{order_id}", summary="删除工单")
def delete_order(order_id: str, db: Session = Depends(get_db)):
    order = _get_order(db, order_id)
    db.query(W.OrderTimeline).filter(W.OrderTimeline.order_id == order_id).delete()
    db.delete(order)
    db.commit()
    return ok("删除成功")


# ------------------------------------------------------------------ 过程跟踪
@router.get("/process/{order_id}", response_model=S.ProcessOut, summary="工单流程与时间线")
def get_process(order_id: str, db: Session = Depends(get_db)):
    order = _get_order(db, order_id)
    timeline = (db.query(W.OrderTimeline)
                .filter(W.OrderTimeline.order_id == order_id)
                .order_by(W.OrderTimeline.id.asc()).all())
    index = next((i for i, s in enumerate(PROCESS_STEPS)
                  if STEP_TO_STATUS[s["code"]] == order.status), 0)
    return {
        "steps": PROCESS_STEPS,
        "current_step_index": index,
        "timeline": [{"step": t.step, "step_name": t.step_name, "at": t.at,
                      "operator": t.operator, "note": t.note or ""} for t in timeline],
    }


@router.post("/process/advance", summary="推进工单流程")
def advance_process(body: S.AdvanceBody, db: Session = Depends(get_db)):
    order = _get_order(db, body.order_id)
    if body.step not in STEP_TO_STATUS:
        raise HTTPException(status_code=422,
                            detail=f"未知流程节点：{body.step}")

    new_status = STEP_TO_STATUS[body.step]
    order.status = new_status
    step_name = next(s["name"] for s in PROCESS_STEPS if s["code"] == body.step)
    db.add(W.OrderTimeline(order_id=order.order_id, step=body.step,
                           step_name=step_name, at=to_space(CLOCK_BASE),
                           operator=order.assignee or "系统",
                           note=body.note or step_name))
    if new_status in ("resolved", "closed"):
        order.resolved_at = to_iso(CLOCK_BASE)
        order.rating = order.rating if order.rating is not None else 5
    db.commit()
    return ok("流程已推进")


# ------------------------------------------------------------------ 智能派单
@router.get("/dispatch/recommend", response_model=S.DispatchRecommendOut,
            summary="派单候选与评分")
def dispatch_recommend(
    order_id: str = Query(..., description="工单ID"),
    top_n: int = Query(6, ge=1, le=50),
    db: Session = Depends(get_db),
):
    order = _get_order(db, order_id)
    required = order.required_skill or ""
    staff_list = db.query(W.Staff).all()

    candidates = []
    for s in staff_list:
        skills = split_skills(s.skills)
        match = required in skills or any(required and required in k for k in skills)
        skill_score = 30.0 if match else (12.0 if skills else 5.0)
        dist_score = max(0.0, round(25 - s.distance_m / 400.0, 1))
        rating_score = round(s.avg_rating * 4.5, 1)
        load_score = max(0.0, round(18 - s.active_orders * 4, 1))
        total = round(skill_score + dist_score + rating_score + load_score, 1)
        candidates.append({
            "staff_id": s.staff_id, "name": s.name, "skills": skills,
            "status": s.status, "status_name": STAFF_STATUS_NAME.get(s.status, s.status),
            "location": s.location or "", "distance_m": s.distance_m,
            "skill_match": match, "avg_rating": s.avg_rating,
            "total_score": total,
            "score_breakdown": {"技能匹配": skill_score, "距离": dist_score,
                                "评分": rating_score, "负载": load_score},
        })

    candidates.sort(key=lambda c: (-int(c["skill_match"]), -c["total_score"]))
    candidates = candidates[:top_n]

    if candidates:
        top = candidates[0]
        reason = "技能匹配且距离最近" if top["skill_match"] else "综合评分最高"
        recommendation = f"推荐{top['name']}，{reason}"
    else:
        recommendation = "暂无可用人员"

    return {"order_id": order.order_id, "required_skill": required,
            "location": order.location or "", "candidates": candidates,
            "recommendation": recommendation}


@router.post("/dispatch/assign", summary="派单（指派处理人）")
def assign_order(body: S.AssignBody, db: Session = Depends(get_db)):
    order = _get_order(db, body.order_id)
    staff = db.query(W.Staff).filter(W.Staff.staff_id == body.staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail=f"人员不存在：{body.staff_id}")

    order.assignee = staff.name
    order.status = "assigned"
    staff.active_orders = (staff.active_orders or 0) + 1
    if staff.active_orders >= 3:
        staff.status = "busy"
    db.add(W.OrderTimeline(order_id=order.order_id, step="dispatched",
                           step_name="派单", at=to_space(CLOCK_BASE),
                           operator="调度中心", note=f"指派给{staff.name}"))
    db.commit()
    return ok("派单成功")


@router.get("/dispatch/logs", summary="派单记录")
def dispatch_logs(limit: int = Query(20, ge=1, le=500),
                  db: Session = Depends(get_db)):
    rows = (db.query(W.OrderTimeline)
            .filter(W.OrderTimeline.step == "dispatched")
            .order_by(W.OrderTimeline.id.desc()).limit(limit).all())
    return {"logs": [{"order_id": r.order_id, "at": r.at,
                      "operator": r.operator, "note": r.note or ""} for r in rows]}


# ------------------------------------------------------------------ 运维人员
@router.get("/staff", response_model=S.StaffListOut, summary="人员列表（分页）")
def list_staff(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0, le=100000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(W.Staff)
    if status:
        q = q.filter(W.Staff.status == status)
    p = page if page else 1
    size = page_size if (page and page_size) else 100000
    items, total = paginate(q.order_by(W.Staff.staff_id.asc()), p, size)
    return {"staff": [{"staff_id": s.staff_id, "name": s.name,
                       "skills": split_skills(s.skills), "status": s.status,
                       "location": s.location or "", "phone": s.phone or "",
                       "completed_orders": s.completed_orders,
                       "avg_rating": s.avg_rating} for s in items],
            "total": total}


@router.get("/staff/workload", response_model=S.WorkloadListOut, summary="人员工作负载")
def staff_workload(db: Session = Depends(get_db)):
    rows = db.query(W.Staff).order_by(W.Staff.staff_id.asc()).all()
    return {"workload": [
        {"staff_id": s.staff_id, "name": s.name, "status": s.status,
         "status_name": STAFF_STATUS_NAME.get(s.status, s.status),
         "active_orders": s.active_orders or 0,
         "completed_orders": s.completed_orders,
         "avg_rating": s.avg_rating} for s in rows]}


@router.get("/staff/{staff_id}", response_model=S.StaffOut, summary="人员详情")
def staff_detail(staff_id: str, db: Session = Depends(get_db)):
    s = db.query(W.Staff).filter(W.Staff.staff_id == staff_id).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"人员不存在：{staff_id}")
    return {"staff_id": s.staff_id, "name": s.name, "skills": split_skills(s.skills),
            "status": s.status, "location": s.location or "", "phone": s.phone or "",
            "completed_orders": s.completed_orders, "avg_rating": s.avg_rating}


# ------------------------------------------------------------------ SLA
@router.get("/sla/rules", response_model=S.SlaRulesOut, summary="SLA 规则")
def sla_rules(db: Session = Depends(get_db)):
    rows = db.query(W.SlaRule).all()
    order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    rows.sort(key=lambda r: order.get(r.priority, 9))
    return {"rules": [{"priority": r.priority, "priority_name": r.priority_name,
                       "response_hours": r.response_hours,
                       "warning_threshold": r.warning_threshold,
                       "escalate_multiplier": r.escalate_multiplier,
                       "escalate_target": r.escalate_target,
                       "desc": r.desc} for r in rows]}


@router.get("/sla/monitor", response_model=S.SlaMonitorOut, summary="SLA 实时监控")
def sla_monitor(db: Session = Depends(get_db)):
    rules = {r.priority: r for r in db.query(W.SlaRule).all()}
    orders = (db.query(W.WorkOrder)
              .filter(W.WorkOrder.status.notin_(["resolved", "closed"]))
              .order_by(W.WorkOrder.priority.asc()).all())
    prio_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    orders.sort(key=lambda o: (prio_order.get(o.priority, 9),
                               o.created_at or ""))

    items, summary = [], {"normal": 0, "warning": 0, "overdue": 0, "escalated": 0}
    for o in orders:
        created = parse_iso(o.created_at) or CLOCK_BASE
        elapsed = round((CLOCK_BASE - created).total_seconds() / 3600.0, 1)
        sla = o.sla_hours or 24
        remaining = round(sla - elapsed, 1)

        if o.escalated:
            st = "escalated"
        elif remaining < 0:
            st = "overdue"
        else:
            rule = rules.get(o.priority)
            warn_ratio = 1 - (rule.warning_threshold if rule else 0.75)
            st = "warning" if remaining / sla <= warn_ratio else "normal"
        summary[st] += 1

        items.append({
            "order_id": o.order_id, "title": o.title, "priority": o.priority,
            "priority_name": PRIORITY_NAME.get(o.priority, o.priority),
            "status": o.status, "status_name": STATUS_NAME.get(o.status, o.status),
            "assignee": o.assignee, "elapsed_hours": elapsed, "sla_hours": sla,
            "remaining_hours": remaining, "sla_status": st,
            "sla_status_name": SLA_STATUS_NAME[st], "sla_deadline": o.sla_deadline,
        })

    return {"monitored": len(items), "summary": summary, "items": items}


@router.post("/sla/escalate", summary="SLA 升级")
def escalate(order_id: str = Query(..., description="工单ID"),
             db: Session = Depends(get_db)):
    order = _get_order(db, order_id)
    order.escalated = True
    db.add(W.OrderTimeline(order_id=order.order_id, step="processing",
                           step_name="SLA升级", at=to_space(CLOCK_BASE),
                           operator="SLA监控", note="超时自动升级至运维主管"))
    db.commit()
    return ok("已升级")
