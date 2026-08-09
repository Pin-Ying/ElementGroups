<template>
  <div class="fb">
    <!-- 組出來的結果 -->
    <div class="fb-result">
      <span v-if="nodes.length" class="fb-formula">{{ display }}</span>
      <span v-else class="fb-empty">點下方元素開始組合</span>
      <button v-if="nodes.length" class="fb-clear" type="button" @click="clearAll">清空</button>
    </div>

    <!-- 已加入的節點：可就地調整數量、包成群組、刪除 -->
    <div v-if="nodes.length" class="fb-nodes">
      <FormulaNode
        v-for="(node, i) in nodes"
        :key="i"
        :node="node"
        @update="n => updateNode(i, n)"
        @remove="removeNode(i)"
      />
    </div>

    <!-- 選元素 -->
    <div class="fb-picker">
      <input
        class="input fb-search"
        type="text"
        v-model="query"
        aria-label="搜尋元素"
      />
      <div class="fb-elements">
        <button
          v-for="el in filtered"
          :key="el.Symbol"
          class="fb-element"
          type="button"
          :style="{ borderColor: '#' + el.CPKHexColor }"
          :title="el.Name"
          @click="addElement(el.Symbol)"
        >{{ el.Symbol }}</button>
      </div>
      <p v-if="!filtered.length" class="fb-hint">找不到符合的元素</p>
    </div>

    <div class="fb-actions">
      <button class="button secondary" type="button" :disabled="!nodes.length" @click="wrapInGroup">
        （ ）把目前內容包成群組
      </button>
      <span class="fb-note">群組用於 Ca(OH)₂ 這類需要括號的分子式</span>
    </div>
  </div>
</template>

<script>
// 視覺化組出分子式。互動方式參考運算式建構器：節點可就地編輯、
// 調數量、包成群組、刪除，結果即時序列化成可查詢的分子式。
import { elementsState, ensureElements } from '../store/elements'
import { toFormula, toDisplay, elementNode, groupNode } from '../utils/formula'
import FormulaNode from './FormulaNode.vue'

export default {
  components: { FormulaNode },
  props: {
    modelValue: { type: Array, default: () => [] }
  },
  emits: ['update:modelValue', 'change'],
  data() {
    return { query: '', elementsState }
  },
  computed: {
    nodes() {
      return this.modelValue
    },
    display() {
      return toDisplay(this.nodes)
    },
    formula() {
      return toFormula(this.nodes)
    },
    filtered() {
      const q = this.query.trim().toLowerCase()
      const all = this.elementsState.elements
      if (!q) return all
      return all.filter(e =>
        e.Symbol?.toLowerCase().startsWith(q) ||
        e.Name?.toLowerCase().includes(q) ||
        String(e.AtomicNumber) === q
      )
    }
  },
  created() {
    ensureElements()
  },
  methods: {
    emit(next) {
      this.$emit('update:modelValue', next)
      this.$emit('change', { nodes: next, formula: toFormula(next) })
    },
    addElement(symbol) {
      const next = [...this.nodes]
      const last = next[next.length - 1]
      // 連點同一個元素時直接加數量，比較符合直覺
      if (last && last.type === 'element' && last.symbol === symbol) {
        next[next.length - 1] = { ...last, count: last.count + 1 }
      } else {
        next.push(elementNode(symbol))
      }
      this.emit(next)
    },
    updateNode(i, node) {
      const next = [...this.nodes]
      next[i] = node
      this.emit(next)
    },
    removeNode(i) {
      const next = [...this.nodes]
      next.splice(i, 1)
      this.emit(next)
    },
    wrapInGroup() {
      this.emit([groupNode(this.nodes)])
    },
    clearAll() {
      this.emit([])
    }
  }
}
</script>

<style scoped>
.fb {
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 10px;
  padding: 14px;
  background: rgba(3, 1, 12, 0.35);
}

.fb-result {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 46px;
  padding: 8px 14px;
  border-radius: 8px;
  background: rgba(60, 40, 75, 0.4);
  margin-bottom: 12px;
}

.fb-formula {
  font-size: 26px;
  font-weight: 700;
  color: #e4fbff;
  letter-spacing: 0.02em;
  word-break: break-all;
}

.fb-empty {
  font-size: 13px;
  color: rgba(228, 251, 255, 0.35);
}

.fb-clear {
  margin-left: auto;
  border: none;
  background: none;
  font-family: inherit;
  font-size: 12px;
  color: rgba(228, 251, 255, 0.45);
  cursor: pointer;
  flex-shrink: 0;
}

.fb-clear:hover { color: #ff6b6b; }

.fb-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.fb-search {
  margin: 0 0 8px;
}

.fb-elements {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-height: 168px;
  overflow-y: auto;
  padding: 2px;
}

.fb-element {
  min-width: 40px;
  padding: 6px 8px;
  border: 1px solid;
  border-radius: 6px;
  background: rgba(60, 40, 75, 0.45);
  color: rgba(228, 251, 255, 0.9);
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.12s, transform 0.12s;
}

.fb-element:hover {
  background: rgba(100, 70, 120, 0.75);
  transform: translateY(-1px);
}

.fb-hint {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.35);
  margin: 8px 0 0;
}

.fb-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(228, 251, 255, 0.1);
}

.fb-note {
  font-size: 11px;
  color: rgba(228, 251, 255, 0.35);
}
</style>
