<template>
  <div class="elements-box">
    <div
      v-for="elt in elements"
      :key="elt.Symbol"
      class="element"
      :style="{ borderColor: '#' + elt.CPKHexColor }"
    >
      <router-link :to="'/stroy/' + elt.Symbol">
        {{ elt.AtomicNumber }}<br />{{ elt.Symbol }}
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
