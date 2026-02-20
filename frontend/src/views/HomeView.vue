<template>
  <div>
    <div class="group-type-button">
      <button class="button" @click="showMode = 'none'">AtomicNumber</button>
      <button class="button" @click="loadGroups('cp')">Chemical Properties</button>
      <button class="button" @click="loadGroups('vs')">Valence Shell</button>
    </div>

    <!-- Without group -->
    <div v-if="showMode === 'none'" id="non-group">
      <PeriodicTable :elements="elements" />
    </div>

    <!-- With group -->
    <div v-else id="group">
      <GroupBox :elements="elements" :groups="groups" />
    </div>
  </div>
</template>

<script>
import { getElements, getGroups } from '../api'
import PeriodicTable from '../components/PeriodicTable.vue'
import GroupBox from '../components/GroupBox.vue'

export default {
  components: { PeriodicTable, GroupBox },
  data() {
    return {
      elements: [],
      groups: {},
      showMode: 'none'
    }
  },
  async created() {
    try {
      const res = await getElements()
      this.elements = res.data.elements
      this.groups = res.data.groups
    } catch (e) {
      console.error('Failed to load elements:', e)
    }
  },
  methods: {
    async loadGroups(type) {
      try {
        const res = await getGroups(type)
        this.groups = res.data.groups
        this.showMode = 'grouped'
      } catch (e) {
        console.error('Failed to load groups:', e)
      }
    }
  }
}
</script>
