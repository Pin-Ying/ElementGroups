<template>
  <div v-for="groupName in uniqueGroups" :key="groupName" class="group-box">
    <div class="group-title">{{ groupName.toUpperCase() }}</div>
    <div class="elements-box">
      <div
        v-for="elt in groupedElements(groupName)"
        :key="elt.Symbol"
        class="element"
        :style="{ borderColor: '#' + elt.CPKHexColor }"
      >
        <router-link :to="'/stroy/' + elt.Symbol">
          <span class="el-num">{{ elt.AtomicNumber }}</span>
          <span class="el-sym">{{ elt.Symbol }}</span>
          <span class="el-name">{{ elt.Name }}</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    elements: { type: Array, required: true },
    groups: { type: Object, required: true }
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
