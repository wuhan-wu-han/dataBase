import { computed, reactive } from 'vue'

const TOKEN_KEY = 'rbac_access_token'
const USER_KEY = 'rbac_user'

function readUser() {
  try { return JSON.parse(sessionStorage.getItem(USER_KEY) || 'null') } catch { return null }
}

export const authState = reactive({
  token: sessionStorage.getItem(TOKEN_KEY) || '',
  user: readUser()
})

export const isAuthenticated = computed(() => Boolean(authState.token && authState.user))

export function setSession(payload) {
  authState.token = payload.accessToken
  authState.user = payload.user
  sessionStorage.setItem(TOKEN_KEY, payload.accessToken)
  sessionStorage.setItem(USER_KEY, JSON.stringify(payload.user))
}

export function clearSession() {
  authState.token = ''
  authState.user = null
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(USER_KEY)
}

export function can(permission) {
  const permissions = authState.user?.permissions || []
  return permissions.includes('*') || permissions.includes(permission)
}

