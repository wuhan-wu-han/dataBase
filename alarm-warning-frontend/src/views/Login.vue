<template>
  <main class="login-page">
    <section class="login-card">
      <div class="login-brand"><el-icon :size="30"><Odometer /></el-icon></div>
      <p class="login-kicker">URBAN LIFELINE</p>
      <h1>登录智慧安全平台</h1>
      <p class="login-subtitle">使用您的平台账号继续访问</p>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model.trim="form.username" size="large" autocomplete="username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" size="large" type="password" show-password autocomplete="current-password"
                    placeholder="请输入密码" @keyup.enter="submit" />
        </el-form-item>
        <el-button class="login-button" type="primary" size="large" :loading="loading" @click="submit">登录</el-button>
      </el-form>
      <p class="login-hint">演示账号：admin / Admin@123</p>
    </section>
  </main>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Odometer } from '@element-plus/icons-vue'
import { login } from '@/api/auth'
import { setSession } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function submit() {
  if (loading.value || !(await formRef.value?.validate().catch(() => false))) return
  loading.value = true
  try {
    setSession(await login(form))
    ElMessage.success('登录成功')
    router.replace(typeof route.query.redirect === 'string' ? route.query.redirect : '/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; background:
  radial-gradient(circle at 15% 15%, rgba(0,113,227,.18), transparent 34%),
  radial-gradient(circle at 88% 82%, rgba(88,86,214,.14), transparent 34%), #f5f7fb; }
.login-card { width: min(420px, 100%); padding: 42px; border: 1px solid rgba(255,255,255,.75); border-radius: 28px;
  background: rgba(255,255,255,.82); backdrop-filter: blur(24px); box-shadow: 0 24px 70px rgba(26,42,70,.12); }
.login-brand { display: grid; place-items: center; width: 58px; height: 58px; margin-bottom: 24px; border-radius: 18px;
  color: #fff; background: linear-gradient(135deg,#0071e3,#5856d6); box-shadow: 0 10px 24px rgba(0,113,227,.25); }
.login-kicker { margin: 0 0 8px; color: #0071e3; font-size: 11px; font-weight: 700; letter-spacing: .14em; }
h1 { margin: 0; color: #1d1d1f; font-size: 28px; letter-spacing: -.03em; }
.login-subtitle { margin: 10px 0 30px; color: #6e6e73; }
.login-button { width: 100%; margin-top: 8px; font-weight: 600; }
.login-hint { margin: 22px 0 0; color: #86868b; font-size: 12px; text-align: center; }
@media (max-width: 520px) { .login-card { padding: 30px 24px; } }
</style>

