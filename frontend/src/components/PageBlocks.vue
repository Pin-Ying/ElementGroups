<template>
  <div class="page-blocks">
    <template v-for="(block, i) in blocks" :key="i">
      <!-- 標題 -->
      <h2 v-if="block.type === 'heading' && block.data.level !== 'h3'" class="pb-h2">
        {{ block.data.text }}
      </h2>
      <h3 v-else-if="block.type === 'heading'" class="pb-h3">
        {{ block.data.text }}
      </h3>

      <!-- 圖片 -->
      <figure v-else-if="block.type === 'image' && block.data.image" class="pb-figure">
        <img :src="block.data.image" :alt="block.data.caption || ''" />
        <figcaption v-if="block.data.caption">{{ block.data.caption }}</figcaption>
      </figure>

      <!-- 圖片集 -->
      <div v-else-if="block.type === 'gallery'" class="pb-gallery">
        <figure v-for="(img, j) in block.data.images || []" :key="j" class="pb-gallery-item">
          <img v-if="img.image" :src="img.image" :alt="img.caption || ''" />
          <figcaption v-if="img.caption">{{ img.caption }}</figcaption>
        </figure>
      </div>

      <hr v-else-if="block.type === 'divider'" class="pb-divider" />

      <!-- 其餘都轉成 Markdown 走既有的渲染器，樣式自然與站上其他地方一致 -->
      <MarkdownContent v-else :source="toMarkdown(block)" />
    </template>
  </div>
</template>

<script>
// 頁面區塊的前台渲染（issue #20）。
//
// 只有圖片、圖片集、標題、分隔線需要真的 DOM；其餘一律轉成 Markdown 交給
// 既有的 renderMarkdown 處理。utils/markdown.js 本來就支援 :::cards、
// :::note、:::links，重寫一套只會多一份要維護的樣式。
import MarkdownContent from './MarkdownContent.vue'

export default {
  components: { MarkdownContent },
  props: {
    blocks: { type: Array, default: () => [] }
  },
  methods: {
    toMarkdown(block) {
      const d = block.data || {}

      if (block.type === 'text' || block.type === 'markdown') return d.body || ''
      if (block.type === 'note') return `:::note\n${d.body || ''}\n:::`
      if (block.type === 'links') return ':::links\n:::'

      if (block.type === 'cards') {
        const items = (d.items || [])
          .filter(it => (it.title || '').trim() || (it.body || '').trim())
          .map(it => {
            // 標題與附註用 | 分隔，是 :::cards 既有的格式
            const heading = it.note ? `${it.title} | ${it.note}` : it.title
            return `### ${heading}\n${it.body || ''}`
          })
        return items.length ? `:::cards\n${items.join('\n\n')}\n:::` : ''
      }

      return ''
    }
  }
}
</script>

<style scoped>
.page-blocks > * {
  margin-bottom: 18px;
}

.pb-h2 {
  font-size: 21px;
  font-weight: bold;
  color: #e4fbff;
  margin: 28px 0 10px;
}

.pb-h3 {
  font-size: 17px;
  font-weight: bold;
  color: rgba(228, 251, 255, 0.9);
  margin: 22px 0 8px;
}

.pb-figure {
  margin: 0 0 18px;
  text-align: center;
}

.pb-figure img {
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(228, 251, 255, 0.12);
}

.pb-figure figcaption,
.pb-gallery-item figcaption {
  margin-top: 6px;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.6);
}

.pb-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.pb-gallery-item {
  margin: 0;
  text-align: center;
}

.pb-gallery-item img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(228, 251, 255, 0.12);
}

.pb-divider {
  border: none;
  border-top: 1px solid rgba(228, 251, 255, 0.14);
  margin: 26px 0;
}
</style>
