"""
百度地图 Web API 代理模块

职责：
1. POI 地点搜索（Place API v2/search）
2. 地理编码 / 逆地理编码（Geocoding v3）
3. 坐标转换（Convertor API：WGS84/GCJ02 → BD09）
4. 驾车路线规划（Directionlite v1/driving，轻量级接口）

设计原则：
- AK 只存在后端环境变量 / 配置文件中，前端完全不接触
- 所有请求透传百度官方响应，只做最薄的一层 HTTP 代理
- 使用 requests.Session 复用连接，减少 TLS 握手开销
- 百度 API 每日有配额限制，后端可在此层做缓存/限流（当前为基础实现，未内置）
"""

from __future__ import annotations

import os
import json
import time
from typing import List, Optional, Tuple

import requests
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

# 百度地图 AK：优先从环境变量读取，其次使用硬编码（开发便捷）
BAIDU_AK = os.environ.get("BAIDU_MAP_AK", "5XWMEKfXwj68UvF2bDrpBR6sBPwPsOP8")

# 百度 Web API 基础域名
BAIDU_API_BASE = "https://api.map.baidu.com"

# 统一 requests Session，复用连接池
_session = requests.Session()
_session.headers.update({
    "User-Agent": "AnAnMapProxy/1.0 (+alarm-warning-frontend)",
    "Accept": "application/json",
    "Timeout": "5",
})

# 安塞区中心（搜索默认城市）
DEFAULT_CITY = "延安市安塞区"

# ---------------------------------------------------------------------------
# 公共工具
# ---------------------------------------------------------------------------

def _baidu_get(path: str, params: dict) -> dict:
    """统一调用百度 Web API 的 GET 接口，自动注入 AK。"""
    params = dict(params)
    params.setdefault("output", "json")
    params["ak"] = BAIDU_AK
    url = f"{BAIDU_API_BASE}{path}"
    try:
        resp = _session.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"百度 API 请求失败: {exc}")

    # 百度统一用 status/result/status_code 表示成功
    # Place API: status == 0
    # Direction API: status == 0
    # Convertor API: status == 0
    code = data.get("status", -1)
    if code != 0:
        msg = data.get("message") or data.get("result") or f"百度返回错误码 {code}"
        raise HTTPException(status_code=400, detail=f"百度 API 返回错误: {msg}")
    return data


# ---------------------------------------------------------------------------
# 坐标转换
# ---------------------------------------------------------------------------

# 坐标系常量（百度 Convertor API）
# from 原始坐标系：1=WGS84  3=GCJ02  4=BD09（百度加密坐标）
# to   目标坐标系：5=BD09  2=GCJ02  1=WGS84
COORD_WGS84 = 1
COORD_GCJ02 = 3
COORD_BD09 = 4  # 原始 BD09
COORD_BD09_ENCRYPTED = 5  # 百度加密后的 BD09（地图展示用）


class CoordsConvertRequest(BaseModel):
    """批量坐标转换请求。"""
    coords: List[Tuple[float, float]] = Field(
        ..., description="坐标列表，每项 [lon, lat]，最多 50 个"
    )
    from_coord: int = Field(default=COORD_WGS84, description="原始坐标系: 1=WGS84, 3=GCJ02")
    to_coord: int = Field(default=COORD_BD09_ENCRYPTED, description="目标坐标系: 5=BD09")


def convert_coords(coords: List[Tuple[float, float]],
                   from_coord: int = COORD_WGS84,
                   to_coord: int = COORD_BD09_ENCRYPTED) -> List[Tuple[float, float]]:
    """调用百度 geoconv/v1 接口批量转换坐标。"""
    if not coords:
        return []
    if len(coords) > 50:
        raise HTTPException(status_code=400, detail="单次最多转换 50 个坐标")

    # 百度用分号分隔 "lng1,lat1;lng2,lat2;..."
    coords_str = ";".join(f"{lng},{lat}" for lng, lat in coords)
    data = _baidu_get("/geoconv/v1/", {
        "coords": coords_str,
        "from": from_coord,
        "to": to_coord,
    })

    result = data.get("result", [])
    converted = []
    for i, item in enumerate(result):
        if item.get("error") == 0:
            converted.append((float(item["x"]), float(item["y"])))
        elif i < len(coords):
            # 转换失败降级用原坐标
            converted.append(coords[i])
    return converted


# ---------------------------------------------------------------------------
# POI 地点搜索
# ---------------------------------------------------------------------------

def search_poi(keyword: str, city: str = DEFAULT_CITY,
               page_size: int = 10, page_num: int = 0) -> dict:
    """百度 Place API v2/search — 搜索 POI。"""
    if not keyword or not keyword.strip():
        return {"pois": [], "total": 0}

    data = _baidu_get("/place/v2/search", {
        "query": keyword.strip(),
        "region": city,
        "page_size": min(page_size, 50),
        "page_num": page_num,
    })

    # 归一化输出结构，方便前端直接消费
    pois_raw = data.get("results", [])
    pois = []
    for p in pois_raw:
        pt = p.get("location", {})
        pois.append({
            "name": p.get("name", ""),
            "address": p.get("address", ""),
            "lng": float(pt.get("lng", 0)),
            "lat": float(pt.get("lat", 0)),
            "district": p.get("district", ""),
            "province": p.get("province", ""),
        })

    return {
        "pois": pois,
        "total": data.get("total", len(pois)),
    }


# ---------------------------------------------------------------------------
# 路线规划（驾车）
# ---------------------------------------------------------------------------

