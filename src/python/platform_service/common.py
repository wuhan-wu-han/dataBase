"""公共工具：统一响应格式、时间基准、JSON 列表读写"""
import json
from datetime import datetime
from typing import Any, List

from fastapi.responses import JSONResponse


# 平台演示逻辑时钟：种子数据以 2026-08-30 14:00 为基准，
# 新建记录同样落在该基准上，保证 SLA 已用/剩余时长自洽。
CLOCK_BASE = datetime(2026, 8, 30, 14, 0, 0)

ISO_FMT = "%Y-%m-%dT%H:%M:%S"
SPACE_FMT = "%Y-%m-%d %H:%M:%S"

TZ_SUFFIX = "+08:00"


def ok(message: str = "ok", **extra) -> JSONResponse:
    return JSONResponse({"success": True, "code": 200, "message": message, **extra})


def parse_iso(value):
    """解析不带/带时区的 ISO 字符串，失败返回 None"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace(TZ_SUFFIX, "").replace("Z", ""))
    except (ValueError, TypeError):
        return None


def to_iso(dt: datetime) -> str:
    return dt.strftime(ISO_FMT)


def to_space(dt: datetime) -> str:
    return dt.strftime(SPACE_FMT)


def now_iso() -> str:
    return to_iso(CLOCK_BASE)


def now_with_tz() -> str:
    return to_iso(CLOCK_BASE) + TZ_SUFFIX


def now_space() -> str:
    return to_space(CLOCK_BASE)


def json_list(raw, default: List[Any] = None) -> List[Any]:
    """数据库文本列 → Python 列表"""
    if raw in (None, ""):
        return list(default or [])
    if isinstance(raw, list):
        return raw
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else (default or [])
    except (ValueError, TypeError):
        return [s for s in str(raw).split(",") if s]


def dump_list(items) -> str:
    return json.dumps(items if items is not None else [], ensure_ascii=False)


def split_skills(raw) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def paginate(query, page: int, page_size: int):
    """标准分页：page<=0 或 page_size>=100000 视为不分页返回全量"""
    total = query.count()
    if page and page > 0 and page_size and page_size > 0:
        items = query.offset((page - 1) * page_size).limit(page_size).all()
    else:
        items = query.all()
    return items, total
