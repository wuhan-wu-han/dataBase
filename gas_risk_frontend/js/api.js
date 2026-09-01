/* ==========================================================================
   api.js — 后端接口统一封装
   ========================================================================== */
// 后端服务地址（默认本机 8000 端口，可通过 localStorage.setItem('apiBase', ...) 覆盖）
const API_BASE = localStorage.getItem("apiBase") || "http://localhost:8000";

/**
 * 通用请求封装：自动拼 JSON、解析响应、抛出带状态码的错误
 * @param {string} path  接口路径，如 "/api/monitoring/realtime"
 * @param {string} method  HTTP 方法
 * @param {object} body  请求体（自动 JSON 序列化）
 */
async function api(path, method = "GET", body = undefined) {
  const opt = { method, headers: {} };
  if (body !== undefined) {
    opt.headers["Content-Type"] = "application/json";
    opt.body = JSON.stringify(body);
  }
  const res = await fetch(API_BASE + path, opt);
  if (!res.ok) {
    let msg = res.statusText;
    try { msg = JSON.stringify(await res.json()); } catch (e) { /* ignore */ }
    throw new Error(`接口 ${path} 返回 ${res.status}: ${msg}`);
  }
  return res.json();
}

/* ---------------- 公共工具 ---------------- */
// 毫秒时间戳 → 本地时间字符串
function fmtTs(ts) {
  if (!ts) return "-";
  const d = new Date(ts);
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

// 毫秒时间戳 → 时分秒
function fmtTime(ts) {
  if (!ts) return "-";
  const d = new Date(ts);
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

// 风险级别 → 徽章 HTML
function levelBadge(level) {
  const map = {
    severe: ["严重", "red"], "严重": ["严重", "red"],
    warning: ["预警", "orange"], "预警": ["预警", "orange"], "中": ["中", "orange"],
    notice: ["关注", "blue"], "关注": ["关注", "blue"],
    normal: ["正常", "green"], "正常": ["正常", "green"], "低": ["低", "green"],
    "高": ["高", "red"],
    open: ["开启", "green"], closed: ["关闭", "red"],
    unknown: ["未扫描", "gray"],
  };
  const [text, cls] = map[level] || [level, "gray"];
  return `<span class="badge ${cls}">${text}</span>`;
}

// 轻提示
function toast(msg, isError = false) {
  let el = document.querySelector(".toast");
  if (!el) {
    el = document.createElement("div");
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.toggle("error", isError);
  el.classList.add("show");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove("show"), 3200);
}

// ECharts 深色主题公共配置
const CHART_THEME = {
  backgroundColor: "transparent",
  textStyle: { color: "#8ba3c0" },
};
function baseAxis() {
  return {
    axisLine: { lineStyle: { color: "#24344d" } },
    axisLabel: { color: "#8ba3c0", fontSize: 11 },
    splitLine: { lineStyle: { color: "rgba(36,52,77,.5)" } },
  };
}
