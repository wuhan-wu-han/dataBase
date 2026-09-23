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
        <div class="login-actions">
          <el-button link type="primary" @click="openRegister">注册账号</el-button>
          <el-button link type="primary" @click="openForgotPassword">忘记密码？</el-button>
        </div>
        <el-button class="login-button" type="primary" size="large" :loading="loading" @click="submit">登录</el-button>
      </el-form>
    </section>

    <el-dialog v-model="forgotVisible" title="重置密码" width="420px" append-to-body destroy-on-close>
      <el-alert title="请输入账号及该账号已绑定的邮箱或手机号" type="info" :closable="false" show-icon />
      <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules" label-position="top" class="forgot-form">
        <el-form-item label="用户名" prop="username">
          <el-input v-model.trim="forgotForm.username" autocomplete="username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="绑定邮箱或手机号" prop="contact">
          <el-input v-model.trim="forgotForm.contact" placeholder="请输入已绑定的邮箱或手机号" />
        </el-form-item>
        <el-form-item label="验证码" prop="code">
          <div class="code-field">
            <div class="code-input">
              <el-input v-model.trim="forgotForm.code" maxlength="6" placeholder="6 位验证码" />
              <el-button :loading="forgotSending" :disabled="forgotCountdown > 0" @click="sendForgotCode">
                {{ forgotCountdown ? `重新发送 ${forgotCountdown}s` : '获取验证码' }}
              </el-button>
            </div>
            <span v-if="forgotExpiry > 0" class="code-expiry">验证码有效期 {{ formatExpiry(forgotExpiry) }}</span>
          </div>
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="forgotForm.newPassword" type="password" show-password autocomplete="new-password" placeholder="至少 8 位，包含字母和数字" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="forgotForm.confirmPassword" type="password" show-password autocomplete="new-password" placeholder="请再次输入新密码" @keyup.enter="resetPassword" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="forgotVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetting" @click="resetPassword">确认重置</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="registerVisible" title="注册账号" width="460px" append-to-body destroy-on-close>
      <el-alert title="注册成功后默认为只读用户，更多权限请联系管理员分配" type="info" :closable="false" show-icon />
      <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-position="top" class="forgot-form">
        <div class="form-grid">
          <el-form-item label="用户名" prop="username">
            <el-input v-model.trim="registerForm.username" autocomplete="username" placeholder="4-32 位，以字母开头" />
          </el-form-item>
          <el-form-item label="姓名" prop="displayName">
            <el-input v-model.trim="registerForm.displayName" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="电子邮箱" prop="email">
            <el-input v-model.trim="registerForm.email" autocomplete="email" placeholder="请输入用于验证的邮箱" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model.trim="registerForm.phone" autocomplete="tel" placeholder="中国大陆手机号" />
          </el-form-item>
          <el-form-item label="负责部门/区域" class="full-row">
            <el-input v-model.trim="registerForm.departmentId" placeholder="选填" />
          </el-form-item>
          <el-form-item label="邮箱验证码" prop="code" class="full-row">
            <div class="code-field">
              <div class="code-input">
                <el-input v-model.trim="registerForm.code" maxlength="6" placeholder="6 位验证码" />
                <el-button :loading="registerSending" :disabled="registerCountdown > 0" @click="sendRegisterCode">
                  {{ registerCountdown ? `重新发送 ${registerCountdown}s` : '获取验证码' }}
                </el-button>
              </div>
              <span v-if="registerExpiry > 0" class="code-expiry">验证码有效期 {{ formatExpiry(registerExpiry) }}</span>
            </div>
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="registerForm.password" type="password" show-password autocomplete="new-password" placeholder="至少 8 位，包含字母和数字" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="registerForm.confirmPassword" type="password" show-password autocomplete="new-password" placeholder="请再次输入密码" @keyup.enter="submitRegister" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="registerVisible = false">取消</el-button>
        <el-button type="primary" :loading="registering" @click="submitRegister">注册</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Odometer } from '@element-plus/icons-vue'
