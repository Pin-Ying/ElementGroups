<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <ElementHighlights />

    <div class="view-controls">
      <div class="control-group">
        <label class="control-label" for="group-select">分組</label>
        <select id="group-select" class="group-select" :value="showMode" @change="onGroupChange">
          <option v-for="g in GROUP_MODES" :key="g.key" :value="g.key">{{ g.label }}</option>
        </select>
      </div>

      <div v-if="showMode !== 'table'" class="control-group">
        <label class="control-label">檢視</label>
        <div class="style-switch">
          <button
            v-for="s in VIEW_STYLES"
            :key="s.key"
            class="style-button"
            type="button"
            :class="{ active: viewStyle === s.key }"
            :title="s.label"
            @click="setViewStyle(s.key)"
          >{{ s.icon }}<span class="style-text">{{ s.label }}</span></button>
        </div>
      </div>
    </div>

    <!-- 搜尋列（所有模式都顯示） -->
    <div class="search-bar">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        class="search-input"
        v-model="query"
        aria-label="搜尋元素"
        autocomplete="off"
        spellcheck="false"
      />
      <button v-if="query" class="search-clear" @click="query = ''" title="Clear">✕</button>
    </div>

    <!-- 完成度圖例（#5）：一眼看出哪些元素已經有圖片/故事 -->
    <div v-if="completionCount.total > 0" class="completion-legend">
      <button
        class="legend-toggle"
        type="button"
        :class="{ active: showCompletion }"
        @click="toggleCompletion"
      >{{ showCompletion ? '隱藏完成度' : '顯示完成度' }}</button>
      <template v-if="showCompletion">
        <span class="legend-item"><i class="legend-dot legend-dot--image"></i>已上傳圖片 {{ completionCount.image }} / {{ elements.length }}</span>
        <span class="legend-item"><i class="legend-dot legend-dot--story"></i>已寫故事 {{ completionCount.story }} / {{ elements.length }}</span>
      </template>
    </div>

    <div v-if="!loading && elements.length === 0" class="no-results">
      Unable to load elements. Please refresh the page.
    </div>

    <transition v-else name="fade" mode="out-in">
      <div v-if="showMode === 'table'" key="table">
        <div v-if="noMatch" class="no-results">No elements match "{{ query }}"</div>
        <!-- 週期表格排版是固定的 18 欄，不套用檢視樣式；窄螢幕改以族分組 -->
        <PeriodicTableGrid v-else-if="!isMobile" :elements="filteredElements" :completion="activeCompletion" />
        <GroupBox v-else :elements="filteredElements" :groups="tableGroups" view-style="small" :completion="activeCompletion" />
      </div>
      <div v-else-if="showMode === 'none'" key="none" id="non-group">
        <div v-if="noMatch" class="no-results">No elements match "{{ query }}"</div>
        <ElementListView
          v-else-if="viewStyle === 'list'"
          :elements="filteredElements"
          :groups="groups"
          :completion="activeCompletion"
        />
        <ElementIconGrid
          v-else
          :elements="filteredElements"
          :size="viewStyle"
          :completion="activeCompletion"
        />
      </div>
      <div v-else key="group" id="group">
        <div v-if="noMatch" class="no-results">No elements match "{{ query }}"</div>
        <GroupBox v-else :elements="filteredElements" :groups="groups" :view-style="viewStyle" :completion="activeCompletion" />
      </div>
    </transition>

  </div>
</template>

<script>
import { getElements, getGroups, getElementsCompletion } from '../api'
import { elementsState } from '../store/elements'
import { siteSettingsState } from '../store/siteSettings'
import { setPageSeo } from '../utils/seo'
import { buildTableGroups } from '../utils/periodicTableGroups'
import PeriodicTableGrid from '../components/PeriodicTableGrid.vue'
import GroupBox from '../components/GroupBox.vue'
import ElementIconGrid from '../components/ElementIconGrid.vue'
import ElementListView from '../components/ElementListView.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ElementHighlights from '../components/ElementHighlights.vue'

// 分組方式與檢視樣式是兩個獨立的維度，避免選項數量相乘
const GROUP_MODES = [
  { key: 'table', label: 'Periodic Table' },
  { key: 'none', label: 'Atomic Number' },
  { key: 'cp', label: 'Chemical Properties' },
  { key: 'vs', label: 'Valence Shell' }
]

const VIEW_STYLES = [
  { key: 'large', label: '大圖示', icon: '▦' },
  { key: 'small', label: '小圖示', icon: '▪' },
  { key: 'list', label: '詳細清單', icon: '☰' }
]

