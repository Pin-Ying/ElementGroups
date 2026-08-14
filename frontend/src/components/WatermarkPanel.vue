<template>
  <div class="box">
    <AdminBar title="隱形浮水印">
      <button class="button" type="button" :disabled="saving" @click="save">
        {{ saving ? 'Saving…' : '儲存設定' }}
      </button>
    </AdminBar>

    <p class="desc">
      把簽名藏進圖片的色度裡，亮度完全不動——正常觀看看不出來，把色度差放大就會浮出來。
      開啟之後，<strong>後台新上傳的圖片</strong>會自動套用；已經存在的舊圖不會自動處理
      （要補的話在下面的「檢驗」確認，或請工程師跑一次回填腳本）。
    </p>

    <div class="field">
      <label class="checkbox">
        <input type="checkbox" v-model="form.enabled">
        <span>開啟浮水印</span>
      </label>
    </div>

    <div class="field">
      <label class="label">浮水印長相</label>
      <div class="mode-tabs">
        <button
          v-for="m in MODES" :key="m.key" type="button"
          class="button is-small" :class="{ 'is-active': form.mode === m.key }"
          @click="form.mode = m.key"
        >{{ m.label }}</button>
      </div>
    </div>

    <div v-if="form.mode === 'text'" class="field">
      <label class="label">簽名文字</label>
      <input class="input" type="text" maxlength="16" placeholder="例如 EG" v-model="form.text">
      <p class="hint">
        英數字最多 16 個字。文字會被畫成粗塊狀圖樣重複鋪滿整張圖，越短越清楚，建議 2〜4 個字。
        <br>中文要看伺服器有沒有中文字型，沒有的話儲存時會直接告訴你，改用下面的「上傳圖片」即可。
      </p>
    </div>

    <div v-else class="field">
      <label class="label">圖樣圖片</label>
      <input class="input" type="file" accept="image/*" @change="onPatternChange">
      <p class="hint">
        建議用去背 PNG 的簡單標誌（logo、簽名）。圖樣會被縮成小方格再放大成粗塊，
        細線條和漸層留不住，越簡單越好。
      </p>
      <img v-if="form.pattern" :src="form.pattern" class="pattern-preview" alt="圖樣">
    </div>

    <div class="field">
      <label class="label">強度：{{ form.strength }}</label>
      <input type="range" min="1" max="6" v-model.number="form.strength" class="slider">
      <p class="hint">
        色度的位移量。3 是預設值：實測「縮一半再壓 quality 0.6」之後還驗得出來，
        而 4 以上在大片平塗的淺色底上有機會被看出紋路。改完建議用下面的「試套用」看一眼。
      </p>
    </div>

    <hr>

    <!-- 試套用：調參數用 -->
    <div class="field">
      <label class="label">試套用（不會存檔）</label>
      <input class="input" type="file" accept="image/*" @change="onPreviewChange">
      <p class="hint">選一張圖，看看目前的設定套上去長什麼樣、還原之後讀不讀得出簽名。</p>
    </div>

    <div v-if="preview.marked" class="compare">
      <figure>
        <img :src="preview.original" alt="原圖">
        <figcaption>原圖</figcaption>
      </figure>
      <figure>
        <img :src="preview.marked" alt="套用後">
        <figcaption>套用後（出貨的就是這張）</figcaption>
      </figure>
      <figure>
        <img :src="preview.recovered" alt="還原">
        <figcaption>還原（把色度差放大）</figcaption>
      </figure>
    </div>
    <p v-if="preview.marked" class="hint">
      偵測分數 {{ preview.amplitude }}（門檻 {{ preview.threshold }}）。分數越高越禁得起壓縮與縮圖。
    </p>

    <hr>

    <!-- 檢驗：拿到可疑圖片時用 -->
    <div class="field">
      <label class="label">檢驗可疑圖片</label>
      <input class="input" type="file" accept="image/*" @change="onInspectChange">
      <p class="hint">
        丟一張在別處看到的圖進來，看看是不是從這裡拿走的。比對用的是<strong>目前的設定</strong>——
        換過簽名之後，舊圖要用當初那個簽名才驗得出來。
      </p>
    </div>

    <div v-if="check.done" class="check-result" :class="check.found ? 'is-found' : 'is-clean'">
      <p class="check-title">{{ check.found ? '✓ 驗到本站的浮水印' : '✗ 沒有驗到' }}</p>
      <p class="hint">
        分數 {{ check.amplitude }}（門檻 {{ check.threshold }}，比對尺寸 ×{{ check.scale }}）。
        <template v-if="!check.found">
          被裁切、縮很小或反覆轉存過的圖可能低於門檻，右邊的還原圖若仍看得出簽名，一樣算數。
        </template>
      </p>
      <img v-if="check.recovered" :src="check.recovered" class="recovered" alt="還原">
    </div>

    <p v-if="msg" class="msg" :class="msgType">{{ msg }}</p>
  </div>
