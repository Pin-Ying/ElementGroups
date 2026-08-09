<template>
  <div class="frame" :class="'frame--' + effectiveStyle" :style="frameVars">
    <div class="frame-inner">
      <slot />
    </div>
    <!-- 自訂框圖疊在最上層，四邊留白由圖檔本身決定 -->
    <img v-if="frameImage" class="frame-overlay" :src="frameImage" alt="" />

    <template v-if="!frameImage && effectiveStyle === 'classic'">
      <i class="corner corner--tl"></i><i class="corner corner--tr"></i>
      <i class="corner corner--bl"></i><i class="corner corner--br"></i>
    </template>
  </div>
</template>

<script>
// 內建外框款式。加新款式時在這裡補一筆，並在 style 區塊加對應的 .frame--{key}
export const FRAME_STYLES = [
  { key: 'classic', label: '經典圖鑑', desc: '雙線邊框加四角裝飾' },
  { key: 'plate', label: '標本框', desc: '厚實的立體外框' },
  { key: 'glow', label: '光暈', desc: '依元素顏色發光的細框' },
  { key: 'none', label: '無外框', desc: '只顯示圖片本身' }
]

export default {
  props: {
    // 元素的 CPK 顏色，讓外框跟著該元素變化
    color: { type: String, default: '64b8e8' },
    style: { type: String, default: 'classic' },
    frameImage: { type: String, default: '' }
  },
  computed: {
    effectiveStyle() {
      // 有自訂框圖時底層不再畫任何邊框，避免兩層框疊在一起
      if (this.frameImage) return 'none'
      return FRAME_STYLES.some(f => f.key === this.style) ? this.style : 'classic'
    },
    frameVars() {
      return { '--el-color': '#' + (this.color || '64b8e8') }
    }
  }
}
</script>

<style scoped>
.frame {
  --el-color: #64b8e8;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

.frame-inner {
  position: relative;
  overflow: hidden;
  border-radius: 4px;
}

.frame-inner :deep(img) {
  display: block;
  width: 100%;
  border: none;
  border-radius: 0;
  margin: 0;
}

.frame-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  border: none !important;
  border-radius: 0;
}

/* ── 經典圖鑑：雙線 + 四角 ── */
.frame--classic {
  padding: 7px;
  border: 2px solid var(--el-color);
  border-radius: 8px;
  background: color-mix(in srgb, var(--el-color) 10%, rgba(10, 4, 20, 0.6));
}

.frame--classic .frame-inner {
  border: 1px solid color-mix(in srgb, var(--el-color) 55%, transparent);
}

.corner {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid var(--el-color);
}

.corner--tl { top: -2px; left: -2px; border-right: none; border-bottom: none; border-radius: 8px 0 0 0; }
.corner--tr { top: -2px; right: -2px; border-left: none; border-bottom: none; border-radius: 0 8px 0 0; }
.corner--bl { bottom: -2px; left: -2px; border-right: none; border-top: none; border-radius: 0 0 0 8px; }
.corner--br { bottom: -2px; right: -2px; border-left: none; border-top: none; border-radius: 0 0 8px 0; }

/* ── 標本框：厚實立體 ── */
.frame--plate {
  padding: 12px;
  border-radius: 6px;
  background: linear-gradient(145deg, rgba(70, 55, 85, 0.95), rgba(30, 20, 40, 0.95));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    inset 0 -2px 4px rgba(0, 0, 0, 0.5),
    0 6px 18px rgba(0, 0, 0, 0.45);
}

.frame--plate .frame-inner {
  border: 1px solid rgba(0, 0, 0, 0.6);
  box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.55);
}

/* ── 光暈：細框 + 依元素顏色發光 ── */
.frame--glow {
  padding: 4px;
  border: 1px solid color-mix(in srgb, var(--el-color) 70%, transparent);
  border-radius: 10px;
  box-shadow:
    0 0 14px color-mix(in srgb, var(--el-color) 40%, transparent),
    0 0 40px color-mix(in srgb, var(--el-color) 18%, transparent);
}

/* ── 無外框 ── */
.frame--none {
  padding: 0;
}
</style>