export default {
  components: { PeriodicTableGrid, GroupBox, ElementIconGrid, ElementListView, LoadingSpinner, ElementHighlights },
  data() {
    return {
      GROUP_MODES,
      VIEW_STYLES,
      viewStyle: localStorage.getItem('viewStyle') || 'large',
      elements: elementsState.elements,
      groups: {},
      groupsCache: {},
      showMode: 'table',
      loading: false,
      query: '',
      isMobile: window.innerWidth < 600,
      completion: {},
      showCompletion: localStorage.getItem('showCompletion') !== 'false',
      siteSettingsState
    }
  },
  watch: {
    // 網站設定多半比這頁晚回來，回來後把首頁的標題與描述換成後台設定的版本
    'siteSettingsState.loaded'() {
      this.applySeo()
    }
  },
  mounted() {
    this._onResize = () => { this.isMobile = window.innerWidth < 600 }
    window.addEventListener('resize', this._onResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this._onResize)
  },
  computed: {
    tableGroups() {
      return buildTableGroups(this.elements)
    },
    filteredElements() {
      const q = this.query.trim().toLowerCase()
      if (!q) return this.elements
      return this.elements.filter(e =>
        e.Name?.toLowerCase().includes(q) ||
        e.Symbol?.toLowerCase().includes(q) ||
        String(e.AtomicNumber) === q
      )
    },
    noMatch() {
      return !!this.query && this.filteredElements.length === 0
    },
    activeCompletion() {
      return this.showCompletion ? this.completion : null
    },
    completionCount() {
      const entries = Object.values(this.completion)
      return {
        total: entries.length,
        story: entries.filter(e => e && e.story).length,
        image: entries.filter(e => e && e.image).length
      }
    }
  },
  async created() {
    this.applySeo()
    this.loading = true
    try {
      const res = await getElements()
      this.elements = res.data.elements
      this.groups = res.data.groups
      elementsState.elements = res.data.elements
      elementsState.loaded = true
    } catch (e) {
      console.error('Failed to load elements:', e)
    } finally {
      this.loading = false
    }
    this.loadCompletion()
  },
  methods: {
    applySeo() {
      setPageSeo({
        title: siteSettingsState.title,
        description: siteSettingsState.description,
        path: '/'
      })
    },
    // 完成度是次要資訊，獨立載入，失敗也不影響週期表顯示
    async loadCompletion() {
      try {
        const res = await getElementsCompletion()
        this.completion = res.data.completion || {}
      } catch (e) {
        console.error('Failed to load completion:', e)
      }
    },
    onGroupChange(e) {
      const mode = e.target.value
      if (mode === 'cp' || mode === 'vs') {
        this.loadGroups(mode)
      } else {
        this.showMode = mode
      }
    },
    setViewStyle(style) {
      this.viewStyle = style
      localStorage.setItem('viewStyle', style)
    },
    toggleCompletion() {
      this.showCompletion = !this.showCompletion
      localStorage.setItem('showCompletion', String(this.showCompletion))
    },
    async loadGroups(type) {
      if (this.showMode === type) return
      if (this.groupsCache[type]) {
        this.groups = this.groupsCache[type]
        this.showMode = type
        return
      }
      this.loading = true
      try {
        const res = await getGroups(type)
        this.groups = res.data.groups
        this.groupsCache[type] = res.data.groups
        this.showMode = type
      } catch (e) {
        console.error('Failed to load groups:', e)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.search-clear {
  background: none;
  border: none;
  color: rgba(228, 251, 255, 0.4);
  cursor: pointer;
  font-size: 13px;
  padding: 0 2px;
  line-height: 1;
  transition: color 0.15s;
}
.search-clear:hover { color: rgba(228, 251, 255, 0.9); }

/* ── 分組 / 檢視樣式控制列 ── */
.view-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  flex-wrap: wrap;
  margin: 4px 0 14px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(228, 251, 255, 0.4);
}

.group-select {
  padding: 5px 30px 5px 12px;
  font-size: 14px;
  font-family: inherit;
  color: rgba(228, 251, 255, 0.92);
  background-color: rgba(60, 40, 75, 0.5);
  background-image: linear-gradient(45deg, transparent 50%, rgba(228,251,255,0.6) 50%),
                    linear-gradient(135deg, rgba(228,251,255,0.6) 50%, transparent 50%);
  background-position: calc(100% - 15px) 52%, calc(100% - 10px) 52%;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  border: 1px solid rgba(228, 251, 255, 0.25);
  border-radius: 6px;
  cursor: pointer;
  appearance: none;
  transition: border-color 0.15s, background-color 0.15s;
}

.group-select:hover,
.group-select:focus {
  border-color: rgba(228, 251, 255, 0.55);
  background-color: rgba(100, 70, 120, 0.55);
  outline: none;
}

.group-select option {
  background: rgb(30, 20, 40);
  color: #e4fbff;
}

.style-switch {
  display: flex;
  gap: 3px;
  padding: 2px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 8px;
}

.style-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 11px;
  font-size: 13px;
  font-family: inherit;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: rgba(228, 251, 255, 0.5);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.style-button:hover {
  color: rgba(228, 251, 255, 0.85);
  background: rgba(228, 251, 255, 0.07);
}

.style-button.active {
  background: rgba(228, 251, 255, 0.16);
  color: #e4fbff;
}

.style-text {
  font-size: 12px;
}

@media (max-width: 560px) {
  .style-text { display: none; }
  .view-controls { gap: 14px; }
}

/* ── 完成度圖例 ── */
.completion-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  margin: 4px 0 14px;
  font-size: 12px;
  color: rgba(228, 251, 255, 0.5);
}

.legend-toggle {
  padding: 3px 12px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 999px;
  background: transparent;
  color: rgba(228, 251, 255, 0.5);
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.legend-toggle:hover,
.legend-toggle.active {
  border-color: rgba(228, 251, 255, 0.45);
  color: rgba(228, 251, 255, 0.85);
  background: rgba(228, 251, 255, 0.06);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.legend-dot--image {
  background: #45d0e0;
  box-shadow: 0 0 5px rgba(69, 208, 224, 0.9);
}

.legend-dot--story {
  background: #6ee76e;
  box-shadow: 0 0 5px rgba(110, 231, 110, 0.9);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

</style>
