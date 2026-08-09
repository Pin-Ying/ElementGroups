<template>
  <div class="icon-grid" :class="'icon-grid--' + size">
    <router-link
      v-for="elt in elements"
      :key="elt.Symbol"
      class="icon-card"
      :to="'/stroy/' + elt.Symbol"
      :style="{ borderColor: '#' + elt.CPKHexColor }"
    >
      <span class="ic-num">{{ elt.AtomicNumber }}</span>
      <span class="ic-sym" :style="{ color: '#' + elt.CPKHexColor }">{{ elt.Symbol }}</span>
      <span v-if="size === 'large'" class="ic-name">{{ elt.Name }}</span>
      <CompletionDots v-if="completion" :state="completion[elt.Symbol]" />
    </router-link>
  </div>
</template>

<script>
import CompletionDots from './CompletionDots.vue'

export default {
  components: { CompletionDots },
  props: {
    elements: { type: Array, required: true },
    // large = 大圖示、small = 小圖示
    size: { type: String, default: 'large' },
    completion: { type: Object, default: null }
  }
}
</script>

<style scoped>
.icon-grid {
  display: grid;
  gap: 8px;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 8px 16px;
  justify-content: center;
}

.icon-grid--large {
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
}

.icon-grid--small {
  grid-template-columns: repeat(auto-fill, minmax(58px, 1fr));
  gap: 5px;
}

.icon-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  border: 1px solid;
  border-radius: 8px;
  background: rgba(60, 40, 75, 0.45);
  text-decoration: none;
  color: rgba(228, 251, 255, 0.85);
  transition: transform 0.15s, background 0.15s, box-shadow 0.15s;
}

.icon-card:hover {
  transform: scale(1.06);
  background: rgba(100, 70, 120, 0.7);
  box-shadow: 0 0 16px rgba(228, 251, 255, 0.25);
  z-index: 5;
}

.icon-grid--large .icon-card {
  padding: 12px 6px;
  min-height: 92px;
}

.icon-grid--small .icon-card {
  padding: 8px 4px;
  min-height: 54px;
}

.ic-num {
  font-size: 10px;
  opacity: 0.5;
  line-height: 1;
}

.icon-grid--large .ic-sym {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.15;
}

.icon-grid--small .ic-sym {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.15;
}

.ic-name {
  font-size: 11px;
  opacity: 0.72;
  text-align: center;
  line-height: 1.2;
  word-break: break-word;
}
</style>
