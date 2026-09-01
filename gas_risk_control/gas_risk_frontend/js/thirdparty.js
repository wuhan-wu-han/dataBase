/* ==========================================================================
   thirdparty.js — 第三方破坏预警页逻辑
   ========================================================================== */
const chartEvents = echarts.init(document.getElementById("chart-events"));
window.addEventListener("resize", () => chartEvents.resize());

const LEVEL_COLOR = { severe: "#ff5b5b", warning: "#ffc53d", notice: "#3aa6ff" };

async function refresh() {
  const r = await api("/api/third-party/warnings?limit=100");
  document.getElementById("st-severe").textContent = r.summary.severe;
  document.getElementById("st-warning").textContent = r.summary.warning;
  document.getElementById("st-notice").textContent = r.summary.notice;

  // 告警列表
  document.getElementById("warn-body").innerHTML = r.events.map(e => `
    <tr>
      <td class="mono">${fmtTs(e.ts_ms)}</td>
      <td>${e.event_type}</td>
      <td class="mono">${e.location_km}</td>
      <td class="mono">${e.lateral_m}</td>
      <td class="mono">${e.intensity}</td>
      <td class="mono">${e.score}</td>
      <td>${levelBadge(e.level)}</td>
      <td style="white-space:normal;max-width:340px">${e.distance_rule}${e.description ? "｜" + e.description : ""}</td>
    </tr>`).join("") || '<tr><td colspan="8" class="muted">暂无事件</td></tr>';

  // 扰动分布图：管线横轴 + 距离纵轴，用色带标出保护分区
  const scatter = r.events.map(e => ({
    value: [e.location_km, e.lateral_m],
    itemStyle: { color: LEVEL_COLOR[e.level] || "#8ba3c0" },
    symbolSize: 8 + Math.min(e.intensity, 10),
    name: `${e.event_type} @${e.location_km}km`,
  }));
  chartEvents.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "item", formatter: (p) => p.data.name },
    grid: { left: 60, right: 30, top: 36, bottom: 40 },
    xAxis: { type: "value", name: "桩号 km", min: 0, max: 50, ...baseAxis() },
    yAxis: { type: "value", name: "距管道距离 m", min: 0, max: 70, ...baseAxis() },
    series: [{
      type: "scatter", data: scatter,
      markArea: {
        silent: true, itemStyle: { opacity: 0.14 },
        data: [
          [{ yAxis: 0, itemStyle: { color: "#ff5b5b" }, label: { formatter: "保护范围 <5m 禁止作业", color: "#ff5b5b", position: "insideRight" } }, { yAxis: 5 }],
          [{ yAxis: 5, itemStyle: { color: "#ffc53d" }, label: { formatter: "控制作业区 5~20m", color: "#ffc53d", position: "insideRight" } }, { yAxis: 20 }],
          [{ yAxis: 20, itemStyle: { color: "#3aa6ff" }, label: { formatter: "安全控制区 20~50m", color: "#3aa6ff", position: "insideRight" } }, { yAxis: 50 }],
        ],
      },
    }],
  }, { replaceMerge: ["series"] });
}

document.getElementById("btn-report").onclick = async () => {
  try {
    const res = await api("/api/third-party/event", "POST", {
      event_type: document.getElementById("tp-type").value,
      location_km: +document.getElementById("tp-km").value,
      lateral_m: +document.getElementById("tp-dist").value,
      intensity: +document.getElementById("tp-intensity").value,
      description: document.getElementById("tp-desc").value,
    });
    toast(`事件已上报，判定：${res.distance_rule}（评分 ${res.score}）`, res.level === "severe");
    refresh();
  } catch (e) { toast(e.message, true); }
};

document.getElementById("btn-simulate").onclick = async () => {
  try {
    const res = await api("/api/third-party/simulate", "POST", {});
    toast(`模拟事件：${res.event.event_type} @${res.event.location_km}km，距管道 ${res.event.lateral_m}m → ${res.distance_rule}`);
    refresh();
  } catch (e) { toast(e.message, true); }
};

refresh().catch(e => toast("无法连接后端: " + e.message, true));
