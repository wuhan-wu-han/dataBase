/* ==========================================================================
   emergency.js — 应急联动关阀页逻辑
   ========================================================================== */
const chartPipeline = echarts.init(document.getElementById("chart-pipeline"));
window.addEventListener("resize", () => chartPipeline.resize());

let valves = [];
let currentEventId = null;
let leakPos = null;

const STATUS_TEXT = { planned: "方案已生成", executed: "已关阀隔离", restored: "已恢复" };

/* 绘制管线 + 阀门状态 + 泄漏点 */
function drawPipeline() {
  const valveData = valves.map(v => ({
    value: [v.position_km, 0.5],
    name: `${v.id}（${v.status === "open" ? "开启" : "关闭"}）`,
    symbol: v.status === "open" ? "circle" : "rect",
    symbolSize: 18,
    itemStyle: { color: v.status === "open" ? "#2fd08a" : "#ff5b5b" },
    label: { show: true, formatter: v.id, position: "top", color: "#8ba3c0", fontSize: 11 },
  }));
  const series = [{
    type: "scatter", data: valveData,
    markLine: { silent: true, symbol: "none", data: [[{ coord: [0, 0.5] }, { coord: [50, 0.5] }]],
      lineStyle: { color: "#3aa6ff", width: 5, opacity: .55 } },
  }];
  if (leakPos !== null) {
    series.push({
      type: "scatter", data: [[leakPos, 0.5]], symbol: "pin", symbolSize: 44,
      itemStyle: { color: "#ff5b5b" },
      label: { show: true, formatter: "泄漏点", position: "bottom", color: "#ff5b5b", fontSize: 12 },
      zlevel: 2,
    });
  }
  chartPipeline.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "item", formatter: (p) => p.data.name || "" },
    grid: { left: 40, right: 40, top: 30, bottom: 30 },
    xAxis: { type: "value", name: "桩号 km", min: -1, max: 51, ...baseAxis() },
    yAxis: { type: "value", show: false, min: 0, max: 1 },
    series,
  }, { replaceMerge: ["series"] });
}

async function loadValves() {
  valves = await api("/api/emergency/valves");
  drawPipeline();
}

function renderPlan(plan) {
  const seg = plan.isolation_segment;
  document.getElementById("plan-box").className = "result-box show";
  document.getElementById("plan-box").innerHTML = `
    <b>级联关阀方案</b>（泄漏点 ${plan.leak_position_km}km，级别 ${plan.level}）<br>
    ${plan.steps.map(s =>
      `第 ${s.seq} 步：${s.reason}（延迟 ${s.delay_s}s）`).join("<br>")}
    <br><b>隔离评估：</b>隔离段 ${seg.from_km}~${seg.to_km}km（长 ${seg.length_km}km），
    段内估算存气 <b class="num">${seg.stored_gas_m3_std}</b> m³（标态），
    预计影响用户约 <b class="num">${seg.affected_users_estimate}</b> 户<br>
    <span class="muted">${plan.note}</span>`;
}

/* 生成方案 */
document.getElementById("btn-trigger").onclick = async () => {
  try {
    const r = await api("/api/emergency/trigger", "POST", {
      position_km: +document.getElementById("em-km").value,
      level: document.getElementById("em-level").value,
      source: document.getElementById("em-source").value,
    });
    currentEventId = r.event_id;
    leakPos = r.plan.leak_position_km;
    renderPlan(r.plan);
    drawPipeline();
    document.getElementById("btn-execute").disabled = false;
    document.getElementById("btn-restore").disabled = true;
    toast(`应急事件 #${r.event_id} 方案已生成，待执行关阀`);
    loadEvents();
  } catch (e) { toast(e.message, true); }
};

/* 执行关阀 */
document.getElementById("btn-execute").onclick = async () => {
  if (!currentEventId) return;
  try {
    const r = await api(`/api/emergency/events/${currentEventId}/execute`, "POST", {});
    toast(r.isolation.result);
    document.getElementById("btn-execute").disabled = true;
    document.getElementById("btn-restore").disabled = false;
    await loadValves();
    loadEvents();
  } catch (e) { toast(e.message, true); }
};

/* 恢复供气 */
document.getElementById("btn-restore").onclick = async () => {
  if (!currentEventId) return;
  try {
    const r = await api(`/api/emergency/events/${currentEventId}/restore`, "POST", {});
    toast(r.msg);
    document.getElementById("btn-restore").disabled = true;
    leakPos = null;
    await loadValves();
    loadEvents();
  } catch (e) { toast(e.message, true); }
};

async function loadEvents() {
  const r = await api("/api/emergency/events?limit=20");
  document.getElementById("event-body").innerHTML = r.events.map(ev => `
    <tr>
      <td class="mono">#${ev.id}</td>
      <td class="mono">${fmtTs(ev.ts_ms)}</td>
      <td class="mono">${ev.position_km}</td>
      <td>${levelBadge(ev.level)}</td>
      <td>${ev.source === "leak_alarm" ? "泄漏报警联动" : "人工触发"}</td>
      <td><span class="badge ${ev.status === "executed" ? "red" : ev.status === "restored" ? "green" : "blue"}">${STATUS_TEXT[ev.status] || ev.status}</span></td>
      <td><button class="btn sm ghost" onclick="viewEvent(${ev.id})">详情</button></td>
    </tr>`).join("") || '<tr><td colspan="7" class="muted">暂无事件</td></tr>';
}

/* 查看历史事件详情并复现方案 */
async function viewEvent(eventId) {
  try {
    const d = await api(`/api/emergency/events/${eventId}`);
    currentEventId = eventId;
    leakPos = d.position_km;
    renderPlan(d.plan);
    if (d.isolation) {
      document.getElementById("plan-box").innerHTML +=
        `<br><b>执行结果：</b>${d.isolation.result || ""}`;
    }
    drawPipeline();
    document.getElementById("btn-execute").disabled = d.status !== "planned";
    document.getElementById("btn-restore").disabled = d.status !== "executed";
  } catch (e) { toast(e.message, true); }
}
window.viewEvent = viewEvent;

loadValves().catch(e => toast("无法连接后端: " + e.message, true));
loadEvents();
