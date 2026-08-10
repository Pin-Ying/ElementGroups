<template>
  <section v-if="molecules.length" class="related">
    <h2 class="related-title">{{ metaText("story", "molecules_title") }}</h2>

    <div class="related-list">
      <router-link
        v-for="m in molecules"
        :key="m.slug"
        class="related-card"
        :to="'/molecule/' + m.slug"
        :style="{ borderColor: '#' + color }"
      >
        <span class="rc-formula" v-html="subscript(m.formula)"></span>
        <span class="rc-name">{{ m.name }}</span>
      </router-link>
    </div>

    <router-link
      v-if="total > molecules.length"
      class="related-more"
      :to="{ path: '/molecules', query: { element: symbol } }"
    >查看全部 {{ total }} 個 →</router-link>
  </section>
</template>

<script>
// 元素頁下方列出含有該元素的分子。依回饋只顯示最近五個，其餘用「查看更多」
// 導到分子圖鑑的篩選結果——像氫這種元素會出現在非常多分子裡。
import { getMolecules } from '../api'
import { ensurePageMeta, metaText } from '../store/pageMeta'

const LIMIT = 5
const cache = new Map()

export default {
  props: {
    symbol: { type: String, required: true },
    color: { type: String, default: '64b8e8' }
  },
  data() {
    return { molecules: [], total: 0 }
  },
  watch: {
    symbol: { immediate: true, handler: 'load' }
  },
  created() {
    ensurePageMeta()
  },
  methods: {
    metaText,
    async load(symbol) {
      if (!symbol) return
      if (cache.has(symbol)) {
        const cached = cache.get(symbol)
        this.molecules = cached.molecules
        this.total = cached.total
        return
      }
      try {
        const res = await getMolecules({ element: symbol, limit: LIMIT })
        const data = { molecules: res.data.molecules || [], total: res.data.total || 0 }
        cache.set(symbol, data)
        // 回來得比切換慢時不要覆蓋當前元素
        if (this.symbol === symbol) {
          this.molecules = data.molecules
          this.total = data.total
        }
      } catch {
        if (this.symbol === symbol) { this.molecules = []; this.total = 0 }
      }
    },
    subscript(formula) {
      return String(formula || '').replace(/\d/g, d => `<sub>${d}</sub>`)
    }
  }
}
</script>

<style scoped>
.related {
  margin: 26px auto 0;
  width: 100%;
}

.related-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: rgba(228, 251, 255, 0.5);
  text-align: left;
  margin: 0 0 12px;
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.12);
}

.related-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.related-card {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 16px;
  border: 1px solid;
  border-radius: 8px;
  background: rgba(20, 5, 35, 0.5);
  text-decoration: none;
  transition: transform 0.15s, background 0.15s;
}

.related-card:hover {
  transform: translateY(-2px);
  background: rgba(60, 40, 75, 0.6);
}

.rc-formula {
  font-size: 18px;
  font-weight: 700;
  color: #e4fbff;
}

.rc-formula :deep(sub) {
  font-size: 0.6em;
  vertical-align: baseline;
  position: relative;
  bottom: -0.2em;
}

.rc-name {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.65);
}

.related-more {
  display: inline-block;
  margin-top: 12px;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.6);
  text-decoration: none;
}

.related-more:hover { color: #e4fbff; }
</style>
