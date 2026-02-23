<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <div class="group-type-button">
      <button
        class="button"
        :class="{ active: showMode === 'none' }"
        @click="showNone"
      >AtomicNumber</button>
      <button
        class="button"
        :class="{ active: showMode === 'cp' }"
        @click="loadGroups('cp')"
      >Chemical Properties</button>
      <button
        class="button"
        :class="{ active: showMode === 'vs' }"
        @click="loadGroups('vs')"
      >Valence Shell</button>
    </div>

    <transition name="fade" mode="out-in">
      <div v-if="showMode === 'none'" key="none" id="non-group">
        <PeriodicTable :elements="elements" />
      </div>
      <div v-else key="group" id="group">
        <GroupBox :elements="elements" :groups="groups" />
      </div>
    </transition>
  </div>
</template>

<script>
import { getElements, getGroups } from '../api'
import PeriodicTable from '../components/PeriodicTable.vue'
import GroupBox from '../components/GroupBox.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { PeriodicTable, GroupBox, LoadingSpinner },
  data() {
    return {
      elements: [],
      groups: {},
      showMode: 'none',
      loading: false
    }
  },
  async created() {
    this.loading = true
    try {
      const res = await getElements()
      this.elements = res.data.elements
      this.groups = res.data.groups
    } catch (e) {
      console.error('Failed to load elements:', e)
    } finally {
      this.loading = false
    }
  },
  methods: {
    showNone() {
      this.showMode = 'none'
    },
    async loadGroups(type) {
      if (this.showMode === type) return
      this.loading = true
      try {
        const res = await getGroups(type)
        this.groups = res.data.groups
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
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
