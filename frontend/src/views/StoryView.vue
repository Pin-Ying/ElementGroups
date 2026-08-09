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
          <div v-if="section === 'intro'" key="intro" class="element-grid">
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
            <div
              class="element-grid-info"
              :style="{
                borderColor: '#' + elInfo.CPKHexColor,
                backgroundColor: '#' + elInfo.CPKHexColor + '33'
              }"
              id="main-content"
            >
              <div class="atomic-title">
                <span class="title">Atomic NUMBER: {{ elInfo.AtomicNumber }}</span>
                <button
                  v-if="authState.loggedIn"
                  class="btn-edit"
                  type="button"
                  @click="editing = true"
                >Edit</button>
              </div>
              <div class="subtitle">
                {{ elInfo.Name }} / {{ elInfo.Symbol }} / {{ elInfo.ElectronConfiguration }}
              </div>
              <div>
                <template v-if="story">
                  <span v-html="story.replace(/\\n/g, '<br>')"></span>
                </template>
                <template v-else>Still Creating...</template>
              </div>
            </div>

            <ElementGallery class="gallery-span" :images="gallery" :color="elInfo.CPKHexColor" />
          </div>

          <!-- Stats：基本資料 + 能力值 -->
          <div v-else key="stats" class="stats-section">
            <ElementProfile v-if="abilityData" :elInfo="abilityData" />

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
import ElementProfile from '../components/ElementProfile.vue'
import PokedexFrame from '../components/PokedexFrame.vue'
import ElementGallery from '../components/ElementGallery.vue'
import ElementLayers from '../components/ElementLayers.vue'
import StoryEditor from '../components/StoryEditor.vue'
import { outerElectronCount } from '../utils/valence'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { siteSettingsState } from '../store/siteSettings'
import { authState } from '../store/auth'
import { showToast } from '../store/toast'
import { elementsState, ensureElements } from '../store/elements'

export default {
  components: { AbilityChart, AbilityBars, ElementProfile, PokedexFrame, ElementGallery, ElementLayers, StoryEditor, LoadingSpinner },
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
    useLayers() {
      return !!(this.layers && this.layers.nucleus)
    },
    outerElectrons() {
      return outerElectronCount(this.elInfo?.ElectronConfiguration)
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
#main-content {
  display: grid;
  text-align: left;
  border: #ffffff solid 2px;
  border-radius: 2px;
  font-size: 20px;
  margin: 5px;
  padding: 20px 10px;
}

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

.element-grid {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 2fr;
  align-items: center;
  justify-items: center;
  gap: 10px;
  margin: 5px auto;
}

/* 其他樣貌獨立一區，橫跨圖片與故事兩欄 */
.gallery-span {
  grid-column: 1 / -1;
  justify-self: stretch;
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

.element-grid-info {
  height: 100%;
  width: 100%;
  grid-template-rows: 1fr 0.5fr 2.5fr;
}

/* ── Atomic title row ── */
.atomic-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

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
  .element-grid { grid-template-columns: 1fr; }
  .element-grid-info { width: 90%; }
  .wheel-chip { width: 40px; height: 46px; }
  .wheel-chip .chip-sym { font-size: 15px; }
  .wheel-chip--current { width: 64px; height: 58px; }
  .wheel-chip--current .chip-sym { font-size: 24px; }
  .wheel-arrow { width: 26px; height: 40px; font-size: 19px; }
}
</style>
