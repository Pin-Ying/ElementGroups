<template>
  <div class="list-wrap">
    <table class="element-table">
      <thead>
        <tr>
          <th class="col-num">#</th>
          <th class="col-sym">符號</th>
          <th>名稱</th>
          <th class="col-group">分類</th>
          <th class="col-mass">原子量</th>
          <th class="col-state">常溫狀態</th>
          <th v-if="completion" class="col-done">完成度</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="elt in elements" :key="elt.Symbol" @click="$router.push('/story/' + elt.Symbol)">
          <td class="col-num">{{ elt.AtomicNumber }}</td>
          <td class="col-sym">
            <span class="sym-badge" :style="{ borderColor: '#' + elt.CPKHexColor, color: '#' + elt.CPKHexColor }">
              {{ elt.Symbol }}
            </span>
          </td>
          <td>{{ elt.Name }}</td>
          <td class="col-group">{{ groups[elt.Symbol] || '—' }}</td>
          <td class="col-mass">{{ elt.AtomicMass || '—' }}</td>
          <td class="col-state">{{ elt.StandardState || '—' }}</td>
          <td v-if="completion" class="col-done">
            <span v-if="hasDone(elt.Symbol)" class="done-dots">
              <i v-if="completion[elt.Symbol].image" class="done-dot done-dot--image" title="已上傳圖片"></i>
              <i v-if="completion[elt.Symbol].story" class="done-dot done-dot--story" title="已寫故事"></i>
            </span>
            <span v-else class="done-empty">—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  props: {
    elements: { type: Array, required: true },
    groups: { type: Object, default: () => ({}) },
    completion: { type: Object, default: null }
  },
  methods: {
    hasDone(symbol) {
      const state = this.completion?.[symbol]
      return !!(state && (state.story || state.image))
    }
  }
}
</script>

<style scoped>
.list-wrap {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  overflow-x: auto;
  padding: 0 8px 16px;
}

.element-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  text-align: left;
  min-width: 620px;
}

.element-table th {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: rgba(228, 251, 255, 0.45);
  padding: 8px 10px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.15);
  white-space: nowrap;
}

.element-table td {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.06);
  color: rgba(228, 251, 255, 0.82);
}

.element-table tbody tr {
  cursor: pointer;
  transition: background 0.12s;
}

.element-table tbody tr:hover {
  background: rgba(100, 70, 120, 0.35);
}

.col-num {
  width: 52px;
  color: rgba(228, 251, 255, 0.45);
  font-variant-numeric: tabular-nums;
}

.col-sym { width: 68px; }
.col-group { white-space: nowrap; }
.col-mass { width: 90px; font-variant-numeric: tabular-nums; }
.col-state { width: 90px; }
.col-done { width: 80px; }

.sym-badge {
  display: inline-block;
  min-width: 34px;
  text-align: center;
  padding: 2px 6px;
  border: 1px solid;
  border-radius: 5px;
  font-weight: 700;
  background: rgba(60, 40, 75, 0.5);
}

.done-dots {
  display: inline-flex;
  gap: 5px;
  align-items: center;
}

.done-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}

.done-dot--image {
  background: #45d0e0;
  box-shadow: 0 0 5px rgba(69, 208, 224, 0.9);
}

.done-dot--story {
  background: #6ee76e;
  box-shadow: 0 0 5px rgba(110, 231, 110, 0.9);
}

.done-empty { opacity: 0.25; }
</style>
