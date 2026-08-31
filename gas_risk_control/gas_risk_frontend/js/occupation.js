/* ==========================================================================
   occupation.js — 占压隐患管理页逻辑（台账 + 整改闭环 + 时间线）
   ========================================================================== */
const chartType = echarts.init(document.getElementById("chart-type"));
const chartStatus = echarts.init(document.getElementById("chart-status"));
window.addEventListener("resize", () => { chartType.resize(); chartStatus.resize(); });

const STATUS_COLOR = { "待下达": "#ff5b5b", "已下达": "#ff9f43", "整改中": "#ffc53d", "待验收": "#3aa6ff", "已闭环": "#2fd08a" };
let curRecordId = null;

async function refresh() {
  const qs = new URLSearchParams();
  const st = document.getElementById("filter-status").value;
  const tp = document.getElementById("filter-type").value;
  if (st) qs.set("status", st);
  if (tp) qs.set("type", tp);
  const r = await api("/api/occupation/records?" + qs.toString());

  document.getElementById("record-body").innerHTML = r.records.map(rec => `
    <tr>
      <td class="mono">#${rec.id}</td>
      <td>${rec.type}</td>
      <td class="mono">${rec.location_km}</td>
      <td style="white-space:normal;max-width:260px">${rec.description || "-"}</td>
      <td>${levelBadge(rec.risk_level)}</td>
      <td>${rec.responsible || "-"}</td>
      <td>${rec.deadline || "-"}</td>
      <td><span class="badge" style="background:${STATUS_COLOR[rec.status]}22;color:${STATUS_COLOR[rec.status]}">${rec.status}</span></td>
      <td><button class="btn sm ghost" onclick="openRectify(${rec.id})">整改跟踪</button></td>
    </tr>`).join("") || '<tr><td colspan="9" class="muted">无匹配记录</td></tr>';

  refreshStats();
}

async function refreshStats() {
  const s = await api("/api/occupation/stats");
  chartType.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "item" },
    series: [{
      type: "pie", radius: ["34%", "60%"], center: ["50%", "50%"],
      label: { color: "#dce6f2", formatter: "{b}\n{c}" },
      data: s.by_type.map(x => ({ name: x.name, value: x.value })),
    }],
  }, { replaceMerge: ["series"] });

  chartStatus.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "axis" },
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
    xAxis: { type: "category", data: s.by_status.map(x => x.name), ...baseAxis() },
    yAxis: { type: "value", minInterval: 1, ...baseAxis() },
    series: [{
      type: "bar", barWidth: 26,
      data: s.by_status.map(x => ({ value: x.value, itemStyle: { color: STATUS_COLOR[x.name] || "#3aa6ff" } })),
    }],
  }, { replaceMerge: ["series"] });

  document.getElementById("cl-total").textContent = s.total;
  document.getElementById("cl-closed").textContent = s.closed;
  document.getElementById("cl-rate").textContent = s.closure_rate_pct + "%";
}

/* ---------------- 新增隐患 ---------------- */
document.getElementById("btn-new").onclick = () =>
  document.getElementById("modal-new").classList.add("show");

document.getElementById("btn-save-new").onclick = async () => {
  try {
    await api("/api/occupation/records", "POST", {
      type: document.getElementById("new-type").value,
      location_km: +document.getElementById("new-km").value,
      description: document.getElementById("new-desc").value,
      risk_level: document.getElementById("new-level").value,
      responsible: document.getElementById("new-resp").value,
      deadline: document.getElementById("new-deadline").value,
    });
    document.getElementById("modal-new").classList.remove("show");
    toast("隐患已登记入台账");
    refresh();
  } catch (e) { toast(e.message, true); }
};

/* ---------------- 整改跟踪 ---------------- */
async function openRectify(recordId) {
  curRecordId = recordId;
  document.getElementById("modal-rectify").classList.add("show");
  document.getElementById("rectify-title").textContent = `隐患 #${recordId}`;
  await loadTimeline();
}
window.openRectify = openRectify;

async function loadTimeline() {
  const t = await api(`/api/occupation/records/${curRecordId}/timeline`);
  document.getElementById("rectify-timeline").innerHTML = t.timeline.map(log => `
    <li>
      <span class="t-time">${fmtTs(log.ts_ms)}</span>
      <span class="t-status badge blue">${log.status_to}</span><br>
      ${log.action} <span class="muted">— ${log.operator}</span>
    </li>`).join("") || '<li class="muted">暂无记录</li>';
}

document.getElementById("btn-save-rectify").onclick = async () => {
  try {
    await api(`/api/occupation/records/${curRecordId}/rectify`, "POST", {
      action: document.getElementById("rectify-action").value,
      operator: document.getElementById("rectify-operator").value,
      status_to: document.getElementById("rectify-status").value,
    });
    document.getElementById("rectify-action").value = "";
    toast("整改动作已记录，状态已流转");
    await loadTimeline();
    refresh();
  } catch (e) { toast(e.message, true); }
};

/* 弹窗关闭（遮罩点击 / data-close 按钮） */
document.querySelectorAll(".modal-mask").forEach(mask => {
  mask.addEventListener("click", (e) => {
    if (e.target === mask || e.target.hasAttribute("data-close")) mask.classList.remove("show");
  });
});

document.getElementById("filter-status").onchange = refresh;
document.getElementById("filter-type").onchange = refresh;

refresh().catch(e => toast("无法连接后端: " + e.message, true));
