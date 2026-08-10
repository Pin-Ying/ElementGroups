<template>
  <div class="molecule">
    <LoadingSpinner v-if="loading" />

    <template v-if="molecule">
      <header class="dex-head">
        <p class="dex-no">MOLECULE</p>
        <h1 class="dex-name">
          {{ molecule.name }}
          <span class="dex-formula" v-html="subscript(molecule.formula)"></span>
        </h1>
        <p v-if="!molecule.published" class="draft-badge">草稿 — 只有登入後看得到</p>
      </header>

      <div class="dex-body">
        <!-- 左：組成元素，可點回元素頁 -->
        <aside class="dex-tags">
          <p class="dex-label">組成元素</p>
          <router-link
            v-for="sym in molecule.elements"
            :key="sym"
            class="dex-tag"
            :to="'/stroy/' + sym"
            :style="tagStyle(sym)"
          >{{ sym }}<span class="tag-name">{{ elementName(sym) }}</span></router-link>
        </aside>

        <!-- 中：結構圖。沒有自訂圖就用 PubChem 的 -->
        <div class="dex-figure">
          <img
            v-if="imageSrc && !imgBroken"
            :src="imageSrc"
            :alt="molecule.name"
            @error="imgBroken = true"
          />
          <div v-else class="img-placeholder">
            <span class="img-placeholder-sym" v-html="subscript(molecule.formula)"></span>
            <span class="img-placeholder-label">No structure image</span>
          </div>
        </div>

        <!-- 右：基本資料 -->
        <dl class="dex-facts">
          <div v-for="f in facts" :key="f.label" class="dex-fact">
            <dt>{{ f.label }}</dt>
            <dd>{{ f.value }}</dd>
          </div>
        </dl>
      </div>

      <section v-if="molecule.description" class="dex-story">{{ molecule.description }}</section>

      <p class="back-link">
        <router-link to="/molecules">← 回 Molecule Groups</router-link>
      </p>
    </template>

    <div v-else-if="!loading" class="no-results">
      找不到這個分子
      <router-link to="/molecules">回 Molecule Groups</router-link>
    </div>
  </div>
</template>

<script>
import { getMolecule } from '../api'
import { elementsState, ensureElements } from '../store/elements'
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { LoadingSpinner },
  props: { slug: { type: String, required: true } },
  data() {
    return { molecule: null, loading: false, imgBroken: false, elementsState }
  },
  computed: {
    imageSrc() {
      if (!this.molecule) return ''
      // 自訂圖片優先，否則用 PubChem 的 2D 結構圖
      if (this.molecule.img_data) return this.molecule.img_data
      return this.molecule.cid
        ? `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${this.molecule.cid}/PNG`
        : ''
    },
    facts() {
      const m = this.molecule || {}
      return [
        { label: '分子式', value: m.formula },
        { label: '分子量', value: m.weight },
        { label: 'IUPAC 名稱', value: m.iupac_name },
        { label: 'SMILES', value: m.smiles },
        { label: 'PubChem CID', value: m.cid }
      ].filter(f => f.value)
    }
  },
  watch: {
    slug: { immediate: true, handler: 'load' }
  },
  created() {
    ensureElements()
  },
  methods: {
    async load() {
      this.loading = true
      this.molecule = null
      this.imgBroken = false
      try {
        const res = await getMolecule(this.slug)
        this.molecule = res.data
      } catch {
        this.molecule = null
      } finally {
        this.loading = false
      }
    },
    element(symbol) {
      return this.elementsState.elements.find(e => e.Symbol === symbol)
    },
    elementName(symbol) {
      return this.element(symbol)?.Name || ''
    },
    tagStyle(symbol) {
      const color = this.element(symbol)?.CPKHexColor || '64b8e8'
      return {
        borderColor: `#${color}`,
        background: `color-mix(in srgb, #${color} 22%, transparent)`
      }
    },
    subscript(formula) {
      return String(formula || '').replace(/\d/g, d => `<sub>${d}</sub>`)
    }
  }
}
</script>

<style scoped>
.molecule {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px 18px 40px;
}

.dex-head {
  text-align: center;
  margin-bottom: 18px;
}

.dex-no {
  font-size: 13px;
  letter-spacing: 0.22em;
  color: rgba(228, 251, 255, 0.4);
  margin: 0;
}

.dex-name {
  font-size: clamp(24px, 3.6vw, 34px);
  font-weight: 700;
  color: #e4fbff;
  margin: 2px 0 0;
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.dex-formula {
  font-size: 0.72em;
  color: rgba(228, 251, 255, 0.6);
}

.dex-formula :deep(sub),
.img-placeholder-sym :deep(sub) {
  font-size: 0.6em;
  vertical-align: baseline;
  position: relative;
  bottom: -0.2em;
}

.draft-badge {
  display: inline-block;
  font-size: 12px;
  color: #ffc46b;
  border: 1px solid rgba(255, 196, 107, 0.45);
  background: rgba(255, 196, 107, 0.1);
  border-radius: 999px;
  padding: 3px 12px;
  margin: 10px 0 0;
}

.dex-body {
  display: grid;
  grid-template-columns: minmax(150px, 1fr) minmax(240px, 1.5fr) minmax(180px, 1.2fr);
  gap: 22px;
  align-items: center;
}

.dex-tags {
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.dex-label {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: rgba(228, 251, 255, 0.4);
  margin: 0 0 2px;
}

.dex-tag {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 7px 16px;
  border: 1px solid;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 600;
  color: #e4fbff;
  text-decoration: none;
  transition: transform 0.15s;
}

.dex-tag:hover { transform: translateX(3px); }

.tag-name {
  font-size: 12px;
  font-weight: 400;
  color: rgba(228, 251, 255, 0.55);
}

.dex-figure {
  width: 100%;
  min-width: 0;
}

.dex-figure img {
  width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  background: #fff;
}

.img-placeholder {
  width: 100%;
  aspect-ratio: 1 / 1;
  border: 1px dashed rgba(228, 251, 255, 0.25);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.img-placeholder-sym {
  font-size: clamp(28px, 6vw, 48px);
  font-weight: 700;
  color: rgba(228, 251, 255, 0.8);
}

.img-placeholder-label {
  font-size: 12px;
  opacity: 0.45;
}

.dex-facts {
  display: grid;
  gap: 14px;
  margin: 0;
  text-align: left;
}

.dex-fact dt {
  font-size: 11px;
  letter-spacing: 0.12em;
  color: rgba(228, 251, 255, 0.4);
  margin-bottom: 2px;
}

.dex-fact dd {
  font-size: 15px;
  color: rgba(228, 251, 255, 0.92);
  margin: 0;
  word-break: break-all;
}

.dex-story {
  margin-top: 24px;
  padding: 20px 22px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 10px;
  background: rgba(20, 5, 35, 0.4);
  font-size: 16px;
  line-height: 1.95;
  text-align: left;
  white-space: pre-wrap;
}

.back-link {
  text-align: center;
  margin-top: 22px;
}

.back-link a,
.no-results a {
  color: rgba(228, 251, 255, 0.6);
  margin-left: 8px;
}

@media (max-width: 860px) {
  .dex-body { grid-template-columns: 1fr; gap: 18px; }
  .dex-figure { order: -1; width: 100%; max-width: 420px; margin: 0 auto; }
  .dex-facts { grid-template-columns: 1fr 1fr; }
}
</style>
