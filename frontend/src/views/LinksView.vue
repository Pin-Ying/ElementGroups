<template>
  <div class="links-box">
    <p class="title">{{ page.title }}</p>
    <div class="box">
      <PageBlocks :blocks="pageBlocks" />
    </div>
  </div>
</template>

<script>
// 同 GuideView：資料庫的 `links` 頁面優先，沒有才用內建內容。
// 內建內容裡的 :::links 區塊會渲染成目前設定的社群連結。
import { getPage } from '../api'
import { builtinPage } from '../utils/builtinPages'
import { creatorLinksState, ensureCreatorLinks } from '../store/creatorLinks'
import { siteSettingsState } from '../store/siteSettings'
import { setPageSeo, markdownExcerpt } from '../utils/seo'
import PageBlocks from '../components/PageBlocks.vue'
import { blocksFrom, blocksToText } from '../utils/blockTypes'

export default {
  components: { PageBlocks },
  data() {
    return {
      state: creatorLinksState,
      page: builtinPage('links'),
      fromDatabase: false
    }
  },
  computed: {
    // 舊頁面只有 Markdown 內容時即時轉成單一個「自訂 Markdown」區塊
    pageBlocks() {
      return blocksFrom(this.page)
    }
  },
  async created() {
    ensureCreatorLinks()
    try {
      const res = await getPage('links')
      if (res.data?.content) {
        this.page = { title: res.data.title, content: res.data.content }
        this.fromDatabase = true
      }
    } catch {
      // 沒有自訂版本就沿用內建內容
    }
    setPageSeo({
      title: `${this.page.title}｜${siteSettingsState.title}`,
      description: markdownExcerpt(blocksToText(this.pageBlocks)) || creatorLinksState.description,
      path: '/links'
    })
  }
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
</style>
