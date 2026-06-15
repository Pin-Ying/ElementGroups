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

    <transition name="fade" mode="out-in">
      <div v-if="showMode === 'table'" key="table">
        <div v-if="filteredElements.length === 0" class="no-results">No elements match "{{ query }}"</div>
        <PeriodicTableGrid v-else :elements="filteredElements" />
      </div>
      <div v-else-if="showMode === 'none'" key="none" id="non-group">
        <div v-if="filteredElements.length === 0" class="no-results">No elements match "{{ query }}"</div>
        <PeriodicTable v-else :elements="filteredElements" />
      </div>
      <div v-else key="group" id="group">
        <div v-if="filteredElements.length === 0" class="no-results">No elements match "{{ query }}"</div>
        <GroupBox v-else :elements="filteredElements" :groups="groups" />
      </div>
    </transition>
  </div>
</template>

<script>
import { getElements, getGroups } from '../api'
import { elementsState } from '../store/elements'
import PeriodicTableGrid from '../components/PeriodicTableGrid.vue'
import PeriodicTable from '../components/PeriodicTable.vue'
import GroupBox from '../components/GroupBox.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { PeriodicTableGrid, PeriodicTable, GroupBox, LoadingSpinner },
  data() {
    return {
      elements: [],
      groups: {},
      groupsCache: {},
      showMode: 'table',
      loading: false,
      query: ''
    }
  },
  computed: {
    filteredElements() {
      const q = this.query.trim().toLowerCase()
      if (!q) return this.elements
      return this.elements.filter(e =>
        e.Name?.toLowerCase().includes(q) ||
        e.Symbol?.toLowerCase().includes(q) ||
        String(e.AtomicNumber) === q
      )
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
  },
  methods: {
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
