<template>
  <div class="links-box">
    <p class="title">CONNECT</p>
    <div class="box">
      <p class="desc">追蹤創作者的社群帳號</p>

      <div v-if="links.length" class="link-list">
        <a
          v-for="(link, i) in links"
          :key="link.platform + i"
          class="link-button"
          :style="{ '--brand': platformInfo(link.platform).color }"
          :href="link.url"
          target="_blank"
          rel="noopener noreferrer"
        >{{ link.label }}</a>
      </div>
      <p v-else class="placeholder-text">尚未設定任何連結</p>
    </div>
  </div>
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
.links-box {
  text-align: center;
  padding: 20px;
  max-width: 720px;
  margin: 0 auto;
}

.box {
  background: rgba(20, 5, 35, 0.5);
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 8px;
  padding: 24px 28px;
  margin-bottom: 20px;
  text-align: left;
}

.desc {
  font-size: 13px;
  opacity: 0.55;
  margin: 2px 0 14px;
  line-height: 1.5;
}

.placeholder-text {
  font-size: 13px;
  opacity: 0.4;
  margin: 8px 0;
}

.link-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.link-button {
  --brand: #64b8e8;
  display: inline-flex;
  align-items: center;
  padding: 8px 22px;
  font-size: 14px;
  border-radius: 999px;
  text-decoration: none;
  color: rgba(228, 251, 255, 0.9);
  border: 1px solid color-mix(in srgb, var(--brand) 50%, transparent);
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  transition: background 0.18s, border-color 0.18s, color 0.18s, transform 0.18s;
}

.link-button:hover {
  color: #fff;
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 28%, transparent);
  transform: translateY(-1px);
}
</style>
