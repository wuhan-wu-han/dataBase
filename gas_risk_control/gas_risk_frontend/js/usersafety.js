/* ==========================================================================
   usersafety.js — 用户端用气安全页逻辑
   ========================================================================== */
const chartPie = echarts.init(document.getElementById("chart-pie"));
const chartFlow = echarts.init(document.getElementById("chart-flow"));
window.addEventListener("resize", () => { chartPie.resize(); chartFlow.resize(); });

const LEVEL_NAME = { normal: "正常", warning: "预警", severe: "严重" };
const LEVEL_COLOR = { normal: "#2fd08a", warning: "#ffc53d", severe: "#ff5b5b" };

async function initUsers() {
  const r = await api("/api/user-safety/users");
  const sel = document.getElementById("anomaly-user");
  sel.innerHTML = r.users.map(u => `<option value="${u.id}">${u.name}（${u.user_type}）</option>`).join("");
  // 若已有扫描结果则直接渲染
  if (r.users.some(u => u.last_ts_ms)) {
    renderTable(r.users.map(u => ({
      id: u.id, name: u.name, user_type: u.user_type,
      flow_m3h: "-", pressure_kpa: "-", co_ppm: "-", flame: "-",
      level: u.last_level, reasons: u.last_reasons,
    })));
    drawPie({ normal: r.users.filter(u => u.last_level === "normal").length,
              warning: r.users.filter(u => u.last_level === "warning").length,
              severe: r.users.filter(u => u.last_level === "severe").length });
  }
}

function drawPie(summary) {
  chartPie.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "item" },
    legend: { bottom: 0, textStyle: { color: "#8ba3c0" } },
    series: [{
      type: "pie", radius: ["38%", "62%"], center: ["50%", "45%"],
      label: { color: "#dce6f2", formatter: "{b}: {c}" },
      data: [
        { name: "正常", value: summary.normal, itemStyle: { color: LEVEL_COLOR.normal } },
        { name: "预警", value: summary.warning, itemStyle: { color: LEVEL_COLOR.warning } },
        { name: "严重", value: summary.severe, itemStyle: { color: LEVEL_COLOR.severe } },
      ],
    }],
  }, { replaceMerge: ["series"] });
}

function renderTable(results) {
  document.getElementById("user-body").innerHTML = results.map(u => `
    <tr data-uid="${u.id}" style="cursor:pointer">
      <td>${u.name}</td>
      <td>${u.user_type}</td>
      <td class="mono">${typeof u.flow_m3h === "number" ? u.flow_m3h : u.flow_m3h}</td>
      <td class="mono">${u.pressure_kpa}</td>
      <td class="mono">${u.co_ppm}</td>
      <td>${u.flame === 0 ? '<span class="badge red">熄火</span>' : u.flame === 1 ? '<span class="badge green">正常</span>' : "-"}</td>
      <td>${levelBadge(u.level)}</td>
      <td style="white-space:normal;max-width:320px">${(u.reasons || []).join("；")}</td>
    </tr>`).join("");

  // 行点击 → 查看该用户流量历史
  document.querySelectorAll("#user-body tr[data-uid]").forEach(tr => {
    tr.onclick = () => loadHistory(+tr.dataset.uid,
      results.find(x => x.id === +tr.dataset.uid)?.name || "");
  });
}

async function loadHistory(userId, name) {
  const r = await api(`/api/user-safety/history?user_id=${userId}&limit=60`);
  chartFlow.setOption({
    ...CHART_THEME,
    title: { text: name, textStyle: { color: "#dce6f2", fontSize: 13 }, left: 8, top: 0 },
    tooltip: { trigger: "axis" },
    grid: { left: 46, right: 20, top: 34, bottom: 30 },
    xAxis: { type: "category", data: r.points.map(p => fmtTime(p.ts_ms)), ...baseAxis() },
    yAxis: [
      { type: "value", name: "m³/h", ...baseAxis() },
      { type: "value", name: "CO ppm", ...baseAxis() },
    ],
    series: [
      { name: "流量", type: "line", data: r.points.map(p => p.flow_m3h),
        lineStyle: { color: "#3aa6ff" }, itemStyle: { color: "#3aa6ff" }, areaStyle: { color: "rgba(58,166,255,.1)" } },
      { name: "CO", type: "line", yAxisIndex: 1, data: r.points.map(p => p.co_ppm),
        lineStyle: { color: "#ff9f43" }, itemStyle: { color: "#ff9f43" } },
    ],
  }, { replaceMerge: ["series"] });
}

document.getElementById("btn-scan").onclick = async () => {
  try {
    const r = await api("/api/user-safety/scan", "POST", {});
    renderTable(r.results);
    drawPie(r.summary);
    const risky = r.results.filter(x => x.level !== "normal");
    toast(risky.length
      ? `扫描完成：发现 ${risky.length} 个风险用户（${risky.map(x => x.name).join("、")}）`
      : "扫描完成：全部用户正常", risky.some(x => x.level === "severe"));
  } catch (e) { toast(e.message, true); }
};

document.getElementById("btn-inject").onclick = async () => {
  try {
    const res = await api("/api/user-safety/simulate-anomaly", "POST", {
      user_id: +document.getElementById("anomaly-user").value,
      anomaly: document.getElementById("anomaly-type").value,
    });
    toast(res.msg);
  } catch (e) { toast(e.message, true); }
};

initUsers().catch(e => toast("无法连接后端: " + e.message, true));
