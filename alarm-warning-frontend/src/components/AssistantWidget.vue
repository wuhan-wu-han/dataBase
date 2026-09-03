<template>
  <!-- 悬浮触发按钮 -->
  <transition name="ai-fab">
    <button v-show="!open" class="ai-fab" type="button" aria-label="打开智能助手" @click="openPanel">
      <el-icon :size="26"><ChatDotRound /></el-icon>
    </button>
  </transition>

  <!-- 聊天面板 -->
  <transition name="ai-pop">
    <section v-show="open" class="ai-panel" aria-label="平台智能助手">
      <header class="ai-head">
        <div class="ai-head__left">
          <span class="ai-head__avatar"><el-icon :size="18"><MagicStick /></el-icon></span>
          <div>
            <div class="ai-head__title">平台智能助手</div>
            <div class="ai-head__sub">DeepSeek 大模型 · 自然语言查数据 / 跳模块</div>
          </div>
        </div>
        <button class="ai-head__close" type="button" aria-label="关闭" @click="open = false">
          <el-icon :size="18"><Close /></el-icon>
        </button>
      </header>

      <div ref="bodyRef" class="ai-body">
        <!-- 欢迎屏 + 快捷提问 -->
        <div v-if="messages.length === 0" class="ai-welcome">
          <div class="ai-welcome__hi">你好，我是安塞城市生命线平台的智能助手 👋</div>
          <p class="ai-welcome__tip">可以用大白话问我平台里的真实数据，或让我带你跳转到某个模块。试试：</p>
          <div class="ai-chips">
            <button v-for="s in suggestions" :key="s" class="ai-chip" type="button" @click="send(s)">{{ s }}</button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(m, i) in messages" :key="i" class="ai-msg" :class="'ai-msg--' + m.role">
          <div class="ai-bubble">
            <div v-if="m.error" class="ai-error">
              <el-icon :size="14"><WarningFilled /></el-icon> {{ m.error }}
            </div>
            <div v-else-if="m.role === 'assistant'" class="ai-md" v-html="renderMd(m.content)"></div>
            <div v-else class="ai-plain">{{ m.content }}</div>

            <!-- 跳转动作按钮 -->
            <button v-if="m.action" class="ai-navbtn" type="button" @click="go(m.action)">
              前往「{{ m.action.label }}」<el-icon :size="14"><Right /></el-icon>
            </button>

            <!-- 工具查询到的真实数据（可折叠） -->
            <div v-if="m.blocks && m.blocks.length" class="ai-data">
              <button class="ai-data__toggle" type="button" @click="m.showData = !m.showData">
                <el-icon :size="13"><DataLine /></el-icon>
                查看查询到的原始数据（{{ m.blocks.length }} 项）
                <el-icon :size="12" class="ai-data__arrow" :class="{ 'is-open': m.showData }"><ArrowDown /></el-icon>
              </button>
              <div v-show="m.showData" class="ai-data__body">
                <div v-for="(b, bi) in m.blocks" :key="bi" class="ai-block">
                  <div class="ai-block__title">{{ b.title }}</div>
                  <div v-if="b.kv" class="ai-kv">
                    <div v-for="(v, k) in b.kv" :key="k" class="ai-kv__item">
                      <span class="ai-kv__k">{{ k }}</span>
                      <span class="ai-kv__v">{{ v }}</span>
                    </div>
                  </div>
                  <div v-else-if="b.rows" class="ai-tablewrap">
                    <table class="ai-table">
                      <thead><tr><th v-for="c in b.cols" :key="c">{{ c }}</th></tr></thead>
                      <tbody>
                        <tr v-for="(r, ri) in b.rows" :key="ri">
                          <td v-for="c in b.cols" :key="c">{{ r[c] }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 思考中 -->
        <div v-if="loading" class="ai-msg ai-msg--assistant">
          <div class="ai-bubble ai-typing"><span></span><span></span><span></span></div>
        </div>
      </div>

      <footer class="ai-foot">
        <input
          v-model="draft"
          class="ai-input"
          type="text"
          placeholder="问点什么…（Enter 发送）"
          :disabled="loading"
          @keyup.enter="send()"
        />
        <button class="ai-send" type="button" :disabled="loading || !draft.trim()" @click="send()">
          <el-icon :size="16"><Promotion /></el-icon>
        </button>
      </footer>
    </section>
  </transition>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChatDotRound, Close, Right, MagicStick, WarningFilled,
  DataLine, ArrowDown, Promotion
} from '@element-plus/icons-vue'
import { sendChat } from '@/api/assistant'

