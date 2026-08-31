// 用 Google 帳號登入後台。
//
// Firebase SDK 是動態 import 的，不是寫在頂層。理由是體積：整包 bundle 已經
// 一點四 MB，而這個功能只有站長會用到，沒必要讓每個訪客都下載。動態 import
// 會讓 Vite 把 firebase 切成獨立的 chunk，真的按下按鈕才去抓。
//
// 流程：跟後端要設定 → 載入 SDK → signInWithPopup → 拿到 ID token →
// 送去 /api/auth/google 換成後台自己的 session token。後端那一支會驗證
// token 並比對 ADMIN_ACCOUNTS 白名單，**通過 Google 不等於能進後台**。

import { getFirebaseConfig } from '../api'

// 設定與 SDK 實例都只取一次。使用者可能按錯又按一次，沒必要重來
let configPromise = null
let appPromise = null

/**
 * 這個站有沒有開 Google 登入。回傳 { enabled, config }。
 * 後端沒開就只會回 { enabled: false }，前端據此不顯示按鈕，也不下載 SDK。
 * 查詢失敗一律當成沒開——與其顯示一顆按不動的按鈕，不如不要出現。
 */
export function fetchGoogleLoginConfig() {
  if (!configPromise) {
    configPromise = getFirebaseConfig()
      .then(res => res.data || { enabled: false })
      .catch(() => ({ enabled: false }))
  }
  return configPromise
}

async function ensureAuth(config) {
  if (!appPromise) {
    appPromise = (async () => {
      const [{ initializeApp }, auth] = await Promise.all([
        import('firebase/app'),
        import('firebase/auth')
      ])
      const app = initializeApp(config)
      return { auth, instance: auth.getAuth(app) }
    })()
  }
  return appPromise
}

/** Firebase 的錯誤碼換成看得懂的中文。認不出來的就回空字串，讓呼叫端用預設訊息。 */
function readableError(code) {
  switch (code) {
    case 'auth/popup-closed-by-user':
    case 'auth/cancelled-popup-request':
      // 使用者自己關掉視窗，不是錯誤，呼叫端會安靜收掉
      return ''
    case 'auth/popup-blocked':
      return '瀏覽器擋下了登入視窗，請允許彈出視窗後再試一次'
    case 'auth/unauthorized-domain':
      // 這個最容易發生：主控台的授權網域沒加線上網址
      return '這個網域沒有被 Firebase 授權，請在主控台的 Authentication → Settings → 授權網域加入'
    case 'auth/operation-not-allowed':
      return 'Firebase 專案還沒啟用 Google 供應商'
    case 'auth/network-request-failed':
      return '連線失敗，請檢查網路後再試一次'
    default:
      return ''
  }
}

/**
 * 跑完整個 Google 登入流程，回傳 { ok, idToken } 或 { ok: false, message, cancelled }。
 * cancelled 為 true 代表使用者自己關掉視窗，呼叫端不該跳錯誤提示。
 */
export async function signInWithGoogle() {
  const { enabled, config } = await fetchGoogleLoginConfig()
  if (!enabled || !config) {
    return { ok: false, message: 'Google 登入未啟用' }
  }

  try {
    const { auth, instance } = await ensureAuth(config)
    const provider = new auth.GoogleAuthProvider()
    const credential = await auth.signInWithPopup(instance, provider)
    // 這張 token 只是拿去給後端驗證身分，不存起來——後台認的是
    // /api/auth/google 換回來的 session token
    const idToken = await credential.user.getIdToken()
    return { ok: true, idToken }
  } catch (e) {
    const message = readableError(e?.code)
    if (e?.code === 'auth/popup-closed-by-user' || e?.code === 'auth/cancelled-popup-request') {
      return { ok: false, cancelled: true }
    }
    console.error('Google 登入失敗:', e?.code || e)
    return { ok: false, message: message || 'Google 登入失敗，請再試一次' }
  }
}
