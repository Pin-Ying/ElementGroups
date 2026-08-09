<template>
  <div class="stat-panel">
    <div class="stat-list">
      <div v-for="ab in abilities" :key="ab.key" class="stat-row">
        <span class="stat-label">{{ ab.label }}</span>
        <div class="stat-track">
          <div
            class="stat-fill"
            :style="{ width: barWidth(ab.key), background: gradientFor }"
          ></div>
        </div>
        <span class="stat-value">{{ displayValue(ab) }}</span>
      </div>
    </div>
    <p class="stat-note">長條長度為該項目在 118 個元素中的相對比例</p>
  </div>
</template>

<script>
// 對應寶可夢圖鑑的能力值列表
export const ABILITIES = [
  { key: 'MeltingPoint', label: '熔點', unit: 'K' },
  { key: 'BoilingPoint', label: '沸點', unit: 'K' },
  { key: 'ElectronAffinity', label: '電子親和力', unit: 'eV' },
  { key: 'Electronegativity', label: '電負度', unit: '' },
  { key: 'AtomicRadius', label: '原子半徑', unit: 'pm' },
  { key: 'IonizationEnergy', label: '游離能', unit: 'eV' },
  { key: 'Density', label: '密度', unit: 'g/cm³' }
]

export default {
  props: {
    elInfo: { type: Object, required: true },
    color: { type: String, default: '64b8e8' }
  },
  data() {
    return { abilities: ABILITIES }
  },
  computed: {
    gradientFor() {
      // 用該元素的 CPK 顏色做漸層，讓每個元素的頁面有各自的識別色
      return `linear-gradient(90deg, #${this.color}55, #${this.color})`
    }
  },
  methods: {
    barWidth(key) {
      const max = this.elInfo?.abMax?.[key]
      const value = Number(this.elInfo?.[key])
      if (!max || isNaN(value)) return '0%'
      const pct = Math.max(0, Math.min(100, (value / max) * 100))
      return pct + '%'
    },
    displayValue(ab) {
      const raw = this.elInfo?.[ab.key]
      if (raw === undefined || raw === null || raw === '') return '—'
      const num = Number(raw)
      if (isNaN(num)) return String(raw)
      const text = num >= 100 ? num.toFixed(0) : num.toFixed(2).replace(/\.?0+$/, '')
      return ab.unit ? `${text} ${ab.unit}` : text
    }
  }
}
</script>

<style scoped>
.stat-panel {
  width: 100%;
  margin: 5px auto;
  padding: 18px 20px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 8px;
  box-shadow: 0 0 24px rgba(80, 0, 160, 0.15), 0 0 48px rgba(0, 100, 200, 0.08);
  background: rgba(20, 5, 35, 0.35);
  box-sizing: border-box;
}

.stat-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-row {
  display: grid;
  grid-template-columns: 100px 1fr 92px;
  align-items: center;
  gap: 12px;
}

.stat-label {
  font-size: 13px;
  color: rgba(228, 251, 255, 0.7);
  text-align: left;
  white-space: nowrap;
}

.stat-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(228, 251, 255, 0.08);
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}

.stat-value {
  font-size: 13px;
  text-align: right;
  color: rgba(228, 251, 255, 0.9);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stat-note {
  font-size: 11px;
  opacity: 0.35;
  margin: 14px 0 0;
  text-align: center;
}

@media (max-width: 600px) {
  .stat-panel { padding: 14px 12px; }
  .stat-row {
    grid-template-columns: 78px 1fr 76px;
    gap: 8px;
  }
  .stat-label, .stat-value { font-size: 12px; }
}
</style>
