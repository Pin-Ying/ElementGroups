<template>
  <div>
    <div class="element-header">
      <div class="header-inner">
        <router-link to="/" class="header-title">
          <p class="header-logo">Element Groups</p>
          <p class="header-sub">Explore the components of the world.</p>
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
              <button class="button btn-sm" type="button" @click="showLogin = false; errMsg = ''">✕</button>
              <span v-if="errMsg" class="err-msg">{{ errMsg }}</span>
            </form>
          </template>
        </div>
      </div>
    </div>

    <router-view />
  </div>
</template>

<script>
import { authState, login, logout, initAuth } from './store/auth'
import api from './api'

export default {
  data() {
    return {
      authState,
      showLogin: false,
      email: '',
      password: '',
      errMsg: '',
      loggingIn: false
    }
  },
  created() {
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
      this.errMsg = ''
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          this.showLogin = false
          this.email = ''
          this.password = ''
        } else {
          this.errMsg = result.message || 'Login failed'
        }
      } catch (e) {
        this.errMsg = e.response?.data?.message || 'Login failed'
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

.err-msg {
  font-size: 12px;
  color: #ff6b6b;
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
