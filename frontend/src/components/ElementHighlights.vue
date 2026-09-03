<template>
  <div v-if="hasAny" class="highlights">
    <div class="highlight-tabs">
      <button
        v-for="tab in availableTabs"
        :key="tab.key"
        class="highlight-tab"
        :class="{ active: mode === tab.key }"
        type="button"
        @click="mode = tab.key"
      >{{ tab.label }}</button>
    </div>

    <div v-if="current.length" class="highlight-row">
      <router-link
        v-for="el in current"
        :key="el.Symbol"
        class="highlight-card"
        :to="'/story/' + el.Symbol"
        :style="{ borderColor: '#' + el.CPKHexColor }"
      >
        <span class="hc-num">{{ el.AtomicNumber }}</span>
        <span class="hc-sym" :style="{ color: '#' + el.CPKHexColor }">{{ el.Symbol }}</span>
        <span class="hc-name">{{ el.Name }}</span>
        <span v-if="mode === 'popular'" class="hc-meta">{{ el.views }} 次瀏覽</span>
        <span v-else-if="el.updated_at" class="hc-meta">{{ relativeTime(el.updated_at) }}</span>
      </router-link>
    </div>
    <p v-else class="highlight-empty">{{ emptyHint }}</p>
  </div>
</template>

<script>
import { getRecentElements, getPopularElements } from '../api'

export default {
  data() {
    return {
      mode: 'recent',
      recent: [],
      popular: [],
      loaded: false
    }
  },
  computed: {
    availableTabs() {
      return [
        { key: 'recent', label: '最近更新' },
        { key: 'popular', label: '熱門元素' }
      ]
    },
    hasAny() {
      // 兩邊 API 都失敗（例如後端未部署）時整區隱藏
      return this.loaded
    },
    current() {
      return this.mode === 'popular' ? this.popular : this.recent
    },
    emptyHint() {
      return this.mode === 'popular'
        ? '還沒有瀏覽記錄，點進任一元素後就會開始統計'
        : '還沒有更新記錄，在後台儲存任一元素的故事後就會出現在這裡'
    }
  },
  async created() {
    // 兩邊都是次要資訊，任一失敗都不該影響週期表
    const [recentRes, popularRes] = await Promise.allSettled([
      getRecentElements(8),
      getPopularElements(8)
    ])
    if (recentRes.status === 'fulfilled') this.recent = recentRes.value.data.elements || []
    if (popularRes.status === 'fulfilled') this.popular = popularRes.value.data.elements || []
    this.loaded = recentRes.status === 'fulfilled' || popularRes.status === 'fulfilled'

    // 若沒有最近更新資料，預設切到有資料的那個分頁
    if (!this.recent.length && this.popular.length) this.mode = 'popular'
  },
  methods: {
    relativeTime(iso) {
      const then = new Date(iso)
      if (isNaN(then)) return ''
      const diff = Date.now() - then.getTime()
      const mins = Math.floor(diff / 60000)
      if (mins < 1) return '剛剛'
      if (mins < 60) return `${mins} 分鐘前`
      const hours = Math.floor(mins / 60)
      if (hours < 24) return `${hours} 小時前`
      const days = Math.floor(hours / 24)
      if (days < 30) return `${days} 天前`
      return then.toLocaleDateString('zh-TW')
    }
  }
}
</script>

<style scoped>
.highlights {
  max-width: 1100px;
  margin: 0 auto 18px;
  padding: 0 8px;
}

.highlight-tabs {
  display: flex;
  gap: 6px;
  justify-content: center;
  margin-bottom: 10px;
}

.highlight-tab {
  padding: 3px 14px;
  font-size: 12px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 999px;
  background: transparent;
  color: rgba(228, 251, 255, 0.5);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.highlight-tab:hover,
.highlight-tab.active {
  border-color: rgba(228, 251, 255, 0.5);
  color: rgba(228, 251, 255, 0.92);
  background: rgba(228, 251, 255, 0.08);
}

.highlight-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 2px 8px;
  scrollbar-width: thin;
}

.highlight-card {
  flex: 0 0 auto;
  width: 92px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 10px 6px;
  border: 1px solid;
  border-radius: 8px;
  background: rgba(60, 40, 75, 0.4);
  text-decoration: none;
  color: rgba(228, 251, 255, 0.85);
  transition: transform 0.15s, background 0.15s;
}

.highlight-card:hover {
  transform: translateY(-2px);
  background: rgba(100, 70, 120, 0.6);
}

.hc-num {
  font-size: 10px;
  opacity: 0.5;
  line-height: 1;
}

.hc-sym {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.15;
}

.hc-name {
  font-size: 11px;
  opacity: 0.75;
  text-align: center;
  line-height: 1.2;
  word-break: break-word;
}

.hc-meta {
  font-size: 10px;
  opacity: 0.45;
  margin-top: 2px;
}

.highlight-empty {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.35);
  text-align: center;
  margin: 10px 0 4px;
}
</style>
