<template>
  <div class="guide">
    <p class="title">{{ page.title }}</p>
    <p v-if="fromDatabase && !published" class="draft-badge">草稿 — 只有登入後看得到</p>
    <PageBlocks :blocks="pageBlocks" />
  </div>
</template>

<script>
// 內容以資料庫的 `guide` 頁面優先，沒有才用內建的預設內容。
// 這樣既有的 /guide 網址不會壞，後台也還沒編輯過時畫面維持原樣。
import { getPage } from '../api'
import { builtinPage } from '../utils/builtinPages'
import { siteSettingsState } from '../store/siteSettings'
import { setPageSeo, markdownExcerpt } from '../utils/seo'
import PageBlocks from '../components/PageBlocks.vue'
import { blocksFrom } from '../utils/blockTypes'

export default {
  components: { PageBlocks },
  data() {
    return {
      page: builtinPage('guide'),
      fromDatabase: false,
      published: true
    }
  },
  computed: {
    // 舊頁面只有 Markdown 內容時即時轉成單一個「自訂 Markdown」區塊
    pageBlocks() {
      return blocksFrom(this.page)
    }
  },
  async created() {
    try {
      const res = await getPage('guide')
      if (res.data?.content) {
        this.page = { title: res.data.title, content: res.data.content }
        this.fromDatabase = true
        this.published = res.data.published
      }
    } catch {
      // 沒有自訂版本就沿用內建內容
    }
    setPageSeo({
      title: `${this.page.title}｜${siteSettingsState.title}`,
      // Markdown 的前幾行就是這頁在講什麼，拿來當描述比另外寫一句準
      description: markdownExcerpt(this.page.content),
      path: '/guide',
      noindex: this.fromDatabase && !this.published
    })
  }
}
</script>

<style scoped>
.guide {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 18px 40px;
}

.guide .title {
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
</style>
