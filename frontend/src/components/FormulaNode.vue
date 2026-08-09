<template>
  <!-- 單一節點：元素或群組。群組會遞迴渲染子節點，因此可以巢狀 -->
  <span class="fn" :class="'fn--' + node.type">
    <template v-if="node.type === 'element'">
      <span class="fn-symbol">{{ node.symbol }}</span>
    </template>

    <template v-else>
      <span class="fn-paren">(</span>
      <FormulaNode
        v-for="(child, i) in node.children"
        :key="i"
        :node="child"
        @update="n => updateChild(i, n)"
        @remove="removeChild(i)"
      />
      <span class="fn-paren">)</span>
    </template>

    <span class="fn-count">
      <button class="fn-btn" type="button" title="減少" :disabled="node.count <= 1" @click="setCount(node.count - 1)">−</button>
      <span class="fn-num">{{ node.count }}</span>
      <button class="fn-btn" type="button" title="增加" @click="setCount(node.count + 1)">＋</button>
    </span>

    <button class="fn-btn fn-btn--del" type="button" title="刪除" @click="$emit('remove')">✕</button>
  </span>
</template>

<script>
export default {
  name: 'FormulaNode',
  props: {
    node: { type: Object, required: true }
  },
  emits: ['update', 'remove'],
  methods: {
    setCount(count) {
      if (count < 1) return
      this.$emit('update', { ...this.node, count })
    },
    updateChild(i, child) {
      const children = [...this.node.children]
      children[i] = child
      this.$emit('update', { ...this.node, children })
    },
    removeChild(i) {
      const children = [...this.node.children]
      children.splice(i, 1)
      // 群組空了就整個移除，避免留下空括號
      if (!children.length) return this.$emit('remove')
      this.$emit('update', { ...this.node, children })
    }
  }
}
</script>

<style scoped>
.fn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 7px;
  background: rgba(60, 40, 75, 0.4);
}

/* 群組用不同底色，巢狀時層次才看得出來 */
.fn--group {
  background: rgba(90, 70, 160, 0.28);
  border-color: rgba(157, 140, 255, 0.4);
  flex-wrap: wrap;
}

.fn-symbol {
  font-size: 15px;
  font-weight: 700;
  color: #e4fbff;
  padding: 0 2px;
}

.fn-paren {
  font-size: 15px;
  color: rgba(157, 140, 255, 0.9);
  font-weight: 700;
}

.fn-count {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding-left: 4px;
  border-left: 1px solid rgba(228, 251, 255, 0.12);
}

.fn-num {
  min-width: 16px;
  text-align: center;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.85);
  font-variant-numeric: tabular-nums;
}

.fn-btn {
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 4px;
  background: rgba(228, 251, 255, 0.08);
  color: rgba(228, 251, 255, 0.6);
  font-family: inherit;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.fn-btn:hover:not(:disabled) {
  background: rgba(228, 251, 255, 0.2);
  color: #e4fbff;
}

.fn-btn:disabled {
  opacity: 0.25;
  cursor: not-allowed;
}

.fn-btn--del:hover {
  background: rgba(255, 107, 107, 0.25);
  color: #ff6b6b;
}
</style>