import { forgotPassword, login, register, sendVerificationCode, verifyVerificationCode } from '@/api/auth'
import { setSession } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const loading = ref(false)
const resetting = ref(false)
const forgotVisible = ref(false)
const forgotFormRef = ref()
const registerVisible = ref(false)
const registering = ref(false)
const registerFormRef = ref()
const forgotSending = ref(false)
const registerSending = ref(false)
const forgotCountdown = ref(0)
const registerCountdown = ref(0)
const forgotExpiry = ref(0)
const registerExpiry = ref(0)
const activeTimers = new Map()
const registerVerification = reactive({ token: '', target: '', expiresAt: 0 })
const form = reactive({ username: '', password: '' })
const forgotForm = reactive({ username: '', contact: '', code: '', newPassword: '', confirmPassword: '' })
const registerForm = reactive({ username: '', displayName: '', email: '', phone: '', departmentId: '', code: '', password: '', confirmPassword: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const forgotRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  contact: [{ required: true, message: '请输入已绑定的邮箱或手机号', trigger: 'blur' }],
  code: [{ required: true, pattern: /^\d{6}$/, message: '请输入 6 位验证码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,}$/, message: '密码至少 8 位，且必须包含字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [{
    validator: (_rule, value, callback) => value === forgotForm.newPassword ? callback() : callback(new Error('两次输入的密码不一致')),
    trigger: 'blur'
  }]
}
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[A-Za-z][A-Za-z0-9_.-]{3,31}$/, message: '用户名须为 4-32 位，并以字母开头', trigger: 'blur' }
  ],
  displayName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  code: [{ required: true, pattern: /^\d{6}$/, message: '请输入 6 位邮箱验证码', trigger: 'blur' }],
  phone: [{ pattern: /^(?:\+?86)?1\d{10}$|^$/, message: '手机号格式不正确', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,}$/, message: '密码至少 8 位，且必须包含字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [{
    validator: (_rule, value, callback) => value === registerForm.password ? callback() : callback(new Error('两次输入的密码不一致')),
    trigger: 'blur'
  }]
}

function openRegister() {
  Object.assign(registerForm, { username: form.username, displayName: '', email: '', phone: '', departmentId: '', code: '', password: '', confirmPassword: '' })
  Object.assign(registerVerification, { token: '', target: '', expiresAt: 0 })
  registerVisible.value = true
}

async function submitRegister() {
  if (registering.value || !(await registerFormRef.value?.validate().catch(() => false))) return
  if (!registerForm.email) {
    ElMessage.warning('注册必须填写并验证电子邮箱')
    return
  }
  registering.value = true
  try {
    const normalizedEmail = registerForm.email.trim().toLowerCase()
    let verificationToken = registerVerification.target === normalizedEmail &&
      registerVerification.expiresAt > Date.now()
      ? registerVerification.token
      : ''
    if (!verificationToken) {
      const verified = await verifyVerificationCode({
        scene: 'register', channel: 'email', target: normalizedEmail, code: registerForm.code
      })
      verificationToken = verified.verificationToken
      Object.assign(registerVerification, {
        token: verificationToken,
        target: normalizedEmail,
        expiresAt: Date.now() + (Number(verified.expiresIn) || 600) * 1000
      })
    }
    const result = await register({
      username: registerForm.username,
      displayName: registerForm.displayName,
      email: normalizedEmail,
      phone: registerForm.phone,
      departmentId: registerForm.departmentId,
      password: registerForm.password,
      verificationToken
    })
    registerVisible.value = false
    form.username = result.username || registerForm.username
    form.password = ''
    ElMessage.success(result.message || '注册成功，请登录')
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || '注册失败，请重试'
    if (/验证凭证/.test(detail)) Object.assign(registerVerification, { token: '', target: '', expiresAt: 0 })
    ElMessage.closeAll()
    ElMessage.error(error.response?.status === 409 ? `${detail}，请更换用户名后重新提交，验证码仍然有效` : detail)
  } finally {
    registering.value = false
  }
}

