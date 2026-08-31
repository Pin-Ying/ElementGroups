import { reactive } from 'vue'
import { login as apiLogin, logout as apiLogout, getAuthStatus, googleLogin } from '../api'
import { signInWithGoogle } from '../utils/googleAuth'

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

/**
 * Google 登入。跑完 popup 拿到 ID token，再換成後台的 session token——
 * 存進 localStorage 的是後者，跟帳密登入完全一樣，後續請求無從分辨。
 *
 * 回傳 { ok } 或 { ok: false, message?, cancelled? }。cancelled 代表使用者
 * 自己關掉了 Google 的視窗，呼叫端不該當成錯誤跳提示。
 */
export async function loginWithGoogle() {
  const signIn = await signInWithGoogle()
  if (!signIn.ok) return signIn

  try {
    const res = await googleLogin(signIn.idToken)
    if (res.data.result === 'success') {
      localStorage.setItem('auth_token', res.data.token)
      authState.loggedIn = true
      return { ok: true }
    }
    return { ok: false, message: res.data.message }
  } catch (e) {
    // 後端擋下來時回 401，訊息在 body 裡（例如「這個 Google 帳號沒有後台
    // 權限」）。那是站長 ADMIN_ACCOUNTS 填錯時唯一的線索，要透出來
    return { ok: false, message: e.response?.data?.message || 'Google 登入失敗，請再試一次' }
  }
}

export async function logout() {
  await apiLogout()
  localStorage.removeItem('auth_token')
  authState.loggedIn = false
}
