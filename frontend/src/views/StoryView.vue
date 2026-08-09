<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <!-- Edit modal -->
    <div v-if="editing" class="modal-overlay" @click.self="editing = false">
      <div class="modal-box" :style="{ borderColor: '#' + elInfo.CPKHexColor }">
        <div class="modal-header">
          <span>Edit {{ elInfo.Symbol }}</span>
          <button class="modal-close" @click="editing = false">✕</button>
        </div>
        <StoryEditor
          :symbol="elInfo.Symbol"
          :story="story || ''"
          :draft="draft"
          :img-src="resolvedImg"
          @saved="onStorySaved"
          @draft-saved="onDraftSaved"
        >
          <template #extra-actions>
            <button class="btn-cancel" type="button" @click="editing = false">關閉</button>
          </template>
        </StoryEditor>
      </div>
    </div>

    <div v-if="elInfo">
      <!-- Identity + wheel in one row -->
      <div class="nav-wheel-wrap">
        <button
          class="wheel-arrow"
          type="button"
          title="往前捲動元素"
          @click="scrollWheel(-1)"
        >‹</button>

        <div class="nav-wheel" ref="wheelRef" @scroll="onWheelScroll">
          <router-link
            v-for="el in wheelElements"
            :key="el.Symbol"
            :to="'/stroy/' + el.Symbol"
            :class="['wheel-chip', { 'wheel-chip--current': el.current }]"
            :style="el.current ? { borderColor: '#' + elInfo.CPKHexColor } : {}"
          >
            <span class="chip-num">{{ el.AtomicNumber }}</span>
            <span
              class="chip-sym"
              :style="el.current ? { color: '#' + elInfo.CPKHexColor } : {}"
            >{{ el.Symbol }}</span>
            <span v-if="el.current" class="chip-name">{{ elInfo.Name }}</span>
          </router-link>
        </div>

        <button
          class="wheel-arrow"
          type="button"
          title="往後捲動元素"
          @click="scrollWheel(1)"
        >›</button>
      </div>

      <div class="element-story">
        <!-- Section tabs -->
        <div class="group-type-button">
          <button class="button" :class="{ active: section === 'intro' }" @click="section = 'intro'">Story</button>
          <button class="button" :class="{ active: section === 'stats' }" @click="section = 'stats'">Stats</button>
        </div>

        <transition name="fade" mode="out-in">
          <!-- 介紹 -->
          <div v-if="section === 'intro'" key="intro" class="dex">
            <!-- 編號與名稱：比照圖鑑置中在最上方 -->
            <header class="dex-head">
              <p class="dex-no">No.{{ String(elInfo.AtomicNumber).padStart(3, '0') }}</p>
              <h1 class="dex-name" :style="{ color: '#' + elInfo.CPKHexColor }">
                {{ elInfo.Name }}
                <span class="dex-symbol">{{ elInfo.Symbol }}</span>
              </h1>
              <button
                v-if="authState.loggedIn"
                class="btn-edit"
                type="button"
                @click="editing = true"
              >Edit</button>
            </header>

            <div class="dex-body">
              <!-- 左：分類標籤 -->
              <aside class="dex-tags">
                <p class="dex-label">分類</p>
                <span class="dex-tag" :style="tagStyle">{{ elInfo.GroupBlock || '—' }}</span>

                <p class="dex-label">常溫狀態</p>
                <span class="dex-tag" :style="tagStyle">{{ elInfo.StandardState || '—' }}</span>

                <template v-if="outerElectrons">
                  <p class="dex-label">最外層電子</p>
                  <span class="dex-tag" :style="tagStyle">{{ outerElectrons }} 個</span>
                </template>
              </aside>

              <!-- 中：主圖 -->
              <div class="dex-figure">
                <!-- 有分層素材時讓讀者自己選要看動態還是原本的靜態圖 -->
                <div v-if="hasLayers" class="view-switch">
                  <button
                    class="view-switch-btn"
                    type="button"
                    :class="{ active: preferLayers }"
                    @click="setPreferLayers(true)"
                  >動態</button>
                  <button
                    class="view-switch-btn"
                    type="button"
                    :class="{ active: !preferLayers }"
                    @click="setPreferLayers(false)"
                  >靜態</button>
                </div>

                <PokedexFrame
                  v-if="!imgBroken"
                  :color="elInfo.CPKHexColor"
                  :style="site.frame_style"
                  :frame-image="site.frame_image"
                >
                  <!-- 圖層備齊時用分層呈現，否則沿用原本的靜態圖 -->
                  <ElementLayers
                    v-if="useLayers"
                    :nucleus="layers.nucleus"
                    :name-img="layers.name_img"
                    :electron-img="layers.electron_img"
                    :count="outerElectrons"
                    :motion="layers.motion"
                    :bg-color="site.layer_bg"
                    :size="site.electron_size"
                    :orbitals="outerOrbitals"
                    :seed="elInfo.Symbol"
                  />
                  <img
                    v-else
                    :src="resolvedImg"
                    :title="elInfo.Name"
                    alt="Still Creating..."
                    @error="onImgError"
                  />
                </PokedexFrame>
                <div
                  v-else
                  class="img-placeholder"
                  :style="{ borderColor: '#' + elInfo.CPKHexColor, backgroundColor: '#' + elInfo.CPKHexColor + '18' }"
                >
                  <span class="img-placeholder-sym" :style="{ color: '#' + elInfo.CPKHexColor }">{{ elInfo.Symbol }}</span>
                  <span class="img-placeholder-label">No image yet</span>
                </div>
              </div>

              <!-- 右：基本資料，兩欄網格 -->
              <dl class="dex-facts">
                <div v-for="f in facts" :key="f.label" class="dex-fact">
                  <dt>{{ f.label }}</dt>
                  <dd>{{ f.value }}</dd>
                </div>
              </dl>
            </div>

            <!-- 故事全寬 -->
            <section
              class="dex-story"
              :style="{ borderColor: '#' + elInfo.CPKHexColor + '66' }"
              id="main-content"
            >
              <template v-if="storyText">{{ storyText }}</template>
              <template v-else>Still Creating...</template>
            </section>

            <ElementGallery class="gallery-span" :images="gallery" :color="elInfo.CPKHexColor" />
          </div>

          <!-- Stats：基本資料 + 能力值 -->
          <div v-else key="stats" class="stats-section">
            <div class="chart-type-toggle">
              <button :class="{ active: chartType === 'bars' }" @click="chartType = 'bars'">數值條</button>
              <button :class="{ active: chartType === 'radar' }" @click="chartType = 'radar'">雷達圖</button>
            </div>
            <AbilityBars
              v-if="chartType === 'bars' && abilityData"
              :elInfo="abilityData"
              :color="elInfo.CPKHexColor"
            />
            <AbilityChart v-else-if="chartType === 'radar' && abilityData" :elInfo="abilityData" />
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { getElementDetail, getElementAbility, updateStory, recordElementView, getElementGallery, getElementLayers, apiBase } from '../api'
import AbilityChart from '../components/AbilityChart.vue'
import AbilityBars from '../components/AbilityBars.vue'
import PokedexFrame from '../components/PokedexFrame.vue'
import ElementGallery from '../components/ElementGallery.vue'
import ElementLayers from '../components/ElementLayers.vue'
import StoryEditor from '../components/StoryEditor.vue'
import { outerElectronCount, outerElectronOrbitals } from '../utils/valence'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { siteSettingsState } from '../store/siteSettings'
import { authState } from '../store/auth'
import { showToast } from '../store/toast'
import { elementsState, ensureElements } from '../store/elements'

