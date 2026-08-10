<template>
  <section v-if="hasContent" class="archetype">
    <h2 class="archetype-title">主族形象</h2>

    <div class="archetype-body">
      <div v-if="group.img_data" class="archetype-figure">
        <img :src="group.img_data" :alt="group.name || groupLabel" />
      </div>

      <div class="archetype-info">
        <p class="archetype-group">
          {{ groupLabel }}
          <span v-if="groupCommonName" class="archetype-common">{{ groupCommonName }}</span>
        </p>
        <p v-if="group.name" class="archetype-name">{{ group.name }}</p>
        <p v-if="group.description" class="archetype-desc">{{ group.description }}</p>
      </div>
    </div>
  </section>
</template>

<script>
// 元素頁的主族形象區塊：同族元素共用一套設計形象（issue #16）。
// 族別由週期表位置推得，形象內容從 _element_groups 取回並以族為單位快取。
import { getElementGroup } from '../api'
import { buildTableGroups } from '../utils/periodicTableGroups'
import { groupInfo } from '../utils/elementGroups'

const cache = new Map()

export default {
  props: {
    element: { type: Object, required: true }
  },
  data() {
    return { group: null }
  },
  computed: {
    groupKey() {
      if (!this.element?.Symbol) return ''
      const map = buildTableGroups([this.element])
      return map[this.element.Symbol] || ''
    },
    groupLabel() {
      return groupInfo(this.groupKey).label
    },
    groupCommonName() {
      return groupInfo(this.groupKey).name
    },
    hasContent() {
      const g = this.group
      return !!(g && (g.name || g.description || g.img_data))
    }
  },
  watch: {
    groupKey: { immediate: true, handler: 'load' }
  },
  methods: {
    async load(key) {
      if (!key) { this.group = null; return }
      if (cache.has(key)) {
        this.group = cache.get(key)
        return
      }
      try {
        const res = await getElementGroup(key)
        cache.set(key, res.data)
        if (this.groupKey === key) this.group = res.data
      } catch {
        cache.set(key, null)
        if (this.groupKey === key) this.group = null
      }
    }
  }
}
</script>

<style scoped>
.archetype {
  margin: 26px auto 0;
  width: 100%;
}

.archetype-title {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.14em;
  color: rgba(228, 251, 255, 0.5);
  text-align: left;
  margin: 0 0 12px;
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(228, 251, 255, 0.12);
}

.archetype-body {
  display: flex;
  gap: 18px;
  align-items: center;
  text-align: left;
}

.archetype-figure {
  flex: 0 0 110px;
}

.archetype-figure img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: contain;
}

.archetype-info {
  flex: 1;
  min-width: 0;
}

.archetype-group {
  font-size: 12px;
  letter-spacing: 0.12em;
  color: rgba(228, 251, 255, 0.45);
  margin: 0 0 4px;
}

.archetype-common {
  margin-left: 6px;
}

.archetype-name {
  font-size: 17px;
  font-weight: 700;
  color: #e4fbff;
  margin: 0 0 6px;
}

.archetype-desc {
  font-size: 14px;
  line-height: 1.8;
  color: rgba(228, 251, 255, 0.75);
  margin: 0;
  white-space: pre-wrap;
}

@media (max-width: 560px) {
  .archetype-body {
    flex-direction: column;
    align-items: flex-start;
  }
  .archetype-figure { flex-basis: auto; width: 130px; }
}
</style>
