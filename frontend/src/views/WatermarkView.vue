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

    <!-- 自己印一個：簽名是訪客自己打的，和站長的浮水印無關。
         一進頁面就顯示，否則不選圖就看不出這頁還能印，會以為是另一個頁面 -->
    <div class="sign">
      <label class="label" for="wm-text">{{ metaText('watermark', 'sign_label') }}</label>
      <div class="sign-row">
        <input
          id="wm-text"
          class="input"
          type="text"
          :maxlength="MAX_TEXT"
          :placeholder="metaText('watermark', 'sign_placeholder')"
          v-model="signature"
          @keyup.enter="applySignature"
        >
        <button
          class="button"
          type="button"
          :disabled="busy || !ready || !signature.trim()"
          :title="ready ? '' : '先選一張圖'"
          @click="applySignature"
        >{{ busy ? '處理中…' : '印上去' }}</button>
        <button
          v-if="markedUrl"
          class="button"
          type="button"
          @click="download(markedUrl, 'watermarked', markedExt)"
        >下載這張</button>
      </div>
      <p class="hint">{{ metaText('watermark', 'sign_hint') }}</p>
    </div>

    <div v-if="ready" class="result" :class="{ 'is-three': !!markedUrl }">
      <figure>
        <img :src="originalUrl" :alt="metaText('watermark', 'original_label')">
        <figcaption>{{ metaText('watermark', 'original_label') }}</figcaption>
      </figure>
      <figure v-if="markedUrl">
        <img :src="markedUrl" :alt="metaText('watermark', 'marked_label')">
        <figcaption>{{ metaText('watermark', 'marked_label') }}</figcaption>
      </figure>
      <figure>
        <canvas ref="canvas"></canvas>
        <figcaption>{{ metaText('watermark', 'result_label') }}</figcaption>
      </figure>
    </div>

    <div v-if="ready" class="controls">
      <label class="label" for="wm-gain">{{ metaText('watermark', 'gain_label') }} {{ gain }}</label>
      <input id="wm-gain" type="range" :min="MIN_GAIN" :max="MAX_GAIN" v-model.number="gain" class="slider">
      <button class="button" type="button" @click="downloadCanvas">另存這張</button>
    </div>

    <p v-if="ready && scaled" class="hint">
      這張圖很大，已經先等比縮小再處理——紋路會變細一點，簽名照樣看得見。
    </p>
    <p v-if="ready" class="hint">{{ metaText('watermark', 'result_hint') }}</p>
  </div>
</template>

<script>
// 浮水印檢視（issue #25）。給一般讀者用的小工具，兩件事：
//
// 1. 丟一張圖進來，把色度差放大——如果是這個站的作品就會浮出簽名。
// 2. 自己打一個簽名印在自己的圖上，看看「藏得住又讀得出來」是怎麼回事。
//
// 全部在瀏覽器裡算，圖片和簽名都不會上傳（理由寫在 utils/watermark.js）。
// 這頁刻意只「顯示」不「判定」：自動判定必須拿簽名圖樣去比對所有位移與縮放
// 比例，任意比例縮放過的圖對不上模板就會回報「沒有」，那種會說謊的是非題比
// 沒有結論更糟。
import { ensurePageMeta, metaText } from '../store/pageMeta'
import { siteSettingsState } from '../store/siteSettings'
import { setPageSeo } from '../utils/seo'
import { showToast } from '../store/toast'
import {
  chromaResidual, residualToImageData, imageDataFrom, markImage,
  DEFAULT_GAIN, MIN_GAIN, MAX_GAIN, MAX_TEXT
} from '../utils/watermark'

export default {
  data() {
    return {
      MIN_GAIN,
      MAX_GAIN,
      MAX_TEXT,
      gain: DEFAULT_GAIN,
      signature: '',
      busy: false,
      dragging: false,
      ready: false,
      scaled: false,
      originalUrl: '',
      markedUrl: '',
      markedExt: 'jpg',
      sourceData: null,
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
        this.sourceData = imageData
        this.width = width
        this.height = height
        this.scaled = scaled
        this.replaceUrl('originalUrl', URL.createObjectURL(file))
        this.replaceUrl('markedUrl', '')  // 換了圖，上一次印的就不算數了
        await this.show(imageData)
      } catch (e) {
        showToast(e.message || '這張圖讀不出來', 'error')
      } finally {
        this.busy = false
      }
    },
    async applySignature() {
      if (this.busy || !this.signature.trim() || !this.sourceData) return
      this.busy = true
      try {
        const blob = await markImage(this.sourceData, this.signature)
        // 從編碼後的檔案讀回來，而不是直接用記憶體裡那份：真正會被傳出去的是
        // 壓縮過的版本，右邊那張要照實反映壓縮吃掉多少訊號
        const { imageData } = await imageDataFrom(blob)
        this.markedExt = blob.type === 'image/png' ? 'png' : 'jpg'
        this.replaceUrl('markedUrl', URL.createObjectURL(blob))
        await this.show(imageData)
      } catch (e) {
        showToast(e.message || '印不上去', 'error')
      } finally {
        this.busy = false
      }
    },
    async show(imageData) {
      this.residual = chromaResidual(imageData)
      this.ready = true
      await this.$nextTick()
      this.draw()
    },
    draw() {
      const canvas = this.$refs.canvas
      if (!canvas || !this.residual) return
      canvas.width = this.width
      canvas.height = this.height
      canvas.getContext('2d').putImageData(
        residualToImageData(this.residual, this.width, this.height, this.gain), 0, 0)
    },
    replaceUrl(key, url) {
      if (this[key]) URL.revokeObjectURL(this[key])
      this[key] = url
    },
    download(url, name, ext) {
      const link = document.createElement('a')
      link.href = url
      link.download = `${name}.${ext}`
      link.click()
    },
    downloadCanvas() {
      this.$refs.canvas?.toBlob(blob => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        this.download(url, 'watermark-check', 'png')
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
    this.replaceUrl('originalUrl', '')
    this.replaceUrl('markedUrl', '')
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
  margin: 0 auto;
  max-width: 640px;
  text-align: center;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.5);
  white-space: pre-line;
}

.sign {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-top: 22px;
}

.sign-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.sign-row .input {
  width: 220px;
}

.result {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 24px;
}
.result.is-three {
  grid-template-columns: repeat(3, 1fr);
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
  .result,
  .result.is-three {
    grid-template-columns: 1fr;
  }
}
</style>
