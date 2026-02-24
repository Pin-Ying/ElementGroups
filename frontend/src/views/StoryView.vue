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
            <span v-if="saveMsg" :class="saveMsgType" class="save-msg">{{ saveMsg }}</span>
          </div>
        </form>
      </div>
    </div>

    <div v-if="elInfo">
      <div class="element-btns">
        <div>
          <router-link
            class="button"
            :to="'/stroy/' + fEl.Symbol"
            :style="{ borderColor: '#' + fEl.CPKHexColor }"
          >
            PREVIOUS ELEMENT
          </router-link>
        </div>
        <div class="title column">{{ elInfo.Symbol }}'s Story</div>
        <div>
          <router-link
            class="button"
            :to="'/stroy/' + bEl.Symbol"
            :style="{ borderColor: '#' + bEl.CPKHexColor }"
          >
            NEXT ELEMENT
          </router-link>
        </div>
      </div>

      <div class="element-story">
        <div class="element-grid">
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
                @click="editing = true; saveMsg = ''"
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

        <div id="element-ability" :style="{ borderColor: '#' + elInfo.CPKHexColor }">
          <template v-for="ab in abilities" :key="ab.key">
            <div>{{ ab.label }}</div>
            <div class="ability-bar" :style="{ width: abilityWidth(ab.key) }"></div>
          </template>
        </div>

        <AbilityChart v-if="abilityData" :elInfo="abilityData" />
      </div>
    </div>
  </div>
</template>

<script>
import { getElementDetail, getElementAbility, updateStory } from '../api'
import AbilityChart from '../components/AbilityChart.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { authState } from '../store/auth'

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
      elInfo: null,
      fEl: {},
      bEl: {},
      story: null,
      imgSrc: null,
      imgData: null,
      imgFallbackLevel: 0,
      abilityData: null,
      abilities: ABILITIES,
      loading: false,
      editing: false,
      editStory: '',
      saving: false,
      saveMsg: '',
      saveMsgType: ''
    }
  },
  computed: {
    resolvedImg() {
      if (this.imgFallbackLevel === 0) return this.imgSrc
      return this.imgData || ''
    }
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
      this.imgFallbackLevel = 0
      this.editing = false
      this.saveMsg = ''
      try {
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
      }
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
      this.saveMsg = ''
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
        this.saveMsg = res.data.message
        this.saveMsgType = 'msg-success'
      } catch (e) {
        this.saveMsg = e.response?.data?.message || 'Save failed'
        this.saveMsgType = 'msg-error'
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
  grid-auto-rows: 50px;
  gap: 5px;
  text-align: left;
  width: 100%;
  margin: 5px auto;
  padding: 20px 10px;
  border: #e4fbff solid 2px;
  border-radius: 2px;
}

.button {
  border-width: 2px;
  min-width: 200px;
}

.element-btns {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  align-items: center;
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
  background-color: #e4fbff;
  color: #000000;
  transition: width 0.6s ease;
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

.save-msg { font-size: 13px; }
.msg-success { color: #6ee76e; }
.msg-error   { color: #ff6b6b; }

@media only screen and (max-width: 800px) {
  img, #element-ability { width: 90%; }
  .element-btns { display: block; }
  .element-grid { grid-template-columns: 1fr; }
  .element-grid-info { width: 90%; }
}
</style>
