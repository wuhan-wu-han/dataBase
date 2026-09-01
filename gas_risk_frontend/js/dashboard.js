/* ==========================================================================
   dashboard.js — 实时安全监测页逻辑
   ========================================================================== */
let sensors = [];
let curSensorId = 1;

const gaugeLel = echarts.init(document.getElementById("gauge-lel"));
const gaugePressure = echarts.init(document.getElementById("gauge-pressure"));
const gaugeFlow = echarts.init(document.getElementById("gauge-flow"));
const chartHistory = echarts.init(document.getElementById("chart-history"));

window.addEventListener("resize", () =>
  [gaugeLel, gaugePressure, gaugeFlow, chartHistory].forEach(c => c.resize()));

function gaugeOption(title, value, max, unit, color, danger) {
  return {
    ...CHART_THEME,
    series: [{
      type: "gauge", min: 0, max, startAngle: 210, endAngle: -30,
      progress: { show: true, width: 12, itemStyle: { color } },
      axisLine: { lineStyle: { width: 12, color: [[1, "rgba(36,52,77,.9)"]] } },
      axisTick: { show: false }, splitLine: { show: false },
      axisLabel: { color: "#8ba3c0", fontSize: 10, distance: 14 },
      pointer: { show: true, width: 4, itemStyle: { color } },
      anchor: { show: true, size: 8, itemStyle: { color } },
      title: { offsetCenter: [0, "72%"], color: "#8ba3c0", fontSize: 12 },
      detail: {
        offsetCenter: [0, "45%"], fontSize: 22, color: danger ? "#ff5b5b" : "#fff",
        formatter: (v) => v.toFixed(2) + " " + unit,
      },
      data: [{ value, name: title }],
    }],
  };
}

async function initSensors() {
  sensors = await api("/api/monitoring/sensors");
  const sel = document.getElementById("sensor-select");
  const faultSel = document.getElementById("fault-sensor");
  sel.innerHTML = sensors.map(s =>
    `<option value="${s.id}">${s.name}（${s.position_km}km）</option>`).join("");
  faultSel.innerHTML = sel.innerHTML;
  curSensorId = sensors[0].id;
  sel.addEventListener("change", () => { curSensorId = +sel.value; refreshAll(); });
}

async function refreshRealtime() {
  const r = await api("/api/monitoring/realtime");
  const rows = r.data || [];

  // 统计卡片
  document.getElementById("st-sensors").textContent = rows.length;
  const alarming = rows.filter(d => d.alarm_level > 0);
  document.getElementById("st-alarming").textContent = alarming.length;
  const maxLel = rows.length ? Math.max(...rows.map(d => d.lel_pct)) : 0;
  document.getElementById("st-lel").textContent = maxLel.toFixed(2);
  const ps = rows.map(d => d.pressure_mpa);
  document.getElementById("st-pressure").textContent = ps.length
    ? `${Math.min(...ps).toFixed(2)} ~ ${Math.max(...ps).toFixed(2)}` : "-";

  // 当前测站仪表盘
  const cur = rows.find(d => d.sensor_id === curSensorId);
  if (cur) {
    gaugeLel.setOption(gaugeOption("燃气浓度 %LEL", Math.min(cur.lel_pct, 100), 100, "%LEL",
      cur.lel_pct >= 25 ? "#ff5b5b" : cur.lel_pct >= 5 ? "#ffc53d" : "#2fd08a", cur.lel_pct >= 25));
    gaugePressure.setOption(gaugeOption("管内压力 MPa", cur.pressure_mpa, 2.5, "MPa",
      (cur.pressure_mpa < 1.2 || cur.pressure_mpa > 2.0) ? "#ff5b5b" : "#3aa6ff",
      cur.pressure_mpa < 1.2));
    gaugeFlow.setOption(gaugeOption("流量 m³/h", cur.flow_m3h, 2000, "m³/h", "#b085f5", false));
  }
}

async function refreshHistory() {
  const h = await api(`/api/monitoring/history?sensor_id=${curSensorId}&minutes=10`);
  const pts = h.points || [];
  chartHistory.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "axis" },
    legend: { data: ["浓度 %LEL", "压力 MPa", "振动 mm/s"], textStyle: { color: "#8ba3c0" }, top: 0 },
    grid: { left: 50, right: 30, top: 36, bottom: 30 },
    xAxis: { type: "time", ...baseAxis() },
    yAxis: [
      { type: "value", name: "%LEL / mm/s", ...baseAxis() },
      { type: "value", name: "MPa", ...baseAxis() },
    ],
    series: [
      { name: "浓度 %LEL", type: "line", showSymbol: false, data: pts.map(p => [p.ts_ms, p.lel_pct]),
        lineStyle: { color: "#ffc53d" }, itemStyle: { color: "#ffc53d" },
        markLine: { silent: true, symbol: "none",
          data: [{ yAxis: 25, label: { formatter: "严重 25%LEL", color: "#ff5b5b" }, lineStyle: { color: "#ff5b5b", type: "dashed" } }] } },
      { name: "压力 MPa", type: "line", yAxisIndex: 1, showSymbol: false,
        data: pts.map(p => [p.ts_ms, p.pressure_mpa]),
        lineStyle: { color: "#3aa6ff" }, itemStyle: { color: "#3aa6ff" } },
      { name: "振动 mm/s", type: "line", showSymbol: false, data: pts.map(p => [p.ts_ms, p.vibration_mms]),
        lineStyle: { color: "#ff9f43" }, itemStyle: { color: "#ff9f43" } },
    ],
  }, { replaceMerge: ["series"] });
}

async function refreshAlarms() {
  const r = await api("/api/monitoring/alarms?limit=30");
  const body = document.getElementById("alarm-body");
  if (!r.alarms.length) {
    body.innerHTML = '<tr><td colspan="4" class="muted">暂无报警，工况正常</td></tr>';
    return;
  }
  body.innerHTML = r.alarms.map(a => `
    <tr>
      <td class="mono">${fmtTs(a.ts_ms)}</td>
      <td>${a.sensor_name || a.sensor_id}</td>
      <td>${a.level === 2 ? '<span class="badge red">严重</span>' : '<span class="badge orange">预警</span>'}</td>
      <td style="white-space:normal">${a.content}</td>
    </tr>`).join("");
}

async function refreshAll() {
  await Promise.allSettled([refreshRealtime(), refreshHistory(), refreshAlarms()]);
}

// 故障注入按钮
document.getElementById("btn-leak").onclick = async () => {
  const sid = +document.getElementById("fault-sensor").value;
  const mag = +document.getElementById("fault-magnitude").value;
  await api("/api/monitoring/simulate-leak", "POST", { sensor_id: sid, magnitude: mag });
  toast(`已向 ${sid}#测站注入泄漏，浓度将在数秒内上升并触发报警`);
};
document.getElementById("btn-disturb").onclick = async () => {
  const sid = +document.getElementById("fault-sensor").value;
  const mag = +document.getElementById("fault-magnitude").value;
  await api("/api/monitoring/simulate-disturbance", "POST", { sensor_id: sid, magnitude: mag });
  toast(`已向 ${sid}#测站注入施工振动扰动`);
};
document.getElementById("btn-clear").onclick = async () => {
  await api("/api/monitoring/clear-faults", "POST", {});
  toast("已清除注入故障，数据将逐步恢复正常");
};

initSensors().then(refreshAll).catch(e => toast("无法连接后端: " + e.message, true));
setInterval(refreshAll, 2000);   // 2 秒轮询，呈现实时效果
