<template>
  <div class="cropper-overlay" @click.self="$emit('cancel')">
    <div class="cropper-box">
      <p class="cropper-title">裁切圖片</p>
      <p class="cropper-hint">拖曳移動、滾輪或滑桿縮放。框內範圍就是最後儲存的內容。</p>

      <div
        class="cropper-stage"
        ref="stage"
        @mousedown="startDrag"
        @touchstart.prevent="startDrag"
        @wheel.prevent="onWheel"
      >
        <img
          v-if="src"
          :src="src"
          class="cropper-img"
          :style="imgStyle"
          alt=""
          draggable="false"
          @load="onImageLoad"
        />
        <div class="cropper-mask"></div>
      </div>

      <div class="cropper-controls">
        <label class="cropper-zoom">
          縮放
          <input type="range" min="1" max="4" step="0.01" v-model.number="scale" />
        </label>
        <div class="cropper-ratio">
          <button
            v-for="r in RATIOS"
            :key="r.key"
            class="ratio-button"
            type="button"
            :class="{ active: ratio === r.value }"
            @click="setRatio(r.value)"
          >{{ r.label }}</button>
        </div>
      </div>

      <div class="cropper-actions">
        <button class="button" type="button" :disabled="working" @click="apply">
          {{ working ? '處理中…' : '套用' }}
        </button>
        <button class="button secondary" type="button" @click="$emit('cancel')">取消</button>
        <button class="button secondary" type="button" @click="$emit('skip')">不裁切直接使用</button>
      </div>
    </div>
  </div>
</template>

<script>
// 輸出邊長。與 imageCompress 的 MAX_EDGE 一致，裁切後不需要再縮一次。
const OUTPUT_EDGE = 1200

const RATIOS = [
  { key: 'square', label: '1:1', value: 1 },
  { key: 'landscape', label: '4:3', value: 4 / 3 },
  { key: 'portrait', label: '3:4', value: 3 / 4 }
]