</template>

<script>
// 隱形浮水印的後台面板（issue #25）。
//
// 拆成獨立元件而不是塞進 AdminView：那支已經 4860 行、十個分頁擠在一起
// （issue #29），沒必要再往裡面堆。這裡自己打自己的四支端點。
import AdminBar from './AdminBar.vue'
import { getWatermarkSettings, saveWatermarkSettings, previewWatermark, inspectWatermark } from '../api'
import { showToast } from '../store/toast'
import { compressImage } from '../utils/imageCompress'

const MODES = [
  { key: 'text', label: '輸入文字' },
  { key: 'image', label: '上傳圖片' }
]

function readAsDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

export default {
  components: { AdminBar },
  data() {
    return {
      MODES,
      form: { enabled: false, mode: 'text', text: '', pattern: '', strength: 3 },
      preview: { original: '', marked: '', recovered: '', amplitude: 0, threshold: 0 },
      check: { done: false, found: false, amplitude: 0, threshold: 0, scale: 1, recovered: '' },
      saving: false,
      msg: '',
      msgType: ''
    }
  },
  async mounted() {
    try {
      const { data } = await getWatermarkSettings()
      this.form = { ...this.form, ...data }
    } catch (e) {
      this.fail(e)
    }
  },
  methods: {
    fail(e) {
      this.msg = e.response?.data?.message || e.message || '操作失敗'
      this.msgType = 'error'
      showToast(this.msg, 'error')
    },
    async pick(event, options = {}) {
      const file = event.target.files[0]
      event.target.value = ''
      if (!file) return null
      const { blob } = await compressImage(file, options)
      return readAsDataUrl(blob)
    },
    async onPatternChange(event) {
      try {
        // 圖樣要保留去背，才能用透明度當形狀
        this.form.pattern = await this.pick(event, { keepTransparency: true, maxEdge: 256 }) || this.form.pattern
      } catch (e) {
        this.fail(e)
      }
    },
    async onPreviewChange(event) {
      try {
        const img_data = await this.pick(event)
        if (!img_data) return
        const { data } = await previewWatermark({ ...this.form, enabled: true, img_data })
        this.preview = {
          original: img_data,
          marked: data.marked,
          recovered: data.recovered,
          amplitude: data.amplitude,
          threshold: data.threshold
        }
      } catch (e) {
        this.fail(e)
      }
    },
    async onInspectChange(event) {
      try {
        const img_data = await this.pick(event)
        if (!img_data) return
        const { data } = await inspectWatermark(img_data)
        this.check = { done: true, ...data }
      } catch (e) {
        this.fail(e)
      }
    },
    async save() {
      this.saving = true
      try {
        const { data } = await saveWatermarkSettings(this.form)
        this.form = { ...this.form, ...data.settings }
        this.msg = data.message
        this.msgType = 'success'
        showToast(data.message, 'success')
      } catch (e) {
        this.fail(e)
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.desc {
  margin-bottom: 18px;
  line-height: 1.7;
  opacity: 0.85;
}

.hint {
  margin-top: 6px;
  font-size: 0.85rem;
  line-height: 1.6;
  opacity: 0.7;
}

.mode-tabs {
  display: flex;
  gap: 8px;
}

.mode-tabs .is-active {
  border-color: #7ee3f5;
  color: #7ee3f5;
}

.slider {
  width: 240px;
  max-width: 100%;
}

.pattern-preview {
  margin-top: 10px;
  width: 96px;
  height: 96px;
  object-fit: contain;
  background: repeating-conic-gradient(#2a2a33 0% 25%, #1c1c22 0% 50%) 50% / 16px 16px;
  border-radius: 6px;
}

.compare {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
  margin: 14px 0;
}

.compare img {
  width: 100%;
  border-radius: 6px;
}

.compare figcaption {
  margin-top: 6px;
  font-size: 0.82rem;
  opacity: 0.7;
}

.check-result {
  margin: 14px 0;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(228, 251, 255, 0.15);
}

.check-result.is-found {
  border-color: rgba(126, 227, 245, 0.6);
}

.check-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.recovered {
  margin-top: 10px;
  max-width: 320px;
  width: 100%;
  border-radius: 6px;
}

hr {
  margin: 22px 0;
  border: none;
  border-top: 1px solid rgba(228, 251, 255, 0.12);
}
</style>