class DirectionRequest(BaseModel):
    origin_lng: float = Field(..., description="起点经度（BD09 坐标）")
    origin_lat: float = Field(..., description="起点纬度（BD09 坐标）")
    dest_lng: float = Field(..., description="终点经度（BD09 坐标）")
    dest_lat: float = Field(..., description="终点纬度（BD09 坐标）")


def plan_driving(origin_lng: float, origin_lat: float,
                 dest_lng: float, dest_lat: float) -> dict:
    """
    百度 Directionlite v1/driving — 驾车路线规划（轻量级，免费）。
    后端直接解码路线为 [[lng, lat], ...] 坐标数组返回前端，
    避免前端处理压缩 polyline 字符串。
    """
    # DirectionLite 的请求点顺序是“纬度,经度”；BMap.Point 与返回的
    # step.path 则使用“经度,纬度”。这里显式转换，避免路线落到错误地区。
    data = _baidu_get("/directionlite/v1/driving", {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
    })

    route = (data.get("result") or {}).get("routes") or []
    if not route:
        raise HTTPException(status_code=400, detail="未找到可行路线")

    first = route[0]

    # 从每个 step 的 path 字段拼接完整的路线坐标
    path_points: List[Tuple[float, float]] = []
    for step in first.get("steps", []):
        path_str = step.get("path", "")
        if not path_str:
            continue
        for seg in path_str.split(";"):
            seg = seg.strip()
            if not seg:
                continue
            parts = seg.split(",")
            if len(parts) != 2:
                continue
            try:
                path_points.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue

    return {
        "distance": first.get("distance", ""),
        "duration": first.get("duration", ""),
        "path": path_points,
        "steps": [
            {
                "instruction": s.get("instruction", ""),
                "road": s.get("road", ""),
                "distance": s.get("distance", 0),
            }
            for s in first.get("steps", [])
        ],
    }


# ---------------------------------------------------------------------------
# 地理编码
# ---------------------------------------------------------------------------

def geocode(address: str, city: str = DEFAULT_CITY) -> Optional[dict]:
    """地址 → 坐标（地理编码）。"""
    if not address or not address.strip():
        return None
    data = _baidu_get("/geocoding/v3/", {
        "address": address.strip(),
        "city": city,
    })
    result = data.get("result") or {}
    pt = result.get("location")
    if not pt:
        return None
    return {
        "address": result.get("formatted_address", address),
        "lng": float(pt.get("lng", 0)),
        "lat": float(pt.get("lat", 0)),
        "level": result.get("level", ""),
        "precise": result.get("precise", 0),
    }


def reverse_geocode(lng: float, lat: float) -> Optional[dict]:
    """坐标 → 地址（逆地理编码）。"""
    data = _baidu_get("/reverse_geocoding/v3/", {
        "location": f"{lat},{lng}",  # 百度要求 lat,lng 顺序
    })
    result = data.get("result") or {}
    return {
        "address": result.get("formatted_address", ""),
        "lng": lng,
        "lat": lat,
        "province": (result.get("addressComponent") or {}).get("province", ""),
        "city": (result.get("addressComponent") or {}).get("city", ""),
        "district": (result.get("addressComponent") or {}).get("district", ""),
    }


# ---------------------------------------------------------------------------
# FastAPI 路由
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/baidu", tags=["百度地图代理"])


@router.get("/search", summary="POI 地点搜索")
def api_search_poi(
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query(DEFAULT_CITY, description="限定城市"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    page_num: int = Query(0, ge=0, description="页码"),
):
    """调用百度 Place API v2/search。"""
    return search_poi(keyword=keyword, city=city, page_size=page_size, page_num=page_num)


@router.get("/geocode", summary="地理编码（地址→坐标）")
def api_geocode(
    address: str = Query(..., description="地址文本"),
    city: str = Query(DEFAULT_CITY, description="限定城市"),
):
    result = geocode(address=address, city=city)
    if result is None:
        return {"ok": False, "message": "未找到该地址对应的坐标"}
    return {"ok": True, "result": result}


@router.get("/reverse", summary="逆地理编码（坐标→地址）")
def api_reverse_geocode(
    lng: float = Query(..., description="经度 BD09"),
    lat: float = Query(..., description="纬度 BD09"),
):
    result = reverse_geocode(lng=lng, lat=lat)
    if result is None:
        return {"ok": False, "message": "逆地理编码失败"}
    return {"ok": True, "result": result}


@router.post("/convert", summary="批量坐标转换")
def api_convert_coords(body: CoordsConvertRequest = Body(...)):
    """
    将原始坐标系坐标批量转换为百度 BD09（百度地图展示用）。

    默认 from=WGS84(1), to=BD09(5)。
    单次最多 50 个点。
    """
    result = convert_coords(
        coords=body.coords,
        from_coord=body.from_coord,
        to_coord=body.to_coord,
    )
    return {"ok": True, "original_count": len(body.coords), "converted": result}


@router.post("/direction/driving", summary="驾车路线规划")
def api_plan_driving(req: DirectionRequest = Body(...)):
    """
    调用百度 Directionlite v1/driving 接口。
    返回距离、预计用时、路线 polyline 坐标串、分步指引。

    origin / dest 使用 BD09 坐标（可先通过 /convert 转换）。
    """
    result = plan_driving(
        origin_lng=req.origin_lng,
        origin_lat=req.origin_lat,
        dest_lng=req.dest_lng,
        dest_lat=req.dest_lat,
    )
    return {"ok": True, "route": result}


@router.get("/health", summary="百度地图代理健康检查")
def api_baidu_health():
    return {
        "status": "ok",
        "ak_configured": bool(BAIDU_AK),
        "ak_prefix": BAIDU_AK[:4] + "****",
    }
