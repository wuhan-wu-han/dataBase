/* ==========================================================================
   cathodic.js — 阴极保护监测页逻辑
   ========================================================================== */
const chartHistory = echarts.init(document.getElementById("chart-history"));
window.addEventListener("resize", () => chartHistory.resize());

const EV_COLOR = { normal: "green", under: "red", over: "orange", no_data: "gray" };
let piles = [];
let curPileId = null;

async function refresh() {
  const r = await api("/api/cathodic/realtime");
  piles = r.piles;

  const selPile = document.getElementById("sim-pile");
  const repPile = document.getElementById("rep-pile");
  if (!selPile.options.length) {
    const opts = piles.map(p => `<option value="${p.id}">${p.name}（${p.position_km}km）</option>`).join("");
    selPile.innerHTML = opts;
    repPile.innerHTML = opts;
    curPileId = piles[0].id;
  }

  document.getElementById("pile-body").innerHTML = piles.map(p => {
    const ev = p.evaluation || {};
    const l = p.latest || {};
    return `
    <tr data-pid="${p.id}" style="cursor:pointer">
      <td>${p.name}</td>
      <td class="mono">${p.position_km}</td>
      <td class="mono">${l.on_potential_v ?? "-"}</td>
      <td class="mono">${l.off_potential_v ?? "-"}</td>
      <td class="mono">${l.output_current_a ?? "-"}</td>
      <td><span class="badge ${EV_COLOR[ev.status] || "gray"}">${ev.status_text || "无数据"}</span></td>
      <td class="mono">${ev.score ?? "-"}</td>
      <td style="white-space:normal;max-width:320px">${(ev.issues || []).join("；")}</td>
    </tr>`;
  }).join("");

  document.querySelectorAll("#pile-body tr[data-pid]").forEach(tr => {
    tr.onclick = () => { curPileId = +tr.dataset.pid; loadHistory(); };
  });

  if (curPileId) loadHistory();
}

async function loadHistory() {
  const r = await api(`/api/cathodic/history?pile_id=${curPileId}&hours=24`);
  const name = piles.find(p => p.id === curPileId)?.name || "";
  chartHistory.setOption({
    ...CHART_THEME,
    title: { text: `${name} 最近 24 小时`, textStyle: { color: "#dce6f2", fontSize: 13 }, left: 8, top: 0 },
    tooltip: { trigger: "axis" },
    legend: { data: ["断电电位 V", "通电电位 V", "输出电流 A"], textStyle: { color: "#8ba3c0" }, top: 0, right: 10 },
    grid: { left: 55, right: 50, top: 36, bottom: 30 },
    xAxis: { type: "time", ...baseAxis() },
    yAxis: [
      { type: "value", name: "电位 V", max: 0, min: -2, ...baseAxis() },
      { type: "value", name: "电流 A", ...baseAxis() },
    ],
    series: [
      { name: "断电电位 V", type: "line", showSymbol: false, data: r.points.map(p => [p.ts_ms, p.off_potential_v]),
        lineStyle: { color: "#3aa6ff" }, itemStyle: { color: "#3aa6ff" },
        markArea: { silent: true, itemStyle: { color: "rgba(47,208,138,.08)" },
          data: [[{ yAxis: -1.2 }, { yAxis: -0.85 }]] } },
      { name: "通电电位 V", type: "line", showSymbol: false, data: r.points.map(p => [p.ts_ms, p.on_potential_v]),
        lineStyle: { color: "#8ba3c0", type: "dashed" }, itemStyle: { color: "#8ba3c0" } },
      { name: "输出电流 A", type: "line", yAxisIndex: 1, showSymbol: false,
        data: r.points.map(p => [p.ts_ms, p.output_current_a]),
        lineStyle: { color: "#ffc53d" }, itemStyle: { color: "#ffc53d" } },
    ],
  }, { replaceMerge: ["series"] });
}

document.getElementById("btn-evaluate").onclick = async () => {
  try {
    const r = await api("/api/cathodic/evaluate");
    const s = r.summary;
    document.getElementById("eval-summary").textContent =
      `全线 ${s.total} 桩，保护正常 ${s.normal} 桩，保护率 ${s.protection_rate_pct}%，平均得分 ${s.avg_score}`;
    toast("综合评估：" + r.suggestions.join("；"));
    refresh();
  } catch (e) { toast(e.message, true); }
};

document.getElementById("btn-sim-normal").onclick = async () => {
  await api("/api/cathodic/simulate-data", "POST", {});
  toast("已生成一轮全网测试桩数据");
  refresh();
};
document.getElementById("btn-sim-under").onclick = async () => {
  const pid = +document.getElementById("sim-pile").value;
  await api(`/api/cathodic/simulate-data?under_pile=${pid}`, "POST", {});
  toast(`已模拟 ${pid}#桩保护不足（断电电位正于 -0.85V 且输出电流骤降）`);
  refresh();
};
document.getElementById("btn-sim-over").onclick = async () => {
  const pid = +document.getElementById("sim-pile").value;
  await api(`/api/cathodic/simulate-data?over_pile=${pid}`, "POST", {});
  toast(`已模拟 ${pid}#桩过保护（断电电位负于 -1.2V）`);
  refresh();
};

document.getElementById("btn-report").onclick = async () => {
  try {
    const r = await api("/api/cathodic/data", "POST", {
      pile_id: +document.getElementById("rep-pile").value,
      on_potential_v: +document.getElementById("rep-on").value,
      off_potential_v: +document.getElementById("rep-off").value,
      output_current_a: +document.getElementById("rep-current").value,
    });
    document.getElementById("report-result").textContent =
      `评价：${r.evaluation.status_text}（得分 ${r.evaluation.score}）`;
    refresh();
  } catch (e) { toast(e.message, true); }
};

refresh().catch(e => toast("无法连接后端: " + e.message, true));
