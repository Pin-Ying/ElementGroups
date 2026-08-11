<template>
  <button v-if="ai.enabled" class="ai-toggle" type="button" :class="{ active: open }" @click="open = !open">
    ✧ AI 協助
  </button>

  <!-- 面板不能留在切換鈕旁邊：呼叫端多半把鈕放在 display:flex 的標題列裡，
       面板跟著進去就會被壓成細長一條。移到 body 上再用 fixed 定位在
       編輯區上方，版面不受呼叫端的容器影響 -->
  <Teleport v-if="ai.enabled && open" to="body">
    <div class="ai-backdrop" @click="open = false"></div>
    <div class="ai-panel--float">
      <div class="ai-head">
        <span class="ai-title">✧ AI 協助</span>
        <button class="ai-close" type="button" @click="open = false">✕</button>
      </div>
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
        <button class="button" type="button" :disabled="loading || exhausted" @click="run">
          {{ loading ? '產生中…' : (suggestion ? '重新產生' : '產生建議') }}
        </button>
        <span v-if="ai.limit > 0" class="ai-quota" :class="{ low: remaining <= 5, out: exhausted }">
          <template v-if="exhausted">今日額度已用完（{{ ai.limit }} 次），明天會重置</template>
          <template v-else>今日還可用 {{ remaining }} 次（共 {{ ai.limit }}）</template>
        </span>
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
  </Teleport>
</template>

<script>
// 各處共用的 AI 協助面板（issue #26）。
//
// 原本元素故事與頁面內容各有一份幾乎一樣的面板；每多接一個地方就要再抄
// 一次。這裡把面板、額度顯示、套用方式收成一份，各用途的差異只剩
// utils/aiKinds.js 裡的欄位定義。
import { aiSuggest } from '../api'
import { aiKind, emptyAiContext } from '../utils/aiKinds'
import { aiState, ensureAiStatus, setAiUsage } from '../store/ai'
import { showToast } from '../store/toast'

export default {
  props: {
    // 對應後端 SUGGEST_KINDS 的 key
    kind: { type: String, required: true },
    // 目前編輯框的內容，會帶給 AI 當延伸的基礎
    draft: { type: String, default: '' },
    // 呼叫端補充的 context（例如元素故事要帶 symbol），與面板欄位合併
    extra: { type: Object, default: () => ({}) }
  },
  emits: ['apply'],
  data() {
    return {
      open: false,
      loading: false,
      suggestion: '',
      direction: '',
      context: emptyAiContext(this.kind),
      // 額度是全站共用的，直接讀 store，不由呼叫端傳進來
      ai: aiState
    }
  },
  created() {
    ensureAiStatus()
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
    },
    // 額度是全站每天共用的，而現在有八個欄位掛著 AI，用完的機會比只有兩處時
    // 高得多。與其按下去才收到錯誤訊息，不如先把按鈕停掉並說明何時恢復
    remaining() {
      return Math.max(0, this.ai.limit - this.ai.used)
    },
    exhausted() {
      return this.ai.limit > 0 && this.remaining === 0
    },
    // 比對內容而不是物件本身：呼叫端多半是行內字面值或 computed，每次重繪
    // 都是新物件，deep watch 看的是來源引用，會在內容根本沒變時也重設
    extraKey() {
      return JSON.stringify(this.extra)
    }
  },
  watch: {
    // 換了編輯對象就把上一次的輸入與建議清掉，避免張冠李戴。
    // 面板開著時有遮罩擋住，底下的內容不會被改，所以不會打斷輸入到一半的人
    extraKey() {
      this.reset()
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
        setAiUsage(res.data.used, res.data.limit)
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

<style>
/* 這一段刻意不加 scoped：面板 teleport 到 body 之後不在元件的 DOM 子樹裡，
   scoped 樣式吃不到。原本這些規則散在 AdminView 與 StoryEditor 的 scoped
   區塊，隨著面板收成元件也一起搬過來，成為 AI 面板唯一的樣式來源。 */

/* 蓋住底下的內容，也提供點擊關閉的區域 */
.ai-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1090;
  background: rgba(0, 0, 0, 0.5);
}

.ai-panel--float {
  position: fixed;
  top: 10vh;
  left: 50%;
  transform: translateX(-50%);
  width: min(560px, 92vw);
  max-height: 80vh;
  overflow-y: auto;
  z-index: 1100;
  padding: 18px 20px;
  border: 1px solid rgba(157, 140, 255, 0.4);
  border-radius: 10px;
  /* 不能用半透明：浮在內容上方，透出去就看不清楚了 */
  background: rgb(24, 12, 42);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.6);
  text-align: left;
}

.ai-panel--float .ai-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.ai-panel--float .ai-title {
  font-size: 15px;
  font-weight: bold;
  color: #e4fbff;
}

.ai-panel--float .ai-close {
  background: none;
  border: none;
  color: rgba(228, 251, 255, 0.6);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.ai-panel--float .ai-hint {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.6);
  margin: 0 0 10px;
  line-height: 1.6;
}

.ai-panel--float .label {
  display: block;
  color: rgba(228, 251, 255, 0.82);
  margin: 10px 0 4px;
}

.ai-panel--float .ai-label { font-size: 12px; }

.ai-panel--float .ai-check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(228, 251, 255, 0.7);
  margin: 6px 0 10px;
  cursor: pointer;
}

.ai-panel--float .ai-check input { accent-color: #9d8cff; }
.ai-panel--float .ai-reference { min-height: 60px; }

.ai-panel--float .ai-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.ai-panel--float .ai-quota {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.5);
}

.ai-panel--float .ai-quota.low { color: #ffc46b; }
.ai-panel--float .ai-quota.out { color: #ff8f8f; }

.ai-panel--float .ai-result {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(228, 251, 255, 0.1);
}

.ai-panel--float .preview-label {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.5);
  margin: 0 0 6px;
}

.ai-panel--float .ai-suggestion {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.75;
  padding: 12px 14px;
  border-radius: 6px;
  background: rgba(3, 1, 12, 0.6);
  border: 1px solid rgba(228, 251, 255, 0.12);
  max-height: 300px;
  overflow-y: auto;
}

.ai-panel--float .ai-note {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.5);
  margin: 8px 0 0;
}
</style>