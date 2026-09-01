<template>
  <!-- 管理員登入入口。刻意低調：平時只是頁尾一個淡淡的小字，點了才展開表單 -->
  <div class="admin-login">
    <!-- 要點兩下才展開。單擊太容易誤觸——這顆點就在頁尾，滑鼠隨手一按
         就跳出登入框。

         用 click 自己算間隔，不用 @dblclick：iOS Safari 對非輸入元素的
         dblclick 本來就不可靠（實測 iPad 上完全打不開），touch-action
         只能擋掉縮放手勢搶事件，並不保證 Safari 會派發 dblclick。
         自己數兩次 click 在所有平台上行為一致。 -->
    <button
      v-if="!open"
      class="admin-trigger"
      type="button"
      title="管理員登入（點兩下）"
      @click="handleTrigger"
    >·</button>

    <div v-else class="login-panel">
      <p v-if="!methodsLoaded" class="login-hint">…</p>

      <template v-else>
        <!-- Google 可用時這裡就只給 Google，不論後端有沒有同時開著帳密登入。
             這個入口在每一頁的頁尾、面向的是一般訪客，要維持單純；帳密那條
             後路收在 /admin 的「使用其他方式登入」裡，那才是站長自己的頁面。

             Google 沒開時才退回帳密表單，否則頁尾會變成完全沒有登入方式。
             真正擋下帳密登入的是後端 auth.login()，這裡只是不要畫一組送出去
             必定被拒的輸入框。 -->
        <form v-if="!googleEnabled && passwordEnabled" class="login-form" @submit.prevent="handleLogin">
          <input class="input" type="email" v-model="email" aria-label="Email" required />
          <input class="input" type="password" v-model="password" aria-label="Password" required />
          <button class="button btn-sm" type="submit" :disabled="busy">
            {{ loggingIn ? '...' : 'Login' }}
          </button>
        </form>

        <p v-if="!passwordEnabled && !googleEnabled" class="login-hint">
          目前沒有可用的登入方式
        </p>
      </template>

      <div class="login-actions">
        <!-- 後端沒開 GOOGLE_LOGIN_ENABLED 就不會出現，也不會下載 Firebase SDK -->
        <GoogleLoginButton
          v-if="methodsLoaded && googleEnabled"
          :disabled="loggingIn"
          @success="close"
        />

        <!-- 關閉鍵獨立在這裡，不放進表單。帳密登入被關掉時表單整個不存在，
             擺在裡面會連帶消失，就沒有東西可以收起這個面板了 -->
        <button class="button btn-sm" type="button" @click="close">✕</button>
      </div>
    </div>
  </div>
</template>

<script>
import { login } from '../store/auth'
import { fetchGoogleLoginConfig } from '../utils/googleAuth'
import { showToast } from '../store/toast'
import GoogleLoginButton from './GoogleLoginButton.vue'

// 兩次點擊要多接近才算「點兩下」。系統預設的雙擊判定約 500ms，這裡取
// 稍寬的 450ms——太短在觸控裝置上很難達成，太長則會把「先點一下、想想、
// 再點一下」也算進去，失去防誤觸的意義
const DOUBLE_TAP_MS = 450

function parseLoginError(raw) {
  if (!raw) return 'Login failed'
  if (raw.includes('INVALID_LOGIN_CREDENTIALS') || raw.includes('EMAIL_NOT_FOUND') || raw.includes('INVALID_PASSWORD'))
    return 'Incorrect email or password'
  if (raw.includes('TOO_MANY_ATTEMPTS_TRY_LATER'))
    return 'Too many failed attempts, please try again later'
  if (raw.includes('USER_DISABLED'))
    return 'This account has been disabled'
  return 'Login failed, please try again'
}

export default {
  components: { GoogleLoginButton },
  data() {
    return {
      open: false, email: '', password: '', loggingIn: false,
      // 上一次點擊的時間戳，用來判斷有沒有構成「點兩下」
      lastTap: 0,
      // 查到結果之前兩個都不畫，避免表單先出現再被收掉的閃爍
      methodsLoaded: false, googleEnabled: false, passwordEnabled: true
    }
  },
  computed: {
    // Google 按鈕自己管它的 loading，這裡只要顧帳密送出中的狀態
    busy() {
      return this.loggingIn
    }
  },
  watch: {
    // 展開表單時才去問。這個元件在每一頁的頁尾都有，掛載就查的話
    // 等於每個訪客都多打一支 API，而會用到的只有站長
    open(isOpen) {
      if (isOpen) this.loadLoginMethods()
    }
  },
  methods: {
    // 兩次點擊間隔在 DOUBLE_TAP_MS 內才算數。第二次點完就把時間戳歸零，
    // 否則連點三下會被算成兩組，第三下又觸發一次
    handleTrigger() {
      const now = Date.now()
      if (now - this.lastTap < DOUBLE_TAP_MS) {
        this.lastTap = 0
        this.open = true
      } else {
        this.lastTap = now
      }
    },
    async loadLoginMethods() {
      const cfg = await fetchGoogleLoginConfig()
      this.googleEnabled = !!cfg.enabled
      // 舊版後端不會回這個欄位，那時候帳密登入本來就是開的，
      // 只有明確收到 false 才關掉
      this.passwordEnabled = cfg.passwordLogin !== false
      this.methodsLoaded = true
    },
    close() {
      this.open = false
      this.email = ''
      this.password = ''
    },
    async handleLogin() {
      this.loggingIn = true
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          this.close()
          showToast('Logged in successfully', 'success')
        } else {
          showToast(result.message || 'Login failed', 'error')
        }
      } catch (e) {
        showToast(parseLoginError(e.response?.data?.message), 'error')
      } finally {
        this.loggingIn = false
      }
    }
  }
}
</script>

<style scoped>
.admin-login {
  display: flex;
  justify-content: center;
}

.admin-trigger {
  border: none;
  background: none;
  color: rgba(228, 251, 255, 0.14);
  font-size: 18px;
  line-height: 1;
  padding: 4px 12px;
  cursor: pointer;
  transition: color 0.2s;
  /* 兩個作用：停用雙擊縮放（否則連點兩下會把畫面放大），以及去掉 iOS 為了
     等待雙擊而加的約 300ms click 延遲——那個延遲會讓兩次 click 的間隔被
     拉長，剛好落在雙擊判定之外。捲動與雙指縮放不受影響 */
  touch-action: manipulation;
  /* 連點時不要把那個「·」反白選起來 */
  user-select: none;
}

.admin-trigger:hover {
  color: rgba(228, 251, 255, 0.5);
}

.login-form {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.login-form .input {
  width: 150px;
  padding: 4px 8px;
  font-size: 13px;
  font-family: 'Space Grotesk', sans-serif;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(228, 251, 255, 0.35);
  border-radius: 5px;
  color: #fff;
  outline: none;
  transition: border-color 0.2s;
  margin: 0;
}

.login-form .input:focus {
  border-color: rgba(228, 251, 255, 0.6);
}

.btn-sm {
  padding: 4px 12px;
  font-size: 13px;
  border-radius: 5px;
}

.login-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.login-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}

.login-hint {
  margin: 0;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.5);
}

/* Google 按鈕的樣式在 GoogleLoginButton.vue 裡（scoped，不會被這裡影響） */

@media (max-width: 760px) {
  /* 避免 iPhone 聚焦自動放大 (issue #15) */
  .login-form .input { font-size: 16px; }
}
</style>
