/* ==========================================================================
   leak.js — 微泄漏精准定位页逻辑
   ========================================================================== */
const chartConc = echarts.init(document.getElementById("chart-conc"));
const chartPw = echarts.init(document.getElementById("chart-pw"));
window.addEventListener("resize", () => { chartConc.resize(); chartPw.resize(); });

/* 绘制浓度定位结果：拟合曲线 + 实测点 + 定位/真实位置标线 */
function drawConcentration(data, truePos = null) {
  const res = data;
  const curve = (res.curve || []).map(p => [p.position_km, p.fitted_ppm]);
  const readings = (res.readings || []).map(r => [r.position_km, r.concentration_ppm]);

  const markLines = [{
    xAxis: res.position_km,
    label: { formatter: `定位 ${res.position_km}km`, color: "#3aa6ff" },
    lineStyle: { color: "#3aa6ff", width: 2 },
  }];
  if (truePos !== null) {
    markLines.push({
      xAxis: truePos,
      label: { formatter: `真实 ${truePos}km`, color: "#ff5b5b" },
      lineStyle: { color: "#ff5b5b", type: "dashed", width: 2 },
    });
  }

  chartConc.setOption({
    ...CHART_THEME,
    tooltip: { trigger: "item" },
    legend: { data: ["拟合扩散曲线", "测站实测浓度"], textStyle: { color: "#8ba3c0" }, top: 0 },
    grid: { left: 55, right: 30, top: 36, bottom: 40 },
    xAxis: { type: "value", name: "桩号 km", min: 0, max: 50, ...baseAxis() },
    yAxis: { type: "value", name: "浓度 ppm", ...baseAxis() },
    series: [
      { name: "拟合扩散曲线", type: "line", showSymbol: false, data: curve,
        lineStyle: { color: "#2fd08a", width: 2 }, itemStyle: { color: "#2fd08a" },
        areaStyle: { color: "rgba(47,208,138,.08)" },
        markLine: { silent: true, symbol: "none", data: markLines } },
      { name: "测站实测浓度", type: "scatter", data: readings, symbolSize: 12,
        itemStyle: { color: "#ffc53d" } },
    ],
  }, { replaceMerge: ["series"] });
}

function showConcResult(res, truePos = null) {
  const err = truePos !== null ? `｜定位误差 <b class="num">${Math.abs(res.position_km - truePos).toFixed(3)}</b> km` : "";
  const trueLine = truePos !== null ? `真实泄漏点：<b class="num">${truePos}</b> km　` : "";
  document.getElementById("conc-result").className = "result-box show";
  document.getElementById("conc-result").innerHTML =
    `定位结果：<b class="num">${res.position_km}</b> km　` +
    `置信度：<b class="num">${(res.confidence * 100).toFixed(1)}%</b>　` +
    `不确定度：±${res.uncertainty_km} km　拟合优度 R²=${res.r_squared}<br>${trueLine}${err}`;
}

/* 一键演示：随机真实泄漏点，双方法定位对比 */
document.getElementById("btn-demo").onclick = async () => {
  try {
    const d = await api("/api/leak/demo", "POST", {});
    if (d.concentration_result) {
      // 用完整定位接口获取拟合曲线（演示接口仅返回定位结果）
      const full = await api("/api/leak/locate-by-concentration", "POST", {
        readings: d.readings, background_ppm: 4.0, pipeline_length_km: 50 });
      drawConcentration(full, d.true_position_km);
      showConcResult(full, d.true_position_km);
    }
    const pw = d.pressure_wave_result;
    document.getElementById("pw-t1").value = pw.t_upstream_ms;
    document.getElementById("pw-t2").value = pw.t_downstream_ms;
    showPwResult({ position_km: pw.position_km, uncertainty_km: d.errors_km.pressure_wave });
    toast(`演示场景：真实泄漏点 ${d.true_position_km}km；浓度法误差 ${d.errors_km.concentration}km、压力波法误差 ${d.errors_km.pressure_wave}km`);
    loadRecords();
  } catch (e) { toast(e.message, true); }
};