function openForgotPassword() {
  Object.assign(forgotForm, { username: form.username, contact: '', code: '', newPassword: '', confirmPassword: '' })
  forgotVisible.value = true
}

async function resetPassword() {
  if (resetting.value || !(await forgotFormRef.value?.validate().catch(() => false))) return
  resetting.value = true
  try {
    const channel = forgotForm.contact.includes('@') ? 'email' : 'sms'
    const verified = await verifyVerificationCode({
      scene: 'forgot_password', channel, target: forgotForm.contact,
      username: forgotForm.username, code: forgotForm.code
    })
    const result = await forgotPassword({
      username: forgotForm.username,
      newPassword: forgotForm.newPassword,
      resetToken: verified.verificationToken
    })
    forgotVisible.value = false
    form.username = forgotForm.username
    form.password = ''
    ElMessage.success(result.message || '密码重置成功，请使用新密码登录')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || error.message || '密码重置失败，请重试')
  } finally {
    resetting.value = false
  }
}

function runCountdown(state, seconds) {
  const oldTimer = activeTimers.get(state)
  if (oldTimer) window.clearInterval(oldTimer)
  state.value = Math.max(0, Number(seconds) || 0)
  const timer = window.setInterval(() => {
    state.value -= 1
    if (state.value <= 0) {
      state.value = 0
      window.clearInterval(timer)
      activeTimers.delete(state)
    }
  }, 1000)
  activeTimers.set(state, timer)
}

function formatExpiry(seconds) {
  const minutes = Math.floor(seconds / 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
}

async function sendRegisterCode() {
  if (!registerForm.email) return ElMessage.warning('请先填写电子邮箱')
  registerSending.value = true
  try {
    Object.assign(registerVerification, { token: '', target: '', expiresAt: 0 })
    const result = await sendVerificationCode({ scene: 'register', channel: 'email', target: registerForm.email })
    runCountdown(registerCountdown, 60)
    runCountdown(registerExpiry, result.expiresIn || 300)
    ElMessage.success('验证码已发送，5 分钟内有效')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '验证码发送失败')
  } finally { registerSending.value = false }
}

async function sendForgotCode() {
  if (!forgotForm.username || !forgotForm.contact) return ElMessage.warning('请先填写用户名和绑定联系方式')
  forgotSending.value = true
  try {
    const result = await sendVerificationCode({
      scene: 'forgot_password', channel: forgotForm.contact.includes('@') ? 'email' : 'sms',
      target: forgotForm.contact, username: forgotForm.username
    })
    runCountdown(forgotCountdown, 60)
    runCountdown(forgotExpiry, result.expiresIn || 300)
    ElMessage.success('如果账号信息匹配，验证码将在 5 分钟内有效')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '验证码发送失败')
  } finally { forgotSending.value = false }
}

onBeforeUnmount(() => {
  for (const timer of activeTimers.values()) window.clearInterval(timer)
  activeTimers.clear()
})

async function submit() {
  if (loading.value || !(await formRef.value?.validate().catch(() => false))) return
  loading.value = true
  try {
    setSession(await login(form))
    const requestedPath = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    const destination = requestedPath.startsWith('/') && !requestedPath.startsWith('/login') ? requestedPath : '/'
    await router.replace(destination)
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || error.message || '登录失败，请重试')
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
.login-actions { display: flex; justify-content: space-between; margin-top: -12px; }
.forgot-form { margin-top: 18px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 14px; }
.full-row { grid-column: 1 / -1; }
.code-input { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; width: 100%; }
.code-field { width: 100%; }
.code-expiry { display: block; margin-top: 6px; color: #5f6f82; font-size: 12px; font-variant-numeric: tabular-nums; }
@media (max-width: 520px) { .login-card { padding: 30px 24px; } }
@media (max-width: 520px) { .form-grid { grid-template-columns: 1fr; } .full-row { grid-column: auto; } }
</style>

