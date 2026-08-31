/* ==========================================================================
   diffusion.js — 泄漏扩散仿真页逻辑
   ========================================================================== */
const chartHeat = echarts.init(document.getElementById("chart-heat"));
const chartProfile = echarts.init(document.getElementById("chart-profile"));
window.addEventListener("resize", () => { chartHeat.resize(); chartProfile.resize(); });

function collectParams() {
  return {
    leak_rate_kg_s: +document.getElementById("d-rate").value,
    wind_speed_m_s: +document.getElementById("d-wind").value,
    wind_direction_deg: +document.getElementById("d-dir").value,
    pressure_kpa: +document.getElementById("d-pressure").value,
    temperature_c: +document.getElementById("d-temp").value,
    stability: document.getElementById("d-stability").value,
    source_height_m: +document.getElementById("d-height").value,
    max_distance_m: +document.getElementById("d-dist").value,
  };
}

function showZones(field) {
  document.getElementById("zone-cards").style.display = "grid";
  document.getElementById("z-exp").textContent = field.zones.explosion.max_x_m + " m";
  document.getElementById("z-warn").textContent = field.zones.warning.max_x_m + " m";
  document.getElementById("z-evac").textContent = field.evacuation_radius_m + " m";
}

function drawHeatmap(field) {
  const g = field.grid;
  // ECharts heatmap 数据：[x索引, y索引, 值]；浓度截断到 400%LEL 便于显示色阶
  const data = [];
  for (let iy = 0; iy < g.ny; iy++) {
    for (let ix = 0; ix < g.nx; ix++) {
      data.push([ix, iy, Math.min(g.values_lel_pct[iy][ix], 400)]);
    }
  }
  const xLabels = Array.from({ length: 5 }, (_, i) => Math.round(g.x_max_m * i / 4));
  const yLabels = Array.from({ length: 5 }, (_, i) => Math.round(-g.y_max_m + 2 * g.y_max_m * i / 4));

  chartHeat.setOption({
    ...CHART_THEME,
    tooltip: {
      formatter: (p) => {
        const x = ((p.data[0] + 0.5) * g.x_max_m / g.nx).toFixed(0);
        const y = (-g.y_max_m + p.data[1] * (2 * g.y_max_m / (g.ny - 1))).toFixed(0);
        return `下风向 ${x}m，横风向 ${y}m<br>浓度：${g.values_lel_pct[p.data[1]][p.data[0]].toFixed(1)} %LEL`;
      },
    },
    grid: { left: 60, right: 110, top: 20, bottom: 40 },
    xAxis: {
      type: "category", data: Array.from({ length: g.nx }, (_, i) => i),
      name: "下风向距离 m", ...baseAxis(),
      axisLabel: {
        color: "#8ba3c0", fontSize: 11,
        formatter: (v) => Math.round((+v + 0.5) * g.x_max_m / g.nx),
        interval: Math.floor(g.nx / 5),
      },
    },
    yAxis: {
      type: "category", data: Array.from({ length: g.ny }, (_, i) => i),
      name: "横风向 m", ...baseAxis(),
      axisLabel: {
        color: "#8ba3c0", fontSize: 11,
        formatter: (v) => Math.round(-g.y_max_m + +v * (2 * g.y_max_m / (g.ny - 1))),
        interval: Math.floor(g.ny / 5),
      },
    },
    visualMap: {
      min: 0, max: 400, calculable: true, orient: "vertical", right: 8, top: "center",
      text: ["400%LEL", "0"], textStyle: { color: "#8ba3c0" },
      inRange: { color: ["#0d1420", "#1b4a7a", "#2fd08a", "#ffc53d", "#ff9f43", "#ff5b5b", "#b81616"] },
    },
    series: [{ type: "heatmap", data, progressive: 1000, emphasis: { itemStyle: { borderColor: "#fff", borderWidth: 1 } } }],
  }, { replaceMerge: ["series"] });
}

function drawProfile(field) {
  const pts = field.centerline.map(p => [p.x_m, Math.min(p.lel_pct, 2000)]);
  chartProfile.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "axis", formatter: (p) => `下风向 ${p[0].data[0]}m<br>${p[0].data[1].toFixed(1)} %LEL` },
    grid: { left: 60, right: 30, top: 20, bottom: 36 },
    xAxis: { type: "value", name: "下风向距离 m", ...baseAxis() },
    yAxis: { type: "log", name: "%LEL（对数）", min: 1, ...baseAxis() },
    series: [{
      type: "line", showSymbol: false, data: pts,
      lineStyle: { color: "#3aa6ff", width: 2 }, itemStyle: { color: "#3aa6ff" },
      areaStyle: { color: "rgba(58,166,255,.08)" },
      markLine: { silent: true, symbol: "none", data: [
        { yAxis: 100, label: { formatter: "LEL 爆炸下限 100%LEL", color: "#ff5b5b" }, lineStyle: { color: "#ff5b5b", type: "dashed" } },
        { yAxis: 20, label: { formatter: "警戒 20%LEL", color: "#ffc53d" }, lineStyle: { color: "#ffc53d", type: "dashed" } },
      ] },
    }],
  }, { replaceMerge: ["series"] });
}

document.getElementById("btn-sim").onclick = async () => {
  try {
    const field = await api("/api/diffusion/simulate", "POST", collectParams());
    showZones(field);
    drawHeatmap(field);
    drawProfile(field);
    toast(`仿真完成：爆炸危险区最远 ${field.zones.explosion.max_x_m}m，建议疏散半径 ${field.evacuation_radius_m}m`);
  } catch (e) { toast(e.message, true); }
};

document.getElementById("btn-range").onclick = async () => {
  try {
    const r = await api("/api/diffusion/explosion-range", "POST", collectParams());
    showZones(r);
    const box = document.getElementById("advice-box");
    box.className = "result-box show";
    box.innerHTML = "<b>处置建议：</b><br>" + r.advice.map(a => "· " + a).join("<br>");
    toast("爆炸危险范围计算完成");
  } catch (e) { toast(e.message, true); }
};

// 初始默认仿真一次
document.getElementById("btn-sim").click();
