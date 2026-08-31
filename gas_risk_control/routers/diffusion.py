# -*- coding: utf-8 -*-
"""
功能 3：泄漏扩散仿真
====================
基于高斯烟羽（Gaussian Plume）模型模拟燃气泄漏后的浓度时空分布：

    C(x,y,0) = Q / (π·u·σy·σz) · exp(-y²/(2σy²)) · exp(-H²/(2σz²))

其中：
    x —— 下风向距离；y —— 横风向距离；H —— 泄漏源有效高度；
    u —— 风速；Q —— 泄漏质量速率；σy/σz —— Briggs 乡村扩散系数（按大气稳定度）。

体积浓度换算考虑了环境气压与温度（理想气体）：
    ρ气 = P·M / (R·T)； %VOL = C质量浓度 / ρ气 × 100； %LEL = %VOL / 5 × 100

并依据甲烷爆炸极限（LEL=5%VOL，UEL=15%VOL）计算爆炸危险范围。
"""
import math

from fastapi import APIRouter, HTTPException

from models import DiffusionSimReq

router = APIRouter(prefix="/api/diffusion", tags=["3.泄漏扩散仿真"])

M_CH4 = 0.016      # 甲烷摩尔质量 kg/mol
R_GAS = 8.314      # 理想气体常数
LEL_VOL = 5.0      # 爆炸下限 %VOL
UEL_VOL = 15.0     # 爆炸上限 %VOL


# Briggs 乡村扩散系数（σy, σz），按 Pasquill 稳定度 A~F
def _sigma(stability: str, x: float):
    s = stability.upper()
    if s == "A":
        return 0.22 * x / math.sqrt(1 + 0.0001 * x), 0.20 * x
    if s == "B":
        return 0.16 * x / math.sqrt(1 + 0.0001 * x), 0.12 * x
    if s == "C":
        return 0.11 * x / math.sqrt(1 + 0.0001 * x), 0.08 * x / math.sqrt(1 + 0.0002 * x)
    if s == "D":
        return 0.08 * x / math.sqrt(1 + 0.0001 * x), 0.06 * x / math.sqrt(1 + 0.0015 * x)
    if s == "E":
        return 0.06 * x / math.sqrt(1 + 0.0001 * x), 0.03 * x / (1 + 0.0003 * x)
    if s == "F":
        return 0.04 * x / math.sqrt(1 + 0.0001 * x), 0.016 * x / (1 + 0.0003 * x)
    raise HTTPException(400, f"不支持的大气稳定度：{stability}（应为 A~F）")


def _gas_density(pressure_kpa: float, temperature_c: float) -> float:
    """甲烷密度 kg/m³（理想气体），气压越高/温度越低密度越大。"""
    p = pressure_kpa * 1000.0
    t = temperature_c + 273.15
    return p * M_CH4 / (R_GAS * t)


