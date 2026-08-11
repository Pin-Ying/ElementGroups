<template>
  <div class="page">
    <LoadingSpinner v-if="loading" />

    <template v-if="page">
      <p class="title">{{ page.title }}</p>
      <p v-if="page.subtitle" class="page-subtitle">{{ page.subtitle }}</p>
      <p v-if="!page.published" class="draft-badge">草稿 — 只有登入後看得到</p>
      <PageBlocks :blocks="pageBlocks" />
    </template>

    <div v-else-if="!loading" class="not-found">
      <p class="title">找不到這個頁面</p>
      <router-link to="/">回首頁</router-link>
    </div>
  </div>
</template>

<script>
import { getPage } from '../api'
import PageBlocks from '../components/PageBlocks.vue'
import { blocksFrom } from '../utils/blockTypes'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { siteSettingsState } from '../store/siteSettings'
import { setPageSeo, markdownExcerpt } from '../utils/seo'

export default {
  components: { PageBlocks, LoadingSpinner },
  props: { slug: { type: String, required: true } },
  data() {
    return { page: null, loading: false }
  },
  watch: {
    slug: { immediate: true, handler: 'load' }
  },
  computed: {
    // 舊頁面只有 Markdown 內容時即時轉成單一個「自訂 Markdown」區塊
    pageBlocks() {
      return blocksFrom(this.page)
    }
  },
  methods: {
    async load() {
      this.loading = true
      this.page = null
      try {
        const res = await getPage(this.slug)
        this.page = res.data
        // 分頁標題帶上頁面名稱，回首頁時 App 會再改回來
        setPageSeo({
          title: `${this.page.title}｜${siteSettingsState.title}`,
          // 後台沒寫 SEO 描述就退回內文開頭
          description: this.page.seo_description || markdownExcerpt(this.page.content),
          path: `/p/${this.slug}`,
          noindex: !this.page.published
        })
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

/* 與分子圖鑑、基本粒子頁的副標題一致 */
.page-subtitle {
  font-size: 14px;
  color: rgba(228, 251, 255, 0.55);
  margin: 6px 0 18px;
  white-space: pre-wrap;
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