const router = useRouter()
const open = ref(false)
const draft = ref('')
const loading = ref(false)
const messages = ref([])   // {role, content, action?, blocks?, error?, showData?}
const bodyRef = ref(null)

const suggestions = [
  '现在有多少待派单的工单？',
  '资产总净值是多少？',
  '应急预案一共几份、启用的有几份？',
  '打开综合管廊模块',
]

// 常见字段中文标签（提升原始数据可读性，未命中则用原键）
const FIELD_LABELS = {
  total_orders: '工单总数', pending_dispatch: '待派单', overdue_orders: '超期工单',
  active_orders: '进行中', completed_orders: '已完成', escalated_orders: '已升级',
  avg_rating: '平均评分', staff_idle: '空闲人员', total_plans: '预案总数',
  active_plans: '启用预案', draft_plans: '草稿预案', today_match_count: '今日匹配',
  today_drill_count: '今日演练', total_assets: '资产总数', total_original_value: '资产原值',
  total_net_value: '资产净值', total_accumulated_depr: '累计折旧', total_sensors: '传感器总数',
  online_sensors: '在线传感器', online_rate: '在线率', alarms_today: '今日告警',
  unhandled_alarms: '未处理告警', env_health_score: '环境健康分', media_count: '介质总数',
  media_warning_count: '告警介质', route_count: '输送路径', approved_routes: '合规路径',
  deviated_routes: '偏离路径', total_master_data: '主数据总量', pipeline_count: '数据管道',
  equipment_count: '设备数', personnel_count: '人员数', organization_count: '组织数',
}

const TOOL_TITLES = {
  query_workorder_overview: '工单总览', query_workorders: '工单列表',
  query_workorder_stats: '工单统计', query_plan_overview: '预案总览',
  query_plans: '预案列表', query_plan_categories: '预案分类',
  query_asset_overview: '资产总览', query_assets: '资产列表',
  query_asset_cost_analysis: '运维成本分析', query_tunnel_overview: '管廊总览',
  query_tunnel_alarms: '管廊告警', query_tunnel_alarm_stats: '管廊告警统计',
  query_hazmat_overview: '危废总览', query_hazmat_media: '危废介质',
  query_governance_overview: '数据治理总览', query_governance_master_stats: '主数据统计',
  query_governance_master: '主数据明细', navigate_to_module: '模块跳转',
}

const LIST_KEYS = ['records', 'orders', 'data', 'plans', 'assets', 'list', 'media', 'alarms', 'items', 'categories']

function openPanel() {
  open.value = true
  nextTick(() => bodyRef.value?.focus?.())
}

function fmt(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') return Number.isInteger(v) ? v : v.toFixed(2)
  if (typeof v === 'boolean') return v ? '是' : '否'
  if (typeof v === 'object') return JSON.stringify(v)
  return v
}

function label(k) {
  return FIELD_LABELS[k] || k
}

// 把工具结果转成 KV 卡片或表格块
function buildBlocks(toolResults) {
  const blocks = []
  for (const tr of toolResults || []) {
    const d = tr.data
    if (!d || typeof d !== 'object' || d._error) continue
    const title = TOOL_TITLES[tr.tool] || tr.tool

    let arr = null
    for (const k of LIST_KEYS) {
      if (Array.isArray(d[k]) && d[k].length && typeof d[k][0] === 'object') { arr = d[k]; break }
    }
    if (!arr && Array.isArray(d) && d.length && typeof d[0] === 'object') arr = d

    if (arr) {
      const cols = Object.keys(arr[0]).slice(0, 5)
      blocks.push({
        title, cols: cols.map(label),
        rows: arr.slice(0, 8).map((r) => {
          const o = {}
          cols.forEach((c) => { o[label(c)] = fmt(r[c]) })
          return o
        }),
      })
    } else {
      const kv = {}
      for (const [k, v] of Object.entries(d)) {
        if (v === null || ['string', 'number', 'boolean'].includes(typeof v)) kv[label(k)] = fmt(v)
      }
      if (Object.keys(kv).length) blocks.push({ title, kv })
    }
  }
  return blocks
}

// 极简 markdown 渲染（先转义防 XSS，再处理 **粗体**/`code`/列表/段落）
function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
function renderMd(s) {
  if (!s) return ''
  let inList = false
  let html = ''
  for (const raw of String(s).split('\n')) {
    let line = esc(raw)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
    if (/^[-•*]\s+/.test(line)) {
      if (!inList) { html += '<ul>'; inList = true }
      html += '<li>' + line.replace(/^[-•*]\s+/, '') + '</li>'
    } else {
      if (inList) { html += '</ul>'; inList = false }
      html += line.trim() === '' ? '<div class="ai-gap"></div>' : '<p>' + line + '</p>'
    }
  }
  if (inList) html += '</ul>'
  return html
}

