<template>
  <div class="molecules">
    <LoadingSpinner v-if="loading" />

    <p class="title">{{ metaText("molecules", "title") }}</p>
    <p v-if="metaText('molecules', 'subtitle')" class="page-subtitle">{{ metaText("molecules", "subtitle") }}</p>

    <div class="search-bar">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input class="search-input" v-model="query" aria-label="搜尋分子" autocomplete="off" />
      <button v-if="query" class="search-clear" @click="query = ''" title="Clear">✕</button>
    </div>

    <p v-if="element" class="filter-note">
      {{ filterNote }}
      <router-link to="/molecules">查看全部</router-link>
    </p>

    <div v-if="!loading && !filtered.length" class="no-results">
      {{ molecules.length ? `沒有符合「${query}」的分子` : metaText('molecules', 'empty_text') }}
    </div>

    <div v-else class="molecule-grid">
      <router-link
        v-for="m in filtered"
        :key="m.slug"
        class="molecule-card"
        :to="'/molecule/' + m.slug"
      >
        <span class="mc-formula" v-html="subscript(m.formula)"></span>
        <span class="mc-name">{{ m.name }}</span>
        <span v-if="!m.published" class="mc-draft">草稿</span>
        <span class="mc-elements">
          <i v-for="sym in m.elements" :key="sym" class="mc-element">{{ sym }}</i>
        </span>
      </router-link>
    </div>
  </div>
</template>

<script>
import { getMolecules } from '../api'
import { ensurePageMeta, metaText } from '../store/pageMeta'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const SUBSCRIPTS = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']

export default {
  components: { LoadingSpinner },
  props: {
    // 從元素頁的「查看更多」帶過來，只列含該元素的分子
    element: { type: String, default: '' }
  },
  data() {
    return { molecules: [], query: '', loading: false }
  },
  computed: {
    filterNote() {
      return metaText('molecules', 'filter_note').replace('{element}', this.element)
    },
    filtered() {
      const q = this.query.trim().toLowerCase()
      if (!q) return this.molecules
      return this.molecules.filter(m =>
        m.name?.toLowerCase().includes(q) ||
        m.formula?.toLowerCase().includes(q) ||
        m.slug?.includes(q)
      )
    }
  },
  watch: {
    element: { immediate: true, handler: 'load' }
  },
  created() {
    ensurePageMeta()
  },
  methods: {
    metaText,
    async load() {
      this.loading = true
      try {
        const res = await getMolecules(this.element ? { element: this.element } : {})
        this.molecules = res.data.molecules || []
      } catch (e) {
        console.error('Failed to load molecules:', e)
        this.molecules = []
      } finally {
        this.loading = false
      }
    },
    // 分子式的數字轉下標；formula 只含英數與括號，不會有 HTML
    subscript(formula) {
      return String(formula || '').replace(/\d/g, d => `<sub>${d}</sub>`)
    }
  }
}
</script>

<style scoped>
.molecules {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px 18px 40px;
}

.page-subtitle {
  text-align: center;
  font-size: 14px;
  color: rgba(228, 251, 255, 0.55);
  margin: 6px 0 18px;
  white-space: pre-wrap;
}

.filter-note {
  text-align: center;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.55);
  margin: 0 0 14px;
}

.filter-note a {
  color: rgba(228, 251, 255, 0.8);
  margin-left: 8px;
}

.molecule-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.molecule-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 16px 18px;
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 10px;
  background: rgba(20, 5, 35, 0.5);
  text-decoration: none;
  transition: transform 0.15s, border-color 0.15s, background 0.15s;
}

.molecule-card:hover {
  transform: translateY(-2px);
  border-color: rgba(228, 251, 255, 0.4);
  background: rgba(60, 40, 75, 0.55);
}

.mc-formula {
  font-size: 24px;
  font-weight: 700;
  color: #e4fbff;
  line-height: 1.2;
}

.mc-formula :deep(sub) {
  font-size: 0.6em;
  vertical-align: baseline;
  position: relative;
  bottom: -0.2em;
}

.mc-name {
  font-size: 14px;
  color: rgba(228, 251, 255, 0.75);
}

.mc-draft {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 10px;
  color: #ffc46b;
  border: 1px solid rgba(255, 196, 107, 0.4);
  border-radius: 999px;
  padding: 1px 7px;
}

.mc-elements {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.mc-element {
  font-size: 11px;
  font-style: normal;
  padding: 1px 7px;
  border-radius: 999px;
  background: rgba(228, 251, 255, 0.1);
  color: rgba(228, 251, 255, 0.6);
}
</style>
