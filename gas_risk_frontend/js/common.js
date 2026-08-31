/* ==========================================================================
   common.js — 侧边栏导航渲染等公共逻辑
   ========================================================================== */
const NAV_ITEMS = [
  { href: "index.html",      idx: "1", name: "实时安全监测" },
  { href: "leak.html",       idx: "2", name: "微泄漏精准定位" },
  { href: "diffusion.html",  idx: "3", name: "泄漏扩散仿真" },
  { href: "third-party.html",idx: "4", name: "第三方破坏预警" },
  { href: "user-safety.html",idx: "5", name: "用户端用气安全" },
  { href: "occupation.html", idx: "6", name: "占压隐患管理" },
  { href: "cathodic.html",   idx: "7", name: "阴极保护监测" },
  { href: "emergency.html",  idx: "8", name: "应急联动关阀" },
];

// 渲染侧边栏并高亮当前页
function renderSidebar() {
  const el = document.getElementById("sidebar");
  if (!el) return;
  const current = location.pathname.split("/").pop() || "index.html";
  el.innerHTML = `
    <div class="logo">燃气管网安全风控
      <small>Gas Pipeline Safety Risk Control</small>
    </div>
    ${NAV_ITEMS.map(item => `
      <a class="nav-item ${item.href === current ? "active" : ""}" href="${item.href}">
        <span class="idx">${item.idx}</span>${item.name}
      </a>`).join("")}
  `;
}

document.addEventListener("DOMContentLoaded", renderSidebar);