function scroll() {
  nextTick(() => { if (bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight })
}

function ctxHistory() {
  return messages.value
    .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content)
    .slice(-8)
    .map((m) => ({ role: m.role, content: m.content }))
}

async function send(text) {
  const q = (text ?? draft.value).trim()
  if (!q || loading.value) return
  draft.value = ''
  messages.value.push({ role: 'user', content: q })
  loading.value = true
  scroll()
  try {
    const res = await sendChat(q, ctxHistory())
    if (res && res.success) {
      messages.value.push({
        role: 'assistant',
        content: res.answer || '',
        action: res.action || null,
        blocks: buildBlocks(res.tool_results),
        showData: false,
      })
    } else {
      messages.value.push({ role: 'assistant', content: '', error: (res && res.error) || '助手暂时不可用，请稍后再试' })
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '', error: '请求失败：' + (e?.message || e) + '（后端 :8000 是否已启动？）' })
  } finally {
    loading.value = false
    scroll()
  }
}

function go(action) {
  if (action && action.path) {
    router.push(action.path)
    open.value = false
  }
}
</script>

<style scoped>
/* ===== 悬浮按钮 ===== */
.ai-fab {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 100;
  width: 56px;
  height: 56px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0071E3 0%, #5856D6 100%);
  box-shadow: 0 6px 20px rgba(0, 113, 227, 0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.ai-fab:hover { transform: scale(1.08); box-shadow: 0 8px 26px rgba(0, 113, 227, 0.5); }

/* ===== 面板 ===== */
.ai-panel {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 101;
  width: 384px;
  max-width: calc(100vw - 32px);
  height: 580px;
  max-height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
  border-radius: 20px;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.86);
  -webkit-backdrop-filter: blur(28px) saturate(1.8);
  backdrop-filter: blur(28px) saturate(1.8);
  border: 1px solid var(--app-border);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
}

.ai-head {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #0071E3 0%, #5856D6 100%);
  color: #fff;
}
.ai-head__left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.ai-head__avatar {
  width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background-color: rgba(255, 255, 255, 0.22);
}
.ai-head__title { font-size: 15px; font-weight: 600; letter-spacing: -0.01em; }
.ai-head__sub { font-size: 11px; opacity: 0.85; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ai-head__close {
  flex-shrink: 0; width: 30px; height: 30px; border: none; border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.18); color: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: background-color 0.2s;
}
.ai-head__close:hover { background-color: rgba(255, 255, 255, 0.3); }

/* ===== 消息区 ===== */
.ai-body { flex: 1 1 auto; overflow-y: auto; padding: 16px 14px; display: flex; flex-direction: column; gap: 12px; }

.ai-welcome { padding: 8px 6px; }
.ai-welcome__hi { font-size: 15px; font-weight: 600; color: var(--app-text-1); margin-bottom: 6px; }
.ai-welcome__tip { font-size: 13px; color: var(--app-text-3); line-height: 1.6; margin: 0 0 12px; }
.ai-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ai-chip {
  font-size: 12.5px; color: var(--app-primary); cursor: pointer;
  padding: 7px 12px; border-radius: 14px; border: 1px solid var(--app-primary-soft);
  background-color: var(--app-primary-soft); transition: all 0.18s ease; text-align: left;
}
.ai-chip:hover { background-color: var(--app-primary); color: #fff; border-color: var(--app-primary); }

.ai-msg { display: flex; }
.ai-msg--user { justify-content: flex-end; }
.ai-msg--assistant { justify-content: flex-start; }
.ai-bubble {
  max-width: 86%; padding: 10px 13px; border-radius: 16px; font-size: 13.5px; line-height: 1.65;
  word-break: break-word;
}
.ai-msg--user .ai-bubble {
  background: linear-gradient(135deg, #0071E3 0%, #5856D6 100%); color: #fff;
  border-bottom-right-radius: 5px;
}
.ai-msg--assistant .ai-bubble {
  background-color: #fff; color: var(--app-text-1);
  border: 1px solid var(--app-border); border-bottom-left-radius: 5px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.ai-plain { white-space: pre-wrap; }
.ai-md :deep(p) { margin: 0 0 6px; }
.ai-md :deep(p:last-child) { margin-bottom: 0; }
.ai-md :deep(ul) { margin: 4px 0 6px; padding-left: 18px; }
.ai-md :deep(li) { margin: 2px 0; }
.ai-md :deep(strong) { font-weight: 600; color: var(--app-primary); }
.ai-md :deep(code) {
  background-color: var(--app-hover); padding: 1px 5px; border-radius: 5px;
  font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px;
}
.ai-gap { height: 6px; }

.ai-error { display: flex; align-items: center; gap: 6px; color: #C0392B; font-size: 13px; }

/* 跳转按钮 */
.ai-navbtn {
  margin-top: 9px; display: inline-flex; align-items: center; gap: 4px;
  padding: 7px 13px; border: none; border-radius: 10px; cursor: pointer;
  font-size: 13px; font-weight: 500; color: #fff;
  background: linear-gradient(135deg, #0071E3 0%, #5856D6 100%);
  transition: opacity 0.18s ease;
}
.ai-navbtn:hover { opacity: 0.9; }

/* 原始数据折叠区 */
.ai-data { margin-top: 10px; border-top: 1px dashed var(--app-border); padding-top: 8px; }
.ai-data__toggle {
  display: flex; align-items: center; gap: 5px; width: 100%;
  background: none; border: none; cursor: pointer; padding: 2px 0;
  font-size: 12px; color: var(--app-text-3);
}
.ai-data__toggle:hover { color: var(--app-primary); }
.ai-data__arrow { margin-left: auto; transition: transform 0.2s ease; }
.ai-data__arrow.is-open { transform: rotate(180deg); }
.ai-data__body { margin-top: 8px; display: flex; flex-direction: column; gap: 10px; }
.ai-block__title { font-size: 11.5px; font-weight: 600; color: var(--app-text-2); margin-bottom: 5px; }
.ai-kv { display: grid; grid-template-columns: 1fr 1fr; gap: 5px 10px; }
.ai-kv__item { display: flex; justify-content: space-between; gap: 6px; font-size: 12px; }
.ai-kv__k { color: var(--app-text-3); }
.ai-kv__v { color: var(--app-text-1); font-weight: 600; font-variant-numeric: tabular-nums; }
.ai-tablewrap { overflow-x: auto; border-radius: 8px; border: 1px solid var(--app-border); }
.ai-table { width: 100%; border-collapse: collapse; font-size: 11.5px; }
.ai-table th, .ai-table td { padding: 5px 8px; text-align: left; white-space: nowrap; border-bottom: 1px solid var(--app-border); }
.ai-table th { background-color: var(--app-hover); color: var(--app-text-2); font-weight: 600; }
.ai-table tr:last-child td { border-bottom: none; }

/* 思考中动画 */
.ai-typing { display: flex; gap: 4px; align-items: center; padding: 12px 14px; }
.ai-typing span {
  width: 7px; height: 7px; border-radius: 50%; background-color: var(--app-text-4);
  animation: ai-blink 1.2s infinite ease-in-out;
}
.ai-typing span:nth-child(2) { animation-delay: 0.2s; }
.ai-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes ai-blink { 0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); } 40% { opacity: 1; transform: scale(1); } }

/* ===== 输入区 ===== */
.ai-foot { flex: 0 0 auto; display: flex; gap: 8px; padding: 12px 14px; border-top: 1px solid var(--app-border); background-color: rgba(255, 255, 255, 0.6); }
.ai-input {
  flex: 1; min-width: 0; height: 38px; padding: 0 13px; font-size: 13.5px;
  border: 1px solid var(--app-border-strong); border-radius: 11px; outline: none;
  background-color: #fff; color: var(--app-text-1); transition: border-color 0.2s ease;
}
.ai-input:focus { border-color: var(--app-primary); }
.ai-input:disabled { background-color: var(--app-hover); }
.ai-send {
  flex-shrink: 0; width: 38px; height: 38px; border: none; border-radius: 11px; cursor: pointer;
  color: #fff; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0071E3 0%, #5856D6 100%); transition: opacity 0.18s ease;
}
.ai-send:disabled { opacity: 0.45; cursor: not-allowed; }

/* ===== 过渡动画 ===== */
.ai-pop-enter-active, .ai-pop-leave-active { transition: opacity 0.24s ease, transform 0.24s cubic-bezier(0.4, 0, 0.2, 1); }
.ai-pop-enter-from, .ai-pop-leave-to { opacity: 0; transform: translateY(16px) scale(0.96); }
.ai-fab-enter-active, .ai-fab-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.ai-fab-enter-from, .ai-fab-leave-to { opacity: 0; transform: scale(0.8); }

/* ===== 移动端 ===== */
@media (max-width: 767px) {
  .ai-panel { right: 12px; left: 12px; bottom: 12px; width: auto; height: 70vh; }
  .ai-fab { right: 16px; bottom: 16px; }
}
</style>
