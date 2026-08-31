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

    <!-- 只有一種分類時不顯示篩選列，那時候按鈕沒有作用 -->
    <div v-if="!loading && categoryChips.length > 1" class="cat-filter">
      <button
        class="cat-chip"
        :class="{ active: !activeCategory }"
        type="button"
        @click="activeCategory = ''"
      >全部<i class="cat-num">{{ filtered.length }}</i></button>
      <button
        v-for="c in categoryChips"
        :key="c.category"
        class="cat-chip"
        :class="{ active: activeCategory === c.category }"
        type="button"
        :title="categoryHint(c.category)"
        @click="activeCategory = activeCategory === c.category ? '' : c.category"
      >{{ c.category }}<i class="cat-num">{{ c.count }}</i></button>
    </div>

    <div v-if="!loading && !filtered.length" class="no-results">
      {{ molecules.length ? `沒有符合「${query}」的分子` : metaText('molecules', 'empty_text') }}
    </div>

    <template v-else>
      <section v-for="g in groups" :key="g.category" class="cat-section">
        <!-- 已經用篩選鎖定單一分類時，標題是多餘的重複 -->
        <h2 v-if="!activeCategory" class="cat-heading">
          {{ g.category }}
          <span class="cat-count">{{ g.molecules.length }}</span>
          <span v-if="categoryHint(g.category)" class="cat-hint">{{ categoryHint(g.category) }}</span>
        </h2>

        <div class="molecule-grid">
          <router-link
            v-for="m in g.molecules"
            :key="m.slug"
            class="molecule-card"
            :to="'/molecule/' + m.slug"
          >
            <span class="mc-formula" v-html="subscript(m.formula)"></span>
            <span class="mc-name">{{ m.name }}</span>
            <span v-if="!m.published" class="mc-draft">草稿</span>
            <span class="mc-elements">
              <i
                v-for="sym in m.elements"
                :key="sym"
                class="mc-element"
                :class="'mc-element--' + (metallicity(sym) || 'unknown')"
              >{{ sym }}</i>
            </span>
          </router-link>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import { getMolecules } from '../api'
import { ensurePageMeta, metaText } from '../store/pageMeta'
import { siteSettingsState } from '../store/siteSettings'
import { setPageSeo } from '../utils/seo'
import { groupByCategory, metallicity, CATEGORY_HINTS } from '../utils/moleculeCategory'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const SUBSCRIPTS = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']

export default {
  components: { LoadingSpinner },
  props: {
    // 從元素頁的「查看更多」帶過來，只列含該元素的分子
    element: { type: String, default: '' }
  },
  data() {
    return { molecules: [], query: '', loading: false, activeCategory: '' }
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
    },
    // 搜尋之後、套用分類篩選之前的分組。篩選列的數字要以它為準，
    // 不然點了某一類之後其他類的數字全部歸零，看起來像資料不見了
    allGroups() {
      return groupByCategory(this.filtered)
    },
    categoryChips() {
      return this.allGroups.map(g => ({ category: g.category, count: g.molecules.length }))
    },
    groups() {
      if (!this.activeCategory) return this.allGroups
      return this.allGroups.filter(g => g.category === this.activeCategory)
    }
  },
  watch: {
    element: { immediate: true, handler: 'load' },
    // 搜尋把目前選中的分類整個濾掉時，畫面會變成一片空白但篩選列上
    // 那一類已經不見了，使用者沒有東西可以點回來。這裡自動退回「全部」
    categoryChips(chips) {
      if (this.activeCategory && !chips.some(c => c.category === this.activeCategory)) {
        this.activeCategory = ''
      }
    }
  },
  async created() {
    await ensurePageMeta()
    const title = metaText('molecules', 'title')
    setPageSeo({
      title: `${title}｜${siteSettingsState.title}`,
      description: metaText('molecules', 'subtitle') || title,
      // 帶 ?element= 只是同一份清單的篩選，canonical 一律指回沒有參數的網址，
      // 免得 118 個篩選結果被當成 118 個重複頁面
      path: '/molecules'
    })
  },
  methods: {
    metaText,
    metallicity,
    // 自訂分類（後台手填的）不會有說明，回空字串讓 v-if 收掉
    categoryHint(category) {
      return CATEGORY_HINTS[category] || ''
    },
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

/* 元素標籤依金屬性上色，讓卡片自己說明它為什麼被分到這一類。
   色相刻意壓得很淡：這是輔助資訊，不該比分子式還搶眼 */
.mc-element--metal {
  background: rgba(255, 196, 107, 0.14);
  color: rgba(255, 214, 150, 0.85);
}

.mc-element--metalloid {
  background: rgba(201, 163, 255, 0.16);
  color: rgba(214, 186, 255, 0.85);
}

.mc-element--nonmetal {
  background: rgba(127, 227, 255, 0.13);
  color: rgba(160, 235, 255, 0.8);
}

/* 分類篩選列 */
.cat-filter {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin: 16px 0 4px;
}

.cat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 13px;
  font-size: 13px;
  font-family: inherit;
  color: rgba(228, 251, 255, 0.6);
  background: rgba(20, 5, 35, 0.5);
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 999px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.cat-chip:hover {
  color: rgba(228, 251, 255, 0.85);
  border-color: rgba(228, 251, 255, 0.35);
}

.cat-chip.active {
  color: #e4fbff;
  border-color: rgba(228, 251, 255, 0.55);
  background: rgba(60, 40, 75, 0.55);
}

.cat-num {
  font-size: 11px;
  font-style: normal;
  opacity: 0.65;
}

/* 分類分組 */
.cat-section + .cat-section {
  margin-top: 26px;
}

.cat-heading {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
  margin: 22px 0 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.12);
  font-size: 15px;
  font-weight: 600;
  color: rgba(228, 251, 255, 0.9);
}

.cat-count {
  font-size: 12px;
  font-weight: 400;
  color: rgba(228, 251, 255, 0.45);
}

.cat-hint {
  font-size: 12px;
  font-weight: 400;
  color: rgba(228, 251, 255, 0.4);
}

/* 手機上說明文字換行會把標題撐得很高，收起來讓分類名稱自己講 */
@media (max-width: 600px) {
  .cat-hint {
    display: none;
  }
}
</style>
