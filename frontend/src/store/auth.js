import { reactive } from 'vue'
import { login as apiLogin, logout as apiLogout, getAuthStatus } from '../api'

export const authState = reactive({
  loggedIn: false
})

export async function initAuth() {
  const token = localStorage.getItem('auth_token')
  if (!token) return
  try {
    const res = await getAuthStatus()
    if (res.data.loggedIn) {
      authState.loggedIn = true
    } else {
      localStorage.removeItem('auth_token')
    }
  } catch {
    localStorage.removeItem('auth_token')
  }
}

export async function login(email, password) {
  const res = await apiLogin(email, password)
  if (res.data.result === 'success') {
    localStorage.setItem('auth_token', res.data.token)
    authState.loggedIn = true
    return { ok: true }
  }
  return { ok: false, message: res.data.message }
}

export async function logout() {
  await apiLogout()
  localStorage.removeItem('auth_token')
  authState.loggedIn = false
}