/* 使用实时监测数据定位（与监测页联动：先注入泄漏再点此按钮） */
document.getElementById("btn-realtime").onclick = async () => {
  try {
    const rt = await api("/api/monitoring/realtime");
    const readings = rt.data.map(d => ({
      position_km: d.position_km,
      concentration_ppm: +d.concentration_ppm.toFixed(1),
    }));
    const res = await api("/api/leak/locate-by-concentration", "POST", {
      readings, background_ppm: 5.0, pipeline_length_km: 50 });
    drawConcentration(res);
    showConcResult(res);
    toast(`基于实时监测数据定位：${res.position_km}km（可先在监测页注入泄漏）`);
    loadRecords();
  } catch (e) { toast(e.message, true); }
};

/* 压力波法 */
function showPwResult(res) {
  document.getElementById("pw-result").className = "result-box show";
  document.getElementById("pw-result").innerHTML =
    `泄漏位置：<b class="num">${res.position_km}</b> km　` +
    `公式：${res.formula || "x = (L + v·(t_up − t_down)) / 2"}　` +
    `不确定度：±${res.uncertainty_km ?? "-"} km`;
  const L = +document.getElementById("pw-length").value || 50;
  chartPw.setOption({
    ...CHART_THEME,
    grid: { left: 55, right: 30, top: 24, bottom: 36 },
    xAxis: { type: "value", name: "桩号 km", min: 0, max: L, ...baseAxis() },
    yAxis: { type: "value", show: false, min: 0, max: 1 },
    series: [{
      type: "scatter", data: [[res.position_km, 0.5]], symbolSize: 22,
      itemStyle: { color: "#ff5b5b" },
      label: { show: true, formatter: `${res.position_km}km`, position: "top", color: "#ff5b5b" },
      markLine: { silent: true, symbol: "none", data: [
        [{ coord: [0, 0.5] }, { coord: [L, 0.5] }]],
        lineStyle: { color: "#3aa6ff", width: 4, opacity: .5 } },
    }],
  }, { replaceMerge: ["series"] });
}

document.getElementById("btn-pw").onclick = async () => {
  try {
    const res = await api("/api/leak/locate-by-pressure-wave", "POST", {
      pipeline_length_km: +document.getElementById("pw-length").value,
      wave_speed_m_s: +document.getElementById("pw-speed").value,
      t_upstream_ms: +document.getElementById("pw-t1").value,
      t_downstream_ms: +document.getElementById("pw-t2").value,
      timing_error_ms: +document.getElementById("pw-err").value,
    });
    showPwResult(res);
    loadRecords();
  } catch (e) { toast(e.message, true); }
};

document.getElementById("btn-pw-demo").onclick = async () => {
  // 随机真实位置反推两端到达时刻
  const L = +document.getElementById("pw-length").value || 50;
  const v = +document.getElementById("pw-speed").value || 350;
  const x = +(Math.random() * (L - 10) + 5).toFixed(2);
  document.getElementById("pw-t1").value = (x * 1e6 / v + (Math.random() * 6 - 3)).toFixed(1);
  document.getElementById("pw-t2").value = ((L - x) * 1e6 / v + (Math.random() * 6 - 3)).toFixed(1);
  toast(`已按真实位置 ${x}km 生成两端负压波到达时刻，点击「计算泄漏位置」验证`);
};

async function loadRecords() {
  const r = await api("/api/leak/records?limit=15");
  document.getElementById("records-body").innerHTML = r.records.map(x => `
    <tr>
      <td class="mono">${fmtTs(x.ts_ms)}</td>
      <td>${x.method === "concentration" ? "浓度扩散模型" : "压力波时差法"}</td>
      <td class="mono">${x.position_km}</td>
      <td class="mono">${(x.confidence * 100).toFixed(1)}%</td>
    </tr>`).join("") || '<tr><td colspan="4" class="muted">暂无记录</td></tr>';
}

loadRecords().catch(e => toast("无法连接后端: " + e.message, true));
