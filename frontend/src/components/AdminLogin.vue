<template>
  <!-- 管理員登入入口。刻意低調：平時只是頁尾一個淡淡的小字，點了才展開表單 -->
  <div class="admin-login">
    <!-- 要點兩下才展開。單擊太容易誤觸——這顆點就在頁尾，滑鼠隨手一按
         就跳出登入框。touch-action: manipulation 讓手機的連點兩下不會被
         瀏覽器解讀成放大手勢 -->
    <button
      v-if="!open"
      class="admin-trigger"
      type="button"
      title="管理員登入（點兩下）"
      @dblclick="open = true"
    >·</button>

    <div v-else class="login-panel">
      <p v-if="!methodsLoaded" class="login-hint">…</p>

      <template v-else>
        <!-- 後端關掉帳密登入時連表單都不畫。真正擋下來的是 auth.login()，
             這裡只是不要畫一組送出去必定被拒的輸入框 -->
        <form v-if="passwordEnabled" class="login-form" @submit.prevent="handleLogin">
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
        <button
          v-if="methodsLoaded && googleEnabled"
          class="google-btn"
          type="button"
          :disabled="busy"
          @click="handleGoogleLogin"
        >
          <svg class="google-mark" viewBox="0 0 48 48" aria-hidden="true">
            <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"/>
            <path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"/>
            <path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 17.09 2 20.45 2 24c0 3.55.85 6.91 2.34 9.88l7.35-5.7z"/>
            <path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"/>
          </svg>
          {{ googleLoading ? '登入中…' : '用 Google 登入' }}
        </button>

        <!-- 關閉鍵獨立在這裡，不放進表單。帳密登入被關掉時表單整個不存在，
             擺在裡面會連帶消失，就沒有東西可以收起這個面板了 -->
        <button class="button btn-sm" type="button" @click="close">✕</button>
      </div>
    </div>
  </div>
</template>

<script>
import { login, loginWithGoogle } from '../store/auth'
import { fetchGoogleLoginConfig } from '../utils/googleAuth'
import { showToast } from '../store/toast'

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
  data() {
    return {
      open: false, email: '', password: '',
      loggingIn: false, googleLoading: false,
      // 查到結果之前兩個都不畫，避免表單先出現再被收掉的閃爍
      methodsLoaded: false, googleEnabled: false, passwordEnabled: true
    }
  },
  computed: {
    // 兩種登入共用一組禁用狀態，避免使用者在等待時按下另一個
    busy() {
      return this.loggingIn || this.googleLoading
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
    async loadLoginMethods() {
      const cfg = await fetchGoogleLoginConfig()
      this.googleEnabled = !!cfg.enabled
      // 舊版後端不會回這個欄位，那時候帳密登入本來就是開的，
      // 只有明確收到 false 才關掉
      this.passwordEnabled = cfg.passwordLogin !== false
      this.methodsLoaded = true
    },
    async handleGoogleLogin() {
      this.googleLoading = true
      try {
        const result = await loginWithGoogle()
        if (result.ok) {
          this.close()
          showToast('Logged in successfully', 'success')
        } else if (!result.cancelled) {
          // cancelled 是使用者自己關掉 Google 的視窗，不是錯誤
          showToast(result.message || 'Google 登入失敗', 'error')
        }
      } finally {
        this.googleLoading = false
      }
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
  /* 手機上連點兩下預設是放大手勢，會把 dblclick 吃掉。
     manipulation 停用雙擊縮放，但保留捲動與雙指縮放 */
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

/* Google 的品牌指南要求 logo 維持原本的四色，所以按鈕本身走深色、
   只讓標誌保持彩色，這樣在這個站的深色背景上也不會突兀 */
.google-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 14px;
  font-size: 13px;
  font-family: 'Space Grotesk', sans-serif;
  color: rgba(228, 251, 255, 0.85);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(228, 251, 255, 0.35);
  border-radius: 5px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.google-btn:hover:not(:disabled) {
  border-color: rgba(228, 251, 255, 0.6);
  background: rgba(255, 255, 255, 0.13);
}

.google-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.google-mark {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

@media (max-width: 760px) {
  /* 避免 iPhone 聚焦自動放大 (issue #15) */
  .login-form .input { font-size: 16px; }
}
</style>
