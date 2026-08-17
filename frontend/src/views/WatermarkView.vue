<template>
  <div class="wm">
    <p class="title">{{ metaText('watermark', 'title') }}</p>
    <p v-if="metaText('watermark', 'subtitle')" class="subtitle">{{ metaText('watermark', 'subtitle') }}</p>

    <div
      class="drop"
      :class="{ 'is-over': dragging }"
      @dragover.prevent="dragging = true"
      @dragenter.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
    >
      <input ref="picker" class="picker" type="file" accept="image/*" @change="onPick">
      <button class="button" type="button" :disabled="busy" @click="$refs.picker.click()">
        {{ busy ? '處理中…' : '選擇圖片' }}
      </button>
      <p class="hint">{{ metaText('watermark', 'hint') }}</p>
    </div>

    <div v-if="ready" class="result">
      <figure>
        <img :src="originalUrl" :alt="metaText('watermark', 'original_label')">
        <figcaption>{{ metaText('watermark', 'original_label') }}</figcaption>
      </figure>
      <figure>
        <canvas ref="canvas"></canvas>
        <figcaption>{{ metaText('watermark', 'result_label') }}</figcaption>
      </figure>
    </div>

    <div v-if="ready" class="controls">
      <label class="label" for="wm-gain">放大倍率 {{ gain }}</label>
      <input id="wm-gain" type="range" :min="MIN_GAIN" :max="MAX_GAIN" v-model.number="gain" class="slider">
      <button class="button" type="button" @click="download">另存放大後的圖</button>
    </div>

    <p v-if="ready && scaled" class="hint">
      這張圖很大，已經先等比縮小再處理——紋路會變細一點，簽名照樣看得見。
    </p>
    <p v-if="ready" class="hint">{{ metaText('watermark', 'result_hint') }}</p>
  </div>
</template>

<script>
// 浮水印檢視（issue #25）。給一般讀者用：丟一張圖進來，把色度差放大，
// 如果是這個站的作品就會浮出簽名。
//
// 全部在瀏覽器裡算，圖片不會上傳（理由寫在 utils/watermarkReveal.js）。
// 這頁刻意只「顯示」不「判定」：自動判定必須拿簽名圖樣去比對所有位移與
// 縮放比例，任意比例縮放過的圖對不上模板就會回報「沒有」，那種會說謊的
// 是非題比沒有結論更糟。
import { ensurePageMeta, metaText } from '../store/pageMeta'
import { siteSettingsState } from '../store/siteSettings'
import { setPageSeo } from '../utils/seo'
import { showToast } from '../store/toast'
import {
  chromaResidual, residualToImageData, imageDataFrom,
  DEFAULT_GAIN, MIN_GAIN, MAX_GAIN
} from '../utils/watermarkReveal'

export default {
  data() {
    return {
      MIN_GAIN,
      MAX_GAIN,
      gain: DEFAULT_GAIN,
      busy: false,
      dragging: false,
      ready: false,
      scaled: false,
      originalUrl: '',
      residual: null,
      width: 0,
      height: 0
    }
  },
  methods: {
    metaText,
    onPick(event) {
      const file = event.target.files[0]
      event.target.value = ''
      if (file) this.load(file)
    },
    onDrop(event) {
      this.dragging = false
      const file = event.dataTransfer?.files?.[0]
      if (file) this.load(file)
    },
    onPaste(event) {
      const item = [...(event.clipboardData?.items || [])].find(i => i.type.startsWith('image/'))
      const file = item?.getAsFile()
      if (file) this.load(file)
    },
    async load(file) {
      if (!file.type.startsWith('image/')) {
        showToast('請選圖片檔', 'error')
        return
      }
      this.busy = true
      try {
        const { imageData, width, height, scaled } = await imageDataFrom(file)
        this.residual = chromaResidual(imageData)
        this.width = width
        this.height = height
        this.scaled = scaled
        if (this.originalUrl) URL.revokeObjectURL(this.originalUrl)
        this.originalUrl = URL.createObjectURL(file)
        this.ready = true
        await this.$nextTick()
        this.draw()
      } catch (e) {
        showToast(e.message || '這張圖讀不出來', 'error')
      } finally {
        this.busy = false
      }
    },
    draw() {
      const canvas = this.$refs.canvas
      if (!canvas || !this.residual) return
      canvas.width = this.width
      canvas.height = this.height
      canvas.getContext('2d').putImageData(
        residualToImageData(this.residual, this.width, this.height, this.gain), 0, 0)
    },
    download() {
      this.$refs.canvas?.toBlob(blob => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = 'watermark-check.png'
        link.click()
        URL.revokeObjectURL(url)
      }, 'image/png')
    }
  },
  watch: {
    gain() {
      this.draw()
    }
  },
  created() {
    ensurePageMeta().then(() => {
      const title = metaText('watermark', 'title')
      setPageSeo({
        title: `${title}｜${siteSettingsState.title}`,
        description: metaText('watermark', 'subtitle') || title,
        path: '/watermark'
      })
    })
  },
  mounted() {
    window.addEventListener('paste', this.onPaste)
  },
  unmounted() {
    window.removeEventListener('paste', this.onPaste)
    if (this.originalUrl) URL.revokeObjectURL(this.originalUrl)
  }
}
</script>

<style scoped>
.wm {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 16px 60px;
}

.subtitle {
  margin: -6px 0 28px;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.7;
  white-space: pre-line;
}

.drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 20px;
  border: 1px dashed rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  transition: border-color 0.15s, background 0.15s;
}
.drop.is-over {
  border-color: rgba(140, 200, 255, 0.6);
  background: rgba(140, 200, 255, 0.06);
}

.picker {
  display: none;
}

.hint {
  margin: 0;
  max-width: 640px;
  text-align: center;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.5);
  white-space: pre-line;
}

.result {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 28px;
}

.result figure {
  margin: 0;
}

.result img,
.result canvas {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: #000;
}

.result figcaption {
  margin-top: 8px;
  text-align: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 14px;
  margin: 22px 0 10px;
}

.label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.slider {
  width: 220px;
}

@media (max-width: 700px) {
  .result {
    grid-template-columns: 1fr;
  }
}
</style>
