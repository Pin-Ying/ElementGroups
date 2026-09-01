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
        <!-- 登入入口已移到頁尾，這裡只在登入後顯示 -->
        <div v-if="authState.loggedIn" class="admin-area">
          <span class="admin-badge">Admin Mode</span>
          <router-link class="button btn-sm" to="/admin">Admin Page</router-link>
          <button class="button btn-sm" @click="handleLogout">Logout</button>
        </div>
      </div>
    </div>

    <SiteNav />

    <router-view />
    <!-- 後台用 meta.hideFooter 關掉頁尾，見 router/index.js -->
    <SiteFooter v-if="!$route.meta.hideFooter" />
    <ToastContainer />
  </div>
</template>

<script>
import { authState, logout, initAuth } from './store/auth'
import { showToast } from './store/toast'
import ToastContainer from './components/ToastContainer.vue'
import SiteFooter from './components/SiteFooter.vue'
import SiteNav from './components/SiteNav.vue'
import { siteSettingsState, ensureSiteSettings } from './store/siteSettings'
import api from './api'

export default {
  components: { ToastContainer, SiteFooter, SiteNav },
  data() {
    return {
      authState,
      site: siteSettingsState
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
  /* 0.45 只有 4.2:1，差一點過不了 4.5 */
  color: rgba(228, 251, 255, 0.6);
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
}
</style>
