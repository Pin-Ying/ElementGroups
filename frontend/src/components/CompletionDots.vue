<template>
  <span v-if="hasAny" class="completion-dots" :title="titleText">
    <i v-if="state.image" class="dot dot--image"></i>
    <i v-if="state.story" class="dot dot--story"></i>
  </span>
</template>

<script>
export default {
  props: {
    // { story: bool, image: bool }；沒有資料時傳 undefined 即可
    state: { type: Object, default: () => ({}) }
  },
  computed: {
    hasAny() {
      return !!(this.state && (this.state.story || this.state.image))
    },
    titleText() {
      const parts = []
      if (this.state.image) parts.push('已上傳圖片')
      if (this.state.story) parts.push('已寫故事')
      return parts.join('、')
    }
  }
}
</script>

<style scoped>
.completion-dots {
  position: absolute;
  top: 3px;
  right: 3px;
  display: flex;
  gap: 2px;
  pointer-events: none;
}

.dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  display: block;
}

.dot--image {
  background: #45d0e0;
  box-shadow: 0 0 4px rgba(69, 208, 224, 0.9);
}

.dot--story {
  background: #6ee76e;
  box-shadow: 0 0 4px rgba(110, 231, 110, 0.9);
}
</style>
