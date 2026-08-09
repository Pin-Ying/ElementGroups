<template>
  <div class="profile">
    <div v-for="item in items" :key="item.label" class="profile-item">
      <span class="profile-label">{{ item.label }}</span>
      <span class="profile-value">{{ item.value }}</span>
    </div>
  </div>
</template>

<script>
// 週期表資料裡原本就有、但頁面一直沒用到的欄位。
// 對應寶可夢圖鑑的身高／體重／分類那一區。
const FIELDS = [
  { key: 'GroupBlock', label: '分類' },
  { key: 'AtomicMass', label: '原子量', unit: 'u' },
  { key: 'StandardState', label: '常溫狀態' },
  { key: 'ElectronConfiguration', label: '電子組態' },
  { key: 'OxidationStates', label: '常見氧化態' },
  { key: 'YearDiscovered', label: '發現年份' }
]

export default {
  props: {
    elInfo: { type: Object, required: true }
  },
  computed: {
    items() {
      return FIELDS
        .map(f => {
          const raw = this.elInfo?.[f.key]
          if (raw === undefined || raw === null || raw === '') return null
          const value = f.unit ? `${raw} ${f.unit}` : String(raw)
          return { label: f.label, value }
        })
        .filter(Boolean)
    }
  }
}
</script>

<style scoped>
.profile {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1px;
  background: rgba(228, 251, 255, 0.08);
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  overflow: hidden;
  margin: 5px auto 12px;
  width: 100%;
  box-sizing: border-box;
}

.profile-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 14px;
  background: rgba(20, 5, 35, 0.55);
  text-align: left;
}

.profile-label {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(228, 251, 255, 0.42);
}

.profile-value {
  font-size: 14px;
  color: rgba(228, 251, 255, 0.92);
  word-break: break-word;
}
</style>
