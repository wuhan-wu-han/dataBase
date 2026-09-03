#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工单全流程管理 —— SQLite 读写适配层

设计目标：simulator 继续在内存 dict 上做全部业务计算，本层只负责
「启动时把库还原成 dict」与「每次变更后写回库」，因此表列与 dict 键严格一一对应。
"""

import traceback
from typing import Any, Dict, List, Optional

try:                                                  # 从 src/python 目录启动
    from persistence import DB_PATH, SessionLocal, from_json, init_db, to_json
    from persistence.workorder_tables import (
        WoCounter,
        WoDispatchLog,
        WoOrder,
        WoSlaRule,
        WoStaff,
        WoTimeline,
    )
except ImportError:                                   # 从仓库根目录以包路径启动
    from src.python.persistence import DB_PATH, SessionLocal, from_json, init_db, to_json
    from src.python.persistence.workorder_tables import (
        WoCounter,
        WoDispatchLog,
        WoOrder,
        WoSlaRule,
        WoStaff,
        WoTimeline,
    )

ORDER_SEQ_KEY = "order_seq"

_ORDER_FIELDS = (
    "order_id", "title", "channel", "category", "required_skill", "priority",
    "status", "location", "description", "reporter", "created_at",
    "sla_deadline", "sla_hours", "assignee", "assignee_id",
    "resolved_at", "rating", "escalated",
)


def _log_error(action: str, exc: Exception) -> None:
    print("[workorder.store] %s 失败：%s" % (action, exc))
    traceback.print_exc()


def ensure_schema() -> None:
    """建表（幂等）"""
    init_db()


# ==============================================================================
# 读取：库 → 内存 dict
# ==============================================================================

def load_state() -> Optional[Dict[str, Any]]:
    """库中已有工单时返回完整 _state；空库返回 None（由调用方灌种子）"""
    db = SessionLocal()
    try:
        total = db.query(WoOrder).count()
        if total == 0:
            return None

        timelines: Dict[str, List[Dict[str, Any]]] = {}
        for row in db.query(WoTimeline).order_by(WoTimeline.order_id, WoTimeline.seq).all():
            timelines.setdefault(row.order_id, []).append({
                "step": row.step,
                "step_name": row.step_name,
                "at": row.at,
                "operator": row.operator,
                "note": row.note,
            })

        orders = []
        for row in db.query(WoOrder).order_by(WoOrder.created_at.desc()).all():
            order = {key: getattr(row, key) for key in _ORDER_FIELDS}
            order["process"] = timelines.get(row.order_id, [])
            orders.append(order)

        staff = []
        for row in db.query(WoStaff).order_by(WoStaff.staff_id).all():
            staff.append({
                "staff_id": row.staff_id, "name": row.name,
                "skills": from_json(row.skills), "status": row.status,
                "location": row.location, "phone": row.phone,
                "completed_orders": row.completed_orders or 0,
                "avg_rating": row.avg_rating or 0.0,
            })

        sla_rules = [{
            "priority": r.priority, "priority_name": r.priority_name,
            "response_hours": r.response_hours, "warning_threshold": r.warning_threshold,
            "escalate_multiplier": r.escalate_multiplier,
            "escalate_target": r.escalate_target, "desc": r.desc,
        } for r in db.query(WoSlaRule).all()]

        logs = [{
            "order_id": r.order_id, "staff_id": r.staff_id,
            "staff_name": r.staff_name, "dispatched_at": r.dispatched_at,
            "method": r.method,
        } for r in db.query(WoDispatchLog).order_by(WoDispatchLog.id.desc()).all()]

        return {
            "orders": orders,
            "staff": staff,
            "sla_rules": sla_rules,
            "dispatch_logs": logs,
            "order_seq": get_counter(ORDER_SEQ_KEY, 2001),
        }
    finally:
        db.close()


def get_counter(name: str, default: int = 0) -> int:
    db = SessionLocal()
    try:
        row = db.query(WoCounter).filter(WoCounter.name == name).first()
        return row.value if row else default
    finally:
        db.close()


# ==============================================================================
# 写入：内存 dict → 库
# ==============================================================================

def save_state(state: Dict[str, Any]) -> None:
    """首次种子落库（全量写）"""
    db = SessionLocal()
    try:
        for order in state["orders"]:
            db.add(WoOrder(**{key: order.get(key) for key in _ORDER_FIELDS}))
            db.flush()                                  # 父行先落库，子表外键才成立
            _write_timeline(db, order)
        for s in state["staff"]:
            db.add(WoStaff(
                staff_id=s["staff_id"], name=s["name"], skills=to_json(s.get("skills")),
                status=s.get("status"), location=s.get("location"), phone=s.get("phone"),
                completed_orders=s.get("completed_orders", 0), avg_rating=s.get("avg_rating", 0.0),
            ))
        for r in state["sla_rules"]:
            db.add(WoSlaRule(
                priority=r["priority"], priority_name=r.get("priority_name"),
                response_hours=r.get("response_hours"), warning_threshold=r.get("warning_threshold"),
                escalate_multiplier=r.get("escalate_multiplier"),
                escalate_target=r.get("escalate_target"), desc=r.get("desc"),
            ))
        db.add(WoCounter(name=ORDER_SEQ_KEY, value=state.get("order_seq", 2001)))
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("种子数据落库", exc)
        raise
    finally:
        db.close()


def _write_timeline(db, order: Dict[str, Any]) -> None:
    db.query(WoTimeline).filter(WoTimeline.order_id == order["order_id"]).delete()
    for idx, record in enumerate(order.get("process") or [], start=1):
        db.add(WoTimeline(
            order_id=order["order_id"], seq=idx,
            step=record.get("step"), step_name=record.get("step_name"),
            at=record.get("at"), operator=record.get("operator"),
            note=record.get("note"),
        ))


def upsert_order(order: Dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        row = db.query(WoOrder).filter(WoOrder.order_id == order["order_id"]).first()
        if row is None:
            row = WoOrder(order_id=order["order_id"])
            db.add(row)
        for key in _ORDER_FIELDS:
            setattr(row, key, order.get(key))
        db.flush()                                      # 父行先落库，子表外键才成立
        _write_timeline(db, order)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入工单 %s" % order.get("order_id"), exc)
    finally:
        db.close()


def delete_order(order_id: str) -> None:
    db = SessionLocal()
    try:
        db.query(WoTimeline).filter(WoTimeline.order_id == order_id).delete()
        db.query(WoOrder).filter(WoOrder.order_id == order_id).delete()
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("删除工单 %s" % order_id, exc)
    finally:
        db.close()


def upsert_staff(staff: Dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        row = db.query(WoStaff).filter(WoStaff.staff_id == staff["staff_id"]).first()
        if row is None:
            row = WoStaff(staff_id=staff["staff_id"])
            db.add(row)
        row.name = staff.get("name")
        row.skills = to_json(staff.get("skills"))
        row.status = staff.get("status")
        row.location = staff.get("location")
        row.phone = staff.get("phone")
        row.completed_orders = staff.get("completed_orders", 0)
        row.avg_rating = staff.get("avg_rating", 0.0)
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入人员 %s" % staff.get("staff_id"), exc)
    finally:
        db.close()


def add_dispatch_log(entry: Dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        db.add(WoDispatchLog(
            order_id=entry.get("order_id"), staff_id=entry.get("staff_id"),
            staff_name=entry.get("staff_name"), dispatched_at=entry.get("dispatched_at"),
            method=entry.get("method"),
        ))
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入派单记录", exc)
    finally:
        db.close()


def set_counter(name: str, value: int) -> None:
    db = SessionLocal()
    try:
        row = db.query(WoCounter).filter(WoCounter.name == name).first()
        if row is None:
            db.add(WoCounter(name=name, value=value))
        else:
            row.value = value
        db.commit()
    except Exception as exc:                          # noqa: BLE001
        db.rollback()
        _log_error("写入计数器 %s" % name, exc)
    finally:
        db.close()
