<template>
  <div class="elements-box">
    <div
      v-for="elt in elements"
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
</template>

<script>
export default {
  props: {
    elements: { type: Array, required: true }
  }
}
</script>
