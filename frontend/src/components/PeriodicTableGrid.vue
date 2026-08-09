<template>
  <div class="pt-wrapper">
    <div class="pt-grid">
      <!-- 鑭系 / 錒系佔位標示 -->
      <div class="pt-ref" :style="{ gridRow: 6, gridColumn: 3 }">57–71</div>
      <div class="pt-ref" :style="{ gridRow: 7, gridColumn: 3 }">89–103</div>

      <div
        v-for="elt in positioned"
        :key="elt.Symbol"
        class="element"
        :data-name="elt.Name"
        :style="{
          gridRow: elt.row,
          gridColumn: elt.col,
          borderColor: '#' + elt.CPKHexColor
        }"
      >
        <router-link :to="'/stroy/' + elt.Symbol">
          <span class="el-num">{{ elt.AtomicNumber }}</span>
          <span class="el-sym">{{ elt.Symbol }}</span>
        </router-link>
        <CompletionDots v-if="completion" :state="completion[elt.Symbol]" />
      </div>
    </div>
  </div>
</template>

<script>
// AtomicNumber → [row, col]  (row 8 = 間隔; row 9 = 鑭系; row 10 = 錒系)
const POSITION = {
  1: [1,1], 2: [1,18],
  3: [2,1], 4: [2,2], 5: [2,13], 6: [2,14], 7: [2,15], 8: [2,16], 9: [2,17], 10: [2,18],
  11: [3,1], 12: [3,2], 13: [3,13], 14: [3,14], 15: [3,15], 16: [3,16], 17: [3,17], 18: [3,18],
  19: [4,1], 20: [4,2], 21: [4,3], 22: [4,4], 23: [4,5], 24: [4,6], 25: [4,7],
  26: [4,8], 27: [4,9], 28: [4,10], 29: [4,11], 30: [4,12], 31: [4,13], 32: [4,14],
  33: [4,15], 34: [4,16], 35: [4,17], 36: [4,18],
  37: [5,1], 38: [5,2], 39: [5,3], 40: [5,4], 41: [5,5], 42: [5,6], 43: [5,7],
  44: [5,8], 45: [5,9], 46: [5,10], 47: [5,11], 48: [5,12], 49: [5,13], 50: [5,14],
  51: [5,15], 52: [5,16], 53: [5,17], 54: [5,18],
  55: [6,1], 56: [6,2],
  72: [6,4], 73: [6,5], 74: [6,6], 75: [6,7], 76: [6,8], 77: [6,9], 78: [6,10],
  79: [6,11], 80: [6,12], 81: [6,13], 82: [6,14], 83: [6,15], 84: [6,16], 85: [6,17], 86: [6,18],
  87: [7,1], 88: [7,2],
  104: [7,4], 105: [7,5], 106: [7,6], 107: [7,7], 108: [7,8], 109: [7,9], 110: [7,10],
  111: [7,11], 112: [7,12], 113: [7,13], 114: [7,14], 115: [7,15], 116: [7,16], 117: [7,17], 118: [7,18],
  57: [9,3], 58: [9,4], 59: [9,5], 60: [9,6], 61: [9,7], 62: [9,8], 63: [9,9],
  64: [9,10], 65: [9,11], 66: [9,12], 67: [9,13], 68: [9,14], 69: [9,15], 70: [9,16], 71: [9,17],
  89: [10,3], 90: [10,4], 91: [10,5], 92: [10,6], 93: [10,7], 94: [10,8], 95: [10,9],
  96: [10,10], 97: [10,11], 98: [10,12], 99: [10,13], 100: [10,14], 101: [10,15], 102: [10,16], 103: [10,17],
}

import CompletionDots from './CompletionDots.vue'

export default {
  components: { CompletionDots },
  props: {
    elements: { type: Array, required: true },
    // { Symbol: {story, image} }；不傳則不顯示完成度標記
    completion: { type: Object, default: null }
  },
  computed: {
    positioned() {
      return this.elements
        .filter(e => POSITION[Number(e.AtomicNumber)])
        .map(e => ({
          ...e,
          row: POSITION[Number(e.AtomicNumber)][0],
          col: POSITION[Number(e.AtomicNumber)][1],
        }))
    }
  }
}
</script>

<style scoped>
.pt-wrapper {
  width: 100%;
  overflow-x: auto;
  padding: 6px 4px 16px;
  -webkit-overflow-scrolling: touch;
}

.pt-grid {
  display: grid;
  grid-template-columns: repeat(18, minmax(0, 1fr));
  grid-template-rows: repeat(7, auto) 10px repeat(2, auto);
  gap: 3px;
  min-width: 580px;
  max-width: 1320px;
  width: 100%;
  margin: 0 auto;
}

.pt-grid .element {
  width: 100%;
  height: auto;
  aspect-ratio: 1 / 1;
  font-size: clamp(6px, 1vw, 13px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pt-grid .element a {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: 1px;
  text-decoration: none;
  color: #fff;
}

.el-num {
  font-size: 0.6em;
  opacity: 0.6;
  line-height: 1;
}

.el-sym {
  font-size: 1em;
  font-weight: 700;
  line-height: 1;
}

.pt-ref {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(228, 251, 255, 0.3);
  border-radius: 6px;
  background-color: rgba(80, 65, 80, 0.35);
  color: rgba(255, 255, 255, 0.45);
  aspect-ratio: 1 / 1;
  font-size: clamp(5px, 0.65vw, 9px);
}
</style>
