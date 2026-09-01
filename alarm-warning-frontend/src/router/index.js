import { createRouter, createWebHistory } from 'vue-router'

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '监控大屏' }
  },
  {
    path: '/alerts',
    name: 'AlertList',
    component: () => import('@/views/AlertList.vue'),
    meta: { title: '预警事件列表' }
  },
  {
    path: '/alerts/:id',
    name: 'AlertDetail',
    component: () => import('@/views/AlertDetail.vue'),
    meta: { title: '预警详情' }
  },
  {
    path: '/rules',
    name: 'RuleManage',
    component: () => import('@/views/RuleManage.vue'),
    meta: { title: '规则管理' }
  },
  {
    path: '/failure-prediction',
    name: 'FailurePrediction',
    component: () => import('@/views/FailurePrediction.vue'),
    meta: { title: '故障预报与寿命预测' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：设置页面标题
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '智慧管廊预警平台'} - 智慧管廊预警平台`
  next()
})

export default router
