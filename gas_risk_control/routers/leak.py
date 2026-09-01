# -*- coding: utf-8 -*-
"""
功能 2：微泄漏精准定位
======================
两种互补的定位算法：
1. 浓度扩散模型反演：以高斯扩散分布拟合沿线各测点浓度，
   通过二维网格搜索求解 (泄漏位置 μ, 扩散宽度 σ, 幅值 A)，
   使拟合残差最小，反演出泄漏点桩号与置信度；
2. 压力波（负压波）时差法：泄漏瞬间产生向上下游传播的负压波，
   由两端检测时刻之差解算泄漏位置：
       x = (L + v·(t_up - t_down)) / 2
"""
import json
import math
import random
import time

from fastapi import APIRouter, HTTPException

import database as db
from models import LeakLocateReq, PressureWaveReq

router = APIRouter(prefix="/api/leak", tags=["2.微泄漏精准定位"])


# ---------------------------------------------------------------------------
# 算法 1：浓度扩散模型反演
# ---------------------------------------------------------------------------
def _locate_by_gaussian(xs, cs, background, pipe_len):
    """
    模型：c(x) = A·exp(-(x-μ)²/(2σ²)) + b
    在 μ∈[0, L]、σ∈[0.15, 3.0] 上网格搜索最小二乘解（测点少、计算量小）。
    """
    b = background
    best = None  # (sse, mu, sigma, A)
    mu_lo, mu_hi = 0.0, pipe_len
    n_mu, n_sg = 240, 25
    for i in range(n_mu + 1):
        mu = mu_lo + (mu_hi - mu_lo) * i / n_mu
        for j in range(1, n_sg + 1):
            sg = 0.15 + (3.0 - 0.15) * j / n_sg
            g = [math.exp(-(x - mu) ** 2 / (2 * sg * sg)) for x in xs]
            sg2 = sum(gi * gi for gi in g)
            if sg2 < 1e-9:
                continue
            # 给定 μ、σ 时，幅值 A 的最小二乘闭式解
            A = sum((c - b) * gi for c, gi in zip(cs, g)) / sg2
            if A <= 0:
                continue
            sse = sum((c - (A * gi + b)) ** 2 for c, gi in zip(cs, g))
            if best is None or sse < best[0]:
                best = (sse, mu, sg, A)
    if best is None:
        return None
    sse, mu, sg, A = best

    # 拟合优度 R² 与置信度（测点越多、拟合越好，置信度越高）
    mean_c = sum(cs) / len(cs)
    sst = sum((c - mean_c) ** 2 for c in cs)
    r2 = 1 - sse / sst if sst > 1e-9 else 0.0
    confidence = max(0.0, min(1.0, r2)) * min(1.0, len(xs) / 3.0)
    # 定位不确定度：扩散宽度越大、测点越少，不确定度越大
    uncertainty_km = round(sg / math.sqrt(max(len(xs), 1)) * 1.5, 3)
    return {
        "position_km": round(mu, 3),
        "confidence": round(confidence, 3),
        "uncertainty_km": uncertainty_km,
        "r_squared": round(max(0.0, r2), 4),
        "amplitude_ppm": round(A, 1),
        "diffusion_sigma_km": round(sg, 3),
    }


@router.post("/locate-by-concentration", summary="浓度扩散模型定位")
def locate_by_concentration(req: LeakLocateReq):
    """
    输入沿线各测点浓度，基于高斯扩散模型反演微小泄漏点位置。
    适用于缓慢微泄漏：泄漏云团沿管线呈高斯分布，峰值附近即泄漏点。
    """
    xs = [r.position_km for r in req.readings]
    cs = [r.concentration_ppm for r in req.readings]
    active = [(x, c) for x, c in zip(xs, cs) if c > req.background_ppm + 3]
    if len(active) < 2:
        raise HTTPException(400, "有效异常测点不足 2 个，无法反演定位（请确认存在浓度升高的测点）")

    result = _locate_by_gaussian(xs, cs, req.background_ppm, req.pipeline_length_km)
    if result is None:
        raise HTTPException(400, "无法拟合出有效泄漏源（所有测点浓度均低于背景值）")

    # 生成拟合曲线供前端叠加显示
    curve = []
    x = 0.0
    while x <= req.pipeline_length_km + 1e-6:
        fitted = result["amplitude_ppm"] * math.exp(
            -(x - result["position_km"]) ** 2 / (2 * result["diffusion_sigma_km"] ** 2)) + req.background_ppm
        curve.append({"position_km": round(x, 2), "fitted_ppm": round(fitted, 1)})
        x += 0.1

    detail = {
        "method": "concentration",
        "readings": [{"position_km": x, "concentration_ppm": c} for x, c in zip(xs, cs)],
        "background_ppm": req.background_ppm,
        "curve": curve,
        **result,
    }
    _save_record("concentration", result["position_km"], result["confidence"], detail)
    return detail


