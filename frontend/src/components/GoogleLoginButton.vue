<template>
  <button
    class="google-btn"
    type="button"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <svg class="google-mark" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"/>
      <path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"/>
      <path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 17.09 2 20.45 2 24c0 3.55.85 6.91 2.34 9.88l7.35-5.7z"/>
      <path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"/>
    </svg>
    {{ loading ? '登入中…' : label }}
  </button>
</template>

<script>
// 「用 Google 登入」按鈕。頁尾的登入入口與 /admin 的登入頁共用同一顆。
//
// 抽成元件的理由不只是那四行 SVG：登入流程、錯誤處理、以及「使用者自己
// 關掉彈出視窗不該跳錯誤」這個判斷，兩邊寫兩份遲早會分岔。版面差異由外層
// 決定，這裡只管一顆按鈕本身。
import { loginWithGoogle } from '../store/auth'
import { showToast } from '../store/toast'

export default {
  props: {
    // 外層有其他動作進行中時一併禁用
    disabled: { type: Boolean, default: false },
    label: { type: String, default: '用 Google 登入' }
  },
  emits: ['success'],
  data() {
    return { loading: false }
  },
  methods: {
    async handleClick() {
      this.loading = true
      try {
        const result = await loginWithGoogle()
        if (result.ok) {
          showToast('Logged in successfully', 'success')
          this.$emit('success')
        } else if (!result.cancelled) {
          // cancelled 是使用者自己關掉 Google 的視窗，不是錯誤
          showToast(result.message || 'Google 登入失敗', 'error')
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
/* Google 的品牌指南要求標誌維持四色，所以按鈕走深色、只讓標誌保持彩色，
   在這個站的深色背景上才不會突兀 */
.google-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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
</style>
