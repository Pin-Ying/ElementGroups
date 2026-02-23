import { reactive } from 'vue'
import { login as apiLogin, logout as apiLogout, getAuthStatus } from '../api'

export const authState = reactive({
  loggedIn: false
})

export async function initAuth() {
  try {
    const res = await getAuthStatus()
    // 只允許設為 true（恢復頁面重整後的登入狀態）
    // 不設 false，避免 pending request 在用戶登入後才返回而覆蓋狀態
    if (res.data.loggedIn) {
      authState.loggedIn = true
    }
  } catch {
    // 忽略，不改變狀態
  }
}

export async function login(email, password) {
  const res = await apiLogin(email, password)
  if (res.data.result === 'success') {
    authState.loggedIn = true
    return { ok: true }
  }
  return { ok: false, message: res.data.message }
}

export async function logout() {
  await apiLogout()
  authState.loggedIn = false
}