export default {
  components: { AbilityChart, AbilityBars, PokedexFrame, ElementGallery, ElementLayers, StoryEditor, LoadingSpinner },
  props: { symbol: { type: String, required: true } },
  data() {
    return {
      authState,
      elementsState,
      elInfo: null,
      story: null,
      draft: '',
      imgSrc: null,
      imgData: null,
      imgFallbackLevel: 0,
      abilityData: null,
      site: siteSettingsState,
      gallery: [],
      layers: null,
      preferLayers: localStorage.getItem('preferLayers') !== 'false',
      section: 'intro',
      chartType: 'bars',
      loading: false,
      editing: false,
      saving: false
    }
  },
  computed: {
    resolvedImg() {
      const defaultImg = apiBase + '/elements/default-img'
      if (this.imgFallbackLevel === 0) return this.imgSrc
      if (this.imgFallbackLevel === 1) return this.imgData || defaultImg
      if (this.imgFallbackLevel === 2) return defaultImg
      return null
    },
    // 原子核是必要的；沒有它就沒有分層的基礎
    hasLayers() {
      return !!(this.layers && this.layers.nucleus)
    },
    // 有素材，且讀者選擇看動態版
    useLayers() {
      return this.hasLayers && this.preferLayers
    },
    outerElectrons() {
      return outerElectronCount(this.elInfo?.ElectronConfiguration)
    },
    // 每顆電子所屬的軌域，決定它的運動形態
    outerOrbitals() {
      return outerElectronOrbitals(this.elInfo?.ElectronConfiguration)
    },
    // 用純文字輸出搭配 white-space: pre-wrap 顯示換行。
    // 原本走 v-html 只把字面的 \n 換成 <br>，抓不到後台實際輸入的換行字元；
    // 而且 v-html 會執行故事裡的 HTML（含 AI 產生的內容），是不必要的 XSS 風險。
    storyText() {
      // 舊資料可能存的是字面的反斜線 n，一併還原成真正的換行
      return (this.story || '').replace(/\\n/g, '\n')
    },
    tagStyle() {
      const c = this.elInfo?.CPKHexColor || '64b8e8'
      return {
        borderColor: `#${c}`,
        background: `color-mix(in srgb, #${c} 22%, transparent)`
      }
    },
    // 右側基本資料。沒有值的欄位不列出，避免一排「—」
    facts() {
      const el = this.elInfo || {}
      return [
        { label: '原子量', value: el.AtomicMass ? `${el.AtomicMass} u` : '' },
        { label: '電子組態', value: el.ElectronConfiguration },
        { label: '常見氧化態', value: el.OxidationStates },
        { label: '發現年份', value: el.YearDiscovered }
      ].filter(f => f.value)
    },
    imgBroken() {
      return this.imgFallbackLevel >= 3
    },
    // 整列 118 個元素都渲染，讓左右箭頭可以一路捲動瀏覽並直接點選，
    // 而不只是看到目前元素的前後幾個
    wheelElements() {
      const all = elementsState.elements
      if (!all.length || !this.elInfo) return []
      // 明確依原子序排序，不倚賴資料來源的順序
      return [...all]
        .sort((a, b) => Number(a.AtomicNumber) - Number(b.AtomicNumber))
        .map(el => ({ ...el, current: el.Symbol === this.elInfo.Symbol }))
    }
  },
  mounted() {
    this._onWheelResize = () => this.updateWheelDepth()
    window.addEventListener('resize', this._onWheelResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this._onWheelResize)
    if (this._wheelRaf) cancelAnimationFrame(this._wheelRaf)
  },
  watch: {
    symbol: {
      immediate: true,
      handler() { this.loadData() }
    }
  },
  methods: {
    async loadData() {
      this.loading = true
      this.elInfo = null
      this.gallery = []
      this.layers = null
      this.imgFallbackLevel = 0
      this.section = 'intro'
      this.editing = false
      try {
        ensureElements()  // fire-and-forget; static fallback already populated
        const [detailRes, abilityRes] = await Promise.all([
          getElementDetail(this.symbol),
          getElementAbility(this.symbol)
        ])
        const detail = detailRes.data
        this.elInfo = detail.el_info
        this.story = detail.story
        this.imgSrc = apiBase + '/elements/' + this.symbol + '/img'
        this.imgData = detail.img_data
        this.draft = detail.draft || ''
        this.abilityData = abilityRes.data
        // 首頁「熱門元素」用的點閱計數；失敗不影響頁面
        recordElementView(this.symbol).catch(() => {})
        // 其他樣貌是附加內容，獨立載入，沒有或失敗都不影響主要畫面
        getElementGallery(this.symbol)
          .then(res => { this.gallery = res.data.images || [] })
          .catch(() => { this.gallery = [] })
        // 圖層是選用的，沒設定就沿用靜態圖
        getElementLayers(this.symbol)
          .then(res => { this.layers = res.data })
          .catch(() => { this.layers = null })
      } catch (e) {
        console.error('Failed to load element data:', e)
      } finally {
        this.loading = false
        this.$nextTick(() => this.scrollWheelToActive())
      }
    },
    scrollWheelToActive() {
      const wrap = this.$refs.wheelRef
      if (!wrap) return
      const active = wrap.querySelector('.wheel-chip--current')
      if (!active) return
      const wrapCenter = wrap.offsetWidth / 2
      const chipCenter = active.offsetLeft + active.offsetWidth / 2
      wrap.scrollLeft = chipCenter - wrapCenter
      this.updateWheelDepth()
    },
    setPreferLayers(value) {
      this.preferLayers = value
      localStorage.setItem('preferLayers', String(value))
    },
    onWheelScroll() {
      // 捲動事件很密集，用 rAF 節流
      if (this._wheelRaf) return
      this._wheelRaf = requestAnimationFrame(() => {
        this._wheelRaf = null
        this.updateWheelDepth()
      })
    },
    // 依每個元素距離視窗中央的遠近縮放，保留原本「近的大、遠的小」的滾輪感；
    // 整列渲染後距離會隨捲動改變，沒辦法像以前那樣用靜態的 class 表示
    updateWheelDepth() {
      const wrap = this.$refs.wheelRef
      if (!wrap) return
      const center = wrap.scrollLeft + wrap.offsetWidth / 2
      const reach = wrap.offsetWidth / 2 || 1
      for (const chip of wrap.children) {
        const dist = Math.abs(chip.offsetLeft + chip.offsetWidth / 2 - center)
        const t = Math.min(dist / reach, 1)
        chip.style.transform = `scale(${(1 - t * 0.4).toFixed(3)})`
        chip.style.opacity = (1 - t * 0.62).toFixed(3)
      }
    },
    // 左右箭頭：捲動元素列讓使用者找元素，不是切換到上/下一個元素
    scrollWheel(direction) {
      const wrap = this.$refs.wheelRef
      if (!wrap) return
      wrap.scrollBy({ left: direction * wrap.offsetWidth * 0.7, behavior: 'smooth' })
    },
    onImgError() {
      if (this.imgFallbackLevel < 3) this.imgFallbackLevel++
    },
    onStorySaved({ story, hasImage }) {
      this.story = story
      this.draft = ''
      this.editing = false
      // 換過圖片就重新載入，讓畫面取到新圖
      if (hasImage) this.loadData()
    },
    onDraftSaved({ story }) {
      this.draft = story
    }
  }
}
</script>

