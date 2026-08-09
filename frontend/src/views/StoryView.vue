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
        <form @submit.prevent="handleSubmit">
          <label class="edit-label">Story</label>
          <textarea
            class="edit-textarea"
            v-model="editStory"
            rows="6"
            placeholder="Write the story..."
          ></textarea>
          <label class="edit-label">Image (.jpg)</label>
          <input class="edit-file" type="file" accept=".jpg" ref="imageInput" />
          <div class="edit-actions">
            <button class="btn-save" type="submit" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
            <button class="btn-cancel" type="button" @click="editing = false">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="elInfo" @touchstart="onTouchStart" @touchend="onTouchEnd">
      <!-- Identity + wheel in one row -->
      <div class="nav-wheel-wrap">
        <div class="nav-wheel" ref="wheelRef">
          <component
            v-for="el in wheelElements"
            :key="el.Symbol"
            :is="el.empty ? 'div' : 'router-link'"
            :to="el.empty ? undefined : '/stroy/' + el.Symbol"
            :class="['wheel-chip', 'wheel-chip--d' + el.dist, { 'wheel-chip--empty': el.empty }]"
            :style="el.dist === 0 ? { borderColor: '#' + elInfo.CPKHexColor } : {}"
          >
            <template v-if="!el.empty">
              <span class="chip-num">{{ el.AtomicNumber }}</span>
              <span
                class="chip-sym"
                :style="el.dist === 0 ? { color: '#' + elInfo.CPKHexColor } : {}"
              >{{ el.Symbol }}</span>
              <span v-if="el.dist === 0" class="chip-name">{{ elInfo.Name }}</span>
            </template>
          </component>
        </div>
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
            <img
              v-if="!imgBroken"
              :style="{ borderColor: '#' + elInfo.CPKHexColor }"
              :src="resolvedImg"
              :title="elInfo.Name"
              alt="Still Creating..."
              @error="onImgError"
            />
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
          </div>

          <!-- Stats：雷達 / 條狀切換 -->
          <div v-else key="stats">
            <div class="chart-type-toggle">
              <button :class="{ active: chartType === 'radar' }" @click="chartType = 'radar'">Radar</button>
              <button :class="{ active: chartType === 'bars' }" @click="chartType = 'bars'">Bars</button>
            </div>
            <AbilityChart v-if="chartType === 'radar' && abilityData" :elInfo="abilityData" />
            <div v-else-if="chartType === 'bars'" id="element-ability">
              <template v-for="ab in abilities" :key="ab.key">
                <div>{{ ab.label }}</div>
                <div class="ability-bar" :style="{ width: abilityWidth(ab.key) }"></div>
              </template>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { getElementDetail, getElementAbility, updateStory, recordElementView, apiBase } from '../api'
import AbilityChart from '../components/AbilityChart.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { authState } from '../store/auth'
import { showToast } from '../store/toast'
import { elementsState, ensureElements } from '../store/elements'

const ABILITIES = [
  { key: 'MeltingPoint', label: 'MeltingPoint (K)' },
  { key: 'BoilingPoint', label: 'BoilingPoint (K)' },
  { key: 'ElectronAffinity', label: 'ElectronAffinity (eV)' },
  { key: 'Electronegativity', label: 'Electronegativity (Pauling Scale)' },
  { key: 'AtomicRadius', label: 'AtomicRadius (van der Waals)' },
  { key: 'IonizationEnergy', label: 'IonizationEnergy (eV)' },
  { key: 'Density', label: 'Density (g/cm³)' }
]

