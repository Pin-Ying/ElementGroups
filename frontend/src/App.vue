<template>
  <div>
    <!-- 後台設定的首頁背景圖（沒設定就維持原本的漸層底色） -->
    <div v-if="site.bg_image" class="site-bg" :style="{ backgroundImage: `url(${site.bg_image})` }"></div>

    <div class="element-header">
      <div class="header-inner">
        <router-link to="/" class="header-title">
          <p class="header-logo">{{ site.title }}</p>
          <p class="header-sub">{{ site.subtitle }}</p>
        </router-link>

        <!-- Admin area -->
        <div class="admin-area">
          <template v-if="authState.loggedIn">
            <span class="admin-badge">Admin Mode</span>
            <router-link class="button btn-sm" to="/admin">Admin Page</router-link>
            <button class="button btn-sm" @click="handleLogout">Logout</button>
          </template>
          <template v-else>
            <button v-if="!showLogin" class="button btn-sm" @click="showLogin = true">Admin Login</button>
            <form v-else class="login-form" @submit.prevent="handleLogin">
              <input class="input" type="email" v-model="email" placeholder="Email" required />
              <input class="input" type="password" v-model="password" placeholder="Password" required />
              <button class="button btn-sm" type="submit" :disabled="loggingIn">
                {{ loggingIn ? '...' : 'Login' }}
              </button>
              <button class="button btn-sm" type="button" @click="showLogin = false">✕</button>
            </form>
          </template>
        </div>
      </div>
    </div>

    <router-view />
    <SiteFooter />
    <ToastContainer />
  </div>
</template>

<script>
import { authState, login, logout, initAuth } from './store/auth'
import { showToast } from './store/toast'
import ToastContainer from './components/ToastContainer.vue'
import SiteFooter from './components/SiteFooter.vue'
import { siteSettingsState, ensureSiteSettings } from './store/siteSettings'
import api from './api'

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
  components: { ToastContainer, SiteFooter },
  data() {
    return {
      authState,
      site: siteSettingsState,
      showLogin: false,
      email: '',
      password: '',
      loggingIn: false
    }
  },
  created() {
    ensureSiteSettings()
    // 若後端 session 失效（401），立即更新前端狀態
    api.interceptors.response.use(
      res => res,
      err => {
        if (err.response?.status === 401) {
          authState.loggedIn = false
        }
        return Promise.reject(err)
      }
    )
    initAuth()
  },
  methods: {
    async handleLogin() {
      this.loggingIn = true
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          this.showLogin = false
          this.email = ''
          this.password = ''
          showToast('Logged in successfully', 'success')
        } else {
          showToast(result.message || 'Login failed', 'error')
        }
      } catch (e) {
        showToast(parseLoginError(e.response?.data?.message), 'error')
      } finally {
        this.loggingIn = false
      }
    },
    async handleLogout() {
      await logout()
    }
  }
}
</script>

<style scoped>
/* 背景圖鋪滿視窗、固定不隨捲動，上面壓一層暗色確保文字可讀 */
.site-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.35;
}

.site-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(rgba(3, 1, 10, 0.55), rgba(3, 1, 10, 0.8));
}

.header-inner {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-title {
  text-decoration: none;
  flex-shrink: 0;
}

.header-logo {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #e4fbff;
  margin: 0;
  line-height: 1.2;
}

.header-sub {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.45);
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.02em;
}

.admin-area {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.login-form {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.login-form .input {
  width: 150px;
  padding: 4px 8px;
  font-size: 13px;
  font-family: 'Space Grotesk', sans-serif;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(228, 251, 255, 0.35);
  border-radius: 5px;
  color: #fff;
  outline: none;
  transition: border-color 0.2s;
}

.login-form .input:focus {
  border-color: rgba(228, 251, 255, 0.6);
}

.btn-sm {
  padding: 4px 12px;
  font-size: 13px;
  border-radius: 5px;
}

.admin-badge {
  font-size: 11px;
  color: #6ee76e;
  border: 1px solid rgba(110, 231, 110, 0.5);
  border-radius: 4px;
  padding: 2px 8px;
  letter-spacing: 0.06em;
  font-weight: 600;
  background: rgba(110, 231, 110, 0.08);
}

@media (max-width: 600px) {
  .header-inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .admin-area { justify-content: flex-start; }
  .login-form { justify-content: flex-start; }
}
</style>
