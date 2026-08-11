// AI 建議各用途的輸入定義（issue #26）。
//
// 與後端 app/ai.py 的 SUGGEST_KINDS 用同一組 key 對應。分工是：
//
//   後端  這個 kind 的提示怎麼組（API key 在伺服器端，提示只能在那裡）
//   前端  這個 kind 要收哪些輸入、怎麼組成 context（介面只能在瀏覽器端）
//
// 這個切分是本質上的，不是可以消掉的重複。兩邊唯一的約定就是 key 字串
// 與 context 的欄位名稱。
//
// 要新增一個 AI 用途：這裡補一筆，後端補一個 builder。不必再寫端點，也
// 不必再做一組面板。

// 欄位型別：text 單行／textarea 多行／checkbox 勾選
export const AI_KINDS = {
  'element-story': {
    hint: '會自動帶入這個元素的週期表資料（原子序、分類、熔沸點等）。',
    fields: [
      { name: 'include_group', label: '帶入主族形象設定（後台「主族形象」的共同設計特色）', type: 'checkbox', default: false },
      { name: 'reference', label: '補充參考資料（選填）', type: 'textarea', default: '' }
    ]
  },
  'page-content': {
    hint: 'AI 會產生 Markdown 內容，適合時會用上本站的 :::cards、:::note 區塊。',
    fields: [
      { name: 'topic', label: '頁面主題', type: 'text', default: '', placeholder: '例如：介紹週期表的讀法' }
    ]
  },

  // 創作型：產生的是同族共用的設計語彙，不是化學知識
  'group-archetype': {
    hint: '會帶入這一族有哪些元素，以及你已經定的形象名稱。產生的是同族共用的設計特色。',
    fields: []
  },

  // 摘要型：從頁面既有內容濃縮，不自己發明
  'page-seo': {
    hint: '會帶入這個頁面的標題與目前的區塊內容，濃縮成一句搜尋結果會顯示的描述。',
    fields: []
  }
}

export function aiKind(key) {
  return AI_KINDS[key] || null
}

/** 依定義生出空白的輸入值。 */
export function emptyAiContext(key) {
  const def = aiKind(key)
  if (!def) return {}
  const out = {}
  for (const f of def.fields) out[f.name] = f.default
  return out
}
