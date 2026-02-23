<template>
  <div>
    <div class="element-header">
      <div class="header-inner">
        <router-link to="/" class="header-title">
          <p class="title is-2">Element Groups</p>
          <p class="title is-4">Explore the components of the world.</p>
        </router-link>

        <!-- Admin area -->
        <div class="admin-area" style="text-align:left">
          <template v-if="authState.loggedIn">
            <span class="admin-badge">Admin Mode</span>
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
import { authState, login, logout } from './store/auth'

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
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.header-title {
  text-align: left;
}

.admin-area {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.login-form {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.login-form .input {
  width: 160px;
  padding: 4px 8px;
  font-size: 13px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(228, 251, 255, 0.4);
  border-radius: 4px;
  color: #fff;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 13px;
  border-radius: 4px;
}

.admin-badge {
  font-size: 12px;
  color: #6ee76e;
  border: 1px solid #6ee76e;
  border-radius: 4px;
  padding: 2px 8px;
  letter-spacing: 0.05em;
}

.err-msg {
  font-size: 12px;
  color: #ff6b6b;
}
</style>
