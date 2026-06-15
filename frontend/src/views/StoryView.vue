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
      <!-- Element identity -->
      <div class="element-identity-block">
        <span class="identity-num">{{ elInfo.AtomicNumber }}</span>
        <span class="identity-sym" :style="{ color: '#' + elInfo.CPKHexColor }">{{ elInfo.Symbol }}</span>
        <span class="identity-name">{{ elInfo.Name }}</span>
      </div>

      <!-- Scroll wheel navigation -->
      <div class="nav-wheel-wrap">
        <div class="nav-wheel" ref="wheelRef">
          <router-link
            v-for="el in wheelElements"
            :key="el.Symbol"
            :to="'/stroy/' + el.Symbol"
            class="wheel-chip"
            :class="{ 'wheel-chip--active': el.Symbol === elInfo.Symbol }"
            :style="el.Symbol === elInfo.Symbol ? { borderColor: '#' + elInfo.CPKHexColor, color: '#' + elInfo.CPKHexColor } : {}"
          >
            <span class="wheel-num">{{ el.AtomicNumber }}</span>
            <span class="wheel-sym">{{ el.Symbol }}</span>
          </router-link>
        </div>
      </div>

      <div class="element-story">
        <!-- Section tabs -->
        <div class="group-type-button">
          <button class="button" :class="{ active: section === 'intro' }" @click="section = 'intro'">Story</button>
          <button class="button" :class="{ active: section === 'radar' }" @click="section = 'radar'">Radar</button>
          <button class="button" :class="{ active: section === 'bars' }" @click="section = 'bars'">Ability</button>
        </div>

        <transition name="fade" mode="out-in">
          <!-- 介紹 -->
          <div v-if="section === 'intro'" key="intro" class="element-grid">
            <img
              :style="{ borderColor: '#' + elInfo.CPKHexColor }"
              :src="resolvedImg"
              :title="elInfo.Name"
              alt="Still Creating..."
              @error="onImgError"
            />
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

          <!-- 雷達圖 -->
          <div v-else-if="section === 'radar'" key="radar">
            <AbilityChart v-if="abilityData" :elInfo="abilityData" />
          </div>

          <!-- 能力圖 -->
          <div v-else key="bars" id="element-ability">
            <template v-for="ab in abilities" :key="ab.key">
              <div>{{ ab.label }}</div>
              <div class="ability-bar" :style="{ width: abilityWidth(ab.key) }"></div>
            </template>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { getElementDetail, getElementAbility, updateStory } from '../api'
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
      touchStartX: 0,
      loading: false,
      editing: false,
      editStory: '',
      saving: false
    }
  },
  computed: {
    resolvedImg() {
      if (this.imgFallbackLevel === 0) return this.imgSrc
      return this.imgData || ''
    },
    wheelElements() {
      const all = elementsState.elements
      if (!all.length || !this.elInfo) return []
      const idx = all.findIndex(e => e.Symbol === this.elInfo.Symbol)
      if (idx === -1) return []
      const start = Math.max(0, idx - 4)
      const end = Math.min(all.length - 1, idx + 4)
      return all.slice(start, end + 1)
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
        this.imgSrc = '/api/elements/' + this.symbol + '/img'
        this.imgData = detail.img_data
        this.editStory = detail.story || ''
        this.abilityData = abilityRes.data
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
      const active = wrap.querySelector('.wheel-chip--active')
      if (!active) return
      const wrapCenter = wrap.offsetWidth / 2
      const chipCenter = active.offsetLeft + active.offsetWidth / 2
      wrap.scrollLeft = chipCenter - wrapCenter
    },
    onImgError() {
      if (this.imgFallbackLevel < 2) this.imgFallbackLevel++
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

/* ── Element identity block ── */
.element-identity-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 16px 0 8px;
}

.identity-num {
  font-size: 13px;
  font-weight: 400;
  opacity: 0.5;
  letter-spacing: 0.04em;
}

.identity-sym {
  font-size: 52px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
}

.identity-name {
  font-size: 15px;
  font-weight: 400;
  opacity: 0.75;
  letter-spacing: 0.03em;
}

/* ── Navigation wheel ── */
.nav-wheel-wrap {
  position: relative;
  margin: 8px auto 16px;
  max-width: 680px;
}

.nav-wheel-wrap::before,
.nav-wheel-wrap::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 40px;
  z-index: 2;
  pointer-events: none;
}
.nav-wheel-wrap::before {
  left: 0;
  background: linear-gradient(to right, #03010a, transparent);
}
.nav-wheel-wrap::after {
  right: 0;
  background: linear-gradient(to left, #03010a, transparent);
}

.nav-wheel {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scroll-behavior: smooth;
  scrollbar-width: none;
  padding: 6px 48px;
  justify-content: flex-start;
}
.nav-wheel::-webkit-scrollbar { display: none; }

.wheel-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 48px;
  height: 52px;
  border-radius: 6px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  background: rgba(60, 40, 75, 0.3);
  text-decoration: none;
  color: rgba(228, 251, 255, 0.45);
  gap: 1px;
  transition: all 0.18s ease;
}

.wheel-chip:hover {
  background: rgba(100, 70, 120, 0.55);
  border-color: rgba(228, 251, 255, 0.4);
  color: #e4fbff;
  transform: translateY(-2px);
}

.wheel-chip--active {
  width: 60px;
  height: 64px;
  border-width: 1.5px;
  background: rgba(80, 50, 100, 0.55);
  color: inherit;
  transform: none;
  pointer-events: none;
}

.wheel-num {
  font-size: 9px;
  opacity: 0.65;
  line-height: 1;
}

.wheel-sym {
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.01em;
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
  .wheel-chip { width: 42px; height: 46px; }
  .wheel-chip--active { width: 52px; height: 58px; }
  .wheel-sym { font-size: 14px; }
}
</style>