def _compute_field(req: DiffusionSimReq):
    """核心计算：生成地面浓度网格（%LEL）并统计各危险区域范围。"""
    u = max(req.wind_speed_m_s, 0.5)
    rho = _gas_density(req.pressure_kpa, req.temperature_c)  # kg/m3
    Q = req.leak_rate_kg_s
    H = req.source_height_m

    xmax = req.max_distance_m
    ymax = max(60.0, min(300.0, xmax * 0.4))   # 横风向半幅
    nx = int(req.grid_points)
    ny = 61
    dx = xmax / nx
    dy = 2 * ymax / (ny - 1)

    # 地面浓度网格 C(x,y)，x=0 处取首个网格点避免奇点
    grid = []          # [row(y)][col(x)] = %LEL
    centerline = []    # 轴线浓度剖面
    for iy in range(ny):
        y = -ymax + iy * dy
        row_vals = []
        for ix in range(nx):
            x = (ix + 0.5) * dx
            sy, sz = _sigma(req.stability, x)
            # 高斯烟羽地面浓度（含地面全反射）
            c = (Q / (math.pi * u * sy * sz)
                 * math.exp(-y * y / (2 * sy * sy))
                 * math.exp(-H * H / (2 * sz * sz)))
            lel = c / rho * 100.0 / LEL_VOL * 100.0  # → %LEL
            row_vals.append(round(lel, 2))
            if iy == ny // 2:
                centerline.append({"x_m": round(x, 1), "lel_pct": round(lel, 2)})
        grid.append(row_vals)

    # 分区统计：爆炸区 100~300%LEL（5~15%VOL）、富集区 >300%LEL（>UEL）、警戒区 ≥20%LEL
    zones = {
        "explosion": {"name": "爆炸危险区（5%~15%VOL）", "min_lel": 100, "max_lel": 300,
                      "max_x_m": 0.0, "max_half_width_m": 0.0, "area_m2": 0.0},
        "rich": {"name": "过富集区（>15%VOL，遇新鲜空气仍可爆）", "min_lel": 300, "max_lel": 1e12,
                 "max_x_m": 0.0, "max_half_width_m": 0.0, "area_m2": 0.0},
        "warning": {"name": "警戒区（≥20%LEL）", "min_lel": 20, "max_lel": 1e12,
                    "max_x_m": 0.0, "max_half_width_m": 0.0, "area_m2": 0.0},
    }
    cell_area = dx * dy
    for iy in range(ny):
        y = -ymax + iy * dy
        for ix in range(nx):
            v = grid[iy][ix]
            x = (ix + 0.5) * dx
            for z in zones.values():
                if z["min_lel"] <= v < z["max_lel"]:
                    z["area_m2"] += cell_area
                    # 取单元格边界，避免仅中轴线达标时半宽为 0 的分辨率假象
                    z["max_x_m"] = max(z["max_x_m"], x + dx / 2)
                    z["max_half_width_m"] = max(z["max_half_width_m"], abs(y) + dy / 2)
    for z in zones.values():
        z["max_x_m"] = round(z["max_x_m"], 1)
        z["max_half_width_m"] = round(z["max_half_width_m"], 1)
        z["area_m2"] = round(z["area_m2"], 0)

    # 警戒/疏散半径：取警戒区最远端再留 1.2 倍安全系数
    evacuation_radius = round(zones["warning"]["max_x_m"] * 1.2, 1)

    return {
        "params": {
            "wind_speed_m_s": u, "wind_direction_deg": req.wind_direction_deg,
            "stability": req.stability.upper(), "leak_rate_kg_s": Q,
            "pressure_kpa": req.pressure_kpa, "temperature_c": req.temperature_c,
            "source_height_m": H, "gas_density_kg_m3": round(rho, 4),
        },
        "grid": {
            "nx": nx, "ny": ny,
            "x_max_m": xmax, "y_max_m": ymax,       # y ∈ [-y_max, y_max]
            "values_lel_pct": grid,
        },
        "centerline": centerline,
        "zones": zones,
        "evacuation_radius_m": evacuation_radius,
    }


@router.post("/simulate", summary="泄漏扩散仿真（浓度时空分布）")
def simulate(req: DiffusionSimReq):
    """
    输入泄漏速率、风速、风向、气压、温度、大气稳定度等，
    返回下风向/横风向地面浓度网格（%LEL）、轴线浓度剖面与各危险分区范围。
    风速越低、气压越高、稳定度越强（E/F），扩散越差、危险范围越大。
    """
    return _compute_field(req)


@router.post("/explosion-range", summary="爆炸危险范围计算")
def explosion_range(req: DiffusionSimReq):
    """
    仅返回爆炸危险范围评估结论（不返回大网格），适合嵌入预案系统：
    - 爆炸危险区（LEL~UEL）最远下风距离与最大横向半宽
    - 过富集区（>UEL）范围
    - 警戒区范围与建议疏散半径
    """
    field = _compute_field(req)
    return {
        "params": field["params"],
        "zones": field["zones"],
        "evacuation_radius_m": field["evacuation_radius_m"],
        "advice": _advice(field),
    }


def _advice(field: dict) -> list:
    """根据分区结果生成处置建议。"""
    advice = []
    exp = field["zones"]["explosion"]
    rich = field["zones"]["rich"]
    if exp["max_x_m"] > 0 or rich["max_x_m"] > 0:
        advice.append(f"下风向 {max(exp['max_x_m'], rich['max_x_m']):.0f}m 内存在爆炸风险，立即切断火源、禁行禁动火")
    advice.append(f"建议疏散半径 {field['evacuation_radius_m']:.0f}m，并在上风向设置警戒线")
    if field["params"]["wind_speed_m_s"] < 1.5:
        advice.append("风速低，燃气易在低洼处/管沟内积聚，需检测地下空间")
    if field["params"]["stability"] in ("E", "F"):
        advice.append("大气稳定（夜间/静稳），云团不易抬升稀释，危险范围偏保守估计")
    return advice
