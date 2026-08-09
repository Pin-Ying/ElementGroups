<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <div v-if="links.length" class="footer-social">
        <div class="social-list">
          <a
            v-for="(link, i) in links"
            :key="link.platform + i"
            class="social-chip"
            :style="{ '--brand': platformInfo(link.platform).color }"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
          >{{ link.label }}</a>
        </div>
      </div>

      <nav class="footer-nav">
        <router-link to="/guide">元素說明書</router-link>
        <span class="footer-sep">·</span>
        <router-link to="/links">Connect</router-link>
        <span class="footer-sep">·</span>
        <a href="https://pubchem.ncbi.nlm.nih.gov/periodic-table/" target="_blank" rel="noopener noreferrer">資料來源 PubChem</a>
      </nav>
    </div>
  </footer>
</template>

<script>
import { creatorLinksState, ensureCreatorLinks } from '../store/creatorLinks'
import { platformInfo } from '../utils/socialPlatforms'

export default {
  data() {
    return { creatorLinksState }
  },
  computed: {
    links() {
      return this.creatorLinksState.links
    }
  },
  created() {
    ensureCreatorLinks()
  },
  methods: { platformInfo }
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

.social-chip {
  --brand: #64b8e8;
  display: inline-flex;
  align-items: center;
  padding: 5px 16px;
  font-size: 13px;
  border-radius: 999px;
  text-decoration: none;
  color: rgba(228, 251, 255, 0.85);
  border: 1px solid color-mix(in srgb, var(--brand) 45%, transparent);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  transition: background 0.18s, border-color 0.18s, color 0.18s, transform 0.18s;
}

.social-chip:hover {
  color: #fff;
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 26%, transparent);
  transform: translateY(-1px);
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
</style>