export default {
  props: {
    // 原始檔案（未壓縮），裁切後才做壓縮
    file: { type: File, required: true }
  },
  emits: ['done', 'cancel', 'skip'],
  data() {
    return {
      RATIOS,
      src: '',
      scale: 1,
      ratio: 1,
      offsetX: 0,
      offsetY: 0,
      natural: { w: 0, h: 0 },
      stageSize: { w: 0, h: 0 },
      working: false,
      drag: null
    }
  },
  computed: {
    // 讓圖片在未縮放時剛好覆蓋整個裁切框
    baseScale() {
      if (!this.natural.w || !this.stageSize.w) return 1
      return Math.max(
        this.stageSize.w / this.natural.w,
        this.stageSize.h / this.natural.h
      )
    },
    imgStyle() {
      const s = this.baseScale * this.scale
      return {
        width: this.natural.w * s + 'px',
        height: this.natural.h * s + 'px',
        transform: `translate(calc(-50% + ${this.offsetX}px), calc(-50% + ${this.offsetY}px))`
      }
    }
  },
  created() {
    this.src = URL.createObjectURL(this.file)
  },
  beforeUnmount() {
    if (this.src) URL.revokeObjectURL(this.src)
    this.stopDrag()
  },
  methods: {
    onImageLoad(e) {
      this.natural = { w: e.target.naturalWidth, h: e.target.naturalHeight }
      this.measureStage()
    },
    measureStage() {
      const el = this.$refs.stage
      if (el) this.stageSize = { w: el.clientWidth, h: el.clientHeight }
    },
    setRatio(value) {
      this.ratio = value
      this.offsetX = 0
      this.offsetY = 0
      this.$nextTick(() => this.measureStage())
    },
    pointer(e) {
      const t = e.touches ? e.touches[0] : e
      return { x: t.clientX, y: t.clientY }
    },
    startDrag(e) {
      const p = this.pointer(e)
      this.drag = { x: p.x, y: p.y, ox: this.offsetX, oy: this.offsetY }
      window.addEventListener('mousemove', this.onDrag)
      window.addEventListener('mouseup', this.stopDrag)
      window.addEventListener('touchmove', this.onDrag, { passive: false })
      window.addEventListener('touchend', this.stopDrag)
    },
    onDrag(e) {
      if (!this.drag) return
      if (e.cancelable) e.preventDefault()
      const p = this.pointer(e)
      this.offsetX = this.drag.ox + (p.x - this.drag.x)
      this.offsetY = this.drag.oy + (p.y - this.drag.y)
      this.clampOffset()
    },
    stopDrag() {
      this.drag = null
      window.removeEventListener('mousemove', this.onDrag)
      window.removeEventListener('mouseup', this.stopDrag)
      window.removeEventListener('touchmove', this.onDrag)
      window.removeEventListener('touchend', this.stopDrag)
    },
    onWheel(e) {
      const next = this.scale * (e.deltaY < 0 ? 1.08 : 0.92)
      this.scale = Math.min(4, Math.max(1, next))
      this.clampOffset()
    },
    // 不讓圖片被拖出裁切框，否則會露出空白
    clampOffset() {
      const s = this.baseScale * this.scale
      const maxX = Math.max(0, (this.natural.w * s - this.stageSize.w) / 2)
      const maxY = Math.max(0, (this.natural.h * s - this.stageSize.h) / 2)
      this.offsetX = Math.min(maxX, Math.max(-maxX, this.offsetX))
      this.offsetY = Math.min(maxY, Math.max(-maxY, this.offsetY))
    },
    async apply() {
      this.working = true
      try {
        const outW = this.ratio >= 1 ? OUTPUT_EDGE : Math.round(OUTPUT_EDGE * this.ratio)
        const outH = this.ratio >= 1 ? Math.round(OUTPUT_EDGE / this.ratio) : OUTPUT_EDGE

        const canvas = document.createElement('canvas')
        canvas.width = outW
        canvas.height = outH
        const ctx = canvas.getContext('2d')

        // 畫面上的縮放比 → 換算回原圖座標
        const s = this.baseScale * this.scale
        const viewToSource = 1 / s
        const srcW = this.stageSize.w * viewToSource
        const srcH = this.stageSize.h * viewToSource
        const srcX = (this.natural.w - srcW) / 2 - this.offsetX * viewToSource
        const srcY = (this.natural.h - srcH) / 2 - this.offsetY * viewToSource

        const img = new Image()
        img.src = this.src
        if (!img.complete) await new Promise(res => { img.onload = res })
        ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, outW, outH)

        const blob = await new Promise((resolve, reject) => {
          canvas.toBlob(b => (b ? resolve(b) : reject(new Error('裁切失敗'))), 'image/jpeg', 0.85)
        })
        this.$emit('done', { blob, width: outW, height: outH, originalSize: this.file.size })
      } catch (e) {
        this.$emit('cancel')
      } finally {
        this.working = false
      }
    }
  },
  watch: {
    ratio() {
      this.$nextTick(() => { this.measureStage(); this.clampOffset() })
    }
  }
}
</script>

<style scoped>
.cropper-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.cropper-box {
  width: min(460px, 94vw);
  padding: 20px 22px 18px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 10px;
  background: rgb(24, 14, 34);
  text-align: left;
}

.cropper-title {
  font-size: 16px;
  font-weight: 600;
  color: #e4fbff;
  margin: 0 0 4px;
}

.cropper-hint {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.5);
  line-height: 1.6;
  margin: 0 0 12px;
}

.cropper-stage {
  position: relative;
  width: 100%;
  aspect-ratio: v-bind(ratio);
  overflow: hidden;
  border-radius: 8px;
  background: #000;
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.cropper-stage:active { cursor: grabbing; }

.cropper-img {
  position: absolute;
  top: 50%;
  left: 50%;
  max-width: none;
  border: none;
  border-radius: 0;
  pointer-events: none;
}

.cropper-mask {
  position: absolute;
  inset: 0;
  pointer-events: none;
  box-shadow: inset 0 0 0 1px rgba(228, 251, 255, 0.55);
  border-radius: 8px;
}

.cropper-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
  margin: 14px 0 4px;
}

.cropper-zoom {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(228, 251, 255, 0.6);
  flex: 1;
  min-width: 160px;
}

.cropper-zoom input { flex: 1; }

.cropper-ratio {
  display: flex;
  gap: 4px;
}

.ratio-button {
  padding: 3px 11px;
  font-size: 12px;
  font-family: inherit;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 999px;
  background: transparent;
  color: rgba(228, 251, 255, 0.55);
  cursor: pointer;
}

.ratio-button.active,
.ratio-button:hover {
  border-color: rgba(228, 251, 255, 0.55);
  color: #e4fbff;
  background: rgba(228, 251, 255, 0.08);
}

.cropper-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}
</style>
