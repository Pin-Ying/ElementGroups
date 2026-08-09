<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <div class="group-type-button">
      <button class="button" :class="{ active: showMode === 'table' }" @click="showMode = 'table'">Periodic Table</button>
      <button class="button" :class="{ active: showMode === 'none' }" @click="showMode = 'none'">Atomic Number</button>
      <button class="button" :class="{ active: showMode === 'cp' }" @click="loadGroups('cp')">Chemical Properties</button>
      <button class="button" :class="{ active: showMode === 'vs' }" @click="loadGroups('vs')">Valence Shell</button>
    </div>

    <!-- 搜尋列（所有模式都顯示） -->
    <div class="search-bar">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        class="search-input"
        v-model="query"
        placeholder="Search by name, symbol or number…"
        autocomplete="off"
        spellcheck="false"
      />
      <button v-if="query" class="search-clear" @click="query = ''" title="Clear">✕</button>
    </div>

    <ElementHighlights />

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
        <div v-if="query && filteredElements.length === 0" class="no-results">No elements match "{{ query }}"</div>
        <PeriodicTableGrid v-else-if="!isMobile" :elements="filteredElements" :completion="activeCompletion" />
        <GroupBox v-else :elements="filteredElements" :groups="tableGroups" :completion="activeCompletion" />
      </div>
      <div v-else-if="showMode === 'none'" key="none" id="non-group">
        <div v-if="query && filteredElements.length === 0" class="no-results">No elements match "{{ query }}"</div>
        <PeriodicTable v-else :elements="filteredElements" :completion="activeCompletion" />
      </div>
      <div v-else key="group" id="group">
        <div v-if="query && filteredElements.length === 0" class="no-results">No elements match "{{ query }}"</div>
        <GroupBox v-else :elements="filteredElements" :groups="groups" :completion="activeCompletion" />
      </div>
    </transition>

  </div>
</template>

<script>
import { getElements, getGroups, getElementsCompletion } from '../api'
import { elementsState } from '../store/elements'
import { buildTableGroups } from '../utils/periodicTableGroups'
import PeriodicTableGrid from '../components/PeriodicTableGrid.vue'
import PeriodicTable from '../components/PeriodicTable.vue'
import GroupBox from '../components/GroupBox.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ElementHighlights from '../components/ElementHighlights.vue'

export default {
  components: { PeriodicTableGrid, PeriodicTable, GroupBox, LoadingSpinner, ElementHighlights },
  data() {
    return {
      elements: elementsState.elements,
      groups: {},
      groupsCache: {},
      showMode: 'table',
      loading: false,
      query: '',
      isMobile: window.innerWidth < 600,
      completion: {},
      showCompletion: localStorage.getItem('showCompletion') !== 'false'
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
    // 完成度是次要資訊，獨立載入，失敗也不影響週期表顯示
    async loadCompletion() {
      try {
        const res = await getElementsCompletion()
        this.completion = res.data.completion || {}
      } catch (e) {
        console.error('Failed to load completion:', e)
      }
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
