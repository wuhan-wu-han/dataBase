"""应急预案路由 —— 前缀 /plan（网关 /api/platform/plan/** StripPrefix=2 后落到此处）"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models_emergency as E
import schemas_emergency as S
from common import CLOCK_BASE, dump_list, json_list, ok, paginate, parse_iso
from database import get_db

router = APIRouter(prefix="/plan", tags=["应急预案"])

LEVEL_ROMAN = {1: "Ⅰ级", 2: "Ⅱ级", 3: "Ⅲ级", 4: "Ⅳ级"}
CABIN_NAME = {"GS": "燃气舱", "EL": "电力舱", "WS": "水舱",
              "CS": "综合舱", "HX": "危化品舱"}


def _logical_today(db: Session):
    latest = db.query(E.LiveMatch).order_by(E.LiveMatch.time.desc()).first()
    if latest and latest.time:
        parsed = parse_iso(latest.time)
        if parsed:
            return parsed.date()
    return CLOCK_BASE.date()


def _stamp_with_tz(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "+08:00"


def _plan_dict(p: E.EmergencyPlan, nodes=None) -> dict:
    return {
        "plan_id": p.plan_id, "plan_name": p.plan_name, "category": p.category,
        "level_min": p.level_min, "level_max": p.level_max, "priority": p.priority,
        "status": p.status, "commander": p.commander or "",
        "scope_cabins": json_list(p.scope_cabins),
        "scope_zones": json_list(p.scope_zones),
        "tags": json_list(p.tags),
        "objective": p.objective or "",
        "created_at": p.created_at, "updated_at": p.updated_at,
        "flow_nodes": [_node_dict(n) for n in (nodes or [])],
    }


def _node_dict(n: E.FlowNode) -> dict:
    return {"node_id": n.node_id, "seq": n.seq, "node_type": n.node_type,
            "title": n.title, "desc": n.desc or "",
            "deadline_min": n.deadline_min, "exit_condition": n.exit_condition or ""}


def _get_plan(db: Session, plan_id: str) -> E.EmergencyPlan:
    plan = db.query(E.EmergencyPlan).filter(
        E.EmergencyPlan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"预案不存在：{plan_id}")
    return plan


def _nodes_of(db: Session, plan_id: str):
    return (db.query(E.FlowNode).filter(E.FlowNode.plan_id == plan_id)
            .order_by(E.FlowNode.seq.asc()).all())


def _next_plan_id(db: Session) -> str:
    seq = db.query(E.EmergencyPlan).count() + 1
    pid = f"EP-2026-{seq:04d}"
    while db.query(E.EmergencyPlan).filter(
            E.EmergencyPlan.plan_id == pid).first():
        seq += 1
        pid = f"EP-2026-{seq:04d}"
    return pid


def _cat_name(db: Session, code: str) -> str:
    c = db.query(E.PlanCategory).filter(E.PlanCategory.code == code).first()
    return c.name if c else (code or "")


# ============================================================ 总览与字典
@router.get("/overview", response_model=S.OverviewOut, summary="预案总览统计")
def overview(db: Session = Depends(get_db)):
    today = _logical_today(db)
    total = db.query(E.EmergencyPlan).count()
    active = db.query(E.EmergencyPlan).filter(
        E.EmergencyPlan.status == "active").count()
    matches = sum(1 for m in db.query(E.LiveMatch).all()
                  if (parse_iso(m.time) or CLOCK_BASE).date() == today)
    drills = sum(1 for a in db.query(E.Activation).all()
                 if "演练" in (a.trigger or "")
                 and (parse_iso(a.activated_at) or CLOCK_BASE).date() == today)
    return {"total_plans": total, "active_plans": active,
            "today_match_count": matches, "today_drill_count": drills}


@router.get("/categories", summary="事件类别（含预案数量统计）")
def categories(db: Session = Depends(get_db)):
    out = []
    for c in db.query(E.PlanCategory).all():
        plan_count = db.query(E.EmergencyPlan).filter(
            E.EmergencyPlan.category == c.code).count()
        active_count = db.query(E.EmergencyPlan).filter(
            E.EmergencyPlan.category == c.code,
            E.EmergencyPlan.status == "active").count()
        out.append({"code": c.code, "name": c.name, "description": c.description or "",
                    "sensor_metrics": json_list(c.sensor_metrics),
                    "drill_alarm_code": c.drill_alarm_code or "",
                    "plan_count": plan_count, "active_count": active_count})
    return {"categories": out}


# ============================================================ 预案 CRUD
@router.get("/plans", summary="预案列表（分页 + 条件查询）")
def list_plans(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0, le=100000),
    category: Optional[str] = None,
    status: Optional[str] = None,
    level: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(E.EmergencyPlan)
    if category:
        q = q.filter(E.EmergencyPlan.category == category)
    if status:
        q = q.filter(E.EmergencyPlan.status == status)
    if level:
        q = q.filter(E.EmergencyPlan.level_min <= level,
                     E.EmergencyPlan.level_max >= level)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(E.EmergencyPlan.plan_name.like(like) |
                     E.EmergencyPlan.commander.like(like))
    p = page if page else 1
    size = page_size if (page and page_size) else 100000
    items, total = paginate(q.order_by(E.EmergencyPlan.priority.desc(),
                                       E.EmergencyPlan.plan_id.asc()), p, size)
    return {"plans": [_plan_dict(p_, _nodes_of(db, p_.plan_id)) for p_ in items],
            "total": total}


@router.get("/plans/{plan_id}", response_model=S.PlanOut, summary="预案详情（含流程节点）")
def plan_detail(plan_id: str, db: Session = Depends(get_db)):
    plan = _get_plan(db, plan_id)
    return _plan_dict(plan, _nodes_of(db, plan_id))


@router.post("/plans", summary="新增预案")
def create_plan(body: S.PlanBody, db: Session = Depends(get_db)):
    if (body.level_min or 1) > (body.level_max or 2):
        raise HTTPException(status_code=422, detail="最低级别不得大于最高级别")

    stamp = _stamp_with_tz(CLOCK_BASE)
    plan = E.EmergencyPlan(
        plan_id=body.plan_id or _next_plan_id(db),
        plan_name=body.plan_name.strip(), category=body.category,
        level_min=body.level_min, level_max=body.level_max,
        priority=body.priority, status=body.status,
        commander=body.commander or "",
        scope_cabins=dump_list(body.scope_cabins),
        scope_zones=dump_list(body.scope_zones),
        tags=dump_list(body.tags), objective=body.objective or "",
        created_at=stamp, updated_at=stamp,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return ok("创建成功", plan_id=plan.plan_id)


@router.put("/plans/{plan_id}", summary="编辑预案 / 切换状态")
def update_plan(plan_id: str, body: S.PlanPatch, db: Session = Depends(get_db)):
    plan = _get_plan(db, plan_id)
    payload = body.model_dump(exclude_unset=True)

    for f in ("plan_name", "category", "level_min", "level_max", "priority",
              "status", "commander", "objective"):
        if payload.get(f) is not None:
            setattr(plan, f, payload[f])
    for f in ("scope_cabins", "scope_zones", "tags"):
        if payload.get(f) is not None:
            setattr(plan, f, dump_list(payload[f]))

    if (plan.level_min or 0) > (plan.level_max or 0):
        raise HTTPException(status_code=422, detail="最低级别不得大于最高级别")
    plan.updated_at = _stamp_with_tz(CLOCK_BASE)
    db.commit()
    return ok("更新成功")


@router.delete("/plans/{plan_id}", summary="删除预案（级联删除流程节点）")
def delete_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = _get_plan(db, plan_id)
    running = db.query(E.Activation).filter(
        E.Activation.plan_id == plan_id,
        E.Activation.status == "running").count()
    if running:
        raise HTTPException(status_code=409, detail="该预案存在进行中的激活实例，无法删除")
    db.query(E.FlowNode).filter(E.FlowNode.plan_id == plan_id).delete()
    db.delete(plan)
    db.commit()
    return ok("删除成功")


# ============================================================ 流程节点
@router.post("/plans/{plan_id}/nodes", summary="新增流程节点")
def add_node(plan_id: str, body: S.NodeBody, db: Session = Depends(get_db)):
    plan = _get_plan(db, plan_id)
    existing = _nodes_of(db, plan_id)
    seq = max([n.seq for n in existing], default=0) + 1
    num = plan_id.split("-")[-1]
    node = E.FlowNode(node_id=f"N-{num}-{seq:02d}", plan_id=plan_id, seq=seq,
                      node_type=body.node_type or "action", title=body.title.strip(),
                      desc=body.desc or "", deadline_min=body.deadline_min or 30,
                      exit_condition=body.exit_condition or "")
    db.add(node)
    plan.updated_at = _stamp_with_tz(CLOCK_BASE)
    db.commit()
    return ok("节点已新增", node_id=node.node_id)


@router.put("/plans/{plan_id}/nodes/{node_id}", summary="编辑流程节点")
def update_node(plan_id: str, node_id: str, body: S.NodePatch,
                db: Session = Depends(get_db)):
    node = db.query(E.FlowNode).filter(
        E.FlowNode.plan_id == plan_id, E.FlowNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"流程节点不存在：{node_id}")

    payload = body.model_dump(exclude_unset=True)
    for f in ("node_type", "title", "desc", "deadline_min", "exit_condition"):
        if payload.get(f) is not None:
            setattr(node, f, payload[f])
    db.commit()
    return ok("节点已更新")


@router.delete("/plans/{plan_id}/nodes/{node_id}", summary="删除流程节点")
def delete_node(plan_id: str, node_id: str, db: Session = Depends(get_db)):
    node = db.query(E.FlowNode).filter(
        E.FlowNode.plan_id == plan_id, E.FlowNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"流程节点不存在：{node_id}")
    db.delete(node)
    db.commit()
    return ok("节点已删除")


# ============================================================ 智能匹配
def _match(db: Session, level: int, top_n: int, category, cabin, zone,
           active_only=True):
    q = db.query(E.EmergencyPlan)
    if active_only:
        q = q.filter(E.EmergencyPlan.status == "active")
    plans = q.all()
    out = []

    for p in plans:
        score, reasons = 0.0, []
        if category and p.category == category:
            score += 50
            reasons.append(f"类别匹配:{_cat_name(db, p.category)}")
        elif category:
            continue
        else:
            reasons.append("未限定类别，按级别与范围排序")

        if p.level_min <= level <= p.level_max:
            score += 25
            reasons.append(f"级别适用:{LEVEL_ROMAN.get(level, level)}")
        elif abs(p.level_min - level) == 1:
            score += 10
            reasons.append(f"级别相邻:{LEVEL_ROMAN.get(p.level_min, p.level_min)}")

        cabins = json_list(p.scope_cabins)
        if cabin:
            if cabin in cabins or "*" in cabins:
                score += 15
                reasons.append(f"舱室覆盖:{CABIN_NAME.get(cabin, cabin)}")
            elif not cabins:
                score += 5
        elif "*" in cabins:
            score += 8

        zones = json_list(p.scope_zones)
        if zone and (zone in zones or "*" in zones):
            score += 10
            reasons.append(f"区域覆盖:{zone}")

        score += round((p.priority or 0) * 0.5, 1)
        out.append({"plan_id": p.plan_id, "plan_name": p.plan_name,
                    "score": round(min(score, 99.9), 1), "reasons": reasons})

    out.sort(key=lambda c: -c["score"])
    out = out[:top_n]
    candidates = [{"rank": i + 1, **c} for i, c in enumerate(out)]
    fallback = not candidates or candidates[0]["score"] < 40
    message = "未匹配到适用预案，建议启动综合应急值班响应" if fallback else ""
    return {"candidates": candidates, "fallback": fallback,
            "fallback_message": message}


@router.post("/match", response_model=S.MatchOut, summary="智能匹配预案")
def match_plans(body: S.MatchBody, db: Session = Depends(get_db)):
    result = _match(db, body.level, body.top_n, body.category, body.cabin, body.zone)

    db.add(E.LiveMatch(
        time=_stamp_with_tz(CLOCK_BASE),
        alarm_id=f"AL-MANUAL-{CLOCK_BASE.strftime('%m%d%H%M')}",
        alarm_desc=f"人工匹配：{body.category or '全类别'} {LEVEL_ROMAN.get(body.level, '')}",
        metric=_sensor_hint(db, body.category),
        category_name=_cat_name(db, body.category) if body.category else "综合",
        best_plan_name=result["candidates"][0]["plan_name"] if result["candidates"] else "-",
        best_score=result["candidates"][0]["score"] if result["candidates"] else 0.0,
        auto_acked=False, fallback=result["fallback"],
    ))
    db.commit()
    return result


def _sensor_hint(db: Session, category):
    if not category:
        return "综合"
    c = db.query(E.PlanCategory).filter(E.PlanCategory.code == category).first()
    metrics = json_list(c.sensor_metrics) if c else []
    return metrics[0] if metrics else "综合"


@router.get("/match/live", summary="实时匹配记录")
def live_matches(limit: int = Query(20, ge=1, le=200),
                 db: Session = Depends(get_db)):
    rows = (db.query(E.LiveMatch).order_by(E.LiveMatch.time.desc())
            .limit(limit).all())
    return {"matches": [
        {"time": r.time, "alarm_id": r.alarm_id,
         "alarm": {"alarm_desc": r.alarm_desc, "metric": r.metric},
         "category_name": r.category_name,
         "best": {"plan_name": r.best_plan_name, "score": r.best_score},
         "auto_acked": bool(r.auto_acked), "fallback": bool(r.fallback)}
        for r in rows]}


# ============================================================ 演练与激活
def _next_activation_id(db: Session) -> str:
    seq = db.query(E.Activation).count() + 1
    aid = f"ACT-2026-{115 + seq}"
    while db.query(E.Activation).filter(
            E.Activation.activation_id == aid).first():
        seq += 1
        aid = f"ACT-2026-{115 + seq}"
    return aid


def _create_activation(db: Session, plan: E.EmergencyPlan, trigger: str, at: datetime):
    act_id = _next_activation_id(db)
    db.add(E.Activation(
        activation_id=act_id, plan_id=plan.plan_id, plan_name=plan.plan_name,
        category_name=_cat_name(db, plan.category), trigger=trigger,
        status="running", activated_at=_stamp_with_tz(at), finished_at=None))

    nodes = _nodes_of(db, plan.plan_id)
    for i, n in enumerate(nodes):
        db.add(E.ActivationNode(
            activation_id=act_id, node_id=n.node_id, seq=i + 1,
            node_type=n.node_type, title=n.title,
            status="running" if i == 0 else "pending", finished_at=None))
    db.commit()
    return act_id


@router.post("/drill", summary="发起演练")
def run_drill(body: S.DrillBody, db: Session = Depends(get_db)):
    result = _match(db, body.level, body.top_n, body.category, body.cabin, body.zone)
    top = result["candidates"][0] if result["candidates"] else None

    if top and body.activate_best:
        plan = _get_plan(db, top["plan_id"])
        _create_activation(db, plan, f"手动发起演练：{body.description or '桌面演练'}",
                           CLOCK_BASE)
    return {"match": result}


@router.post("/activate", summary="实战激活预案")
def activate_plan(body: S.DrillBody, db: Session = Depends(get_db)):
    plan_id = body.plan_id
    if plan_id:
        plan = _get_plan(db, plan_id)
    else:
        result = _match(db, body.level, 1, body.category, body.cabin, body.zone)
        if not result["candidates"]:
            raise HTTPException(status_code=404, detail="未匹配到可激活的预案")
        plan = _get_plan(db, result["candidates"][0]["plan_id"])

    act_id = _create_activation(db, plan, body.description or "告警自动触发", CLOCK_BASE)
    return ok("预案已激活", activation_id=act_id)


@router.get("/activations", summary="激活/演练记录（分页 + 状态筛选）")
def list_activations(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0, le=100000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(E.Activation)
    if status:
        q = q.filter(E.Activation.status == status)
    p = page if page else 1
    size = page_size if (page and page_size) else 100000
    items, total = paginate(q.order_by(E.Activation.activated_at.desc()), p, size)

    out = []
    for a in items:
        nodes = (db.query(E.ActivationNode)
                 .filter(E.ActivationNode.activation_id == a.activation_id)
                 .order_by(E.ActivationNode.seq.asc()).all())
        out.append({
            "activation_id": a.activation_id, "plan_id": a.plan_id,
            "plan_name": a.plan_name, "category_name": a.category_name,
            "trigger": a.trigger or "", "status": a.status,
            "activated_at": a.activated_at, "finished_at": a.finished_at,
            "nodes": [{"node_id": n.node_id, "node_type": n.node_type,
                       "title": n.title, "status": n.status,
                       "finished_at": n.finished_at} for n in nodes],
        })
    return {"activations": out, "total": total}


@router.post("/activations/{activation_id}/nodes/{node_id}/done", summary="标记节点完成")
def mark_node_done(activation_id: str, node_id: str, db: Session = Depends(get_db)):
    act = db.query(E.Activation).filter(
        E.Activation.activation_id == activation_id).first()
    if not act:
        raise HTTPException(status_code=404, detail=f"激活实例不存在：{activation_id}")
    if act.status == "finished":
        raise HTTPException(status_code=409, detail="该实例已完结，节点不可再变更")

    node = db.query(E.ActivationNode).filter(
        E.ActivationNode.activation_id == activation_id,
        E.ActivationNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"节点不存在：{node_id}")

    node.status = "done"
    node.finished_at = _stamp_with_tz(CLOCK_BASE)

    # 自动点亮下一个待执行节点
    nxt = (db.query(E.ActivationNode)
           .filter(E.ActivationNode.activation_id == activation_id,
                   E.ActivationNode.status == "pending")
           .order_by(E.ActivationNode.seq.asc()).first())
    if nxt:
        nxt.status = "running"

    all_nodes = (db.query(E.ActivationNode)
                 .filter(E.ActivationNode.activation_id == activation_id).all())
    done = sum(1 for n in all_nodes if n.status == "done")
    progress = round(done * 100.0 / max(len(all_nodes), 1), 1)

    if done == len(all_nodes) and all_nodes:
        act.status = "finished"
        act.finished_at = _stamp_with_tz(CLOCK_BASE)
    db.commit()
    return {"progress": progress, "success": True}


@router.post("/activations/{activation_id}/finish", summary="完结激活实例")
def finish_activation(activation_id: str, db: Session = Depends(get_db)):
    act = db.query(E.Activation).filter(
        E.Activation.activation_id == activation_id).first()
    if not act:
        raise HTTPException(status_code=404, detail=f"激活实例不存在：{activation_id}")

    act.status = "finished"
    act.finished_at = _stamp_with_tz(CLOCK_BASE)
    db.query(E.ActivationNode).filter(
        E.ActivationNode.activation_id == activation_id,
        E.ActivationNode.status.in_(["pending", "running"])
    ).update({"status": "done", "finished_at": act.finished_at},
             synchronize_session=False)
    db.commit()
    return ok("实例已完结")
