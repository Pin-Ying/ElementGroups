<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <div v-if="links.length" class="footer-social">
        <div class="social-list">
          <SocialLink
            v-for="(link, i) in links"
            :key="link.platform + i"
            :link="link"
            :shape="creatorLinksState.avatar_shape"
            size="sm"
          />
        </div>
      </div>

      <nav class="footer-nav">
        <template v-for="(item, i) in navItems" :key="item.to">
          <span v-if="i > 0" class="footer-sep">·</span>
          <router-link :to="item.to">
            {{ item.label }}
            <span v-if="item.draft" class="footer-draft">草稿</span>
          </router-link>
        </template>
        <span v-if="navItems.length" class="footer-sep">·</span>
        <a href="https://pubchem.ncbi.nlm.nih.gov/periodic-table/" target="_blank" rel="noopener noreferrer">資料來源 PubChem</a>
      </nav>

      <AdminLogin v-if="!authState.loggedIn" />
    </div>
  </footer>
</template>

<script>
import { creatorLinksState, ensureCreatorLinks } from '../store/creatorLinks'
import SocialLink from './SocialLink.vue'
import AdminLogin from './AdminLogin.vue'
import { authState } from '../store/auth'
import { pagesState, ensurePages, navItemsFor } from '../store/pages'

export default {
  components: { SocialLink, AdminLogin },
  data() {
    return { creatorLinksState, authState, pagesState }
  },
  computed: {
    links() {
      return this.creatorLinksState.links
    },
    navItems() {
      // 依賴 pagesState 才能在後台改完設定後即時更新
      return this.pagesState.loaded || true ? navItemsFor('footer') : []
    }
  },
  created() {
    ensureCreatorLinks()
    ensurePages()
  }
}
</script>

<style scoped>
.site-footer {
  margin-top: 48px;
  padding: 28px 20px 32px;
  border-top: 1px solid rgba(228, 251, 255, 0.08);
  background: rgba(3, 1, 12, 0.5);
}

.footer-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.footer-social {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.social-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.footer-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
}

.footer-nav a {
  color: rgba(228, 251, 255, 0.45);
  text-decoration: none;
  transition: color 0.15s;
}

.footer-nav a:hover {
  color: #e4fbff;
}

.footer-sep {
  color: rgba(228, 251, 255, 0.2);
}

.footer-draft {
  font-size: 10px;
  color: #ffc46b;
  border: 1px solid rgba(255, 196, 107, 0.4);
  border-radius: 999px;
  padding: 0 5px;
  margin-left: 4px;
}
</style>