# ---------------------------------------------------------------------------
# 算法 2：压力波时差法
# ---------------------------------------------------------------------------
@router.post("/locate-by-pressure-wave", summary="压力波时差法定位")
def locate_by_pressure_wave(req: PressureWaveReq):
    """
    x = (L + v·(t_up - t_down)) / 2
    其中 t_up、t_down 分别为上、下游站端检测到负压波的时刻（同一时钟基准）。
    返回定位桩号及由时钟同步误差传递的定位不确定度。
    """
    L = req.pipeline_length_km
    v = req.wave_speed_m_s
    dt_s = (req.t_upstream_ms - req.t_downstream_ms) / 1000.0  # 秒
    x = (L + v * dt_s / 1000.0) / 2.0  # v·dt 单位 m → /1000 转 km

    if not (0 <= x <= L):
        raise HTTPException(400, f"时差 {dt_s*1000:.0f}ms 超出物理范围（|v·Δt| 应 ≤ 管长），请检查两端时刻")

    # 误差传递：δx = v·δt/2（米），再换算为 km
    uncertainty_km = round(v * (req.timing_error_ms / 1000.0) / 2.0 / 1000.0, 4)
    confidence = max(0.5, min(0.99, 0.98 - req.timing_error_ms / 50.0))

    detail = {
        "method": "pressure_wave",
        "position_km": round(x, 3),
        "confidence": round(confidence, 3),
        "uncertainty_km": uncertainty_km,
        "formula": "x = (L + v·(t_up - t_down)) / 2",
        "params": {"pipeline_length_km": L, "wave_speed_m_s": v,
                   "t_upstream_ms": req.t_upstream_ms, "t_downstream_ms": req.t_downstream_ms},
    }
    _save_record("pressure_wave", x, confidence, detail)
    return detail


# ---------------------------------------------------------------------------
# 演示场景：内置一个“真实泄漏点”，自动生成两种方法的观测数据并定位对比
# ---------------------------------------------------------------------------
@router.post("/demo", summary="生成演示场景并执行双方法定位")
def demo():
    """
    随机选取一个真实泄漏点：
    - 按高斯扩散生成各监测站的浓度读数 → 浓度模型反演；
    - 按波速生成两端负压波到达时刻（含 ±3ms 噪声）→ 压力波法解算。
    返回两种方法的结果与真实位置，便于评估定位误差。
    """
    conn = db.get_conn()
    try:
        sensors = db.rows_to_list(conn.execute("SELECT id,name,position_km FROM sensors ORDER BY position_km"))
    finally:
        conn.close()

    true_pos = round(random.uniform(5, 45), 2)
    true_amp = random.uniform(400, 1200)   # 泄漏点峰值浓度
    true_sigma = random.uniform(0.8, 1.6)  # 云团扩散宽度
    background = 4.0

    readings = [{
        "position_km": s["position_km"],
        "concentration_ppm": round(background + true_amp * math.exp(
            -(s["position_km"] - true_pos) ** 2 / (2 * true_sigma ** 2))
            + random.uniform(-2, 2), 1),
    } for s in sensors]

    # 浓度模型反演
    conc = _locate_by_gaussian([r["position_km"] for r in readings],
                               [r["concentration_ppm"] for r in readings],
                               background, 50.0)

    # 压力波观测数据（波速 350 m/s）+ 定位
    v = 350.0
    t_up = true_pos * 1000.0 / v * 1000.0 + random.uniform(-3, 3)      # ms
    t_down = (50.0 - true_pos) * 1000.0 / v * 1000.0 + random.uniform(-3, 3)
    x_wave = (50.0 + v * (t_up - t_down) / 1e6) / 2.0

    result = {
        "true_position_km": true_pos,
        "readings": readings,
        "concentration_result": conc,
        "pressure_wave_result": {
            "position_km": round(x_wave, 3),
            "t_upstream_ms": round(t_up, 1),
            "t_downstream_ms": round(t_down, 1),
            "wave_speed_m_s": v,
        },
        "errors_km": {
            "concentration": round(abs(conc["position_km"] - true_pos), 3) if conc else None,
            "pressure_wave": round(abs(x_wave - true_pos), 3),
        },
    }
    if conc:
        _save_record("concentration", conc["position_km"], conc["confidence"],
                     {"demo": True, "true_position_km": true_pos})
    return result


@router.get("/records", summary="定位历史记录")
def records(limit: int = 20):
    """最近 N 条定位结果（含方法与置信度）。"""
    conn = db.get_conn()
    try:
        rows = db.rows_to_list(conn.execute(
            "SELECT id,ts_ms,method,position_km,confidence FROM leak_records ORDER BY id DESC LIMIT ?",
            (limit,)))
        return {"records": rows}
    finally:
        conn.close()


def _save_record(method, position_km, confidence, detail):
    conn = db.get_conn()
    try:
        conn.execute("INSERT INTO leak_records(ts_ms,method,position_km,confidence,detail) VALUES(?,?,?,?,?)",
                     (int(time.time() * 1000), method, position_km, confidence, json.dumps(detail, ensure_ascii=False)))
        conn.commit()
    finally:
        conn.close()
