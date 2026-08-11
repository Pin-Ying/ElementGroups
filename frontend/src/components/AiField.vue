<template>
  <div class="ai-field">
    <div class="label-row">
      <label class="label" :for="fieldId">{{ label }}</label>
      <span class="label-row-actions">
        <!-- 呼叫端額外要放的膠囊按鈕（語法說明、載入模板…） -->
        <slot name="actions"></slot>
        <AiAssist v-if="kind" :kind="kind" :draft="modelValue" :extra="extra" @apply="apply" />
      </span>
    </div>

    <p v-if="hint" class="field-hint">{{ hint }}</p>

    <textarea
      v-if="multiline"
      :id="fieldId"
      class="textarea"
      :rows="rows"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    ></textarea>
    <input
      v-else
      :id="fieldId"
      class="input"
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script>
// 一個「帶 AI 的文字欄位」（issue #26）。
//
// AiAssist 只給面板，標籤、輸入框、以及把建議寫回欄位的處理仍要各呼叫端
// 自己寫——結果三個地方各有一份幾乎一樣的 applyXxxSuggestion，連「附加時
// 要不要 trim」都寫得不一樣。而且面板放在 display:flex 的標籤列裡還被壓
// 成細長一條過一次。
//
// 這一層把標籤列、輸入框、套用邏輯一起收進來，呼叫端只要：
//
//   <AiField label="Story" kind="element-story" v-model="storyText"
//            :extra="{ symbol }" multiline :rows="6" />
//
// 新增一種 AI 用途仍要兩筆註冊：utils/aiKinds.js 定義要收哪些輸入，後端
// app/ai.py 的 SUGGEST_KINDS 定義提示怎麼組。那是前後端本質的分工（API
// key 只能在伺服器端、介面只能在瀏覽器端），不是可以消掉的重複。
//
// kind 留空就是一個普通欄位，不長 AI 按鈕——這樣同一個元件也能用在還沒
// 接 AI 的欄位上，版面才會一致。
import AiAssist from './AiAssist.vue'
import { showToast } from '../store/toast'

let seq = 0

export default {
  components: { AiAssist },
  props: {
    label: { type: String, required: true },
    // 對應 AI_KINDS / SUGGEST_KINDS 的 key；留空則不顯示 AI 按鈕
    kind: { type: String, default: '' },
    modelValue: { type: String, default: '' },
    // 這個 kind 需要的額外 context（例如元素故事要帶 symbol）
    extra: { type: Object, default: () => ({}) },
    multiline: { type: Boolean, default: false },
    rows: { type: [Number, String], default: 6 },
    placeholder: { type: String, default: '' },
    // 標籤下方的說明文字
    hint: { type: String, default: '' }
  },
  emits: ['update:modelValue'],
  data() {
    // label 與輸入框要靠 for/id 綁在一起才點得到，同一頁可能有多個欄位
    return { fieldId: `ai-field-${++seq}` }
  },
  methods: {
    // 附加會空一行接在現有內容後面，覆蓋則整段換掉。
    // 兩種都只改編輯框，仍要按儲存才會寫入。
    apply({ text, mode }) {
      if (!text) return
      const current = (this.modelValue || '').trim()
      const next = mode === 'replace' || !current ? text : `${current}\n\n${text}`
      this.$emit('update:modelValue', next)
      showToast('已套用到編輯框，記得儲存', 'success')
    }
  }
}
</script>

<style scoped>
/* .label-row / .textarea / .ai-toggle 來自 assets/forms.css，這裡只補
   這個元件自己的間距 */
.ai-field {
  margin-bottom: 4px;
}

.label {
  display: block;
  color: rgba(228, 251, 255, 0.82);
  font-size: 13px;
  margin: 10px 0 4px;
}
</style>
