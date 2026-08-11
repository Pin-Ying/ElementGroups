<template>
  <div v-if="ai.enabled" class="ai-assist">
    <button class="ai-toggle" type="button" :class="{ active: open }" @click="open = !open">✧ AI 協助</button>

    <div v-if="open" class="ai-panel">
      <p class="ai-hint">
        {{ hint }}
        <template v-if="(draft || '').trim()">你目前已寫的內容會一併帶入，AI 會延伸潤飾而不是整段重寫。</template>
      </p>

      <template v-for="f in fields" :key="f.name">
        <label v-if="f.type === 'checkbox'" class="ai-check">
          <input type="checkbox" v-model="context[f.name]" />
          {{ f.label }}
        </label>
        <template v-else>
          <label class="label ai-label">{{ f.label }}</label>
          <textarea
            v-if="f.type === 'textarea'"
            class="textarea ai-reference"
            rows="3"
            v-model="context[f.name]"
            :aria-label="f.label"
          ></textarea>
          <input
            v-else
            class="input"
            type="text"
            v-model="context[f.name]"
            :placeholder="f.placeholder || ''"
            :aria-label="f.label"
          />
        </template>
      </template>

      <label class="label ai-label">風格／方向（選填）</label>
      <input class="input" type="text" v-model="direction" aria-label="風格方向" />

      <div class="ai-actions">
        <button class="button" type="button" :disabled="loading" @click="run">
          {{ loading ? '產生中…' : (suggestion ? '重新產生' : '產生建議') }}
        </button>
        <span v-if="ai.limit > 0" class="ai-quota">今日已用 {{ ai.used }} / {{ ai.limit }}</span>
      </div>

      <div v-if="suggestion" class="ai-result">
        <p class="preview-label">AI 建議（尚未套用）</p>
        <div class="ai-suggestion">{{ suggestion }}</div>
        <div class="ai-actions">
          <button class="button secondary" type="button" @click="apply('append')">附加到編輯框</button>
          <button class="button secondary" type="button" @click="apply('replace')">直接覆蓋</button>
          <button class="button secondary" type="button" @click="suggestion = ''">捨棄</button>
        </div>
        <p class="ai-note">套用後仍需按儲存才會真正寫入。</p>
      </div>
    </div>
  </div>
</template>

<script>
// 各處共用的 AI 協助面板（issue #26）。
//
// 原本元素故事與頁面內容各有一份幾乎一樣的面板；每多接一個地方就要再抄
// 一次。這裡把面板、額度顯示、套用方式收成一份，各用途的差異只剩
// utils/aiKinds.js 裡的欄位定義。
import { aiSuggest } from '../api'
import { aiKind, emptyAiContext } from '../utils/aiKinds'
import { showToast } from '../store/toast'

export default {
  props: {
    // 對應後端 SUGGEST_KINDS 的 key
    kind: { type: String, required: true },
    // 目前編輯框的內容，會帶給 AI 當延伸的基礎
    draft: { type: String, default: '' },
    // 呼叫端補充的 context（例如元素故事要帶 symbol），與面板欄位合併
    extra: { type: Object, default: () => ({}) },
    // AI 狀態（是否啟用、今日用量），由呼叫端傳入避免每個面板各抓一次
    ai: { type: Object, required: true }
  },
  emits: ['apply', 'used'],
  data() {
    return {
      open: false,
      loading: false,
      suggestion: '',
      direction: '',
      context: emptyAiContext(this.kind)
    }
  },
  computed: {
    def() {
      return aiKind(this.kind)
    },
    hint() {
      return this.def?.hint || ''
    },
    fields() {
      return this.def?.fields || []
    }
  },
  watch: {
    // 換了編輯對象就把上一次的輸入與建議清掉，避免張冠李戴
    extra: {
      deep: true,
      handler() {
        this.reset()
      }
    }
  },
  methods: {
    reset() {
      this.suggestion = ''
      this.direction = ''
      this.context = emptyAiContext(this.kind)
    },
    async run() {
      this.loading = true
      try {
        const res = await aiSuggest({
          kind: this.kind,
          context: { ...this.context, ...this.extra },
          draft: this.draft,
          direction: this.direction
        })
        this.suggestion = res.data.suggestion || ''
        this.$emit('used', { used: res.data.used, limit: res.data.limit })
      } catch (e) {
        showToast(e.response?.data?.message || 'AI 產生失敗', 'error')
      } finally {
        this.loading = false
      }
    },
    apply(mode) {
      this.$emit('apply', { text: this.suggestion, mode })
      this.suggestion = ''
    }
  }
}
</script>

<style scoped>
.ai-assist { display: contents; }
</style>
