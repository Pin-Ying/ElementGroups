<template>
  <!-- 管理員登入入口。刻意低調：平時只是頁尾一個淡淡的小字，點了才展開表單 -->
  <div class="admin-login">
    <button
      v-if="!open"
      class="admin-trigger"
      type="button"
      title="管理員登入"
      @click="open = true"
    >·</button>

    <form v-else class="login-form" @submit.prevent="handleLogin">
      <input class="input" type="email" v-model="email" aria-label="Email" required />
      <input class="input" type="password" v-model="password" aria-label="Password" required />
      <button class="button btn-sm" type="submit" :disabled="loggingIn">
        {{ loggingIn ? '...' : 'Login' }}
      </button>
      <button class="button btn-sm" type="button" @click="close">✕</button>
    </form>
  </div>
</template>

<script>
import { login } from '../store/auth'
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
    return { open: false, email: '', password: '', loggingIn: false }
  },
  methods: {
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
</style>
