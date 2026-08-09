<template>
  <!-- 前台左側導覽。沒有任何側邊頁面時整個不顯示，版面維持原樣 -->
  <aside v-if="items.length" class="site-nav" :class="{ open }">
    <button class="nav-toggle" type="button" @click="open = !open">
      <span class="nav-toggle-icon">{{ open ? '‹' : '›' }}</span>
      <span class="nav-toggle-label">選單</span>
    </button>

    <nav class="nav-items">
      <router-link
        v-for="item in items"
        :key="item.to"
        class="nav-link"
        :to="item.to"
        @click="open = false"
      >
        {{ item.label }}
        <span v-if="item.draft" class="nav-draft">草稿</span>
      </router-link>
    </nav>
  </aside>
</template>

<script>
import { pagesState, ensurePages, navItemsFor } from '../store/pages'

export default {
  data() {
    return { open: false, pagesState }
  },
  computed: {
    items() {
      // 讀一下 pages 讓 computed 依賴它，後台改完設定才會即時更新
      this.pagesState.pages.length
      return navItemsFor('sidebar')
    }
  },
  created() {
    ensurePages()
  }
}
</script>

<style scoped>
.site-nav {
  position: fixed;
  /* 偏上一點，不擋住畫面正中央的內容 */
  top: 30%;
  left: 0;
  z-index: 90;
  display: flex;
  align-items: center;
}

.nav-toggle {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 6px;
  border: 1px solid rgba(228, 251, 255, 0.16);
  border-left: none;
  border-radius: 0 8px 8px 0;
  background: rgba(20, 5, 35, 0.9);
  color: rgba(228, 251, 255, 0.6);
  font-family: inherit;
  font-size: 11px;
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
  order: 2;
}

.nav-toggle:hover {
  color: #e4fbff;
  background: rgba(60, 40, 75, 0.95);
}

.nav-toggle-icon {
  font-size: 15px;
  line-height: 1;
}

.nav-toggle-label {
  writing-mode: vertical-rl;
  letter-spacing: 0.14em;
}

.nav-items {
  order: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 0;
  overflow: hidden;
  padding: 8px 0;
  border: 1px solid transparent;
  border-left: none;
  background: rgba(20, 5, 35, 0.95);
  transition: width 0.22s ease, padding 0.22s ease;
}

.site-nav.open .nav-items {
  width: 176px;
  padding: 8px;
  border-color: rgba(228, 251, 255, 0.16);
  border-radius: 0 8px 8px 0;
}

.nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.7);
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.nav-link:hover,
.nav-link.router-link-active {
  background: rgba(228, 251, 255, 0.1);
  color: #e4fbff;
}

.nav-draft {
  font-size: 10px;
  color: #ffc46b;
  border: 1px solid rgba(255, 196, 107, 0.4);
  border-radius: 999px;
  padding: 1px 6px;
}

@media (max-width: 700px) {
  .site-nav { top: auto; bottom: 16px; }
  .site-nav.open .nav-items { width: 150px; }
  .nav-toggle { padding: 10px 5px; }
}
</style>
