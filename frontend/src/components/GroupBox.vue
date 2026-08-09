<template>
  <div v-for="groupName in uniqueGroups" :key="groupName" class="group-box">
    <div class="group-title">{{ groupName.toUpperCase() }}</div>
    <ElementListView
      v-if="viewStyle === 'list'"
      :elements="groupedElements(groupName)"
      :groups="groups"
      :completion="completion"
    />
    <ElementIconGrid
      v-else
      :elements="groupedElements(groupName)"
      :size="viewStyle"
      :completion="completion"
    />
  </div>
</template>

<script>
import ElementIconGrid from './ElementIconGrid.vue'
import ElementListView from './ElementListView.vue'

export default {
  components: { ElementIconGrid, ElementListView },
  props: {
    elements: { type: Array, required: true },
    groups: { type: Object, required: true },
    // large | small | list
    viewStyle: { type: String, default: 'large' },
    completion: { type: Object, default: null }
  },
  computed: {
    uniqueGroups() {
      return [...new Set(Object.values(this.groups))]
    }
  },
  methods: {
    groupedElements(groupName) {
      return this.elements.filter(elt => this.groups[elt.Symbol] === groupName)
    }
  }
}
</script>