<style scoped>
.stats-section {
  width: 100%;
}

.chart-type-toggle {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin: 10px 0 4px;
}
.chart-type-toggle button {
  padding: 4px 18px;
  border: 1px solid rgba(228, 251, 255, 0.3);
  border-radius: 20px;
  background: transparent;
  color: rgba(228, 251, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.chart-type-toggle button.active,
.chart-type-toggle button:hover {
  background: rgba(228, 251, 255, 0.12);
  color: rgba(228, 251, 255, 0.95);
  border-color: rgba(228, 251, 255, 0.6);
}

/* ── Navigation wheel (identity integrated) ── */
.nav-wheel-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 8px 8px;
  max-width: 1100px;
  margin: 0 auto;
}

.wheel-arrow {
  flex-shrink: 0;
  width: 30px;
  height: 46px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 8px;
  background: rgba(60, 40, 75, 0.4);
  color: rgba(228, 251, 255, 0.6);
  font-size: 22px;
  line-height: 1;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.wheel-arrow:hover {
  background: rgba(100, 70, 120, 0.7);
  border-color: rgba(228, 251, 255, 0.45);
  color: #e4fbff;
}

.nav-wheel {
  /* 必須是定位祖先：置中與遠近縮放都用 chip.offsetLeft 計算，
     沒有它的話 offsetParent 會變成 body，座標基準與 scrollLeft 不一致 */
  position: relative;
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 5px;
  overflow-x: auto;
  scroll-behavior: smooth;
  scrollbar-width: none;
  padding: 2px 0;
  /* 手機上直接滑這條列即可瀏覽元素（原本的整頁滑動切換手勢已移除，
     那個容易在捲動頁面時誤觸）；帶慣性並貼齊到元素 */
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  scroll-snap-type: x proximity;
}

.nav-wheel > * {
  scroll-snap-align: center;
}

.nav-wheel::-webkit-scrollbar { display: none; }

.wheel-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 46px;
  height: 52px;
  border-radius: 7px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  background: rgba(60, 40, 75, 0.3);
  text-decoration: none;
  color: rgba(228, 251, 255, 0.6);
  transition: background 0.18s, border-color 0.18s, color 0.18s;
  overflow: hidden;
  /* transform / opacity 由捲動時的 updateWheelDepth() 設定 */
  transform-origin: center center;
  will-change: transform, opacity;
}

.wheel-chip:hover {
  background: rgba(100, 70, 120, 0.6);
  border-color: rgba(228, 251, 255, 0.4);
  color: rgba(228, 251, 255, 0.95);
}

/* 目前所在的元素：放大並顯示全名 */
.wheel-chip--current {
  width: 76px;
  height: 66px;
  border-width: 1.5px;
  background: rgba(80, 50, 100, 0.6);
  color: rgba(228, 251, 255, 0.95);
  pointer-events: none;
  gap: 2px;
}

.chip-num {
  font-size: 10px;
  opacity: 0.5;
  line-height: 1;
}

.chip-sym {
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.01em;
  font-size: 17px;
}

.wheel-chip--current .chip-sym { font-size: 28px; }

.chip-name {
  font-size: 11px;
  opacity: 0.72;
  line-height: 1.2;
  letter-spacing: 0.01em;
  text-align: center;
}

.element-story {
  width: 100%;
  display: grid;
}

/* ── 圖鑑式排版 ── */
.dex {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 8px;
}

.dex-head {
  position: relative;
  text-align: center;
  margin-bottom: 18px;
}

.dex-no {
  font-size: 13px;
  letter-spacing: 0.22em;
  color: rgba(228, 251, 255, 0.4);
  margin: 0;
}

.dex-name {
  font-size: clamp(26px, 4vw, 38px);
  font-weight: 700;
  line-height: 1.2;
  margin: 2px 0 0;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 10px;
}

.dex-symbol {
  font-size: 0.5em;
  color: rgba(228, 251, 255, 0.55);
  letter-spacing: 0.04em;
}

.dex-head .btn-edit {
  position: absolute;
  top: 0;
  right: 0;
}

/* 左標籤／中圖／右資料 */
.dex-body {
  display: grid;
  grid-template-columns: minmax(150px, 1fr) minmax(240px, 1.5fr) minmax(180px, 1.2fr);
  gap: 22px;
  align-items: center;
}

.dex-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.dex-label {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: rgba(228, 251, 255, 0.4);
  margin: 12px 0 2px;
}

.dex-label:first-child { margin-top: 0; }

.dex-tag {
  display: inline-block;
  padding: 6px 16px;
  border: 1px solid;
  border-radius: 999px;
  font-size: 14px;
  color: #e4fbff;
  text-align: center;
}

.dex-figure {
  min-width: 0;
  /* 必須給明確寬度：分層呈現是 width:100% + aspect-ratio，本身沒有固有
     尺寸，父層若是 shrink-to-fit（例如只給 margin:auto）就會塌陷成一小塊，
     而靜態的 <img> 因為有固有尺寸看起來卻正常 */
  width: 100%;
}

.view-switch {
  display: flex;
  justify-content: center;
  gap: 3px;
  margin-bottom: 8px;
  padding: 2px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 999px;
  width: fit-content;
  margin-left: auto;
  margin-right: auto;
}

.view-switch-btn {
  padding: 3px 14px;
  font-size: 12px;
  font-family: inherit;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: rgba(228, 251, 255, 0.5);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.view-switch-btn:hover { color: rgba(228, 251, 255, 0.85); }

.view-switch-btn.active {
  background: rgba(228, 251, 255, 0.16);
  color: #e4fbff;
}

.dex-facts {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin: 0;
  text-align: left;
}

.dex-fact dt {
  font-size: 11px;
  letter-spacing: 0.12em;
  color: rgba(228, 251, 255, 0.4);
  margin-bottom: 2px;
}

.dex-fact dd {
  font-size: 15px;
  color: rgba(228, 251, 255, 0.92);
  margin: 0;
  word-break: break-word;
}

.dex-story {
  /* 保留後台輸入的換行與空行 */
  white-space: pre-wrap;
  margin-top: 24px;
  padding: 20px 22px;
  border: 1px solid;
  border-radius: 10px;
  background: rgba(20, 5, 35, 0.4);
  font-size: 16px;
  line-height: 1.95;
  text-align: left;
}

.gallery-span {
  margin-top: 8px;
}

@media (max-width: 860px) {
  .dex-body {
    grid-template-columns: 1fr;
    gap: 18px;
  }
  /* 手機上先看圖，再看標籤與資料。平板寬度時 320px 太小，放寬到 420px；
     窄螢幕靠 width:100% 自動收斂 */
  .dex-figure { order: -1; width: 100%; max-width: 420px; margin: 0 auto; }
  .dex-facts { grid-template-columns: 1fr 1fr; }
  .dex-head .btn-edit { position: static; margin-top: 8px; }
}

.img-placeholder {
  width: 100%;
  aspect-ratio: 1 / 1;
  border: 2px solid;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.img-placeholder-sym {
  font-size: clamp(36px, 8vw, 72px);
  font-weight: 700;
  line-height: 1;
}
.img-placeholder-label {
  font-size: 12px;
  opacity: 0.5;
  letter-spacing: 0.05em;
}

/* ── Atomic title row ── */
.btn-edit {
  font-size: 12px;
  padding: 2px 10px;
  border: 1px solid rgba(228, 251, 255, 0.5);
  border-radius: 4px;
  background: rgba(228, 251, 255, 0.1);
  color: #e4fbff;
  cursor: pointer;
  transition: background 0.15s;
  flex-shrink: 0;
}

.btn-edit:hover {
  background: rgba(228, 251, 255, 0.22);
}

/* ── Modal ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: rgb(30, 25, 30);
  border: 2px solid;
  border-radius: 8px;
  width: min(560px, 92vw);
  padding: 24px;
  text-align: left;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 16px;
  color: #e4fbff;
}

.modal-close {
  background: none;
  border: none;
  color: #aaa;
  font-size: 18px;
  cursor: pointer;
  line-height: 1;
}

.modal-close:hover { color: #fff; }

.edit-label {
  display: block;
  font-size: 13px;
  margin: 10px 0 4px;
  opacity: 0.7;
}

.edit-textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(228, 251, 255, 0.3);
  border-radius: 4px;
  color: #fff;
  padding: 8px;
  font-size: 15px;
  resize: vertical;
  box-sizing: border-box;
}

.edit-file {
  display: block;
  margin: 4px 0;
}

.edit-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.btn-save, .btn-cancel {
  padding: 6px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  border: 1px solid;
  transition: background 0.15s;
}

.btn-save {
  background: rgba(228, 251, 255, 0.15);
  border-color: #e4fbff;
  color: #fff;
}
.btn-save:hover { background: rgba(228, 251, 255, 0.28); }
.btn-save:disabled { opacity: 0.5; cursor: default; }

.btn-cancel {
  background: transparent;
  border-color: #666;
  color: #aaa;
}
.btn-cancel:hover { border-color: #aaa; color: #fff; }

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media only screen and (max-width: 800px) {
  img { width: 90%; }
  .wheel-chip { width: 40px; height: 46px; }
  .wheel-chip .chip-sym { font-size: 15px; }
  .wheel-chip--current { width: 64px; height: 58px; }
  .wheel-chip--current .chip-sym { font-size: 24px; }
  .wheel-arrow { width: 26px; height: 40px; font-size: 19px; }
}
</style>
