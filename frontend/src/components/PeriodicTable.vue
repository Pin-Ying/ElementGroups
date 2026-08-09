<template>
  <div class="elements-box">
    <div
      v-for="elt in elements"
      :key="elt.Symbol"
      class="element"
      :data-name="elt.Name"
      :style="{ borderColor: '#' + elt.CPKHexColor }"
    >
      <router-link :to="'/stroy/' + elt.Symbol">
        <span class="el-num">{{ elt.AtomicNumber }}</span>
        <span class="el-sym">{{ elt.Symbol }}</span>
        <span class="el-name">{{ elt.Name }}</span>
      </router-link>
      <CompletionDots v-if="completion" :state="completion[elt.Symbol]" />
    </div>
  </div>
</template>

<script>
import CompletionDots from './CompletionDots.vue'

export default {
  components: { CompletionDots },
  props: {
    elements: { type: Array, required: true },
    // { Symbol: {story, image} }；不傳則不顯示完成度標記
    completion: { type: Object, default: null }
  }
}
</script>
