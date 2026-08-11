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
      <figure v-else-if="block.type === 'image' && srcOf(block.data)" class="pb-figure">
        <img :src="srcOf(block.data)" :alt="block.data.caption || ''" />
        <figcaption v-if="block.data.caption">{{ block.data.caption }}</figcaption>
      </figure>

      <!-- 圖片集 -->
      <div v-else-if="block.type === 'gallery'" class="pb-gallery">
        <figure v-for="(img, j) in block.data.images || []" :key="j" class="pb-gallery-item">
          <img v-if="srcOf(img)" :src="srcOf(img)" :alt="img.caption || ''" />
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
import { blockToMarkdown } from '../utils/blockTypes'

export default {
  components: { MarkdownContent },
  props: {
    blocks: { type: Array, default: () => [] },
    // 後台預覽用：前台拿到的 blocks 已由後端把參照解析成圖片，不需要這個
    libraries: { type: Array, default: () => [] }
  },
  methods: {
    // 圖庫參照優先；沒有參照就是自己上傳的圖
    srcOf(data) {
      const ref = data?.image_ref
      if (ref?.library && ref.image) {
        const lib = this.libraries.find(l => l.id === ref.library)
        const img = lib?.images.find(i => i.id === ref.image)
        if (img) return img.img_data
      }
      return data?.image || ''
    },
    toMarkdown(block) {
      return blockToMarkdown(block)
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