export default {
  components: { AbilityChart, LoadingSpinner },
  props: { symbol: { type: String, required: true } },
  data() {
    return {
      authState,
      elementsState,
      elInfo: null,
      fEl: {},
      bEl: {},
      story: null,
      imgSrc: null,
      imgData: null,
      imgFallbackLevel: 0,
      abilityData: null,
      abilities: ABILITIES,
      section: 'intro',
      chartType: 'radar',
      touchStartX: 0,
      loading: false,
      editing: false,
      editStory: '',
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
    imgBroken() {
      return this.imgFallbackLevel >= 3
    },
    wheelElements() {
      const all = elementsState.elements
      if (!all.length || !this.elInfo) return []
      const idx = all.findIndex(e => e.Symbol === this.elInfo.Symbol)
      if (idx === -1) return []
      const WING = 4
      const result = []
      for (let d = WING; d >= 1; d--) {
        const pos = idx - d
        result.push(pos >= 0
          ? { ...all[pos], dist: d, empty: false }
          : { Symbol: `_L${d}`, AtomicNumber: '', dist: d, empty: true })
      }
      result.push({ ...all[idx], dist: 0, empty: false })
      for (let d = 1; d <= WING; d++) {
        const pos = idx + d
        result.push(pos < all.length
          ? { ...all[pos], dist: d, empty: false }
          : { Symbol: `_R${d}`, AtomicNumber: '', dist: d, empty: true })
      }
      return result
    }
  },
  watch: {
    symbol: {
      immediate: true,
      handler() { this.loadData() }
    }
  },
  methods: {
    onTouchStart(e) {
      this.touchStartX = e.touches[0].clientX
    },
    onTouchEnd(e) {
      const dx = e.changedTouches[0].clientX - this.touchStartX
      if (Math.abs(dx) < 50) return
      if (dx > 0) {
        this.$router.push('/stroy/' + this.fEl.Symbol)
      } else {
        this.$router.push('/stroy/' + this.bEl.Symbol)
      }
    },
    async loadData() {
      this.loading = true
      this.elInfo = null
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
        this.fEl = detail.f_el
        this.bEl = detail.b_el
        this.story = detail.story
        this.imgSrc = apiBase + '/elements/' + this.symbol + '/img'
        this.imgData = detail.img_data
        this.editStory = detail.story || ''
        this.abilityData = abilityRes.data
        // 首頁「熱門元素」用的點閱計數；失敗不影響頁面
        recordElementView(this.symbol).catch(() => {})
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
      const active = wrap.querySelector('.wheel-chip--d0')
      if (!active) return
      const wrapCenter = wrap.offsetWidth / 2
      const chipCenter = active.offsetLeft + active.offsetWidth / 2
      wrap.scrollLeft = chipCenter - wrapCenter
    },
    onImgError() {
      if (this.imgFallbackLevel < 3) this.imgFallbackLevel++
    },
    abilityWidth(key) {
      if (!this.abilityData || !this.abilityData.abMax) return '0%'
      const value = this.abilityData[key] / this.abilityData.abMax[key] * 100
      return (isNaN(value) ? 0 : value) + '%'
    },
    async handleSubmit() {
      this.saving = true
      const formData = new FormData()
      formData.append('symbol', this.elInfo.Symbol)
      formData.append('stroy', this.editStory)
      const imageFile = this.$refs.imageInput?.files[0]
      if (imageFile) formData.append('image', imageFile)
      try {
        const res = await updateStory(formData)
        this.story = this.editStory
        if (imageFile) {
          this.imgFallbackLevel = 0
          await this.loadData()
        }
        showToast(res.data.message || 'Saved successfully', 'success')
        this.editing = false
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.saving = false
      }
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

#element-ability {
  display: grid;
  grid-template-columns: 1fr 2fr;
  grid-auto-rows: 36px;
  gap: 4px;
  text-align: left;
  width: 100%;
  margin: 5px auto;
  padding: 16px 10px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 6px;
  box-shadow: 0 0 24px rgba(80, 0, 160, 0.15), 0 0 48px rgba(0, 100, 200, 0.08);
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
  overflow-x: auto;
  scrollbar-width: none;
  padding: 12px 0 8px;
}
.nav-wheel-wrap::-webkit-scrollbar { display: none; }

.nav-wheel {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-width: max-content;
  margin: 0 auto;
  padding: 0 24px;
}

.wheel-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 7px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  background: rgba(60, 40, 75, 0.3);
  text-decoration: none;
  color: rgba(228, 251, 255, 0.4);
  transition: background 0.18s, border-color 0.18s, opacity 0.18s;
  overflow: hidden;
}

.wheel-chip:hover {
  background: rgba(100, 70, 120, 0.55);
  border-color: rgba(228, 251, 255, 0.35);
  color: rgba(228, 251, 255, 0.85);
}

/* Current element — large with full identity */
.wheel-chip--empty {
  background: transparent !important;
  border-color: transparent !important;
  pointer-events: none;
}

.wheel-chip--d0 {
  width: 76px;
  padding: 12px 6px 10px;
  border-width: 1.5px;
  background: rgba(80, 50, 100, 0.5);
  color: rgba(228, 251, 255, 0.9);
  pointer-events: none;
  gap: 3px;
}
.wheel-chip--d0:hover { background: rgba(80, 50, 100, 0.5); }

/* Neighbouring chips shrink by distance */
.wheel-chip--d1 { width: 52px; height: 60px; color: rgba(228, 251, 255, 0.65); }
.wheel-chip--d2 { width: 42px; height: 48px; color: rgba(228, 251, 255, 0.48); opacity: 0.88; }
.wheel-chip--d3 { width: 33px; height: 38px; color: rgba(228, 251, 255, 0.35); opacity: 0.68; }
.wheel-chip--d4 { width: 26px; height: 30px; color: rgba(228, 251, 255, 0.25); opacity: 0.48; }

/* Text inside chips */
.chip-num {
  font-size: 10px;
  opacity: 0.55;
  line-height: 1;
}
.wheel-chip:not(.wheel-chip--d0) .chip-num { display: none; }

.chip-sym {
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.01em;
}
.wheel-chip--d0 .chip-sym { font-size: 34px; }
.wheel-chip--d1 .chip-sym { font-size: 18px; }
.wheel-chip--d2 .chip-sym { font-size: 15px; }
.wheel-chip--d3 .chip-sym { font-size: 12px; }
.wheel-chip--d4 .chip-sym { font-size: 10px; }

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

.ability-bar {
  background: linear-gradient(90deg, rgba(90, 0, 160, 0.75), rgba(0, 190, 210, 0.75));
  border-radius: 2px;
  transition: width 0.6s ease;
  box-shadow: 0 0 6px rgba(0, 190, 210, 0.3);
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
  img, #element-ability { width: 90%; }
  .element-grid { grid-template-columns: 1fr; }
  .element-grid-info { width: 90%; }
  .wheel-chip--d0 { width: 64px; padding: 10px 4px 8px; }
  .wheel-chip--d0 .chip-sym { font-size: 28px; }
  .wheel-chip--d1 { width: 44px; height: 52px; }
  .wheel-chip--d2 { width: 36px; height: 42px; }
  .wheel-chip--d3 { width: 28px; height: 34px; }
  .wheel-chip--d4 { width: 22px; height: 26px; }
}
</style>
