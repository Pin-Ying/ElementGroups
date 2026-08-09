<template>
  <div class="md">
    <!-- html 由 utils/markdown.js 產生，所有使用者輸入都已 escape -->
    <div v-html="rendered.html"></div>

    <!-- 需要即時資料的區塊，用實際元件補上 -->
    <div v-if="rendered.blocks.includes('links')" class="md-links">
      <SocialLink
        v-for="(link, i) in creatorLinksState.links"
        :key="link.platform + i"
        :link="link"
        :shape="creatorLinksState.avatar_shape"
        size="md"
      />
    </div>
  </div>
</template>

<script>
import { renderMarkdown } from '../utils/markdown'
import { creatorLinksState, ensureCreatorLinks } from '../store/creatorLinks'
import SocialLink from './SocialLink.vue'

export default {
  components: { SocialLink },
  props: {
    source: { type: String, default: '' }
  },
  data() {
    return { creatorLinksState }
  },
  computed: {
    rendered() {
      return renderMarkdown(this.source)
    }
  },
  created() {
    if (this.rendered.blocks.includes('links')) ensureCreatorLinks()
  },
  watch: {
    source() {
      if (this.rendered.blocks.includes('links')) ensureCreatorLinks()
    }
  }
}
</script>

<style scoped>
.md {
  text-align: left;
  color: rgba(228, 251, 255, 0.82);
}

.md :deep(h2) {
  font-size: 17px;
  font-weight: 600;
  color: #e4fbff;
  margin: 26px 0 8px;
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.15);
}

.md :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  color: #e4fbff;
  margin: 18px 0 6px;
}

.md :deep(h4) {
  font-size: 14px;
  font-weight: 600;
  color: rgba(228, 251, 255, 0.9);
  margin: 14px 0 4px;
}

.md :deep(p) {
  font-size: 14px;
  line-height: 1.9;
  margin: 0 0 12px;
}

.md :deep(strong) { color: #e4fbff; }

.md :deep(a) {
  color: #7fd4e8;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.md :deep(a:hover) { color: #e4fbff; }

.md :deep(code) {
  font-size: 13px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(3, 1, 12, 0.6);
  border: 1px solid rgba(228, 251, 255, 0.12);
}

.md :deep(ul),
.md :deep(ol) {
  margin: 0 0 12px;
  padding-left: 22px;
}

.md :deep(li) {
  font-size: 14px;
  line-height: 1.85;
  margin-bottom: 3px;
}

.md :deep(hr) {
  border: none;
  border-top: 1px solid rgba(228, 251, 255, 0.12);
  margin: 22px 0;
}

/* ── 卡片格線區塊 ── */
.md :deep(.md-cards) {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
  margin: 0 0 16px;
}

.md :deep(.md-card) {
  padding: 14px 16px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(20, 5, 35, 0.45);
}

.md :deep(.md-card-head) {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.md :deep(.md-card-title) {
  font-size: 15px;
  font-weight: 600;
  color: #e4fbff;
}

.md :deep(.md-card-note) {
  font-size: 11px;
  color: rgba(228, 251, 255, 0.4);
}

.md :deep(.md-card-body) {
  font-size: 13px;
  line-height: 1.75;
  margin: 0;
}

/* ── 提示區塊 ── */
.md :deep(.md-note) {
  padding: 12px 16px;
  border-left: 3px solid rgba(157, 140, 255, 0.7);
  border-radius: 0 6px 6px 0;
  background: rgba(90, 70, 160, 0.14);
  font-size: 13px;
  line-height: 1.8;
  margin: 0 0 16px;
}

.md-links {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 0 0 16px;
}
</style>
