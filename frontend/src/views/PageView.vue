<template>
  <div class="page">
    <LoadingSpinner v-if="loading" />

    <template v-if="page">
      <p class="title">{{ page.title }}</p>
      <p v-if="!page.published" class="draft-badge">草稿 — 只有登入後看得到</p>
      <MarkdownContent :source="page.content" />
    </template>

    <div v-else-if="!loading" class="not-found">
      <p class="title">找不到這個頁面</p>
      <router-link to="/">回首頁</router-link>
    </div>
  </div>
</template>

<script>
import { getPage } from '../api'
import MarkdownContent from '../components/MarkdownContent.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { siteSettingsState } from '../store/siteSettings'

export default {
  components: { MarkdownContent, LoadingSpinner },
  props: { slug: { type: String, required: true } },
  data() {
    return { page: null, loading: false }
  },
  watch: {
    slug: { immediate: true, handler: 'load' }
  },
  methods: {
    async load() {
      this.loading = true
      this.page = null
      try {
        const res = await getPage(this.slug)
        this.page = res.data
        // 分頁標題帶上頁面名稱，回首頁時 App 會再改回來
        document.title = `${this.page.title}｜${siteSettingsState.title}`
      } catch {
        this.page = null
      } finally {
        this.loading = false
      }
    }
  },
  unmounted() {
    document.title = siteSettingsState.title
  }
}
</script>

<style scoped>
.page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 18px 40px;
}

.page .title {
  text-align: center;
}

.draft-badge {
  display: inline-block;
  font-size: 12px;
  color: #ffc46b;
  border: 1px solid rgba(255, 196, 107, 0.45);
  background: rgba(255, 196, 107, 0.1);
  border-radius: 999px;
  padding: 3px 12px;
  margin: 0 0 16px;
}

.not-found {
  text-align: center;
  padding: 40px 0;
}

.not-found a {
  color: rgba(228, 251, 255, 0.6);
}
</style>
