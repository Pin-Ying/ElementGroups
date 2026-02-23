import { reactive } from 'vue'
import { login as apiLogin, logout as apiLogout, getAuthStatus } from '../api'

export const authState = reactive({
  loggedIn: false
})

export async function initAuth() {
  try {
    const res = await getAuthStatus()
    authState.loggedIn = res.data.loggedIn
  } catch {
    authState.loggedIn = false
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
