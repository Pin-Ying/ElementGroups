<template>
  <div class="links-box">
    <p class="title">{{ page.title }}</p>
    <div class="box">
      <MarkdownContent :source="page.content" />
    </div>
  </div>
</template>

<script>
// 同 GuideView：資料庫的 `links` 頁面優先，沒有才用內建內容。
// 內建內容裡的 :::links 區塊會渲染成目前設定的社群連結。
import { getPage } from '../api'
import { builtinPage } from '../utils/builtinPages'
import { creatorLinksState, ensureCreatorLinks } from '../store/creatorLinks'
import MarkdownContent from '../components/MarkdownContent.vue'

export default {
  components: { MarkdownContent },
  data() {
    return {
      state: creatorLinksState,
      page: builtinPage('links'),
      fromDatabase: false
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
