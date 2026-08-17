<template>
  <div class="box">
    <AdminBar title="隱形浮水印">
      <button class="button" type="button" :disabled="saving" @click="save">
        {{ saving ? 'Saving…' : '儲存設定' }}
      </button>
    </AdminBar>

    <p class="desc">
      把簽名藏進圖片的色度裡，亮度完全不動——正常觀看看不出來，把色度差放大就會浮出來。
      開啟之後，<strong>後台新上傳的圖片</strong>會自動套用，同時把沒有浮水印的原圖另外
      備份起來（存在單獨的節點，前台讀不到）。
      <br>
      之後<strong>改了簽名、強度或開關，按下儲存就會用原圖把既有的圖重印一遍</strong>——
      不重印的話站上會同時存在新舊兩種簽名。在啟用浮水印之前就上傳的舊圖沒有原圖備份，
      那些要請工程師跑一次回填腳本。
    </p>

    <p v-if="repainting" class="hint">
      正在用新設定重印既有的圖片…{{ repainting.done }} / {{ repainting.total }}
      （已重印 {{ repainting.images }} 張）
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
      看第二張確認肉眼看不出差別、第三張讀得出簽名。讀不出來就把強度調高一級再試。
    </p>

    <hr>

    <p class="desc">
      要查一張在別處看到的圖是不是從這裡拿走的，用前台的
      <router-link to="/watermark">浮水印檢視</router-link>頁——那頁在瀏覽器裡把色度差放大給人看，
      讀者自己也能查。這裡不做「是／不是」的自動判定：判定得對上圖片被縮放的比例，
      而稍微縮過的圖就對不上，只會給出看起來很確定卻是錯的答案。
    </p>

    <p v-if="msg" class="msg" :class="msgType">{{ msg }}</p>
  </div>
</template>

<script>
// 隱形浮水印的後台面板（issue #25）。
//
// 拆成獨立元件而不是塞進 AdminView：那支已經 4860 行、十個分頁擠在一起
// （issue #29），沒必要再往裡面堆。這裡自己打自己的四支端點。
import AdminBar from './AdminBar.vue'
import {
  getWatermarkSettings, saveWatermarkSettings, previewWatermark,
  getRepaintTargets, repaintWatermark
} from '../api'
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
      preview: { original: '', marked: '', recovered: '' },
      repainting: null,
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
        this.preview = { original: img_data, marked: data.marked, recovered: data.recovered }
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
        await this.repaint()
      } catch (e) {
        this.fail(e)
      } finally {
        this.saving = false
      }
    },
    /**
     * 用新設定把既有的圖重印一遍。
     *
     * 改了簽名卻不重印，站上的舊圖還是舊簽名，兩種簽名混在一起之後就分不出
     * 哪張是什麼時候的了。重印一定是從備份的原圖重來——拿已經套過的圖再套
     * 一次只會疊上去。
     *
     * 一個位置一次請求：全部一起做會超過後端的 30 秒上限，而且只有一個
     * worker（issue #28），整站會在那段時間沒反應。
     */
    async repaint() {
      this.repainting = { total: 0, done: 0, images: 0 }
      try {
        const { data } = await getRepaintTargets()
        const targets = data.targets || []
        this.repainting.total = targets.length
        if (!targets.length) return
        for (const path of targets) {
          try {
            const { data: one } = await repaintWatermark(path)
            this.repainting.images += one.count || 0
          } catch (e) {
            // 單一位置失敗不該中斷整批：其餘照樣重印，最後一次報告
            console.error('重印失敗:', path, e)
            this.repainting.failed = (this.repainting.failed || 0) + 1
          }
          this.repainting.done++
        }
        const failed = this.repainting.failed
        showToast(
          `既有圖片已用新設定重印 ${this.repainting.images} 張`
            + (failed ? `，有 ${failed} 個位置失敗（見主控台）` : ''),
          failed ? 'error' : 'success')
      } catch (e) {
        this.fail(e)
      } finally {
        this.repainting = null
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

hr {
  margin: 22px 0;
  border: none;
  border-top: 1px solid rgba(228, 251, 255, 0.12);
}
</style>
