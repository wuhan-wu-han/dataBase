import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { can, isAuthenticated } from '@/stores/auth'

// 路由配置：AppLayout 作为父路由，所有业务路由嵌套其下，统一布局
const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录', public: true } },
  { path: '/403', name: 'Forbidden', component: () => import('@/views/Forbidden.vue'), meta: { title: '无权访问' } },
  {
    path: '/',
    component: AppLayout,
    children: [
      // ===== 主平台已实现模块 =====
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '监控大屏' }
      },
      {
        path: 'gis',
        name: 'GISSituation',
        component: () => import('@/views/gis/GISMap.vue'),
        // fullBleed：AppLayout 内容区去掉内边距并锁定视口高度，地图铺满顶栏以下区域
        meta: { title: '综合态势', fullBleed: true }
      },
      {
        path: 'alerts',
        name: 'AlertList',
        component: () => import('@/views/AlertList.vue'),
        meta: { title: '预警事件' }
      },
      {
        path: 'alerts/:id',
        name: 'AlertDetail',
        component: () => import('@/views/AlertDetail.vue'),
        meta: { title: '预警详情' }
      },
      {
        path: 'rules',
        name: 'RuleManage',
        component: () => import('@/views/RuleManage.vue'),
        meta: { title: '规则管理' }
      },
      {
        path: 'failure-prediction',
        name: 'FailurePrediction',
        component: () => import('@/views/FailurePrediction.vue'),
        meta: { title: '故障预报' }
      },

      // ===== 已迁移模块：路由直接跳转到本地页面组件 =====
      {
        // 燃气风控：从 gas_risk_frontend 迁移到 src/views/gasRisk/
        path: 'gas-risk',
        name: 'GasRisk',
        component: () => import('@/views/gasRisk/Index.vue'),
        meta: { title: '燃气风控' }
      },
      {
        // 资产管理：从 gas_asset_frontend 迁移到 src/views/asset/
        path: 'asset',
        name: 'Asset',
        component: () => import('@/views/asset/Index.vue'),
        meta: { title: '资产管理' }
      },
      {
        // 道路塌陷：从 road_hazard_frontend 迁移到 src/views/roadHazard/
        path: 'road-hazard',
        name: 'RoadHazard',
        component: () => import('@/views/roadHazard/Index.vue'),
        meta: { title: '道路塌陷' }
      },

      // ===== 新增业务模块 =====
      {
        path: 'risk-analysis',
        name: 'RiskAnalysis',
        component: () => import('@/views/riskAnalysis/Index.vue'),
        meta: { title: '风险研判' }
      },
      {
        path: 'hazmat',
        name: 'Hazmat',
        component: () => import('@/views/hazmat/Index.vue'),
        meta: { title: '危化品监管' }
      },
      {
        path: 'utility-tunnel',
        name: 'UtilityTunnel',
        component: () => import('@/views/tunnel/Index.vue'),
        meta: { title: '综合管廊' }
      },
      {
        path: 'emergency-plan',
        name: 'EmergencyPlan',
        component: () => import('@/views/emergencyPlan/Index.vue'),
        meta: { title: '应急预案' }
      },
      {
        path: 'asset-cost',
        name: 'AssetCost',
        component: () => import('@/views/assetCost/Index.vue'),
        meta: { title: '资产成本' }
      },
      {
        path: 'work-order',
        name: 'WorkOrder',
        component: () => import('@/views/workOrder/Index.vue'),
        meta: { title: '工单管理' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/UserManagement.vue'),
        meta: { title: '用户管理', permission: 'user:manage' }
      }
    ]
  },
  // 兜底：未匹配路由统一重定向到首页
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：设置页面标题
const APP_NAME = '安塞区城市安全生命线管网AI智慧平台'
router.beforeEach((to, from, next) => {
  document.title = to.meta?.title ? `${to.meta.title} - ${APP_NAME}` : APP_NAME
  if (!to.meta.public && !isAuthenticated.value) return next({ path: '/login', query: { redirect: to.fullPath } })
  if (to.path === '/login' && isAuthenticated.value) return next('/')
  if (to.meta.permission && !can(to.meta.permission)) return next('/403')
  next()
})

export default router
